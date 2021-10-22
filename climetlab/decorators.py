# (C) Copyright 2021 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#
import inspect
import logging
import os
import threading
from functools import wraps

from climetlab.arg_manager import ArgsManager, AvailabilityWrapper, NormalizerWrapper
from climetlab.utils.availability import Availability

LOG = logging.getLogger(__name__)


def dict_args(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        m = []
        p = {}
        for q in args:
            if isinstance(q, dict):
                p.update(q)
            else:
                m.append(q)
        p.update(kwargs)
        return func(*m, **p)

    return wrapped


LOCK = threading.RLock()


def locked(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        with LOCK:
            return func(*args, **kwargs)

    return wrapped


def _make_norm_wrapper(name, values, **kwargs):
    from climetlab.normalize import _find_normaliser

    values = kwargs.pop("values", values)

    for k, v in kwargs.items():
        assert not k.startswith("_")

    norm = _find_normaliser(values)

    alias = kwargs.pop("alias", {})
    if alias:
        if not hasattr(norm, "alias"):
            raise ValueError(f"Normalizer {norm} does not accept argument alias")
        norm.alias = alias

    return NormalizerWrapper(name, norm)


def add_default_values_and_kwargs(args, kwargs, func):
    sig = inspect.signature(func)
    bnd = sig.bind(*args, **kwargs)

    print("bb", bnd.arguments)
    bnd.apply_defaults()
    print("bb", bnd.arguments)

    print("a", args)
    print("a", bnd.args)

    print("k", kwargs)
    print("k", bnd.kwargs)

    provided = inspect.getcallargs(func, *args, **kwargs)
    print()
    print(1, args, kwargs, func)
    print(provided)

    new_kwargs = {}

    for name, param in sig.parameters.items():
        # We don't support *args
        # for example this is not allowed
        # @normalize(...)
        # def foo(a, b, *args):
        #   pass
        msg = f"Positional *{name} not supported"
        assert param.kind is not param.VAR_POSITIONAL, msg

        # We support **kwargs
        # for example this is ok
        # @normalize(...)
        # def foo(a, b, **kwargs):
        #   pass
        if param.kind is param.VAR_KEYWORD:
            print("  Adding {param} because it is the VAR_KEYWORD")
            new_kwargs.update(provided.pop(name, {}))
            continue

        # value provided by user
        if name in provided:
            new_kwargs[name] = provided.pop(name)
            continue

        # do nothing if no default value
        if param.default is inspect.Parameter.empty:
            continue

        # add default values
        new_kwargs[name] = param.default
        LOG.debug(f"  ok -> adding {param} in kwargs")

    print(2, args, new_kwargs, func)

    # if "self" in new_kwargs.keys():
    # if hasattr(func, '__self__'):
    #    #    assert hasattr(func, '__self__'), func
    #    print("stolen self")
    #    LOG.debug("Stolen self")
    ##    args = [new_kwargs.pop("self")]
    #    args = [func.__self__]
    # else:
    #    assert not hasattr(func, "__self__"), func
    args = ()

    print(3, args, new_kwargs, func)
    LOG.debug("return", args, new_kwargs)
    return args, new_kwargs


class NormalizeDecorator(object):
    def __init__(self, name, values, **kwargs):
        self.transforms = [_make_norm_wrapper(name, values, **kwargs)]

    def __call__(self, func):
        if hasattr(func, "_args_manager"):
            args_manager = func._args_manager
            func = func.__wrapped__
        else:
            args_manager = ArgsManager(func)
            func._args_manager = args_manager

        args_manager.append_list(self.transforms)

        @wraps(func)
        def inner(*args, **kwargs):
            print("  arg_manager", args_manager)
            args, kwargs = add_default_values_and_kwargs(args, kwargs, func)
            args, kwargs = args_manager(args, kwargs)
            print(f"calling {func} kwargs={kwargs}")
            # kwargs = kwargs['kwargs']
            return func(*args, **kwargs)

        return inner


normalize = NormalizeDecorator


class AvailabilityDecorator(object):
    def __init__(self, avail):
        from climetlab.normalize import _find_normaliser

        if isinstance(avail, str):
            if not os.path.isabs(avail):
                caller = os.path.dirname(inspect.stack()[1].filename)
                avail = os.path.join(caller, avail)

        avail = Availability(avail)

        self.transforms = []

        for key, value in avail.unique_values().items():
            print(key, value)
            norm = _find_normaliser(value)
            self.transforms.append(NormalizerWrapper(key, norm))

        self.transforms.append(AvailabilityWrapper(avail))

    def __call__(self, func):
        if hasattr(func, "_args_manager"):
            args_manager = func._args_manager
            func = func.__wrapped__
        else:
            args_manager = ArgsManager(func)
            func._args_manager = args_manager

        args_manager.append_list(self.transforms)

        @wraps(func)
        def inner(*args, **kwargs):
            args, kwargs = add_default_values_and_kwargs(args, kwargs, func)
            args, kwargs = args_manager(args, kwargs)
            return func(*args, **kwargs)

        return inner


availability = AvailabilityDecorator


def normalize_args(**kwargs):
    # TODO: dead code

    LOG.error("@normalize_arg is obsolete")
    print("@normalize_arg is obsolete")

    from climetlab.normalize import _find_normaliser

    args_wrappers = []

    availability = kwargs.pop("_availability", None)
    if availability is not None:
        args_wrappers.append(AvailabilityWrapper(availability))

    alias = kwargs.pop("_alias", {})

    for k, v in kwargs.items():
        norm = _find_normaliser(v)
        if hasattr(norm, "alias"):
            norm.alias = alias.get(k, None)
        args_wrappers.append(NormalizerWrapper(k, norm))

    def outer(func):

        args_manager = ArgsManager.from_func(func, disable=True)
        args_manager.append(args_wrappers)
        LOG.debug("Normalizers: %s", args_manager)

        @wraps(func)
        def inner(*args, **kwargs):
            provided = inspect.getcallargs(func, *args, **kwargs)
            for name, param in inspect.signature(func).parameters.items():
                # See https://docs.python.org/3.5/library/inspect.html#inspect.signature
                assert param.kind is not param.VAR_POSITIONAL
                if param.kind is param.VAR_KEYWORD:
                    provided.update(provided.pop(name, {}))

            #_other = provided.pop("self", None)

            args, provided = args_manager.apply((), provided)

            #if _other is not None:
            #    provided["self"] = _other

            return func(*args, **provided)

        inner._args_manager = args_manager

        return inner

    return outer
