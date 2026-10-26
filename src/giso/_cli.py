import json
from pathlib import Path
from typing import IO

import rich_click as click
import shapely


def _handle_result(
    result: shapely.MultiPolygon | shapely.Polygon | dict | str | None,
    output: IO | None = None,
    overwrite: bool = False,
    to_json: bool = False,
    indent: int = 0,
) -> None:
    if result is None:
        click.echo("No results")
        return

    if indent < 1:
        out_indent = None
    else:
        out_indent = indent

    if to_json:
        if isinstance(result, (shapely.MultiPolygon, shapely.Polygon)):
            result = shapely.to_geojson(result, indent=out_indent)
        elif isinstance(result, dict):
            result = json.dumps(result, indent=out_indent)
        elif isinstance(result, str):
            pass
        else:
            raise TypeError(result)  # pragma: no cover
    else:
        result = str(result)

    assert isinstance(result, str), result

    if output:
        fp = Path(output.name).absolute()
        if not overwrite and fp.exists():
            click.echo("Output file already exists, retry with --overwrite flag")
            return

        click.echo(f"Writing output to '{fp.as_posix()}'")
        output.write(result)
        output.close()
        click.echo("Done!")
    else:
        click.echo(result)


@click.command(no_args_is_help=True, context_settings={"ignore_unknown_options": True})
@click.argument("args", nargs=-1)
@click.option(
    "--output",
    "-o",
    type=click.File(mode="w", lazy=True),
    default=None,
    help="Save the output to a file instead of stdout.",
)
@click.option(
    "--overwrite",
    "-w",
    is_flag=True,
    default=False,
    help="Overwrite an existing output file.",
)
@click.option(
    "--to-json",
    "-j",
    is_flag=True,
    default=False,
    help="Provide results in JSON format.",
)
@click.option(
    "--indent",
    "-i",
    type=int,
    default=0,
    show_default=True,
    help="Indent level for JSON output.",
)
@click.option(
    "--update",
    type=bool,
    default=False,
    is_flag=True,
    hidden=True,
    help="Re-download the lookup dataset before querying it.",
)
@click.option(
    "--update-source",
    type=str,
    default=None,
    hidden=True,
    help="URL or path to a source dataset .geojson to be converted to .parquet - only use in addition to the --update flag",
)
@click.option(
    "--src",
    type=str,
    default=None,
    hidden=True,
    help="URL or path to a source dataset .parquet for use in this lookup operation",
)
@click.version_option(package_name="giso", prog_name="giso")
def cli(
    args: list[str],
    output: IO | None,
    overwrite: bool,
    to_json: bool,
    indent: int,
    update: bool,
    update_source: str | None,
    src: str | None,
) -> None:
    """
    A simple command line tool to help with geocoding country/region ISO 3166-2 codes.

    Takes one of two inputs:

    - A longitude/latitude coordinate pair. Returns the corresponding ISO 3166-2 code, if found. Example:

        > giso -122.2483823, 37.8245529

        US-CA

    - A valid ISO 3166-2 code. Returns the corresponding geometry as Well-Known Text (WKT). Example:

        > giso US-CA

        MULTIPOLYGON (((-114.724285 32.712836, -114.764541 32.709839, [...]
"""
    if update:
        from ._core import update as _update

        _update(src=src, overwrite=True, update_source=update_source)
        if len(args) == 0:
            return

    iso_code, x, y = None, None, None
    try:
        if len(args) == 1:
            arg = args[0]
            if "-" in arg and not arg.startswith("-"):  # geocode
                iso_code = arg.strip().upper()
                assert len(iso_code.split("-")) == 2
            elif "," in arg:  # reverse geocode comma delimited
                coordinates = arg.split(",")
                x, y = map(float, coordinates)

            elif " " in arg:  # reverse geocode space delimited
                while "  " in arg:
                    arg = arg.replace("  ", " ")
                coordinates = arg.split(" ")
                x, y = map(float, coordinates)
            else:
                assert False

        elif len(args) == 2:  # reverse geocode
            x = float(args[0].strip(","))
            y = float(args[1].strip(","))

        else:
            assert False

    except (AssertionError, ValueError):
        click.echo(
            "Invalid input: Please provide either a valid ISO 3166-2 code "
            "or a comma/space-separated longitude/latitude pair.",
            err=True,
        )
        return

    if iso_code:
        # click.echo(f"Geocoding: {iso_code}")
        from ._core import geocode

        result = geocode(iso_code)
        _handle_result(result, output, overwrite, to_json, indent)

        return

    elif x and y:
        # click.echo(f"Reverse geocoding: x={x}, y={y}")
        from ._core import reverse_geocode

        result = reverse_geocode(x, y, to_json)
        _handle_result(result, output, overwrite, to_json, indent)

        return


if __name__ == "__main__":
    cli()  # pragma: no cover
