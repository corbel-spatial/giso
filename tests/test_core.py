import shapely

import giso


def test_init(tmp_data_file, test_data_url) -> None:
    g = giso.Giso(data_file=tmp_data_file, data_url=test_data_url)
    assert isinstance(g, giso.Giso)


def test_init_autoupdate(tmp_data_file, test_data_url):
    g = giso.Giso(data_file=tmp_data_file, data_url=test_data_url, autoupdate=True)
    assert isinstance(g, giso.Giso)


def test_update(g: giso.Giso) -> None:
    g.update()


def test_update_clear(g: giso.Giso) -> None:
    g.clear()


def test_update_overwrite(g: giso.Giso) -> None:
    g.update(overwrite=True)


def test_geocode(g: giso.Giso) -> None:
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


def test_reverse_geocode(g: giso.Giso) -> None:
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
