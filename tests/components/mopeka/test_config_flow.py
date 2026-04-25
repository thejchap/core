"""Test the Mopeka config flow."""

from unittest.mock import patch

import voluptuous as vol
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.mopeka.const import CONF_MEDIUM_TYPE, DOMAIN, MediumType
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import NOT_MOPEKA_SERVICE_INFO, PRO_SERVICE_INFO

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
        data=PRO_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")

    with patch("homeassistant.components.mopeka.async_setup_entry", return_value=True):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_MEDIUM_TYPE: MediumType.PROPANE.value}
        )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Pro Plus EEFF")
    expect(result2["data"]).to_equal({CONF_MEDIUM_TYPE: MediumType.PROPANE.value})
    expect(result2["result"].unique_id).to_equal("aa:bb:cc:dd:ee:ff")


@test
async def async_step_bluetooth_not_mopeka(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery via bluetooth not mopeka."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=NOT_MOPEKA_SERVICE_INFO,
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
        "homeassistant.components.mopeka.config_flow.async_discovered_service_info",
        return_value=[PRO_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    with patch("homeassistant.components.mopeka.async_setup_entry", return_value=True):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"address": "aa:bb:cc:dd:ee:ff"},
        )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Pro Plus EEFF")
    expect(CONF_MEDIUM_TYPE in result2["data"]).to_be(True)
    expect(
        result2["data"][CONF_MEDIUM_TYPE]
        in [medium_type.value for medium_type in MediumType]
    ).to_be(True)
    expect(result2["result"].unique_id).to_equal("aa:bb:cc:dd:ee:ff")


@test
async def async_step_user_replace_ignored(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup from service info can replace an ignored entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=PRO_SERVICE_INFO.address,
        data={},
        source=config_entries.SOURCE_IGNORE,
    )
    entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.mopeka.config_flow.async_discovered_service_info",
        return_value=[PRO_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    with patch("homeassistant.components.mopeka.async_setup_entry", return_value=True):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"address": "aa:bb:cc:dd:ee:ff"},
        )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Pro Plus EEFF")
    expect(CONF_MEDIUM_TYPE in result2["data"]).to_be(True)
    expect(
        result2["data"][CONF_MEDIUM_TYPE]
        in [medium_type.value for medium_type in MediumType]
    ).to_be(True)
    expect(result2["result"].unique_id).to_equal("aa:bb:cc:dd:ee:ff")


@test
async def async_step_user_device_added_between_steps(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the device gets added via another flow between steps."""
    with patch(
        "homeassistant.components.mopeka.config_flow.async_discovered_service_info",
        return_value=[PRO_SERVICE_INFO],
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

    with patch("homeassistant.components.mopeka.async_setup_entry", return_value=True):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"address": "aa:bb:cc:dd:ee:ff"},
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
        unique_id="aa:bb:cc:dd:ee:ff",
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.mopeka.config_flow.async_discovered_service_info",
        return_value=[PRO_SERVICE_INFO],
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
        unique_id="aa:bb:cc:dd:ee:ff",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=PRO_SERVICE_INFO,
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
        data=PRO_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=PRO_SERVICE_INFO,
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
        data=PRO_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")

    with patch(
        "homeassistant.components.mopeka.config_flow.async_discovered_service_info",
        return_value=[PRO_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
        expect(result["type"]).to_be(FlowResultType.FORM)

    with patch("homeassistant.components.mopeka.async_setup_entry", return_value=True):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"address": "aa:bb:cc:dd:ee:ff"},
        )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Pro Plus EEFF")
    expect(CONF_MEDIUM_TYPE in result2["data"]).to_be(True)
    expect(
        result2["data"][CONF_MEDIUM_TYPE]
        in [medium_type.value for medium_type in MediumType]
    ).to_be(True)
    expect(result2["result"].unique_id).to_equal("aa:bb:cc:dd:ee:ff")

    expect(bool(hass.config_entries.flow.async_progress(DOMAIN))).to_be(False)


@test
async def async_step_reconfigure_options(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfig options: change MediumType from air to fresh water."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:75:10",
        title="TD40/TD200 7510",
        data={CONF_MEDIUM_TYPE: MediumType.AIR.value},
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    expect(entry.data[CONF_MEDIUM_TYPE]).to_equal(MediumType.AIR.value)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")
    schema: vol.Schema = result["data_schema"]
    medium_type_key = next(
        iter(key for key in schema.schema if key == CONF_MEDIUM_TYPE)
    )
    expect(medium_type_key.default()).to_equal(MediumType.AIR.value)

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_MEDIUM_TYPE: MediumType.FRESH_WATER.value},
    )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)

    expect(entry.data[CONF_MEDIUM_TYPE]).to_equal(MediumType.FRESH_WATER.value)
