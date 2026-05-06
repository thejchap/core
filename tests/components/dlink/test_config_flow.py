"""Test D-Link Smart Plug config flow."""

from unittest.mock import MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.dlink.const import DEFAULT_NAME, DOMAIN
from homeassistant.config_entries import SOURCE_DHCP, SOURCE_USER
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from tests.common import MockConfigEntry
from tests.components.dlink._fixtures import (
    CONF_DATA,
    CONF_DHCP_DATA,
    CONF_DHCP_FLOW,
    CONF_DHCP_FLOW_NEW_IP,
    config_entry,
    config_entry_with_uid,
    mock_zeroconf,
    mocked_plug,
    mocked_plug_legacy,
    mocked_plug_legacy_no_auth,
    patch_config_flow,
)
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


def _patch_setup_entry():
    return patch("homeassistant.components.dlink.async_setup_entry", return_value=True)


@test
async def flow_user(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    mocked_plug: MagicMock = Depends(mocked_plug),
) -> None:
    """Test user initialized flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    with patch_config_flow(mocked_plug), _patch_setup_entry():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONF_DATA,
        )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(DEFAULT_NAME)
    expect(result["data"]).to_equal(CONF_DATA)


@test
async def flow_user_already_configured(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _config_entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test user initialized flow with duplicate server."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=CONF_DATA
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test
async def flow_user_cannot_connect(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    mocked_plug_legacy: MagicMock = Depends(mocked_plug_legacy),
    mocked_plug_legacy_no_auth: MagicMock = Depends(mocked_plug_legacy_no_auth),
) -> None:
    """Test user initialized flow with unreachable server."""
    with patch_config_flow(mocked_plug_legacy_no_auth):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONF_DATA
        )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]["base"]).to_equal("cannot_connect")

    with patch_config_flow(mocked_plug_legacy), _patch_setup_entry():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONF_DATA,
        )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(DEFAULT_NAME)
    expect(result["data"]).to_equal(CONF_DATA)


@test
async def flow_user_unknown_error(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    mocked_plug: MagicMock = Depends(mocked_plug),
) -> None:
    """Test user initialized flow with unreachable server."""
    with patch_config_flow(mocked_plug) as mock:
        mock.side_effect = Exception
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONF_DATA
        )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]["base"]).to_equal("unknown")

    with patch_config_flow(mocked_plug), _patch_setup_entry():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONF_DATA,
        )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(DEFAULT_NAME)
    expect(result["data"]).to_equal(CONF_DATA)


@test
async def dhcp(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    mocked_plug: MagicMock = Depends(mocked_plug),
) -> None:
    """Test we can process the discovery from dhcp."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=CONF_DHCP_FLOW
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("confirm_discovery")
    with patch_config_flow(mocked_plug), _patch_setup_entry():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONF_DHCP_DATA,
        )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(DEFAULT_NAME)
    expect(result["data"]).to_equal(CONF_DATA)


@test
async def dhcp_failed_legacy_auth(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    mocked_plug: MagicMock = Depends(mocked_plug),
    mocked_plug_legacy_no_auth: MagicMock = Depends(mocked_plug_legacy_no_auth),
) -> None:
    """Test we can recover from failed legacy authentication during dhcp flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=CONF_DHCP_FLOW
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("confirm_discovery")
    with patch_config_flow(mocked_plug_legacy_no_auth):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONF_DHCP_DATA,
        )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]["base"]).to_equal("cannot_connect")

    with patch_config_flow(mocked_plug), _patch_setup_entry():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONF_DHCP_DATA,
        )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(DEFAULT_NAME)
    expect(result["data"]).to_equal(CONF_DATA)


@test
async def dhcp_already_configured(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    config_entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test dhcp initialized flow with duplicate server."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=CONF_DHCP_FLOW
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")
    expect(config_entry.unique_id).to_equal("aabbccddeeff")


@test
async def dhcp_unique_id_assignment(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    mocked_plug: MagicMock = Depends(mocked_plug),
) -> None:
    """Test dhcp initialized flow with no unique id for matching entry."""
    dhcp_data = DhcpServiceInfo(
        ip="2.3.4.5",
        macaddress="112233445566",
        hostname="dsp-w215",
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=dhcp_data
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("confirm_discovery")
    with patch_config_flow(mocked_plug), _patch_setup_entry():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONF_DHCP_DATA,
        )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["data"]).to_equal(CONF_DATA | {CONF_HOST: "2.3.4.5"})
    expect(result["result"].unique_id).to_equal("112233445566")


@test
async def dhcp_changed_ip(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    config_entry_with_uid: MockConfigEntry = Depends(config_entry_with_uid),
) -> None:
    """Test that we successfully change IP address for device with known mac address."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=CONF_DHCP_FLOW_NEW_IP
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")
    expect(config_entry_with_uid.data[CONF_HOST]).to_equal("5.6.7.8")
