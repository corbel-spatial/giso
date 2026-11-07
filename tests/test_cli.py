import pytest
import shapely
from click import Command
from click.testing import CliRunner
from hypothesis import given, settings
from hypothesis import strategies as st

from giso import _cli


@pytest.fixture
def clifn() -> Command:
    return _cli.cli


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


def test_args(cli_runner: CliRunner, clifn: Command) -> None:
    result = cli_runner.invoke(clifn, ["bad", "input"])
    assert "Invalid input" in result.output


def test_help(cli_runner: CliRunner, clifn: Command) -> None:
    result = cli_runner.invoke(clifn, "--help")
    assert result.exit_code == 0
    assert "Usage:" in result.output

    result = cli_runner.invoke(clifn, None)
    assert result.exit_code == 2
    assert "Usage:" in result.output

    result = cli_runner.invoke(clifn, [])
    assert result.exit_code == 2
    assert "Usage:" in result.output


def test_geocode(cli_runner: CliRunner, clifn: Command) -> None:
    result = cli_runner.invoke(clifn, "US-CA")
    assert result.exit_code == 0
    assert "POLYGON" in result.output

    result = cli_runner.invoke(clifn, "bad input")
    assert result.exit_code == 0
    assert "POLYGON" not in result.output


def test_reverse_geocode(cli_runner: CliRunner, clifn: Command) -> None:
    result = cli_runner.invoke(clifn, "-122.2483823, 37.8245529")
    assert result.exit_code == 0
    assert "US-CA" in result.output

    result = cli_runner.invoke(clifn, "-122.2483823,37.8245529")
    assert result.exit_code == 0
    assert "US-CA" in result.output

    result = cli_runner.invoke(clifn, "-122.2483823 37.8245529")
    assert result.exit_code == 0
    assert "US-CA" in result.output

    result = cli_runner.invoke(clifn, ["-122.2483823   37.8245529"])
    assert result.exit_code == 0
    assert "US-CA" in result.output

    result = cli_runner.invoke(clifn, ["-122.2483823", "37.8245529"])
    assert result.exit_code == 0
    assert "US-CA" in result.output

    result = cli_runner.invoke(clifn, ["-122.2483823,", "37.8245529"])
    assert result.exit_code == 0
    assert "US-CA" in result.output

    # Lat/Lon order (auto-detected)
    result = cli_runner.invoke(clifn, "37.8245529, -122.2483823")
    assert result.exit_code == 0
    assert "US-CA" in result.output

    # ArcGIS Pro Copy DD
    result = cli_runner.invoke(clifn, "37.824553N 122.248383W")
    assert result.exit_code == 0
    assert "US-CA" in result.output

    # ArcGIS Pro Copy DDM
    result = cli_runner.invoke(clifn, "37° 49.4732′N 122° 14.9030′W")
    assert result.exit_code == 0
    assert "US-CA" in result.output

    # ArcGIS Pro Copy DMS
    result = cli_runner.invoke(clifn, """37° 49′ 28.39″N 122° 14′ 54.18″W""")
    assert result.exit_code == 0
    assert "US-CA" in result.output

    # UTM
    result = cli_runner.invoke(clifn, "10S 566147 4186615")
    assert result.exit_code == 0
    assert "US-CA" in result.output

    # MGRS / USNG
    result = cli_runner.invoke(clifn, "10SEG6614786615")
    assert result.exit_code == 0
    assert "US-CA" in result.output

    result = cli_runner.invoke(clifn, ["10S", "EG", "6614", "8661"])
    assert result.exit_code == 0
    assert "US-CA" in result.output

    # CLI unquoted tokens for all coordinate formats
    # DD
    result = cli_runner.invoke(clifn, ["37.824553N", "122.248383W"])
    assert result.exit_code == 0
    assert "US-CA" in result.output

    result = cli_runner.invoke(clifn, ["37.824553", "N", "122.248383", "W"])
    assert result.exit_code == 0
    assert "US-CA" in result.output

    # DDM unquoted
    result = cli_runner.invoke(clifn, ["37°", "49.4732′", "N,", "122°", "14.9030′", "W"])
    assert result.exit_code == 0
    assert "US-CA" in result.output

    result = cli_runner.invoke(clifn, ["37", "49.4732", "N", "122", "14.9030", "W"])
    assert result.exit_code == 0
    assert "US-CA" in result.output

    result = cli_runner.invoke(clifn, ["37d", "49.4732m", "N", "122d", "14.9030m", "W"])
    assert result.exit_code == 0
    assert "US-CA" in result.output

    # DMS unquoted
    result = cli_runner.invoke(clifn, ["37°", "49′", "28.39″", "N,", "122°", "14′", "54.18″", "W"])
    assert result.exit_code == 0
    assert "US-CA" in result.output

    result = cli_runner.invoke(clifn, ["37", "49", "28.39", "N", "122", "14", "54.18", "W"])
    assert result.exit_code == 0
    assert "US-CA" in result.output

    result = cli_runner.invoke(clifn, ["37d", "49m", "28.39s", "N", "122d", "14m", "54.18s", "W"])
    assert result.exit_code == 0
    assert "US-CA" in result.output

    # UTM unquoted
    result = cli_runner.invoke(clifn, ["10S", "566147", "4186615"])
    assert result.exit_code == 0
    assert "US-CA" in result.output

    result = cli_runner.invoke(clifn, ["UTM", "Zone", "10N", "566147", "4186615"])
    assert result.exit_code == 0
    assert "US-CA" in result.output

    # GARS unquoted
    result = cli_runner.invoke(clifn, ["006", "AG", "39"])
    assert result.exit_code == 0
    assert "AQ-X01~" in result.output

    # GEOREF unquoted
    result = cli_runner.invoke(clifn, ["MKPG", "12", "04"])
    assert result.exit_code == 0
    assert "GB-WIL" in result.output

    result = cli_runner.invoke(clifn, "badinput")
    assert result.exit_code == 0
    assert "Invalid" in result.output

    result = cli_runner.invoke(clifn, "bad input")
    assert result.exit_code == 0
    assert "Invalid" in result.output

    result = cli_runner.invoke(clifn, ["bad", "input"])
    assert result.exit_code == 0
    assert "Invalid" in result.output

    result = cli_runner.invoke(clifn, ["bad", "input", "badinput"])
    assert result.exit_code == 0
    assert "Invalid" in result.output


def test_update(
    cli_runner: CliRunner, clifn: Command, test_data_url, tmp_data_file
) -> None:
    result = cli_runner.invoke(
        clifn, ["--update", "--update-source", test_data_url, "--src", tmp_data_file]
    )
    assert result.exit_code == 0


def test_version(cli_runner: CliRunner, clifn: Command) -> None:
    result = cli_runner.invoke(clifn, "--version")
    assert result.output.startswith("giso")
    assert result.exit_code == 0


def test_handle_result_geometry() -> None:
    _cli._handle_result(
        result=shapely.Polygon([[0, 0], [1, 0], [1, 1], [0, 1]]), to_json=True
    )


def test_handle_result_none() -> None:
    _cli._handle_result(result=None)


def test_handle_result_str(tmp_path) -> None:
    _cli._handle_result(result="some result", to_json=True, indent=2)


def test_handle_result_dict() -> None:
    _cli._handle_result(result={"iso_3166_2": "US-CA"}, to_json=True)


def test_handle_result_output(tmp_path) -> None:
    with open(tmp_path / "test.txt", "w") as f:
        _cli._handle_result(
            result="some result", output=f, overwrite=False, to_json=True, indent=2
        )

    with open(tmp_path / "test.txt", "w") as f:
        _cli._handle_result(
            result="some result", output=f, overwrite=False, to_json=True, indent=2
        )

    with open(tmp_path / "test.txt", "w") as f:
        _cli._handle_result(
            result="some result", output=f, overwrite=True, to_json=True, indent=2
        )


@settings(deadline=None)
@given(args=st.lists(st.text()))
def test_cli_fuzz(args: list[str]) -> None:
    # print(args)
    runner = CliRunner()
    runner.invoke(_cli.cli, args, catch_exceptions=False)


st_adversarial_coord = st.floats(allow_nan=True, allow_infinity=True).map(str)


@settings(deadline=None)
@given(lon=st_adversarial_coord, lat=st_adversarial_coord)
def test_cli_fuzz_coords(lon: str, lat: str) -> None:
    runner = CliRunner()
    runner.invoke(_cli.cli, [lon, lat], catch_exceptions=False)
