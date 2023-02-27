# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

import torch

LOG = logging.getLogger(__name__)


def _find_device():
    if torch.backends.mps.is_available() and torch.backends.mps.is_built():
        return "mps"
    if torch.cuda.is_available() and torch.backends.cuda.is_built():
        return "cuda"
    LOG.debug("Found no GPU, using CPU")
    return "cpu"


device = _find_device()
