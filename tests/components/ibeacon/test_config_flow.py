"""Test the ibeacon config flow."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.ibeacon.const import CONF_ALLOW_NAMELESS_UUIDS, DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    enable_bluetooth,
    hass as hass_fixture,
    mock_bluetooth_adapters,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _adapters: None = Depends(mock_bluetooth_adapters),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def setup_user_no_bluetooth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setting up via user interaction when bluetooth is not enabled."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("bluetooth_not_available")


@test
async def setup_user(
    _trigger: None = Depends(_trigger_executor),
    _bluetooth: None = Depends(enable_bluetooth),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setting up via user interaction with bluetooth enabled."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    with patch("homeassistant.components.ibeacon.async_setup_entry", return_value=True):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("iBeacon Tracker")
    expect(result2["data"]).to_equal({})


@test
async def setup_user_already_setup(
    _trigger: None = Depends(_trigger_executor),
    _bluetooth: None = Depends(enable_bluetooth),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setting up via user when already setup."""
    MockConfigEntry(domain=DOMAIN).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    _bluetooth: None = Depends(enable_bluetooth),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow options."""
    config_entry = MockConfigEntry(domain=DOMAIN)
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    # Test save invalid uuid.
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "new_uuid": "invalid",
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")
    expect(result["errors"]).to_equal({"new_uuid": "invalid_uuid_format"})

    # Test save new uuid.
    uuid = "daa4b6bb-b77a-4662-aeb8-b3ed56454091"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "new_uuid": uuid,
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({CONF_ALLOW_NAMELESS_UUIDS: [uuid]})

    # Test save duplicate uuid.
    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_ALLOW_NAMELESS_UUIDS: [uuid],
            "new_uuid": uuid,
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({CONF_ALLOW_NAMELESS_UUIDS: [uuid]})

    # Delete.
    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_ALLOW_NAMELESS_UUIDS: [],
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({CONF_ALLOW_NAMELESS_UUIDS: []})
