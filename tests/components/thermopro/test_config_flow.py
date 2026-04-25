"""Test the ThermoPro config flow."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.thermopro.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import NOT_THERMOPRO_SERVICE_INFO, TP357_SERVICE_INFO

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    enable_bluetooth,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _bluetooth: None = Depends(enable_bluetooth),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def async_step_bluetooth_valid_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery via bluetooth with a valid device."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=TP357_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")
    with patch(
        "homeassistant.components.thermopro.async_setup_entry", return_value=True
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("TP357 (2142) AC3D")
    expect(result2["data"]).to_equal({})
    expect(result2["result"].unique_id).to_equal("4125DDBA-2774-4851-9889-6AADDD4CAC3D")


@test
async def async_step_bluetooth_not_thermopro(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery via bluetooth not thermopro."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=NOT_THERMOPRO_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("not_supported")


@test
async def async_step_user_no_devices_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup from service info cache with no devices found."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test
async def async_step_user_with_found_devices(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup from service info cache with devices found."""
    with patch(
        "homeassistant.components.thermopro.config_flow.async_discovered_service_info",
        return_value=[TP357_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    with patch(
        "homeassistant.components.thermopro.async_setup_entry", return_value=True
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"address": "4125DDBA-2774-4851-9889-6AADDD4CAC3D"},
        )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("TP357 (2142) AC3D")
    expect(result2["data"]).to_equal({})
    expect(result2["result"].unique_id).to_equal("4125DDBA-2774-4851-9889-6AADDD4CAC3D")


@test
async def async_step_user_replace_ignored(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup from service info and replace an ignored entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TP357_SERVICE_INFO.address,
        data={},
        source=config_entries.SOURCE_IGNORE,
    )
    entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.thermopro.config_flow.async_discovered_service_info",
        return_value=[TP357_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    with patch(
        "homeassistant.components.thermopro.async_setup_entry", return_value=True
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"address": "4125DDBA-2774-4851-9889-6AADDD4CAC3D"},
        )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("TP357 (2142) AC3D")
    expect(result2["data"]).to_equal({})
    expect(result2["result"].unique_id).to_equal("4125DDBA-2774-4851-9889-6AADDD4CAC3D")


@test
async def async_step_user_device_added_between_steps(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the device gets added via another flow between steps."""
    with patch(
        "homeassistant.components.thermopro.config_flow.async_discovered_service_info",
        return_value=[TP357_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="4125DDBA-2774-4851-9889-6AADDD4CAC3D",
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.thermopro.async_setup_entry", return_value=True
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"address": "4125DDBA-2774-4851-9889-6AADDD4CAC3D"},
        )
    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")


@test
async def async_step_user_with_found_devices_already_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup from service info cache with devices found."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="4125DDBA-2774-4851-9889-6AADDD4CAC3D",
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.thermopro.config_flow.async_discovered_service_info",
        return_value=[TP357_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test
async def async_step_bluetooth_devices_already_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can't start a flow if there is already a config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="4125DDBA-2774-4851-9889-6AADDD4CAC3D",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=TP357_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def async_step_bluetooth_already_in_progress(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can't start a flow for the same device twice."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=TP357_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=TP357_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_in_progress")


@test
async def async_step_user_takes_precedence_over_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test manual setup takes precedence over discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=TP357_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")

    with patch(
        "homeassistant.components.thermopro.config_flow.async_discovered_service_info",
        return_value=[TP357_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
        expect(result["type"]).to_be(FlowResultType.FORM)

    with patch(
        "homeassistant.components.thermopro.async_setup_entry", return_value=True
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"address": "4125DDBA-2774-4851-9889-6AADDD4CAC3D"},
        )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("TP357 (2142) AC3D")
    expect(result2["data"]).to_equal({})
    expect(result2["result"].unique_id).to_equal("4125DDBA-2774-4851-9889-6AADDD4CAC3D")

    expect(bool(hass.config_entries.flow.async_progress(DOMAIN))).to_be(False)
