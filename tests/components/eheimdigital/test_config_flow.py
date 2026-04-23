"""Tests the config flow of EHEIM Digital."""

from ipaddress import ip_address
from unittest.mock import AsyncMock, MagicMock, patch

from aiohttp import ClientConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.eheimdigital.const import DOMAIN
from homeassistant.config_entries import (
    SOURCE_RECONFIGURE,
    SOURCE_USER,
    SOURCE_ZEROCONF,
)
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from tests.common import MockConfigEntry
from tests.components.eheimdigital._fixtures import (
    classic_led_ctrl_mock,
    classic_vario_mock,
    eheimdigital_hub_mock,
    filter_mock,
    heater_mock,
    init_integration,
    mock_config_entry,
    mock_zeroconf,
    reeflex_mock,
)
from tests.hass_fixtures import hass, mock_network

ZEROCONF_DISCOVERY = ZeroconfServiceInfo(
    ip_address=ip_address("192.0.2.1"),
    ip_addresses=[ip_address("192.0.2.1")],
    hostname="eheimdigital.local.",
    name="eheimdigital._http._tcp.local.",
    port=80,
    type="_http._tcp.local.",
    properties={},
)

USER_INPUT = {CONF_HOST: "eheimdigital"}


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


# Re-export nested fixtures so Tryke's static AST discovery can resolve the chain.
classic_led_ctrl_mock = classic_led_ctrl_mock  # noqa: F811
heater_mock = heater_mock  # noqa: F811
classic_vario_mock = classic_vario_mock  # noqa: F811
filter_mock = filter_mock  # noqa: F811
reeflex_mock = reeflex_mock  # noqa: F811


@test
@patch("homeassistant.components.eheimdigital.config_flow.asyncio.Event", new=AsyncMock)
async def full_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    eheimdigital_hub_mock: AsyncMock = Depends(eheimdigital_hub_mock),
) -> None:
    """Test full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    await hass.async_block_till_done()
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    await hass.async_block_till_done()
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(USER_INPUT[CONF_HOST])
    expect(result["data"]).to_equal(USER_INPUT)
    expect(result["result"].unique_id).to_equal(
        eheimdigital_hub_mock.return_value.main.mac_address
    )


@test.cases(
    test.case("cannot_connect", ClientConnectionError(), "cannot_connect"),
    test.case("unknown", Exception(), "unknown"),
)
@patch("homeassistant.components.eheimdigital.config_flow.asyncio.Event", new=AsyncMock)
async def flow_errors(
    side_effect: BaseException,
    error_value: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    eheimdigital_hub_mock: AsyncMock = Depends(eheimdigital_hub_mock),
) -> None:
    """Test flow errors."""
    eheimdigital_hub_mock.return_value.connect.side_effect = side_effect

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    await hass.async_block_till_done()
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({"base": error_value})

    eheimdigital_hub_mock.return_value.connect.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(USER_INPUT[CONF_HOST])
    expect(result["data"]).to_equal(USER_INPUT)
    expect(result["result"].unique_id).to_equal(
        eheimdigital_hub_mock.return_value.main.mac_address
    )


@test
@patch("homeassistant.components.eheimdigital.config_flow.asyncio.Event", new=AsyncMock)
async def zeroconf_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    eheimdigital_hub_mock: AsyncMock = Depends(eheimdigital_hub_mock),
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

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    await hass.async_block_till_done()
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(ZEROCONF_DISCOVERY.host)
    expect(result["data"]).to_equal({CONF_HOST: ZEROCONF_DISCOVERY.host})
    expect(result["result"].unique_id).to_equal(
        eheimdigital_hub_mock.return_value.main.mac_address
    )


@test.cases(
    test.case("cannot_connect", ClientConnectionError(), "cannot_connect"),
    test.case("unknown", Exception(), "unknown"),
)
@patch("homeassistant.components.eheimdigital.config_flow.asyncio.Event", new=AsyncMock)
async def zeroconf_flow_errors(
    side_effect: BaseException,
    error_value: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    eheimdigital_hub_mock: MagicMock = Depends(eheimdigital_hub_mock),
) -> None:
    """Test zeroconf flow errors."""
    eheimdigital_hub_mock.return_value.connect.side_effect = side_effect

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY,
    )
    await hass.async_block_till_done()
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal(error_value)


@test
@patch("homeassistant.components.eheimdigital.config_flow.asyncio.Event", new=AsyncMock)
async def abort(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    eheimdigital_hub_mock: AsyncMock = Depends(eheimdigital_hub_mock),
) -> None:
    """Test flow abort on matching data or unique_id."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    await hass.async_block_till_done()
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    await hass.async_block_till_done()
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(USER_INPUT[CONF_HOST])
    expect(result["data"]).to_equal(USER_INPUT)
    expect(result["result"].unique_id).to_equal(
        eheimdigital_hub_mock.return_value.main.mac_address
    )

    result2 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    await hass.async_block_till_done()
    expect(result2["type"] is FlowResultType.FORM).to_be(True)
    expect(result2["step_id"]).to_equal("user")

    result2 = await hass.config_entries.flow.async_configure(
        result2["flow_id"], USER_INPUT
    )
    await hass.async_block_till_done()
    expect(result2["type"] is FlowResultType.ABORT).to_be(True)
    expect(result2["reason"]).to_equal("already_configured")

    result3 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    await hass.async_block_till_done()
    expect(result3["type"] is FlowResultType.FORM).to_be(True)
    expect(result3["step_id"]).to_equal("user")

    result2 = await hass.config_entries.flow.async_configure(
        result3["flow_id"], {CONF_HOST: "eheimdigital2"}
    )
    await hass.async_block_till_done()
    expect(result2["type"] is FlowResultType.ABORT).to_be(True)
    expect(result2["reason"]).to_equal("already_configured")


@test.cases(
    test.case("cannot_connect", ClientConnectionError(), "cannot_connect"),
    test.case("unknown", Exception(), "unknown"),
)
@patch("homeassistant.components.eheimdigital.config_flow.asyncio.Event", new=AsyncMock)
async def reconfigure(
    side_effect: Exception,
    error_value: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    eheimdigital_hub_mock: AsyncMock = Depends(eheimdigital_hub_mock),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfigure flow."""
    await init_integration(hass, mock_config_entry)

    result = await mock_config_entry.start_reconfigure_flow(hass)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal(SOURCE_RECONFIGURE)

    eheimdigital_hub_mock.return_value.connect.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    await hass.async_block_till_done()
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({"base": error_value})

    eheimdigital_hub_mock.return_value.connect.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    await hass.async_block_till_done()
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(mock_config_entry.unique_id).to_equal(
        eheimdigital_hub_mock.return_value.main.mac_address
    )


@test
@patch("homeassistant.components.eheimdigital.config_flow.asyncio.Event", new=AsyncMock)
async def reconfigure_different_device(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    eheimdigital_hub_mock: AsyncMock = Depends(eheimdigital_hub_mock),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfigure flow with a different device."""
    await init_integration(hass, mock_config_entry)

    eheimdigital_hub_mock.return_value.main.mac_address = "00:00:00:00:00:02"

    result = await mock_config_entry.start_reconfigure_flow(hass)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal(SOURCE_RECONFIGURE)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    await hass.async_block_till_done()
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("unique_id_mismatch")
