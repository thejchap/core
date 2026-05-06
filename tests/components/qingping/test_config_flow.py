"""Test the Qingping config flow."""

from __future__ import annotations

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.qingping.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import enable_bluetooth as enable_bluetooth_fx

from . import (
    LIGHT_AND_SIGNAL_SERVICE_INFO,
    NO_DATA_SERVICE_INFO,
    NOT_QINGPING_SERVICE_INFO,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _bt: None = Depends(enable_bluetooth_fx),
) -> None:
    """Wire mock_network + enable_bluetooth for every test."""


@test
async def async_step_bluetooth_valid_device(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery via bluetooth with a valid device."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=LIGHT_AND_SIGNAL_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")
    with patch(
        "homeassistant.components.qingping.async_setup_entry", return_value=True
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Motion & Light EEFF")
    expect(result2["data"]).to_equal({})
    expect(result2["result"].unique_id).to_equal("aa:bb:cc:dd:ee:ff")


@test
async def async_step_bluetooth_not_enough_info_at_start(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery via bluetooth with only a partial adv at the start."""
    with patch(
        "homeassistant.components.qingping.config_flow.async_process_advertisements",
        return_value=LIGHT_AND_SIGNAL_SERVICE_INFO,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_BLUETOOTH},
            data=NO_DATA_SERVICE_INFO,
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")
    with patch(
        "homeassistant.components.qingping.async_setup_entry", return_value=True
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Qingping Motion & Light")
    expect(result2["data"]).to_equal({})
    expect(result2["result"].unique_id).to_equal("aa:bb:cc:dd:ee:ff")


@test
async def async_step_bluetooth_not_qingping(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery via bluetooth not qingping."""
    with patch(
        "homeassistant.components.qingping.config_flow.async_process_advertisements",
        side_effect=TimeoutError,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_BLUETOOTH},
            data=NOT_QINGPING_SERVICE_INFO,
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("not_supported")


@test
async def async_step_user_no_devices_found(
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
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup from service info cache with devices found."""
    with patch(
        "homeassistant.components.qingping.config_flow.async_discovered_service_info",
        return_value=[LIGHT_AND_SIGNAL_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    with patch(
        "homeassistant.components.qingping.async_setup_entry", return_value=True
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"address": "aa:bb:cc:dd:ee:ff"},
        )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Motion & Light EEFF")
    expect(result2["data"]).to_equal({})
    expect(result2["result"].unique_id).to_equal("aa:bb:cc:dd:ee:ff")


@test
async def async_step_user_replace_ignored(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup from service info can replace an ignored entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=LIGHT_AND_SIGNAL_SERVICE_INFO.address,
        source=config_entries.SOURCE_IGNORE,
        data={},
    )
    entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.qingping.config_flow.async_discovered_service_info",
        return_value=[LIGHT_AND_SIGNAL_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    with patch(
        "homeassistant.components.qingping.async_setup_entry", return_value=True
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"address": "aa:bb:cc:dd:ee:ff"},
        )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Motion & Light EEFF")
    expect(result2["data"]).to_equal({})
    expect(result2["result"].unique_id).to_equal("aa:bb:cc:dd:ee:ff")


@test
async def async_step_user_device_added_between_steps(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the device gets added via another flow between steps."""
    with patch(
        "homeassistant.components.qingping.config_flow.async_discovered_service_info",
        return_value=[LIGHT_AND_SIGNAL_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.qingping.async_setup_entry", return_value=True
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"address": "aa:bb:cc:dd:ee:ff"},
        )
    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")


@test
async def async_step_user_with_found_devices_already_setup(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup from service info cache with devices found."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.qingping.config_flow.async_discovered_service_info",
        return_value=[LIGHT_AND_SIGNAL_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test
async def async_step_bluetooth_devices_already_setup(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can't start a flow if there is already a config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=LIGHT_AND_SIGNAL_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def async_step_bluetooth_already_in_progress(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can't start a flow for the same device twice."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=LIGHT_AND_SIGNAL_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=LIGHT_AND_SIGNAL_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_in_progress")


@test
async def async_step_user_takes_precedence_over_discovery(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test manual setup takes precedence over discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=LIGHT_AND_SIGNAL_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")

    with patch(
        "homeassistant.components.qingping.config_flow.async_discovered_service_info",
        return_value=[LIGHT_AND_SIGNAL_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
        expect(result["type"]).to_be(FlowResultType.FORM)

    with patch(
        "homeassistant.components.qingping.async_setup_entry", return_value=True
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"address": "aa:bb:cc:dd:ee:ff"},
        )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Motion & Light EEFF")
    expect(result2["data"]).to_equal({})
    expect(result2["result"].unique_id).to_equal("aa:bb:cc:dd:ee:ff")

    expect(bool(hass.config_entries.flow.async_progress(DOMAIN))).to_be(False)
