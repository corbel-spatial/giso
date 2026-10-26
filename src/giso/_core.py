import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import rich_click as click
import sedonadb
import shapely
from sedonadb import dataframe as sdf

_DATA_DIR = (Path(__file__).parent / "data").absolute()
_DATA_FILE = (_DATA_DIR / "ne_10m_admin_1_states_provinces.parquet").absolute()
_DATA_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_1_states_provinces.geojson"


class Giso:
    """
    This class provides functionality to download, read, and geocode
    natural earth vector data.
    """

    def __init__(
        self,
        data_file: Path = _DATA_FILE,
        data_url: str = _DATA_URL,
        autoupdate: bool = False,
    ):
        self._data_file = Path(data_file)
        self._data_url = str(data_url)
        self._sd: sedonadb.context.SedonaContext = sedonadb.connect()

        if autoupdate:
            self.update()

        df = self._sd.read_parquet(self._data_file)
        df.to_view("subdivisions")

    def clear(self) -> None:
        """Clears the data file."""
        click.echo(f"Removing {_DATA_FILE}")
        self._data_file.unlink(missing_ok=True)
        click.echo("Done")

    def geocode(self, iso_3166_2: str) -> shapely.MultiPolygon | shapely.Polygon | None:
        """
        This function geocodes a location based on its ISO 3166-2 country code.
        It retrieves the corresponding geographic data from a GeoDataFrame and
        returns it as a GeoJSON feature. If no data is found, it prints a
        message to the console and returns None.
        """
        queried: sdf.DataFrame = self._sd.sql(
            f"SELECT geometry FROM subdivisions WHERE iso_3166_2 = '{iso_3166_2}'"
        )
        queried: pd.DataFrame = queried.to_pandas()
        if len(queried) >= 1:
            result: shapely.Polygon | shapely.MultiPolygon = queried["geometry"][0]
            return result
        else:
            return None

    def reverse_geocode(
        self, x: float, y: float, verbose: bool = False
    ) -> dict[str, str | float] | str | None:
        """
        This function performs a reverse geocode lookup using a GeoDataFrame.

        Args:
            x: The longitude coordinate of the point.
            y: The latitude coordinate of the point.
            verbose: Also return metadata
        """
        query_pt = gpd.GeoDataFrame(geometry=[shapely.Point(x, y)], crs="EPSG:4326")
        query_pt = self._sd.create_data_frame(query_pt)
        query_pt.to_view("query_pt")

        queried: sdf.DataFrame = self._sd.sql("""
            SELECT
                f.iso_3166_2,
                f.adm1_code,
                f.wikipedia,
                f.iso_a2,
                f.name,
                f.name_alt,
                f.name_local,
                f.type,
                f.type_en,
                f.code_local,
                f.code_hasc,
                f.postal,
                f.sov_a3,
                f.adm0_a3,
                f.adm0_label,
                f.latitude,
                f.longitude,
                f.admin,
                f.geonunit,
                f.gu_a3,
                f.gn_id,
                f.gn_name,
                f.gns_id,
                f.gns_name,
                f.gn_region,
                f.gn_a1_code,
                f.region_sub,
                f.sub_code,
                f.gns_lang,
                f.gns_adm1,
                f.gns_region,
                f.wikidataid,
                f.geometry
            FROM subdivisions f
                     JOIN query_pt ON ST_Intersects(f.geometry, query_pt.geometry)
            """)
        queried: pd.DataFrame = queried.to_pandas()
        self._sd.drop_view("query_pt")

        if len(queried) >= 1:
            if verbose:
                result = queried.drop(columns="geometry")
                result = result.to_json(orient="table")
                result = json.loads(result)["data"][0]
                assert isinstance(result, dict)
                del result["index"]
                return result
            else:
                result = queried["iso_3166_2"][0]
                assert isinstance(result, str)
                return result
        else:
            return None

    def update(
        self,
        src: str | Path | None = None,
        overwrite: bool = False,
        update_source: str | None = None,
    ) -> None:
        """
        Pulls from a public domain dataset on GitHub

        References:
            - https://github.com/nvkelso/natural-earth-vector
            - https://www.naturalearthdata.com/

        """

        if src is not None:
            self._data_file = Path(src)

        self._data_file = self._data_file.with_suffix(".parquet")

        if self._data_file.exists() and overwrite is False:
            return

        if overwrite:
            self.clear()

        src = self._data_url if update_source is None else update_source
        click.echo(f"Downloading {src} to {self._data_file}")
        gdf = gpd.read_file(src)
        gdf.to_parquet(self._data_file, compression="brotli")
        click.echo("Done!")


_inst = Giso()


def geocode(iso_3166_2: str) -> shapely.Polygon | shapely.MultiPolygon | None:
    return _inst.geocode(iso_3166_2=iso_3166_2)


def reverse_geocode(
    x: float, y: float, verbose: bool = False
) -> dict[str, str | float] | str | None:
    return _inst.reverse_geocode(x=x, y=y, verbose=verbose)


def update(
    src: str | Path | None = None,
    overwrite: bool = False,
    update_source: str | None = None,
) -> None:
    _inst.update(src=src, overwrite=overwrite, update_source=update_source)
