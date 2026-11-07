import json
import re
from pathlib import Path
from typing import IO

import rich_click as click
import shapely

from ._coords import parse_coordinates

click.rich_click.TEXT_MARKUP = "rich"


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

    \u00a0

    Takes one of two inputs:


    - A [bold yellow]coordinate[/bold yellow] in any of the following formats. Returns the corresponding ISO 3166-2 code, if found.

        [bold]Decimal Degrees (DD):[/bold]
        [green]> giso -122.2483823, 37.8245529[/green]
        [green]> giso 37.8245529N 122.2483823W[/green]

        [bold]Degrees Decimal Minutes (DDM):[/bold]
        [green]> giso 37° 49.473′ N, 122° 14.903′ W[/green]
        [green]> giso 37 49.473 N, 122 14.903 W[/green]

        [bold]Degrees Minutes Seconds (DMS):[/bold]
        [green]> giso 37° 49′ 28.4″ N, 122° 14′ 54.2″ W[/green]
        [green]> giso 37 49 28.4 N, 122 14 54.2 W[/green]

        [bold]Universal Transverse Mercator (UTM):[/bold]
        [green]> giso 10S 566147 4186615[/green]
        [green]> giso UTM Zone 10N 566147 4186615[/green]

        [bold]Military Grid Reference System (MGRS) / US National Grid (USNG):[/bold]
        [green]> giso 10SEG6614786615[/green]
        [green]> giso 10S EG 6614 8661[/green]

        [bold]Global Area Reference System (GARS):[/bold]
        [green]> giso 006AG39[/green]

        [bold]World Geographic Reference System (GEOREF):[/bold]
        [green]> giso MKPG1204[/green]

        Quotes or escapes are not needed for any coordinate format.


    - A valid [bold yellow]ISO 3166-2 code[/bold yellow]. Returns the corresponding geometry as Well-Known Text (WKT).

        [green]> giso US-CA

        MULTIPOLYGON (((-114.724285 32.712836, -114.764541 32.709839, [...][/green]
    """
    if update:
        from ._core import update as _update

        _update(src=src, overwrite=True, update_source=update_source)
        if len(args) == 0:
            return

    if len(args) == 0:
        return

    # Check if input is an ISO 3166-2 code (e.g. US-CA, SG-01, GB-LND)
    if len(args) == 1 and re.fullmatch(r"[A-Za-z]{2}-[A-Za-z0-9]{1,3}", args[0].strip()):
        from ._core import geocode

        iso_code = args[0].strip().upper()
        result = geocode(iso_code)
        _handle_result(result, output, overwrite, to_json, indent)
        return

    # Attempt to parse as coordinates
    coords = parse_coordinates(*args)
    if coords is not None:
        from ._core import reverse_geocode

        x, y = coords
        result = reverse_geocode(x, y, to_json)
        _handle_result(result, output, overwrite, to_json, indent)
        return

    click.echo(
        "Invalid input: Please provide either a valid ISO 3166-2 code "
        "or a supported coordinate format.",
        err=True,
    )
    return


if __name__ == "__main__":
    cli()  # pragma: no cover
