"""Tests for 1-Wire config flow."""

from __future__ import annotations

from ipaddress import ip_address
from unittest.mock import AsyncMock, patch

from aio_ownet.exceptions import OWServerConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.onewire.const import (
    DOMAIN,
    INPUT_ENTRY_CLEAR_OPTIONS,
    INPUT_ENTRY_DEVICE_SELECTION,
)
from homeassistant.config_entries import SOURCE_HASSIO, SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.service_info.hassio import HassioServiceInfo
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from tests.common import MockConfigEntry
from tests.components.onewire._fixtures import (
    config_entry,
    filled_device_registry,
    mock_setup_entry,
)
from tests.hass_fixtures import hass as hass_fixture, mock_network

_HASSIO_DISCOVERY = HassioServiceInfo(
    config={"host": "1302b8e0-owserver", "port": 4304, "addon": "owserver (1-wire)"},
    name="owserver (1-wire)",
    slug="1302b8e0_owserver",
    uuid="e3fa56560d93458b96a594cbcea3017e",
)
_ZEROCONF_DISCOVERY = ZeroconfServiceInfo(
    ip_address=ip_address("5.6.7.8"),
    ip_addresses=[ip_address("5.6.7.8")],
    hostname="ubuntu.local.",
    name="OWFS (1-wire) Server",
    port=4304,
    type="_owserver._tcp.local.",
    properties={},
)


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _mse: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Wire mock_network + mock_setup_entry for every test."""


@test
async def user_flow(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with patch(
        "homeassistant.components.onewire.onewirehub.OWServerStatelessProxy.validate",
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "1.2.3.4", CONF_PORT: 1234},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    new_entry = result["result"]
    expect(new_entry.title).to_equal("1.2.3.4")
    expect(new_entry.data).to_equal({CONF_HOST: "1.2.3.4", CONF_PORT: 1234})


@test
async def user_flow_recovery(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test user flow recovery after invalid server."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with patch(
        "homeassistant.components.onewire.onewirehub.OWServerStatelessProxy.validate",
        side_effect=OWServerConnectionError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "1.2.3.4", CONF_PORT: 1234},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    with patch(
        "homeassistant.components.onewire.onewirehub.OWServerStatelessProxy.validate",
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "1.2.3.4", CONF_PORT: 1234},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    new_entry = result["result"]
    expect(new_entry.title).to_equal("1.2.3.4")
    expect(new_entry.data).to_equal({CONF_HOST: "1.2.3.4", CONF_PORT: 1234})


@test
async def user_duplicate(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test user duplicate flow."""
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(bool(result["errors"])).to_equal(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "1.2.3.4", CONF_PORT: 1234},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reconfigure_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry),
    setup_mock: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test reconfigure flow."""
    result = await entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(bool(result["errors"])).to_equal(False)

    with patch(
        "homeassistant.components.onewire.onewirehub.OWServerStatelessProxy.validate",
        side_effect=OWServerConnectionError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "2.3.4.5", CONF_PORT: 2345},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    with patch(
        "homeassistant.components.onewire.onewirehub.OWServerStatelessProxy.validate",
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "2.3.4.5", CONF_PORT: 2345},
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(entry.data).to_equal({CONF_HOST: "2.3.4.5", CONF_PORT: 2345})
    expect(len(setup_mock.mock_calls)).to_equal(1)


@test
async def reconfigure_duplicate(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry),
    setup_mock: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test reconfigure duplicate flow."""
    other_config_entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        data={
            CONF_HOST: "2.3.4.5",
            CONF_PORT: 2345,
        },
        entry_id="other",
    )
    other_config_entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(bool(result["errors"])).to_equal(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "2.3.4.5", CONF_PORT: 2345},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")

    expect(len(setup_mock.mock_calls)).to_equal(0)
    expect(entry.data).to_equal({CONF_HOST: "1.2.3.4", CONF_PORT: 1234})
    expect(other_config_entry.data).to_equal({CONF_HOST: "2.3.4.5", CONF_PORT: 2345})


@test
async def hassio_flow(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test HassIO discovery flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_HASSIO},
        data=_HASSIO_DISCOVERY,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")
    expect(bool(result["errors"])).to_equal(False)

    with patch(
        "homeassistant.components.onewire.onewirehub.OWServerStatelessProxy.validate",
        side_effect=OWServerConnectionError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    with patch(
        "homeassistant.components.onewire.onewirehub.OWServerStatelessProxy.validate",
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    new_entry = result["result"]
    expect(new_entry.title).to_equal("owserver (1-wire)")
    expect(new_entry.data).to_equal({CONF_HOST: "1302b8e0-owserver", CONF_PORT: 4304})


@test
async def hassio_duplicate(
    hass: HomeAssistant = Depends(hass_fixture),
    _entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test HassIO discovery duplicate flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_HASSIO},
        data=_HASSIO_DISCOVERY,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def zeroconf_flow(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test zeroconf discovery flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=_ZEROCONF_DISCOVERY,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")
    expect(bool(result["errors"])).to_equal(False)

    with patch(
        "homeassistant.components.onewire.onewirehub.OWServerStatelessProxy.validate",
        side_effect=OWServerConnectionError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    with patch(
        "homeassistant.components.onewire.onewirehub.OWServerStatelessProxy.validate",
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    new_entry = result["result"]
    expect(new_entry.title).to_equal("OWFS (1-wire) Server")
    expect(new_entry.data).to_equal({CONF_HOST: "ubuntu.local.", CONF_PORT: 4304})


@test
async def zeroconf_duplicate(
    hass: HomeAssistant = Depends(hass_fixture),
    _entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test zeroconf discovery duplicate flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=_ZEROCONF_DISCOVERY,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def user_options_clear(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry),
    _reg: dr.DeviceRegistry = Depends(filled_device_registry),
) -> None:
    """Test clearing the options."""
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    result = await hass.config_entries.options.async_init(entry.entry_id)
    expect(result["data_schema"].schema["device_selection"].options).to_equal(
        {
            "28.111111111111": False,
            "28.222222222222": False,
            "28.222222222223": False,
        }
    )

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={INPUT_ENTRY_CLEAR_OPTIONS: True},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({})


@test
async def user_options_empty_selection_recovery(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry),
    _reg: dr.DeviceRegistry = Depends(filled_device_registry),
) -> None:
    """Test leaving the selection of devices empty."""
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    result = await hass.config_entries.options.async_init(entry.entry_id)
    expect(result["data_schema"].schema["device_selection"].options).to_equal(
        {
            "28.111111111111": False,
            "28.222222222222": False,
            "28.222222222223": False,
        }
    )

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={INPUT_ENTRY_DEVICE_SELECTION: []},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("device_selection")
    expect(result["errors"]).to_equal({"base": "device_not_selected"})

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={INPUT_ENTRY_DEVICE_SELECTION: ["28.111111111111"]},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["description_placeholders"]["sensor_id"]).to_equal("28.111111111111")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]["device_options"]["28.111111111111"]["precision"]).to_equal(
        "temperature"
    )


@test
async def user_options_set_single(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry),
    _reg: dr.DeviceRegistry = Depends(filled_device_registry),
) -> None:
    """Test configuring a single device."""
    hass.config_entries.async_update_entry(entry, options={})

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    result = await hass.config_entries.options.async_init(entry.entry_id)
    expect(result["data_schema"].schema["device_selection"].options).to_equal(
        {
            "28.111111111111": False,
            "28.222222222222": False,
            "28.222222222223": False,
        }
    )

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={INPUT_ENTRY_DEVICE_SELECTION: ["28.111111111111"]},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["description_placeholders"]["sensor_id"]).to_equal("28.111111111111")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]["device_options"]["28.111111111111"]["precision"]).to_equal(
        "temperature"
    )


@test
async def user_options_set_multiple(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry),
    device_registry: dr.DeviceRegistry = Depends(filled_device_registry),
) -> None:
    """Test configuring multiple consecutive devices in a row."""
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    for reg_entry in dr.async_entries_for_config_entry(
        device_registry, entry.entry_id
    ):
        device_registry.async_update_device(reg_entry.id, name_by_user="Given Name")
    result = await hass.config_entries.options.async_init(entry.entry_id)
    expect(result["data_schema"].schema["device_selection"].options).to_equal(
        {
            "Given Name (28.111111111111)": False,
            "Given Name (28.222222222222)": False,
            "Given Name (28.222222222223)": False,
        }
    )

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            INPUT_ENTRY_DEVICE_SELECTION: [
                "Given Name (28.111111111111)",
                "Given Name (28.222222222222)",
            ]
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["description_placeholders"]["sensor_id"]).to_equal(
        "Given Name (28.222222222222)"
    )

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"precision": "temperature"},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["description_placeholders"]["sensor_id"]).to_equal(
        "Given Name (28.111111111111)"
    )

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"precision": "temperature9"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]["device_options"]["28.222222222222"]["precision"]).to_equal(
        "temperature"
    )
    expect(result["data"]["device_options"]["28.111111111111"]["precision"]).to_equal(
        "temperature9"
    )


@test
async def user_options_no_devices(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test that options does not change when no devices are available."""
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_configurable_devices")
