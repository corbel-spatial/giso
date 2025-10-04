import os

import pytest
import shapely

import giso
from giso._core import Giso  # noqa


data_url = os.path.abspath("./tests/data/ne_10m_admin_1_states_provinces.geojson")


@pytest.fixture
def g():
    g = Giso(data_url=data_url)
    return g


def test_init():
    g = Giso(data_url=data_url, autoupdate=True)
    g = Giso(data_url=data_url, autoupdate=False)


def test_update(g):
    g.update()
    giso.clear()
    os.rmdir(os.path.dirname(g._data_file))
    g.update()
    g.update()
    g.update(overwrite=True)


def test_geocode(g):
    assert isinstance(g.geocode("US-CA"), shapely.MultiPolygon)
    assert isinstance(giso.geocode("US-CA"), shapely.MultiPolygon)
    assert isinstance(g.geocode("US-PR"), shapely.MultiPolygon)
    assert isinstance(giso.geocode("US-PR"), shapely.MultiPolygon)
    assert isinstance(g.geocode("GB-LND"), shapely.Polygon)
    assert isinstance(giso.geocode("GB-LND"), shapely.Polygon)
    assert isinstance(g.geocode("SG-01"), shapely.Polygon)
    assert isinstance(giso.geocode("SG-01"), shapely.Polygon)
    assert g.geocode("") is None
    assert giso.geocode("") is None


def test_reverse_geocode(g):
    assert g.reverse_geocode(-122.2483823, 37.8245529) == "US-CA"
    assert giso.reverse_geocode(-122.2483823, 37.8245529) == "US-CA"
    assert g.reverse_geocode(-66.5830656, 18.2698972) == "US-PR"
    assert giso.reverse_geocode(-66.5830656, 18.2698972) == "US-PR"
    assert g.reverse_geocode(-0.0891538, 51.5134394) == "GB-LND"
    assert giso.reverse_geocode(-0.0891538, 51.5134394) == "GB-LND"
    assert g.reverse_geocode(103.8455041, 1.2936855) == "SG-01"
    assert giso.reverse_geocode(103.8455041, 1.2936855) == "SG-01"
    assert g.reverse_geocode(0, 0) is None
    assert giso.reverse_geocode(0, 0) is None
