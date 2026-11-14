import json

import pytest

from src.config import METADATA_PATH


@pytest.fixture(scope="session")
def schema():
    return json.loads(METADATA_PATH.read_text())["feature_schema"]
