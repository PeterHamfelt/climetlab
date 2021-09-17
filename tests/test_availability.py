#!/usr/bin/env python3

# (C) Copyright 2021 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import pandas as pd
import pytest
import yaml

from climetlab.utils.availability import Availability, availability

s2s_config = """
ecmwf:
    param: ['2t', 'ci', 'gh', 'lsm', 'msl', 'q', 'rsn', 'sm100', 'sm20', 'sp', 'sst', 'st100', 'st20', 't', 'tcc', 'tcw', 'tp', 'ttr', 'u', 'v']
    number: 50
    alldates: {start: '2020-01-02', end: '2020-12-31', freq: 'w-thu'}
eccc:
    param: ['2t', 'ci', 'gh', 'lsm', 'msl', 'q', 'rsn', 'sp', 'sst', 't', 'tcc', 'tcw', 'tp', 'ttr', 'u', 'v']
    number: 20
    alldates: {start: '2020-01-02', end: '2020-12-31', freq: 'w-thu'}
ncep:
    param: ['2t', 'ci', 'gh', 'lsm', 'msl', 'q', 'sm100', 'sm20', 'sp', 'sst', 'st100', 'st20', 't', 'tcc', 'tcw', 'tp', 'ttr', 'u', 'v']
    number: 15
    alldates: {start: '2010-01-02', end: '2010-12-31', freq: 'w-thu'}
"""

import os

import pandas
import yaml

import climetlab as cml
import climetlab.utils
import climetlab.utils.conventions

C0 = [
    {"level": "500", "param": "Z", "step": "24"},
    {"level": "500", "param": "Z", "step": "36"},
    {"level": "500", "param": "Z", "step": "48"},
    {"level": "500", "param": "T", "step": "24"},
    {"level": "500", "param": "T", "step": "36"},
    {"level": "500", "param": "T", "step": "48"},
    {"level": "850", "param": "T", "step": "36"},
    {"level": "850", "param": "T", "step": "48"},
    {"level": "1000", "param": "Z", "step": "24"},
    {"level": "1000", "param": "Z", "step": "48"},
]


@availability(C0)
def func1(level, param, step):
    pass


def test_availability_1():
    func1("1000", "Z", "24")


@availability("availability.json")
def func2(level, param, step):
    pass


def test_availability_2():
    func2("1000", "Z", "24")


def test_availability_3():
    avail = Availability(C0)
    print(avail)


def test_s2s():
    config = yaml.safe_load(s2s_config)

    availability_list = []

    for k, v in config.items():
        dic = dict(origin=k)
        dic["date"] = [x.strftime("%Y-%m-%d") for x in pd.date_range(**v["alldates"])][
            :3
        ]
        dic["number"] = list(range(1, v["number"] + 1))
        dic["param"] = v["param"][:3]
        availability_list.append(dic)

    av = Availability(availability_list)
    print(av.tree())
    #
    #    with pytest.raises(ValueError):
    #        av.check(number=75)
    #    av.check(number=7)
    #
    #    av.check(number=30, origin='ecmwf')
    #    with pytest.raises(ValueError):
    #        av.check(number=30, origin='eccc')

    #   av.check(origin='ncep')
    av.check(origin="ncep", date="2020-01-09")


#    av.check(origin='ncep', date='2020-01-09',number=30 )
#    try:
#        av.check(number=30, origin='eccc')
#    except ValueError as e:
#        assert str(e)[:3] == 'No '


if __name__ == "__main__":
    from climetlab.testing import main

    main(globals())
