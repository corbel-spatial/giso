import os

import geopandas as gpd
import sedona.db
import shapely


_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
_DATA_FILE = os.path.join(_DATA_DIR, "ne_10m_admin_1_states_provinces.parquet")
_DATA_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_1_states_provinces.geojson"

__all__ = ["Giso", "clear", "geocode", "reverse_geocode", "update"]


def clear():
    """Clears the data directory and file.

    This function removes the data directory and its contents.
    It first checks if the data file exists and removes it if it does.
    Then, it checks if the data directory exists and removes it if it does.
    """
    if os.path.exists(_DATA_FILE):
        print(f"Removing {_DATA_FILE}")
        os.remove(_DATA_FILE)


class Giso:
    """
    This class provides functionality to download, read, and geocode
    natural earth vector data.
    """

    def __init__(
        self,
        data_file: str = _DATA_FILE,
        data_url: str = _DATA_URL,
        autoupdate: bool = True,
    ):
        self._data_file = data_file
        self._data_url = data_url
        self._sd: sedona.db.context.SedonaContext = sedona.db.connect()

        if autoupdate:
            self.update()

        if not os.path.exists(self._data_file):
            print("Giso object must be initialized with Giso.update()")
        else:
            df = self._sd.read_parquet(self._data_file)
            df.to_view("subdivisions")

    def geocode(
        self, iso_3166_2: str
    ) -> type[shapely.Polygon, shapely.MultiPolygon] | None:
        """
        This function geocodes a location based on its ISO 3166-2 country code.
        It retrieves the corresponding geographic data from a GeoDataFrame and
        returns it as a GeoJSON feature. If no data is found, it prints a
        message to the console and returns None.
        """
        queried: sedona.db.dataframe.DataFrame = self._sd.sql(
            f"SELECT geometry FROM subdivisions WHERE iso_3166_2 = '{iso_3166_2}'"
        )
        queried: gpd.GeoDataFrame = queried.to_pandas()
        if len(queried) >= 1:
            result: type[shapely.Polygon, shapely.MultiPolygon] = queried["geometry"][0]
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

        queried: sedona.db.dataframe.DataFrame = self._sd.sql(
            """
            SELECT
                subdivisions.iso_3166_2 as iso_3166_2,
                subdivisions.geometry as geometry
            FROM subdivisions
                     JOIN query_pt ON ST_Intersects(subdivisions.geometry, query_pt.geometry)
            """
        )
        queried: gpd.GeoDataFrame = queried.to_pandas()
        self._sd.drop_view("query_pt")

        if len(queried) >= 1:
            result = queried["iso_3166_2"][0]
            assert isinstance(result, str)
            return result
        else:
            return None

    def update(self, overwrite: bool = False) -> None:
        """
        Pulls from a public domain dataset on GitHub

        References:
            - https://github.com/nvkelso/natural-earth-vector
            - https://www.naturalearthdata.com/

        """
        data_dir = os.path.dirname(self._data_file)

        if os.path.exists(self._data_file):
            if not overwrite:
                # print("File already exists")
                return
            else:
                print(f"Removing {self._data_file}")
                os.remove(self._data_file)

        if not os.path.exists(data_dir):
            os.mkdir(data_dir)

        print(f"Downloading {self._data_url} to {self._data_file}")
        gdf = gpd.read_file(self._data_url)
        gdf.to_parquet(self._data_file, compression="brotli")

        try:
            assert os.path.exists(self._data_file)
            assert os.path.getsize(self._data_file) > 1000
        except AssertionError:
            raise ValueError(f"Invalid file {self._data_file}")

        print("Done!")


_inst = Giso()


def geocode(iso_3166_2: str) -> type[shapely.Polygon, shapely.MultiPolygon] | None:
    return _inst.geocode(iso_3166_2=iso_3166_2)


def reverse_geocode(x: float, y: float) -> str | None:
    return _inst.reverse_geocode(x=x, y=y)


def update(overwrite: bool = False):
    _inst.update(overwrite=overwrite)
