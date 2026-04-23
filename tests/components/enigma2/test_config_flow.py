"""Test the Enigma2 config flow."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

from aiohttp.client_exceptions import ClientError
from openwebif.error import InvalidAuthError
from tryke import Depends, expect, fixture, test

from homeassistant.components.enigma2.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, ConfigEntryState
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.enigma2._fixtures import (
    TEST_REQUIRED,
    mock_config_entry,
    mock_zeroconf,
    openwebif_device_mock,
)
from tests.components.enigma2.conftest import TEST_FULL
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test.cases(
    test.case("full", TEST_FULL),
    test.case("required", TEST_REQUIRED),
)
async def form_user(
    test_config: dict[str, Any],
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _openwebif_device_mock: AsyncMock = Depends(openwebif_device_mock),
) -> None:
    """Test a successful user initiated flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], test_config
    )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(test_config[CONF_HOST])
    expect(result["data"]).to_equal(test_config)


@test.cases(
    test.case("invalid_auth", InvalidAuthError, "invalid_auth"),
    test.case("cannot_connect", ClientError, "cannot_connect"),
    test.case("unknown", Exception, "unknown"),
)
async def form_user_errors(
    side_effect: Exception,
    error_value: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    openwebif_device_mock: AsyncMock = Depends(openwebif_device_mock),
) -> None:
    """Test we handle errors."""
    openwebif_device_mock.get_about.side_effect = side_effect
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    await hass.async_block_till_done()
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_FULL
    )
    await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal(SOURCE_USER)
    expect(result["errors"]).to_equal({"base": error_value})

    openwebif_device_mock.get_about.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_FULL,
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(TEST_FULL[CONF_HOST])
    expect(result["data"]).to_equal(TEST_FULL)
    expect(result["result"].unique_id).to_equal(openwebif_device_mock.mac_address)


@test
async def duplicate_host(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _openwebif_device_mock: AsyncMock = Depends(openwebif_device_mock),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that a duplicate host aborts the config flow."""
    mock_config_entry.add_to_hass(hass)

    result2 = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result2["type"] is FlowResultType.FORM).to_be(True)
    expect(result2["step_id"]).to_equal("user")
    result2 = await hass.config_entries.flow.async_configure(
        result2["flow_id"], TEST_FULL
    )
    expect(result2["type"] is FlowResultType.ABORT).to_be(True)
    expect(result2["reason"]).to_equal("already_configured")


@test
async def options_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _openwebif_device_mock: AsyncMock = Depends(openwebif_device_mock),
) -> None:
    """Test the form options."""
    entry = MockConfigEntry(domain=DOMAIN, data=TEST_FULL, options={}, entry_id="1")
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state is ConfigEntryState.LOADED).to_be(True)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"source_bouquet": "Favourites (TV)"}
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(entry.options).to_equal({"source_bouquet": "Favourites (TV)"})

    await hass.async_block_till_done()

    expect(entry.state is ConfigEntryState.LOADED).to_be(True)
