"""Test the Enigma2 config flow."""

from typing import Any
from unittest.mock import AsyncMock

from aiohttp.client_exceptions import ClientError
from openwebif.error import InvalidAuthError
from tryke import Depends, expect, fixture, test

from homeassistant.components.enigma2.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, ConfigEntryState
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    TEST_FULL,
    TEST_REQUIRED,
    mock_config_entry,
    openwebif_device_mock,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture so tryke fully resolves Depends across the module."""


@test.cases(
    test.case("full", test_config=TEST_FULL),
    test.case("required", test_config=TEST_REQUIRED),
)
async def form_user(
    test_config: dict[str, Any],
    hass: HomeAssistant = Depends(hass_fixture),
    _network: None = Depends(mock_network),
    _device: AsyncMock = Depends(openwebif_device_mock),
) -> None:
    """Test a successful user initiated flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], test_config
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(test_config[CONF_HOST])
    expect(result["data"]).to_equal(test_config)


@test.cases(
    test.case("invalid_auth", side_effect=InvalidAuthError, error_value="invalid_auth"),
    test.case("cannot_connect", side_effect=ClientError, error_value="cannot_connect"),
    test.case("unknown", side_effect=Exception, error_value="unknown"),
)
async def form_user_errors(
    side_effect: Exception,
    error_value: str,
    hass: HomeAssistant = Depends(hass_fixture),
    _network: None = Depends(mock_network),
    device: AsyncMock = Depends(openwebif_device_mock),
) -> None:
    """Test we handle errors."""
    device.get_about.side_effect = side_effect
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_FULL
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(SOURCE_USER)
    expect(result["errors"]).to_equal({"base": error_value})

    device.get_about.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_FULL,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_FULL[CONF_HOST])
    expect(result["data"]).to_equal(TEST_FULL)
    expect(result["result"].unique_id).to_equal(device.mac_address)


@test
async def duplicate_host(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    _device: AsyncMock = Depends(openwebif_device_mock),
) -> None:
    """Test that a duplicate host aborts the config flow."""
    entry.add_to_hass(hass)

    result2 = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("user")
    result2 = await hass.config_entries.flow.async_configure(
        result2["flow_id"], TEST_FULL
    )
    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _device: AsyncMock = Depends(openwebif_device_mock),
) -> None:
    """Test the form options."""
    entry = MockConfigEntry(domain=DOMAIN, data=TEST_FULL, options={}, entry_id="1")
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.LOADED)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"source_bouquet": "Favourites (TV)"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(entry.options).to_equal({"source_bouquet": "Favourites (TV)"})

    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.LOADED)
