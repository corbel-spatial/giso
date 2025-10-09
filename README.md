[![PyPI - Version](https://img.shields.io/pypi/v/giso)](https://pypi.org/project/giso/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/giso)](https://pypi.org/project/giso/)
[![PyPI Downloads](https://static.pepy.tech/badge/giso/month)](https://pepy.tech/projects/giso)
[![License: MIT](https://img.shields.io/badge/License-MIT-lightgrey.svg?logo=)](https://github.com/corbel-spatial/giso/blob/main/LICENSE)
[![Pixi](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2Fprefix-dev%2Fpixi%2Fmain%2Fassets%2Fbadge%2Fv0.json&label=%E2%9C%A8)](https://pixi.sh)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

[![Actions Workflow Status: Test Python Prerelease](https://img.shields.io/github/actions/workflow/status/corbel-spatial/giso/py-prerelease.yml?label=3.15.0a0
)](https://github.com/corbel-spatial/giso/actions/workflows/py-prerelease.yml)
[![GitHub Actions Workflow Status: Linux](https://img.shields.io/github/actions/workflow/status/corbel-spatial/giso/pytest-linux.yml?label=Linux&logo=linux&logoColor=white)](https://github.com/corbel-spatial/giso/actions/workflows/pytest-linux.yml)
[![GitHub Actions Workflow Status: Windows](https://img.shields.io/github/actions/workflow/status/corbel-spatial/giso/pytest-windows.yml?label=Windows)](https://github.com/corbel-spatial/giso/actions/workflows/pytest-windows.yml)
[![GitHub Actions Workflow Status: macOS](https://img.shields.io/github/actions/workflow/status/corbel-spatial/giso/pytest-macos.yml?label=macOS)](https://github.com/corbel-spatial/giso/actions/workflows/pytest-macos.yml)
[![GitHub Actions Workflow Status: Black](https://img.shields.io/github/actions/workflow/status/corbel-spatial/giso/lint.yml?label=Black%20%26%20Ruff)](https://github.com/corbel-spatial/giso/actions/workflows/lint.yml)
[![Test Coverage: SlipCover](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fcorbel-spatial%2Fgiso%2Frefs%2Fheads%2Fmain%2Fdocs%2Fpytest_coverage.json&query=%24.summary.percent_covered_display&label=Coverage%20%25&color=brightgreen)](https://github.com/corbel-spatial/giso/actions/workflows/coverage.yml)
# giso

A simple command line tool to help with geocoding country/region [ISO 3166-2](https://en.wikipedia.org/wiki/ISO_3166-2) codes.

Includes a public domain reference dataset from [Natural Earth Data](https://github.com/nvkelso/natural-earth-vector)
which is stored in [GeoParquet](https://geoparquet.org/) format and is accessed with [SedonaDB](https://sedona.apache.org/sedonadb/latest/).

## Installation

```shell
python -m pip install giso
```

## Basic Usage

`giso` takes one of two inputs:

- A longitude/latitude coordinate pair. (Decimal degrees in WGS 1984 separated by a comma or a space.)
Returns the corresponding ISO 3166-2 code.

```shell
giso -122.2483823, 37.8245529
# US-CA
```

- A valid ISO 3166-2 code. Returns the corresponding geometry as Well-Known Text (WKT).

```shell
giso US-CA
# MULTIPOLYGON (((-114.724285 32.712836, -114.764541 32.709839, [...]
```

Returns `None` if there are no hits.

`giso` can also be used as a Python package:

```python
>>> import giso
>>> giso.reverse_geocode(103.8455041, 1.2936855)
'SG-01'
>>> giso.geocode("SG-01")
< POLYGON((103.898 1.305, 103.888 1.301, 103.853 1.277, 103.847 1.272, 103.8 ... >
```


## References

- [Natural Earth Data homepage](https://www.naturalearthdata.com/)
