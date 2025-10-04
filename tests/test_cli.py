import click
import pytest
from click.testing import CliRunner
from giso._cli import cli  # noqa


cli: click.Command


@pytest.fixture
def cli_runner():
    return CliRunner()


def test_help(cli_runner):
    result = cli_runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output

    result = cli_runner.invoke(cli, None)
    assert result.exit_code == 2
    assert "Usage:" in result.output

    result = cli_runner.invoke(cli, [])
    assert result.exit_code == 2
    assert "Usage:" in result.output


def test_geocode(cli_runner):
    result = cli_runner.invoke(cli, "US-CA")
    assert result.exit_code == 0
    assert "POLYGON" in result.output

    result = cli_runner.invoke(cli, "bad input")
    assert result.exit_code == 0
    assert "POLYGON" not in result.output


def test_reverse_geocode(cli_runner):
    result = cli_runner.invoke(cli, "-122.2483823, 37.8245529")
    assert result.exit_code == 0
    assert "US-CA" in result.output

    result = cli_runner.invoke(cli, "-122.2483823,37.8245529")
    assert result.exit_code == 0
    assert "US-CA" in result.output

    result = cli_runner.invoke(cli, "-122.2483823 37.8245529")
    assert result.exit_code == 0
    assert "US-CA" in result.output

    result = cli_runner.invoke(cli, ["-122.2483823   37.8245529"])
    assert result.exit_code == 0
    assert "US-CA" in result.output

    result = cli_runner.invoke(cli, ["-122.2483823", "37.8245529"])
    assert result.exit_code == 0
    assert "US-CA" in result.output

    result = cli_runner.invoke(cli, ["-122.2483823,", "37.8245529"])
    assert result.exit_code == 0
    assert "US-CA" in result.output

    result = cli_runner.invoke(cli, "badinput")
    assert result.exit_code == 0
    assert "Invalid" in result.output

    result = cli_runner.invoke(cli, "bad input")
    assert result.exit_code == 0
    assert "Invalid" in result.output

    result = cli_runner.invoke(cli, ["bad", "input"])
    assert result.exit_code == 0
    assert "Invalid" in result.output

    result = cli_runner.invoke(cli, ["bad", "input", "badinput"])
    assert result.exit_code == 0
    assert "Invalid" in result.output


def test_update(cli_runner):
    result = cli_runner.invoke(cli, "--update")
