"""Test the initialization."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

from fyta_cli.fyta_exceptions import (
    FytaAuthentificationError,
    FytaConnectionError,
    FytaPasswordError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.fyta.const import CONF_EXPIRATION, DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_PASSWORD,
    CONF_USERNAME,
    Platform,
)
from homeassistant.core import HomeAssistant

from . import setup_platform
from ._fixtures import mock_config_entry, mock_fyta_connector
from .const import ACCESS_TOKEN, EXPIRATION, EXPIRATION_OLD, PASSWORD, USERNAME

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def load_unload(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_fyta_connector: AsyncMock = Depends(mock_fyta_connector),
) -> None:
    """Test load and unload."""
    await setup_platform(hass, mock_config_entry, [Platform.SENSOR])
    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(mock_config_entry.entry_id)).to_be(
        True
    )
    await hass.async_block_till_done()
    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def refresh_expired_token(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_fyta_connector: AsyncMock = Depends(mock_fyta_connector),
) -> None:
    """Test we refresh an expired token."""
    mock_fyta_connector.expiration = datetime.fromisoformat(EXPIRATION_OLD).replace(
        tzinfo=UTC
    )
    await setup_platform(hass, mock_config_entry, [Platform.SENSOR])
    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    expect(len(mock_fyta_connector.login.mock_calls)).to_equal(1)
    expect(mock_config_entry.data[CONF_EXPIRATION]).to_equal(EXPIRATION)


@test.cases(
    test.case("auth_error", exception=FytaAuthentificationError),
    test.case("password_error", exception=FytaPasswordError),
)
async def invalid_credentials(
    exception: type[Exception],
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_fyta_connector: AsyncMock = Depends(mock_fyta_connector),
) -> None:
    """Test FYTA credentials changing."""
    mock_fyta_connector.expiration = datetime.fromisoformat(EXPIRATION_OLD).replace(
        tzinfo=UTC
    )
    mock_fyta_connector.login.side_effect = exception

    await setup_platform(hass, mock_config_entry, [Platform.SENSOR])
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)


@test
async def raise_config_entry_not_ready_when_offline(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_fyta_connector: AsyncMock = Depends(mock_fyta_connector),
) -> None:
    """Config entry state is SETUP_RETRY when FYTA is offline."""
    mock_fyta_connector.update_all_plants.side_effect = FytaConnectionError

    await setup_platform(hass, mock_config_entry, [Platform.SENSOR])
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)

    expect(len(hass.config_entries.flow.async_progress())).to_equal(0)


@test
async def raise_config_entry_not_ready_when_offline_and_expired(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_fyta_connector: AsyncMock = Depends(mock_fyta_connector),
) -> None:
    """Config entry state is SETUP_RETRY when FYTA is offline and access_token is expired."""
    mock_fyta_connector.login.side_effect = FytaConnectionError
    mock_fyta_connector.expiration = datetime.fromisoformat(EXPIRATION_OLD).replace(
        tzinfo=UTC
    )

    await setup_platform(hass, mock_config_entry, [Platform.SENSOR])
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)

    expect(len(hass.config_entries.flow.async_progress())).to_equal(0)


@test
async def migrate_config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_fyta_connector: AsyncMock = Depends(mock_fyta_connector),
) -> None:
    """Test successful migration of entry data."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=USERNAME,
        data={
            CONF_USERNAME: USERNAME,
            CONF_PASSWORD: PASSWORD,
        },
        version=1,
        minor_version=1,
    )
    entry.add_to_hass(hass)

    expect(entry.version).to_equal(1)
    expect(entry.minor_version).to_equal(1)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.version).to_equal(1)
    expect(entry.minor_version).to_equal(2)
    expect(entry.data[CONF_USERNAME]).to_equal(USERNAME)
    expect(entry.data[CONF_PASSWORD]).to_equal(PASSWORD)
    expect(entry.data[CONF_ACCESS_TOKEN]).to_equal(ACCESS_TOKEN)
    expect(entry.data[CONF_EXPIRATION]).to_equal(EXPIRATION)
