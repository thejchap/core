"""Tryke fixtures for the Hong Kong Observatory integration."""

import json
from collections.abc import Generator
from unittest.mock import patch

from tryke import fixture

from tests.common import load_fixture


@fixture
def hko_config_flow_connect() -> Generator[None]:
    """Mock valid config flow setup."""
    with patch(
        "homeassistant.components.hko.config_flow.HKO.weather",
        return_value=json.loads(load_fixture("hko/rhrread.json")),
    ):
        yield
