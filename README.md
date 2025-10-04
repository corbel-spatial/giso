[![PyPI - Version](https://img.shields.io/pypi/v/giso)](https://pypi.org/project/giso/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/giso)](https://pypi.org/project/giso/)
[![PyPI Downloads](https://static.pepy.tech/badge/giso/month)](https://pepy.tech/projects/giso)
[![License: MIT](https://img.shields.io/badge/License-MIT-lightgrey.svg?logo=)](https://github.com/corbel-spatial/giso/blob/main/LICENSE)
[![Pixi Badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/prefix-dev/pixi/main/assets/badge/v0.json)](https://pixi.sh)

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