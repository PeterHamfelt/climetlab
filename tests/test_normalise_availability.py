#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import pytest

from climetlab.decorators import availability, normalize
from climetlab.utils.availability import Availability

C1 = [
    {"level": "500", "param": "a", "step": "24"},
    {"level": "500", "param": "a", "step": "36"},
    {"level": "500", "param": "a", "step": "48"},
    {"level": "500", "param": "b", "step": "24"},
    {"level": "500", "param": "b", "step": "36"},
    {"level": "500", "param": "b", "step": "48"},
    {"level": "850", "param": "b", "step": "36"},
    {"level": "850", "param": "b", "step": "48"},
    {"level": "1000", "param": "a", "step": "24"},
    {"level": "1000", "param": "a", "step": "48"},
]

C2 = [
    {"level": 500, "param": "a", "step": 24},
    {"level": 500, "param": "a", "step": 36},
    {"level": 500, "param": "a", "step": 48},
    {"level": 500, "param": "b", "step": 24},
    {"level": 500, "param": "b", "step": 36},
    {"level": 500, "param": "b", "step": 48},
    {"level": 850, "param": "b", "step": 36},
    {"level": 850, "param": "b", "step": 48},
    {"level": 1000, "param": "a", "step": 24},
    {"level": 1000, "param": "a", "step": 48},
]


av_decorator = availability(C1)
av = Availability(C1)


@av_decorator
def func_a(level, param, step):
    return param


class Klass_a:
    @av_decorator
    def __init__(self, level, param, step):
        pass


class Klass_n:
    @normalize("param", ["a", "b", "c"])
    def __init__(self, level, param, step):
        pass


class Klass_a_n:
    @normalize("param", ["a", "b"])
    @av_decorator
    def __init__(self, level, param, step):
        pass


class Klass_n_a:
    @av_decorator
    @normalize("param", ["a", "b"])
    def __init__(self, level, param, step):
        pass


@normalize("param", ["a", "b", "c"])
def func_n(level, param, step):
    return param


@normalize("param", ["a", "b"])
@av_decorator
def func_a_n(level, param, step):
    return param


@av_decorator
@normalize("param", ["a", "b"])
def func_n_a(level, param, step):
    return param


@pytest.mark.parametrize(
    "func",
    [
        func_a,
        # func_n is excluded.
        func_n_a,
        # func_a_n, # TODO
        Klass_a,
        # Klass_n is excluded.
        Klass_n_a,
        # Klass_a_n, # TODO
    ],
)
def test_avail_1(func):
    func(level="1000", param="a", step="24")
    with pytest.raises(ValueError):
        func(level="1032100", param="a", step="24")


@pytest.mark.parametrize(
    "func",
    [func_n, Klass_n],
)
def test_avail_n(func):
    func(level="1000", param="a", step="24")
    func(level="1032100", param="a", step="24")


@pytest.mark.parametrize(
    "func",
    [
        func_a,
        func_n,
        func_n_a,
        # func_a_n,
        Klass_a,
        Klass_n,
        Klass_n_a,
        # Klass_a_n,
    ],
)
def test_norm(func):
    func(level="1000", param="a", step="24")

    with pytest.raises(ValueError):
        func(level="1000", param="zz", step="24")


def test_avail_norm_setup():
    @normalize("param", ["a", "b"])
    @availability(C1)
    def func1(param):
        return param

    @normalize("param", ["unk1", "unk2"])
    @availability(C1)
    def func2(param):
        return param

    with pytest.raises(Exception):

        @normalize("param", ["A", "B"])
        @normalize("step", [24, 36])
        @normalize("param", ["a", "b"])
        def func3(param, step):
            return param

        assert func3("a", 24) == ["a"]

    with pytest.raises(ValueError):

        @normalize("param", ["A", "B"])
        @availability(C1)
        def func5(param):
            return param

        assert func5(param="A") == ["A"]

    @av_decorator
    @normalize("param", ["a", "b"])
    @availability(C1)
    def func6(param):
        return param

    assert func6(param="A") == ["a"]


def test_availability_1():
    @availability(C1)
    def func7(param, step=24):
        return param

    func7("a", step="36")
    # with pytest.raises(ValueError, match=r"Invalid value .*"):
    with pytest.raises(ValueError, match=r"invalid combination .*"):
        func7(3, step="36")


# @availability(C1)
@normalize("level", type=int, multiple=False)
@normalize("param", type=str, multiple=True)
@normalize("step", type=int, multiple=True)
def param_values_1(level, param, step):
    return (level, param, step)


@normalize("level", type=int, multiple=False)
@normalize("param", type=str, multiple=True)
@normalize("step", type=int, multiple=True)
# @availability(C1)
def param_values_2(level, param, step):
    return (level, param, step)


# No type
@availability(C1)
@normalize("level", multiple=False)
@normalize("param", multiple=True)
@normalize("step", multiple=True)
def param_values_3(level, param, step):
    return (level, param, step)


@availability(C2)
@normalize("level", multiple=False)
@normalize("param", multiple=True)
@normalize("step", multiple=True)
def param_values_4(level, param, step):
    return (level, param, step)


def test_dev():

    print("---", param_values_1("1000", "a", "24"))
    assert param_values_1("1000", "a", "24") == (1000, ["a"], [24])

    print("---", param_values_2("1000", "a", "24"))
    assert param_values_2("1000", "a", "24") == (1000, ["a"], [24])

    print("---", param_values_3("1000", "a", "24"))
    assert param_values_3("1000", "a", "24") == ("1000", ["a"], ["24"])

    print("---", param_values_4("1000", "a", "24"))
    assert param_values_4("1000", "a", "24") == (1000, ["a"], [24])


if __name__ == "__main__":
    # test_dev()
    from climetlab.testing import main

    main(__file__)
