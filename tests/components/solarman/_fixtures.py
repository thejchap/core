"""Tryke fixtures for Solarman tests."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from unittest.mock import AsyncMock, patch

from tryke import fixture

from homeassistant.components.solarman.const import CONF_SN, DOMAIN, MODEL_NAME_MAP
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_MODEL

from tests.common import MockConfigEntry, load_json_object_fixture

TEST_HOST = "192.168.1.100"
TEST_PORT = 8080
TEST_DEVICE_SN = "SN1234567890"
TEST_MODEL = "SP-2W-EU"
TEST_MAC = "AA:BB:CC:DD:EE:FF"


@contextmanager
def _patched_solarman(device_fixture: str) -> Generator[AsyncMock]:
    with (
        patch(
            "homeassistant.components.solarman.coordinator.Solarman",
            autospec=True,
        ) as mock_client,
        patch(
            "homeassistant.components.solarman.config_flow.Solarman",
            new=mock_client,
        ),
    ):
        client = mock_client.return_value
        client.get_config.return_value = load_json_object_fixture(
            f"{device_fixture}/config.json", DOMAIN
        )
        client.fetch_data.return_value = load_json_object_fixture(
            f"{device_fixture}/data.json", DOMAIN
        )
        yield client


@fixture
def mock_solarman_p1_2w() -> Generator[AsyncMock]:
    """Mock solarman client for P1-2W device."""
    with _patched_solarman("P1-2W") as client:
        yield client


@fixture
def mock_solarman_sp2w() -> Generator[AsyncMock]:
    """Mock solarman client for SP-2W-EU device."""
    with _patched_solarman("SP-2W-EU") as client:
        yield client


@fixture
def mock_config_entry_sp2w() -> MockConfigEntry:
    """Return the default mocked config entry for SP-2W-EU."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=f"{MODEL_NAME_MAP['SP-2W-EU']} ({TEST_HOST})",
        data={
            CONF_HOST: TEST_HOST,
            CONF_SN: TEST_DEVICE_SN,
            CONF_MODEL: "SP-2W-EU",
            CONF_MAC: TEST_MAC,
        },
        unique_id=TEST_DEVICE_SN,
    )
