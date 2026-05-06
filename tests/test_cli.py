import pytest
from click import Command
from click.testing import CliRunner

from giso._cli import cli  # noqa


@pytest.fixture
def clifn() -> Command:
    return cli  # noqa


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


def test_args(cli_runner: CliRunner, clifn: Command) -> None:
    result = cli_runner.invoke(clifn, ["bad", "input"])
    assert "Invalid input" in result.output


def test_help(cli_runner: CliRunner, clifn: Command) -> None:
    result = cli_runner.invoke(clifn, ["--help"])
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


def test_update(cli_runner: CliRunner, clifn: Command) -> None:
    result = cli_runner.invoke(clifn, "--update")
    assert result.exit_code == 0
