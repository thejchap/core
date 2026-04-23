"""Tryke fixtures for Indevolt tests."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, patch

from tryke import fixture

from homeassistant.components.indevolt.const import (
    CONF_GENERATION,
    CONF_SERIAL_NUMBER,
    DOMAIN,
)
from homeassistant.const import CONF_HOST, CONF_MODEL

from tests.common import MockConfigEntry, load_json_object_fixture

TEST_HOST = "192.168.1.100"
TEST_PORT = 8080
TEST_DEVICE_SN_GEN1 = "BK1600-12345678"
TEST_DEVICE_SN_GEN2 = "SolidFlex2000-87654321"
TEST_FW_VERSION = "1.2.3"

DEVICE_MAPPING = {
    1: {
        "device": "BK1600",
        "generation": 1,
        "sn": TEST_DEVICE_SN_GEN1,
    },
    2: {
        "device": "CMS-SF2000",
        "generation": 2,
        "sn": TEST_DEVICE_SN_GEN2,
    },
}

DEFAULT_GENERATION = 2


@fixture
def entry_data() -> dict[str, Any]:
    """Return the config entry data based on generation."""
    device_info = DEVICE_MAPPING[DEFAULT_GENERATION]
    return {
        CONF_HOST: TEST_HOST,
        CONF_SERIAL_NUMBER: device_info["sn"],
        CONF_MODEL: device_info["device"],
        CONF_GENERATION: device_info["generation"],
    }


@fixture
def mock_config_entry(
    entry_data: dict[str, Any] = None,
) -> MockConfigEntry:
    """Return the default mocked config entry."""
    device_info = DEVICE_MAPPING[DEFAULT_GENERATION]
    data = entry_data if entry_data is not None else {
        CONF_HOST: TEST_HOST,
        CONF_SERIAL_NUMBER: device_info["sn"],
        CONF_MODEL: device_info["device"],
        CONF_GENERATION: device_info["generation"],
    }
    return MockConfigEntry(
        domain=DOMAIN,
        title=device_info["device"],
        version=1,
        data=data,
        unique_id=device_info["sn"],
    )


@fixture
def mock_indevolt() -> Generator[AsyncMock]:
    """Mock an IndevoltAPI client."""
    device_info = DEVICE_MAPPING[DEFAULT_GENERATION]
    fixture_data = load_json_object_fixture(
        f"gen_{DEFAULT_GENERATION}.json", DOMAIN
    )

    with (
        patch(
            "homeassistant.components.indevolt.coordinator.IndevoltAPI",
            autospec=True,
        ) as mock_client,
        patch(
            "homeassistant.components.indevolt.config_flow.IndevoltAPI",
            new=mock_client,
        ),
    ):
        client = mock_client.return_value
        client.fetch_data.return_value = fixture_data
        client.set_data.return_value = True
        client.get_config.return_value = {
            "device": {
                "sn": device_info["sn"],
                "type": device_info["device"],
                "generation": device_info["generation"],
                "fw": TEST_FW_VERSION,
            }
        }

        yield client


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock the async_setup_entry function."""
    with patch(
        "homeassistant.components.indevolt.async_setup_entry",
        return_value=True,
    ) as mock_setup:
        yield mock_setup
