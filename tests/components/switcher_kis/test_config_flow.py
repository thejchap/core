"""Test the Switcher config flow."""

from unittest.mock import AsyncMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.switcher_kis.const import DOMAIN
from homeassistant.const import CONF_TOKEN, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import _bridge_context, mock_bridge_empty, mock_setup_entry
from .consts import (
    DUMMY_DUAL_SHUTTER_SINGLE_LIGHT_DEVICE,
    DUMMY_PLUG_DEVICE,
    DUMMY_SINGLE_SHUTTER_DUAL_LIGHT_DEVICE,
    DUMMY_TOKEN,
    DUMMY_USERNAME,
    DUMMY_WATER_HEATER_DEVICE,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we can finish a config flow."""
    devices = [
        DUMMY_PLUG_DEVICE,
        DUMMY_WATER_HEATER_DEVICE,
        # Make sure we don't detect the same device twice
        DUMMY_WATER_HEATER_DEVICE,
    ]
    with (
        _bridge_context(devices) as bridge,
        patch("homeassistant.components.switcher_kis.utils.DISCOVERY_TIME_SEC", 0),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("confirm")

        result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})

        expect(bridge.is_running).to_be(False)
        expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result2["title"]).to_equal("Switcher")
        expect(result2["result"].data).to_equal(
            {CONF_USERNAME: None, CONF_TOKEN: None}
        )

        await hass.async_block_till_done()

        expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def user_setup_found_token_device_valid_token(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we can finish a config flow with token device found."""
    devices = [
        DUMMY_SINGLE_SHUTTER_DUAL_LIGHT_DEVICE,
        DUMMY_DUAL_SHUTTER_SINGLE_LIGHT_DEVICE,
    ]
    with (
        _bridge_context(devices) as bridge,
        patch("homeassistant.components.switcher_kis.utils.DISCOVERY_TIME_SEC", 0),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")

    result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(bridge.is_running).to_be(False)
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("credentials")

    with patch(
        "homeassistant.components.switcher_kis.config_flow.validate_token",
        return_value=True,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_USERNAME: DUMMY_USERNAME, CONF_TOKEN: DUMMY_TOKEN},
        )

    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3["title"]).to_equal("Switcher")
    expect(result3["result"].data).to_equal(
        {
            CONF_USERNAME: DUMMY_USERNAME,
            CONF_TOKEN: DUMMY_TOKEN,
        }
    )

    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def user_setup_found_token_device_invalid_token(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we can finish a config flow with token device found but invalid token."""
    devices = [
        DUMMY_SINGLE_SHUTTER_DUAL_LIGHT_DEVICE,
        DUMMY_DUAL_SHUTTER_SINGLE_LIGHT_DEVICE,
    ]
    with (
        _bridge_context(devices),
        patch("homeassistant.components.switcher_kis.utils.DISCOVERY_TIME_SEC", 0),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")

    result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("credentials")

    with patch(
        "homeassistant.components.switcher_kis.config_flow.validate_token",
        return_value=False,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_USERNAME: DUMMY_USERNAME, CONF_TOKEN: DUMMY_TOKEN},
        )

    expect(result3["type"]).to_be(FlowResultType.FORM)
    expect(result3["errors"]).to_equal({"base": "invalid_auth"})

    with patch(
        "homeassistant.components.switcher_kis.config_flow.validate_token",
        return_value=True,
    ):
        result4 = await hass.config_entries.flow.async_configure(
            result3["flow_id"],
            {CONF_USERNAME: DUMMY_USERNAME, CONF_TOKEN: DUMMY_TOKEN},
        )

        expect(result4["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result4["title"]).to_equal("Switcher")
        expect(result4["result"].data).to_equal(
            {
                CONF_USERNAME: DUMMY_USERNAME,
                CONF_TOKEN: DUMMY_TOKEN,
            }
        )

    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def user_setup_abort_no_devices_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    bridge: AsyncMock = Depends(mock_bridge_empty),
) -> None:
    """Test we abort a config flow if no devices found."""
    with patch("homeassistant.components.switcher_kis.utils.DISCOVERY_TIME_SEC", 0):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("confirm")

        result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})

        expect(bridge.is_running).to_be(False)
        expect(result2["type"]).to_be(FlowResultType.ABORT)
        expect(result2["reason"]).to_equal("no_devices_found")

        await hass.async_block_till_done()

        expect(len(setup_entry.mock_calls)).to_equal(0)


@test
async def single_instance(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we only allow a single config flow."""
    MockConfigEntry(domain=DOMAIN).add_to_hass(hass)
    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")


@test
async def reauth_successful(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test starting a reauthentication flow."""
    user_input = {CONF_USERNAME: DUMMY_USERNAME, CONF_TOKEN: DUMMY_TOKEN}
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_USERNAME: DUMMY_USERNAME, CONF_TOKEN: DUMMY_TOKEN},
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    with patch(
        "homeassistant.components.switcher_kis.config_flow.validate_token",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=user_input,
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test
async def reauth_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reauthentication flow with invalid credentials."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_USERNAME: DUMMY_USERNAME, CONF_TOKEN: DUMMY_TOKEN},
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    with patch(
        "homeassistant.components.switcher_kis.config_flow.validate_token",
        return_value=False,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_USERNAME: "invalid_user", CONF_TOKEN: "invalid_token"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})

    with patch(
        "homeassistant.components.switcher_kis.config_flow.validate_token",
        return_value=True,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_USERNAME: DUMMY_USERNAME, CONF_TOKEN: DUMMY_TOKEN},
        )

        expect(result3["type"]).to_be(FlowResultType.ABORT)
        expect(result3["reason"]).to_equal("reauth_successful")
