from pathlib import Path
from types import GeneratorType

import pytest

import giso

DATA_NAME = "ne_10m_admin_1_states_provinces"


@pytest.fixture(scope="session")
def test_data_url() -> str:
    return (Path(__file__).parent / "data" / f"{DATA_NAME}.geojson").as_posix()


@pytest.fixture(scope="session")
def tmp_data_file(tmp_path_factory) -> Path:
    temp_dir = tmp_path_factory.mktemp("session_data")
    return temp_dir / f"{DATA_NAME}.parquet"


@pytest.fixture(scope="session")
def g(tmp_data_file: Path, test_data_url: str) -> GeneratorType:
    g = giso.Giso(data_file=tmp_data_file, data_url=test_data_url)
    yield g
