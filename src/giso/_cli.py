import click


@click.command(
    no_args_is_help=True,
    context_settings={"ignore_unknown_options": True},
)
@click.argument("args", nargs=-1)
@click.option(
    "--update", help="Re-download the lookup dataset before querying it.", is_flag=True
)
def cli(args, update):
    # noinspection PyUnresolvedReferences
    """
    A simple command line tool to help with geocoding country/region ISO 3166-2 codes.

    Uses the dataset "ne_10m_admin_1_states_provinces" from https://github.com/nvkelso/natural-earth-vector

    Takes one of two inputs:

    1. A longitude/latitude coordinate pair. (Decimal degrees in WGS 1984 separated by a comma or a space.)
    Returns the corresponding ISO 3166-2 code.

        Example:

        \b
        >>> giso -122.2483823, 37.8245529
        US-CA

    2. A valid ISO 3166-2 code. Returns the corresponding geometry as Well-Known Text (WKT).

        Example:

       \b
        >>> giso US-CA
        MULTIPOLYGON (((-114.724285 32.712836, -114.764541 32.709839, [...]

    """
    if update:
        from ._core import update

        update(overwrite=True)
        if len(args) == 0:
            return None

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
        return None

    if iso_code:
        # click.echo(f"Geocoding: {iso_code}")
        from ._core import geocode

        result = geocode(iso_code)
        click.echo(str(result))
        return result
    elif x and y:
        # click.echo(f"Reverse geocoding: x={x}, y={y}")
        from ._core import reverse_geocode

        result = reverse_geocode(x, y)
        click.echo(str(result))
        return result
    else:
        raise RuntimeError


if __name__ == "__main__":
    cli()
