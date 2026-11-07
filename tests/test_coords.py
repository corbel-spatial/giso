import math
from typing import Any

import pytest

from giso import parse_coordinates

# Canonical test coordinates:
# Oakland, CA coordinates in different formats
OAKLAND_LON = -122.2483823
OAKLAND_LAT = 37.8245529

# DMS representation: 37° 49' 28.39" N, 122° 14' 54.18" W
DMS_EXPECTED_LAT = 37.0 + 49.0 / 60.0 + 28.39 / 3600.0
DMS_EXPECTED_LON = -(122.0 + 14.0 / 60.0 + 54.18 / 3600.0)

# DDM representation: 37° 49.473' N, 122° 14.903' W
DDM_EXPECTED_LAT = 37.0 + 49.473 / 60.0
DDM_EXPECTED_LON = -(122.0 + 14.903 / 60.0)


@pytest.mark.parametrize(
    ("coord_input", "expected_lon", "expected_lat", "tol"),
    [
        # Standard Decimal Degrees (comma, space, semicolon, brackets, slashes)
        ("-122.2483823, 37.8245529", OAKLAND_LON, OAKLAND_LAT, 1e-6),
        ("-122.2483823 37.8245529", OAKLAND_LON, OAKLAND_LAT, 1e-6),
        ("-122.2483823; 37.8245529", OAKLAND_LON, OAKLAND_LAT, 1e-6),
        ("(-122.2483823, 37.8245529)", OAKLAND_LON, OAKLAND_LAT, 1e-6),
        ("[-122.2483823, 37.8245529]", OAKLAND_LON, OAKLAND_LAT, 1e-6),
        (" \t -122.2483823,   37.8245529 \n", OAKLAND_LON, OAKLAND_LAT, 1e-6),
        # Range autodetect (abs > 90 must be longitude)
        ("37.8245529, -122.2483823", OAKLAND_LON, OAKLAND_LAT, 1e-6),
        ("37.8245529 -122.2483823", OAKLAND_LON, OAKLAND_LAT, 1e-6),
        ("37.8245529 / -122.2483823", OAKLAND_LON, OAKLAND_LAT, 1e-6),
        # Hemisphere tags and orientations
        ("37.8245529° N, 122.2483823° W", OAKLAND_LON, OAKLAND_LAT, 1e-6),
        ("37.8245529N, 122.2483823W", OAKLAND_LON, OAKLAND_LAT, 1e-6),
        ("37.8245529 N 122.2483823 W", OAKLAND_LON, OAKLAND_LAT, 1e-6),
        ("122.2483823 W, 37.8245529 N", OAKLAND_LON, OAKLAND_LAT, 1e-6),
        ("122.2483823 W / 37.8245529 N", OAKLAND_LON, OAKLAND_LAT, 1e-6),
        ("N37.8245529, W122.2483823", OAKLAND_LON, OAKLAND_LAT, 1e-6),
        ("N 37.8245529, W 122.2483823", OAKLAND_LON, OAKLAND_LAT, 1e-6),
        ("33.8688 S, 151.2093 E", 151.2093, -33.8688, 1e-6),
        # ArcGIS Pro Copy DD format: Y0.0#####N X0.0#####E
        ("37.824553N 122.248383W", -122.248383, 37.824553, 1e-5),
        # Compact unspaced DD formats
        ("37.824553N122.248383W", -122.248383, 37.824553, 1e-5),
        ("N37.824553W122.248383", -122.248383, 37.824553, 1e-5),
        ("+37.824553-122.248383", -122.248383, 37.824553, 1e-5),
    ],
)
def test_decimal_degrees(coord_input: str, expected_lon: float, expected_lat: float, tol: float) -> None:
    res = parse_coordinates(coord_input)
    assert res is not None, f"Failed to parse DD: {coord_input}"
    lon, lat = res
    assert math.isclose(lon, expected_lon, abs_tol=tol)
    assert math.isclose(lat, expected_lat, abs_tol=tol)


@pytest.mark.parametrize(
    ("coord_input", "expected_lon", "expected_lat", "tol"),
    [
        ("""37° 49' 28.39" N, 122° 14' 54.18" W""", DMS_EXPECTED_LON, DMS_EXPECTED_LAT, 1e-5),
        ("37° 49′ 28.39″ N, 122° 14′ 54.18″ W", DMS_EXPECTED_LON, DMS_EXPECTED_LAT, 1e-5),
        ("""37°49'28.39"N 122°14'54.18"W""", DMS_EXPECTED_LON, DMS_EXPECTED_LAT, 1e-5),
        ("37° 49′ 28.39″N 122° 14′ 54.18″W", DMS_EXPECTED_LON, DMS_EXPECTED_LAT, 1e-5),
        ("37d 49m 28.39s N, 122d 14m 54.18s W", DMS_EXPECTED_LON, DMS_EXPECTED_LAT, 1e-5),
        ("37:49:28.39N, 122:14:54.18W", DMS_EXPECTED_LON, DMS_EXPECTED_LAT, 1e-5),
        ("""+37° 49' 28.39", -122° 14' 54.18\"""", DMS_EXPECTED_LON, DMS_EXPECTED_LAT, 1e-5),
        ("""-122° 14' 54.18", +37° 49' 28.39\"""", DMS_EXPECTED_LON, DMS_EXPECTED_LAT, 1e-5),
        ("""37°49'28.39"N122°14'54.18"W""", DMS_EXPECTED_LON, DMS_EXPECTED_LAT, 1e-5),
        (r"37° 49\' 28.39\" N, 122° 14\' 54.18\" W", DMS_EXPECTED_LON, DMS_EXPECTED_LAT, 1e-5),
        # Unit letter 's' for seconds must not be confused with hemisphere 'S'
        # Default order (lon, lat) applies when neither coordinate has hemisphere tags
        (
            "48d 51m 24s, 2d 21m 7s",
            48.0 + 51.0 / 60.0 + 24.0 / 3600.0,
            2.0 + 21.0 / 60.0 + 7.0 / 3600.0,
            1e-5,
        ),
    ],
)
def test_dms(coord_input: str, expected_lon: float, expected_lat: float, tol: float) -> None:
    res = parse_coordinates(coord_input)
    assert res is not None, f"Failed to parse DMS: {coord_input}"
    lon, lat = res
    assert math.isclose(lon, expected_lon, abs_tol=tol)
    assert math.isclose(lat, expected_lat, abs_tol=tol)


@pytest.mark.parametrize(
    ("coord_input", "expected_lon", "expected_lat", "tol"),
    [
        ("37° 49.473' N, 122° 14.903' W", DDM_EXPECTED_LON, DDM_EXPECTED_LAT, 1e-5),
        ("37°49.473'N 122°14.903'W", DDM_EXPECTED_LON, DDM_EXPECTED_LAT, 1e-5),
        ("37 49.473 N, 122 14.903 W", DDM_EXPECTED_LON, DDM_EXPECTED_LAT, 1e-5),
        ("37d 49.473m N, 122d 14.903m W", DDM_EXPECTED_LON, DDM_EXPECTED_LAT, 1e-5),
        ("37:49.473 N, 122:14.903 W", DDM_EXPECTED_LON, DDM_EXPECTED_LAT, 1e-5),
        # ArcGIS Pro Copy DDM: A0° B0.0#####′N X0° Y0.0#####′E
        (
            "37° 49.4732′N 122° 14.9030′W",
            -(122.0 + 14.9030 / 60.0),
            37.0 + 49.4732 / 60.0,
            1e-4,
        ),
        # Unhemisphered DDM defaults to (lon, lat)
        ("48° 51.4′ 2° 21.1′", 48.0 + 51.4 / 60.0, 2.0 + 21.1 / 60.0, 1e-4),
    ],
)
def test_ddm(coord_input: str, expected_lon: float, expected_lat: float, tol: float) -> None:
    res = parse_coordinates(coord_input)
    assert res is not None, f"Failed to parse DDM: {coord_input}"
    lon, lat = res
    assert math.isclose(lon, expected_lon, abs_tol=tol)
    assert math.isclose(lat, expected_lat, abs_tol=tol)


@pytest.mark.parametrize(
    ("coord_input", "expected_lon", "expected_lat", "tol"),
    [
        # ArcGIS Pro UTM copy formats (Zone 10, Latitude Band S = Northern hemisphere 32-40N)
        ("10S 566147 4186615", -122.24838, 37.82455, 1e-4),
        ("10N 566147 4186615", -122.24838, 37.82455, 1e-4),
        ("10 566147mE 4186615mN", -122.24838, 37.82455, 1e-4),
        ("Zone 10N 566147 4186615", -122.24838, 37.82455, 1e-4),
        ("UTM Zone 10N 566147 4186615", -122.24838, 37.82455, 1e-4),
        ("UTM 10N 566147 4186615", -122.24838, 37.82455, 1e-4),
        ("10 North 566147 4186615", -122.24838, 37.82455, 1e-4),
        # True Southern hemisphere UTM (Sydney Opera House: Zone 56 South)
        ("56 South 334863 6252431", 151.2149, -33.8555, 1e-3),
        ("UTM Zone 56S 334863 6252431", 151.2149, -33.8555, 1e-3),
    ],
)
def test_utm(coord_input: str, expected_lon: float, expected_lat: float, tol: float) -> None:
    res = parse_coordinates(coord_input)
    assert res is not None, f"Failed to parse UTM: {coord_input}"
    lon, lat = res
    assert math.isclose(lon, expected_lon, abs_tol=tol)
    assert math.isclose(lat, expected_lat, abs_tol=tol)


@pytest.mark.parametrize(
    ("coord_input", "expected_lon", "expected_lat", "tol"),
    [
        # MGRS / USNG Oakland, CA
        ("10SEG6614786615", -122.24838, 37.82455, 1e-4),
        ("10S EG 6614 8661", -122.24838, 37.82455, 1e-3),
        # MGRS Paris Eiffel Tower
        ("31UDQ4825211932", 2.2945, 48.8582, 1e-3),
        # MGRS Southern hemisphere: Blue Mountains, Australia
        ("56HKH12345678", 149.8933, -33.7900, 1e-3),
        # GARS
        ("006AG", -177.25, -86.75, 0.5),
        ("006AG39", -177.25, -86.75, 0.5),
        # GEOREF
        ("MKPG1204", -1.7917, 51.075, 1e-3),
        ("GJPJ3417", -76.425, 38.2917, 1e-3),
    ],
)
def test_military_grids(coord_input: str, expected_lon: float, expected_lat: float, tol: float) -> None:
    res = parse_coordinates(coord_input)
    assert res is not None, f"Failed to parse Grid format: {coord_input}"
    lon, lat = res
    assert math.isclose(lon, expected_lon, abs_tol=tol)
    assert math.isclose(lat, expected_lat, abs_tol=tol)


@pytest.mark.parametrize(
    ("args", "expected_lon", "expected_lat", "tol"),
    [
        # Space-separated DMS without quotes or symbols
        (("37", "49", "28.39", "N", "122", "14", "54.18", "W"), DMS_EXPECTED_LON, DMS_EXPECTED_LAT, 1e-5),
        # Hemisphere prefix unquoted
        (("N", "37°", "49′", "28.39″", "W", "122°", "14′", "54.18″"), DMS_EXPECTED_LON, DMS_EXPECTED_LAT, 1e-5),
        # 4 numbers space delimited (DDM)
        (("48", "51.4", "2", "21.1"), 48.0 + 51.4 / 60.0, 2.0 + 21.1 / 60.0, 1e-4),
        # 6 numbers space delimited (DMS)
        (("48", "51", "24", "2", "21", "07"), 48.0 + 51.0 / 60.0 + 24.0 / 3600.0, 2.0 + 21.0 / 60.0 + 7.0 / 3600.0, 1e-4),
        # Unquoted UTM paste
        (("10S", "566147", "4186615"), -122.24838, 37.82455, 1e-4),
        # Unquoted USNG paste
        (("10S", "EG", "6614", "8661"), -122.24838, 37.82455, 1e-3),
        # Unquoted ArcGIS Pro DD paste
        (("37.824553N", "122.248383W"), -122.248383, 37.824553, 1e-5),
    ],
)
def test_unquoted_shell_paste(args: tuple[Any, ...], expected_lon: float, expected_lat: float, tol: float) -> None:
    res = parse_coordinates(*args)
    assert res is not None, f"Failed to parse unquoted args: {args}"
    lon, lat = res
    assert math.isclose(lon, expected_lon, abs_tol=tol)
    assert math.isclose(lat, expected_lat, abs_tol=tol)


@pytest.mark.parametrize(
    ("args", "expected_lon", "expected_lat"),
    [
        # Two numeric float arguments
        ((-122.2483823, 37.8245529), OAKLAND_LON, OAKLAND_LAT),
        # Two numeric float arguments with range autodetect (abs > 90)
        ((37.8245529, -122.2483823), OAKLAND_LON, OAKLAND_LAT),
        # Integer coordinates at origin
        ((0, 0), 0.0, 0.0),
        # Single tuple containing floats
        (((-122.2483823, 37.8245529),), OAKLAND_LON, OAKLAND_LAT),
        # Single list containing floats
        (([-122.2483823, 37.8245529],), OAKLAND_LON, OAKLAND_LAT),
        # Two string arguments
        (("-122.2483823", "37.8245529"), OAKLAND_LON, OAKLAND_LAT),
        (("37.8245529", "-122.2483823"), OAKLAND_LON, OAKLAND_LAT),
    ],
)
def test_numeric_and_container_inputs(args: tuple[Any, ...], expected_lon: float, expected_lat: float) -> None:
    res = parse_coordinates(*args)
    assert res is not None, f"Failed to parse numeric/container: {args}"
    lon, lat = res
    assert math.isclose(lon, expected_lon, abs_tol=1e-6)
    assert math.isclose(lat, expected_lat, abs_tol=1e-6)


@pytest.mark.parametrize(
    "invalid_input",
    [
        "",
        "   ",
        "not coordinates",
        # ISO-3166-2 codes must not be parsed as coordinates
        "US-CA",
        "CA-ON",
        "GB-LND",
        # Out-of-range latitude (> 90)
        "95.0 N, 120.0 W",
        # Out-of-range longitude (> 180)
        "37.0 N, 195.0 W",
        # Duplicate axes
        "37.0 N, 45.0 N",
        "120.0 W, 10.0 E",
        # Minutes or seconds >= 60
        "37° 75' N, 122° 10' W",
        """37° 45' 80" N, 122° 10' 30" W""",
        # Non-finite values
        "nan, 37.0",
        "inf, 37.0",
    ],
)
def test_invalid_inputs(invalid_input: str) -> None:
    assert parse_coordinates(invalid_input) is None, f"Input should be invalid: {invalid_input}"
