"""Tests for the Music Player Daemon config flow."""

from socket import gaierror
from unittest.mock import AsyncMock, MagicMock

import mpd
from tryke import Depends, expect, fixture, test

from homeassistant.components.mpd.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_config_entry, mock_mpd_client, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    mpd_client: MagicMock = Depends(mock_mpd_client),
) -> None:
    """Test the happy flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(not result["errors"]).to_be(True)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.0.1", CONF_PORT: 6600, CONF_PASSWORD: "test123"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Music Player Daemon")
    expect(result["data"]).to_equal(
        {
            CONF_HOST: "192.168.0.1",
            CONF_PORT: 6600,
            CONF_PASSWORD: "test123",
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("timeout", exception=TimeoutError, error="cannot_connect"),
    test.case("gaierror", exception=gaierror, error="cannot_connect"),
    test.case("mpd_connection_error", exception=mpd.ConnectionError, error="cannot_connect"),
    test.case("oserror", exception=OSError, error="cannot_connect"),
    test.case("unknown", exception=Exception, error="unknown"),
)
async def errors(
    exception: type[Exception],
    error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mpd_client: MagicMock = Depends(mock_mpd_client),
) -> None:
    """Test we handle errors correctly."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    mpd_client.password.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.0.1", CONF_PORT: 6600, CONF_PASSWORD: "test123"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    mpd_client.password.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.0.1", CONF_PORT: 6600, CONF_PASSWORD: "test123"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def existing_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we abort if an entry already exists."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(not result["errors"]).to_be(True)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.0.1", CONF_PORT: 6600, CONF_PASSWORD: "test123"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
