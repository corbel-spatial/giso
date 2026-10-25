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

    def reverse_geocode(self, x: float, y: float) -> str | None:
        """
        This function performs a reverse geocode lookup using a GeoDataFrame.

        Args:
            x: The longitude coordinate of the point.
            y: The latitude coordinate of the point.
        """
        query_pt = gpd.GeoDataFrame(geometry=[shapely.Point(x, y)], crs="EPSG:4326")
        query_pt = self._sd.create_data_frame(query_pt)
        query_pt.to_view("query_pt")

        queried: sdf.DataFrame = self._sd.sql("""
            SELECT
                subdivisions.iso_3166_2 as iso_3166_2,
                subdivisions.geometry as geometry
            FROM subdivisions
                     JOIN query_pt ON ST_Intersects(subdivisions.geometry, query_pt.geometry)
            """)
        queried: pd.DataFrame = queried.to_pandas()
        self._sd.drop_view("query_pt")

        if len(queried) >= 1:
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


def reverse_geocode(x: float, y: float) -> str | None:
    return _inst.reverse_geocode(x=x, y=y)


def update(
    src: str | Path | None = None,
    overwrite: bool = False,
    update_source: str | None = None,
) -> None:
    _inst.update(src=src, overwrite=overwrite, update_source=update_source)
