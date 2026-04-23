"""Tests for the AirGradient config flow."""

from ipaddress import ip_address
from unittest.mock import AsyncMock

from airgradient import (
    AirGradientConnectionError,
    AirGradientParseError,
    ConfigurationControl,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.airgradient.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from tests.common import MockConfigEntry
from tests.components.airgradient._fixtures import (
    mock_airgradient_client,
    mock_cloud_airgradient_client,
    mock_config_entry,
    mock_new_airgradient_client,
    mock_setup_entry,
    mock_zeroconf,
)
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


OLD_ZEROCONF_DISCOVERY = ZeroconfServiceInfo(
    ip_address=ip_address("10.0.0.131"),
    ip_addresses=[ip_address("10.0.0.131")],
    hostname="airgradient_84fce612f5b8.local.",
    name="airgradient_84fce612f5b8._airgradient._tcp.local.",
    port=80,
    type="_airgradient._tcp.local.",
    properties={
        "vendor": "AirGradient",
        "fw_ver": "3.0.8",
        "serialno": "84fce612f5b8",
        "model": "I-9PSL",
    },
)

ZEROCONF_DISCOVERY = ZeroconfServiceInfo(
    ip_address=ip_address("10.0.0.131"),
    ip_addresses=[ip_address("10.0.0.131")],
    hostname="airgradient_84fce612f5b8.local.",
    name="airgradient_84fce612f5b8._airgradient._tcp.local.",
    port=80,
    type="_airgradient._tcp.local.",
    properties={
        "vendor": "AirGradient",
        "fw_ver": "3.1.1",
        "serialno": "84fce612f5b8",
        "model": "I-9PSL",
    },
)


@test
async def full_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_new_airgradient_client: AsyncMock = Depends(mock_new_airgradient_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    await hass.async_block_till_done()
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "10.0.0.131"},
    )
    await hass.async_block_till_done()
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("I-9PSL")
    expect(result["data"]).to_equal({CONF_HOST: "10.0.0.131"})
    expect(result["result"].unique_id).to_equal("84fce612f5b8")
    mock_new_airgradient_client.set_configuration_control.assert_awaited_once_with(
        ConfigurationControl.LOCAL
    )


@test
async def flow_with_registered_device(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_cloud_airgradient_client: AsyncMock = Depends(mock_cloud_airgradient_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we don't revert the cloud setting."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "10.0.0.131"},
    )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["result"].unique_id).to_equal("84fce612f5b8")
    mock_cloud_airgradient_client.set_configuration_control.assert_not_called()


@test
async def flow_errors(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_airgradient_client: AsyncMock = Depends(mock_airgradient_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test flow errors."""
    mock_airgradient_client.get_current_measures.side_effect = (
        AirGradientConnectionError()
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    await hass.async_block_till_done()
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "10.0.0.131"},
    )
    await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    mock_airgradient_client.get_current_measures.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "10.0.0.131"},
    )
    await hass.async_block_till_done()
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)


@test
async def flow_old_firmware_version(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_airgradient_client: AsyncMock = Depends(mock_airgradient_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test flow with old firmware version."""
    mock_airgradient_client.get_current_measures.side_effect = AirGradientParseError

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    await hass.async_block_till_done()
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "10.0.0.131"},
    )
    await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("invalid_version")


@test
async def duplicate(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_airgradient_client: AsyncMock = Depends(mock_airgradient_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test duplicate flow."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    await hass.async_block_till_done()
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "10.0.0.131"},
    )
    await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test
async def zeroconf_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_new_airgradient_client: AsyncMock = Depends(mock_new_airgradient_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test zeroconf flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY,
    )
    await hass.async_block_till_done()
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("discovery_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    await hass.async_block_till_done()
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("I-9PSL")
    expect(result["data"]).to_equal({CONF_HOST: "10.0.0.131"})
    expect(result["result"].unique_id).to_equal("84fce612f5b8")
    mock_new_airgradient_client.set_configuration_control.assert_awaited_once_with(
        ConfigurationControl.LOCAL
    )


@test
async def zeroconf_flow_cloud_device(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_cloud_airgradient_client: AsyncMock = Depends(mock_cloud_airgradient_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test zeroconf flow doesn't revert the cloud setting."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY,
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("discovery_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    mock_cloud_airgradient_client.set_configuration_control.assert_not_called()


@test
async def zeroconf_flow_abort_old_firmware(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test zeroconf flow aborts with old firmware."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=OLD_ZEROCONF_DISCOVERY,
    )
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("invalid_version")


@test
async def zeroconf_flow_abort_duplicate(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test zeroconf flow aborts with duplicate."""
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY,
    )
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test
async def user_flow_works_discovery(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_new_airgradient_client: AsyncMock = Depends(mock_new_airgradient_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test user flow can continue after discovery happened."""
    await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY,
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(len(hass.config_entries.flow.async_progress(DOMAIN))).to_equal(2)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "10.0.0.131"},
    )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)

    expect(not hass.config_entries.flow.async_progress(DOMAIN)).to_be(True)


@test
async def reconfigure_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_new_airgradient_client: AsyncMock = Depends(mock_new_airgradient_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfigure flow."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reconfigure_flow(hass)

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "10.0.0.131"},
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(mock_config_entry.data).to_equal({CONF_HOST: "10.0.0.131"})


@test
async def reconfigure_flow_errors(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_new_airgradient_client: AsyncMock = Depends(mock_new_airgradient_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfigure flow."""
    mock_config_entry.add_to_hass(hass)
    mock_new_airgradient_client.get_current_measures.side_effect = (
        AirGradientConnectionError()
    )

    result = await mock_config_entry.start_reconfigure_flow(hass)

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "10.0.0.132"},
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    mock_new_airgradient_client.get_current_measures.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "10.0.0.132"},
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(mock_config_entry.data).to_equal({CONF_HOST: "10.0.0.132"})


@test
async def reconfigure_flow_unique_id_mismatch(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: None = Depends(mock_zeroconf),
    mock_new_airgradient_client: AsyncMock = Depends(mock_new_airgradient_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfigure flow aborts with unique id mismatch."""
    mock_config_entry.add_to_hass(hass)

    mock_new_airgradient_client.get_current_measures.return_value.serial_number = (
        "84fce612f5b9"
    )

    result = await mock_config_entry.start_reconfigure_flow(hass)

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "10.0.0.132"},
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("unique_id_mismatch")
    expect(mock_config_entry.data).to_equal({CONF_HOST: "10.0.0.131"})
