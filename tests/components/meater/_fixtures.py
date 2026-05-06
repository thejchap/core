"""Tryke fixtures for Meater config_flow tests."""

from __future__ import annotations

from collections.abc import Generator
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

from meater.MeaterApi import MeaterCook, MeaterProbe
from tryke import fixture

from homeassistant.components.meater.const import DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from .const import PROBE_ID

from tests.common import MockConfigEntry


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.meater.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_cook() -> Mock:
    """Mock a cook."""
    mock = Mock(spec=MeaterCook)
    mock.id = "123123"
    mock.name = "Whole chicken"
    mock.state = "Started"
    mock.target_temperature = 25.0
    mock.peak_temperature = 27.0
    mock.time_remaining = 32
    mock.time_elapsed = 32
    return mock


def _build_probe(mock_cook: Mock | None) -> Mock:
    """Build a MeaterProbe mock."""
    cook = mock_cook if mock_cook is not None else Mock(spec=MeaterCook)
    mock = Mock(spec=MeaterProbe)
    mock.id = PROBE_ID
    mock.internal_temperature = 26.0
    mock.ambient_temperature = 28.0
    mock.cook = cook
    mock.time_updated = datetime.fromisoformat("2025-06-16T13:53:51+00:00")
    return mock


@fixture
def mock_meater_client() -> Generator[AsyncMock]:
    """Mock a Meater client."""
    with (
        patch(
            "homeassistant.components.meater.coordinator.MeaterApi",
            autospec=True,
        ) as mock_client,
        patch(
            "homeassistant.components.meater.config_flow.MeaterApi",
            new=mock_client,
        ),
    ):
        client = mock_client.return_value
        client.get_all_devices.return_value = [_build_probe(None)]
        yield client


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Mock a config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Meater",
        data={CONF_USERNAME: "user@host.com", CONF_PASSWORD: "password123"},
        unique_id="user@host.com",
    )
