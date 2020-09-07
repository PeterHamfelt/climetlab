# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import os
import yaml
import getpass
from climetlab.utils.html import css
import logging
from typing import Callable


LOG = logging.getLogger(__name__)

DOT_CLIMETLAB = os.path.expanduser("~/.climetlab")

SETTINGS_AND_HELP = {
    "cache-directory": (
        "/var/tmp/climetlab-%s" % (getpass.getuser(),),
        """Directory of where the dowloaded files are cached, with ``${USER}`` is the user id.
        See :ref:`caching` for more information.""",
    ),
    "styles-directories": (
        [os.path.join(DOT_CLIMETLAB, "styles")],
        """See :ref:`styles` for more information.""",
    ),
    "projections-directories": (
        [os.path.join(DOT_CLIMETLAB, "projections")],
        """See :ref:`projections` for more information.""",
    ),
    "layers-directories": (
        [os.path.join(DOT_CLIMETLAB, "layers")],
        """See :ref:`layers` for more information.""",
    ),
    "plotting-options": ({}, """Dictionary of default plotting options.
                         See :ref:`plotting` for more information."""),
}

DEFAULTS = {}
for k, v in SETTINGS_AND_HELP.items():
    DEFAULTS[k] = v[0]


NONE = object()


class Settings:
    def __init__(self, settings_yaml: str, defaults: dict):
        self._defaults = defaults
        self._settings = dict(**defaults)
        self._callbacks = []
        self._settings_yaml = settings_yaml
        self._pytest = None

    def get(self, name: str, default=NONE):
        """[summary]

        Args:
            name (str): [description]
            default ([type], optional): [description]. Defaults to NONE.

        Returns:
            [type]: [description]
        """

        self._check_pytest()

        if default is NONE:
            return self._settings[name]

        return self._settings.get(name, default)

    def set(self, name: str, value):
        """[summary]

        Args:
            name (set): [description]
            value ([type]): [description]
        """
        self._settings[name] = value
        self._changed()

    def reset(self, name: str = None):
        """Reset setting(s) to default values.

        Args:
            name (str, optional): The name of the setting to reset to default. If the setting does not have a default, it is removed. If `None` is passed, all settings are reset to their default values. Defaults to None.
        """
        if name is None:
            self._settings = dict(**DEFAULTS)
        else:
            self._settings.pop(name, None)
            if name in DEFAULTS:
                self._settings[name] = DEFAULTS[name]
        self._changed()

    def _repr_html_(self):
        html = [css("table")]
        html.append("<table class='climetlab'>")
        for k, v in sorted(self._settings.items()):
            html.append(
                "<tr><td>%s</td><td>%r</td><td>%r</td></td>"
                % (k, v, SETTINGS_AND_HELP.get(k, (None, "..."))[0])
            )
        html.append("</table>")
        return "".join(html)

    def _changed(self):
        self._save()
        for cb in self._callbacks:
            cb()

    def on_change(self, callback: Callable[[], None]):
        self._callbacks.append(callback)

    def _save(self):
        # Don't persist changes when running pytest
        if "PYTEST_CURRENT_TEST" in os.environ:
            return

        try:
            with open(self._settings_yaml, "w") as f:
                yaml.dump(self._settings, f, default_flow_style=False)
        except Exception:
            LOG.error(
                "Cannot save CliMetLab settings (%s)",
                self._settings_yaml,
                exc_info=True,
            )

    def _check_pytest(self):
        # We don't want the settings to persist between tests
        if os.environ.get("PYTEST_CURRENT_TEST") != self._pytest:
            self._pytest = os.environ.get("PYTEST_CURRENT_TEST")
            self._settings = dict(**self._defaults)


try:
    if not os.path.exists(DOT_CLIMETLAB):
        os.mkdir(DOT_CLIMETLAB, 0o700)

    settings_yaml = os.path.expanduser("~/.climetlab/settings.yaml")
    if not os.path.exists(settings_yaml):
        with open(settings_yaml, "w") as f:
            yaml.dump(DEFAULTS, f, default_flow_style=False)

except Exception:
    LOG.error(
        "Cannot create CliMetLab settings directory, using defaults (%s)",
        settings_yaml,
        exc_info=True,
    )


settings = dict(**DEFAULTS)
try:
    with open(settings_yaml) as f:
        s = yaml.load(f, Loader=yaml.SafeLoader)
        settings.update(s)

except Exception:
    LOG.error(
        "Cannot load CliMetLab settings (%s), reverting to defaults",
        settings_yaml,
        exc_info=True,
    )

SETTINGS = Settings(settings_yaml, settings)
