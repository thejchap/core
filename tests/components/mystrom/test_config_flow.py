"""Test the myStrom config flow."""

from unittest.mock import AsyncMock, patch

from pymystrom.exceptions import MyStromConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.mystrom.const import DOMAIN
from homeassistant.config_entries import SOURCE_DHCP
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from ._fixtures import DEVICE_MAC, config_entry, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

DHCP_SERVICE_INFO = DhcpServiceInfo(
    ip="1.2.3.4",
    hostname="mystrom-switch-946498",
    macaddress="083a8d946498",
)


@fixture
def _trigger_executor(
    _mn: None = Depends(mock_network),
    _mse: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Trigger the hook executor path."""
    return None


@test
async def form_combined(
    hass: HomeAssistant = Depends(hass_fixture),
    _mse: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    with patch(
        "pymystrom.get_device_info",
        side_effect=AsyncMock(return_value={"type": 101, "mac": DEVICE_MAC}),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "1.1.1.1"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("myStrom Device")
    expect(result2["data"]).to_equal({"host": "1.1.1.1"})


@test
async def form_duplicates(
    hass: HomeAssistant = Depends(hass_fixture),
    _mse: AsyncMock = Depends(mock_setup_entry),
    _cfg: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test abort on duplicate."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    with patch(
        "pymystrom.get_device_info",
        return_value={"type": 101, "mac": DEVICE_MAC},
    ) as mock_session:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "1.1.1.1"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")

    mock_session.assert_called_once()


@test
async def wrong_answer_from_device(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test handling of wrong answers from the device."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})
    with patch(
        "pymystrom.get_device_info",
        side_effect=MyStromConnectionError(),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "1.1.1.1"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("user")
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})

    with patch(
        "pymystrom.get_device_info",
        return_value={"type": 101, "mac": DEVICE_MAC},
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "1.1.1.1"},
        )
        await hass.async_block_till_done()
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("myStrom Device")
    expect(result2["data"]).to_equal({"host": "1.1.1.1"})


@test
async def dhcp_discovery(
    hass: HomeAssistant = Depends(hass_fixture),
    _mse: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test DHCP discovery shows a confirmation form and creates an entry."""
    with patch(
        "homeassistant.components.mystrom.config_flow.pymystrom.get_device_info",
        return_value={"type": 101, "mac": DEVICE_MAC},
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_DHCP},
            data=DHCP_SERVICE_INFO,
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("myStrom Device")
    expect(result["data"]).to_equal({"host": DHCP_SERVICE_INFO.ip})
    expect(result["result"].unique_id).to_equal("083A8D946498")


@test
async def dhcp_discovery_cannot_connect(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test DHCP discovery aborts when the device is unreachable."""
    with patch(
        "homeassistant.components.mystrom.config_flow.pymystrom.get_device_info",
        side_effect=MyStromConnectionError(),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_DHCP},
            data=DHCP_SERVICE_INFO,
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def dhcp_discovery_already_configured_updates_host(
    hass: HomeAssistant = Depends(hass_fixture),
    _mse: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test DHCP discovery updates the host of an already-configured entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="083A8D946498",
        data={CONF_HOST: "1.1.1.1"},
        title="myStrom Device",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DHCP_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(entry.data["host"]).to_equal(DHCP_SERVICE_INFO.ip)
