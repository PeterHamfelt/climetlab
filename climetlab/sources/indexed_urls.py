# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from climetlab import load_source

from .multi import MultiSource


class IndexedUrls(MultiSource):
    def __init__(
        self,
        index,
        request,
        *args,
        filter=None,
        merger=None,
        force=None,
        split_method="minimum-split",
        **kwargs,
    ):

        urls_parts = index.lookup_request(request, split_method=split_method)

        sources = []
        for url, parts in urls_parts:
            source = load_source(
                "url",
                url=url,
                parts=parts,
                filter=filter,
                merger=merger,
                force=force,
                # Load lazily so we can do parallel downloads
                lazily=True,
                **kwargs,
            )
            sources.append(source)
        if not sources:
            raise ValueError("Empty request: no match.")

        super().__init__(sources, filter=filter, merger=merger)


source = IndexedUrls