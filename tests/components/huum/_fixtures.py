"""Tryke fixtures for the Huum integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from huum.const import SaunaStatus
from huum.schemas import HuumStatusResponse, SaunaConfig
from tryke import fixture

from homeassistant.components.huum.const import DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from tests.common import MockConfigEntry


@fixture
def mock_huum_client() -> Generator[AsyncMock]:
    """Mock the Huum API client."""
    with (
        patch(
            "homeassistant.components.huum.coordinator.Huum",
            autospec=True,
        ) as mock_cls,
        patch(
            "homeassistant.components.huum.config_flow.Huum",
            new=mock_cls,
        ),
    ):
        client = mock_cls.return_value
        client.status.return_value = HuumStatusResponse(
            status=SaunaStatus.ONLINE_NOT_HEATING,
            door_closed=True,
            temperature=30,
            sauna_name="123456",
            target_temperature=80,
            config=3,
            light=1,
            humidity=0,
            target_humidity=5,
            sauna_config=SaunaConfig(
                child_lock="OFF",
                max_heating_time=3,
                min_heating_time=0,
                max_temp=110,
                min_temp=40,
                max_timer=0,
                min_timer=0,
            ),
        )
        yield client


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.huum.async_setup_entry", return_value=True
    ) as setup_entry_mock:
        yield setup_entry_mock


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Mock a config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_USERNAME: "huum@sauna.org",
            CONF_PASSWORD: "ukuuku",
        },
        entry_id="AABBCC112233",
    )
