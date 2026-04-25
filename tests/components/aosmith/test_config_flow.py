"""Test the A. O. Smith config flow."""

from datetime import timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from py_aosmith import AOSmithInvalidCredentialsException
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.aosmith.const import (
    DOMAIN,
    ENERGY_USAGE_INTERVAL,
    REGULAR_INTERVAL,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    FIXTURE_USER_INPUT,
    init_integration,
    mock_client,
    mock_setup_entry,
)

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import (
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.aosmith.config_flow.AOSmithAPIClient.get_devices",
        return_value=[],
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT,
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(FIXTURE_USER_INPUT[CONF_EMAIL])
    expect(result2["data"]).to_equal(FIXTURE_USER_INPUT)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "invalid_auth",
        exception=AOSmithInvalidCredentialsException("Invalid credentials"),
        expected_error_key="invalid_auth",
    ),
    test.case("unknown", exception=Exception, expected_error_key="unknown"),
)
async def form_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    *,
    exception: Any,
    expected_error_key: str,
) -> None:
    """Test handling an exception and then recovering on the second attempt."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.aosmith.config_flow.AOSmithAPIClient.get_devices",
        side_effect=exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT,
        )
        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["errors"]).to_equal({"base": expected_error_key})

    with patch(
        "homeassistant.components.aosmith.config_flow.AOSmithAPIClient.get_devices",
        return_value=[],
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            FIXTURE_USER_INPUT,
        )
        await hass.async_block_till_done()

    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3["title"]).to_equal(FIXTURE_USER_INPUT[CONF_EMAIL])
    expect(result3["data"]).to_equal(FIXTURE_USER_INPUT)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "get_devices", api_method="get_devices", wait_interval=REGULAR_INTERVAL
    ),
    test.case(
        "get_energy_use_data",
        api_method="get_energy_use_data",
        wait_interval=ENERGY_USAGE_INTERVAL,
    ),
)
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    freezer: Any = Depends(freezer_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    integration: MockConfigEntry = Depends(init_integration),
    client: MagicMock = Depends(mock_client),
    *,
    api_method: str,
    wait_interval: timedelta,
) -> None:
    """Test reauth works."""
    entries = hass.config_entries.async_entries(DOMAIN)
    expect(len(entries)).to_equal(1)
    expect(entries[0].state).to_be(ConfigEntryState.LOADED)

    getattr(client, api_method).side_effect = AOSmithInvalidCredentialsException(
        "Authentication error"
    )
    freezer.tick(wait_interval)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)
    expect(flows[0]["step_id"]).to_equal("reauth_confirm")

    with (
        patch(
            "homeassistant.components.aosmith.config_flow.AOSmithAPIClient.get_devices",
            return_value=[],
        ),
        patch(
            "homeassistant.components.aosmith.config_flow.AOSmithAPIClient.get_energy_use_data",
            return_value=[],
        ),
        patch("homeassistant.components.aosmith.async_setup_entry", return_value=True),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            flows[0]["flow_id"],
            {CONF_PASSWORD: FIXTURE_USER_INPUT[CONF_PASSWORD]},
        )
        await hass.async_block_till_done()

        expect(result2["type"]).to_be(FlowResultType.ABORT)
        expect(result2["reason"]).to_equal("reauth_successful")


@test
async def reauth_flow_retry(
    _trigger: None = Depends(_trigger_executor),
    freezer: Any = Depends(freezer_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    integration: MockConfigEntry = Depends(init_integration),
    client: MagicMock = Depends(mock_client),
) -> None:
    """Test reauth works with retry."""
    entries = hass.config_entries.async_entries(DOMAIN)
    expect(len(entries)).to_equal(1)
    expect(entries[0].state).to_be(ConfigEntryState.LOADED)

    client.get_devices.side_effect = AOSmithInvalidCredentialsException(
        "Authentication error"
    )
    freezer.tick(REGULAR_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)
    expect(flows[0]["step_id"]).to_equal("reauth_confirm")

    # First attempt at reauth - authentication fails again
    with patch(
        "homeassistant.components.aosmith.config_flow.AOSmithAPIClient.get_devices",
        side_effect=AOSmithInvalidCredentialsException("Authentication error"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            flows[0]["flow_id"],
            {CONF_PASSWORD: FIXTURE_USER_INPUT[CONF_PASSWORD]},
        )
        await hass.async_block_till_done()

        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["errors"]).to_equal({"base": "invalid_auth"})

    # Second attempt at reauth - authentication succeeds
    with (
        patch(
            "homeassistant.components.aosmith.config_flow.AOSmithAPIClient.get_devices",
            return_value=[],
        ),
        patch("homeassistant.components.aosmith.async_setup_entry", return_value=True),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            flows[0]["flow_id"],
            {CONF_PASSWORD: FIXTURE_USER_INPUT[CONF_PASSWORD]},
        )
        await hass.async_block_till_done()

        expect(result3["type"]).to_be(FlowResultType.ABORT)
        expect(result3["reason"]).to_equal("reauth_successful")
