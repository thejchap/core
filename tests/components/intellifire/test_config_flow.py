"""Test the IntelliFire config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

from intellifire4py.exceptions import LoginError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.intellifire.const import DOMAIN, CONF_SERIAL
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from tests.common import MockConfigEntry
from tests.components.intellifire._fixtures import (
    mock_apis_multifp,
    mock_apis_single_fp,
    mock_cloud_interface,
    mock_common_data_local,
    mock_config_entry_current,
    mock_fp,
    mock_local_interface,
    mock_setup_entry,
)
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _mock_zeroconf() -> MagicMock:
    """Patch zeroconf so tests don't require a real zeroconf instance."""
    from zeroconf import DNSCache

    with (
        patch("homeassistant.components.zeroconf.HaZeroconf") as mock_zc,
        patch("homeassistant.components.zeroconf.discovery.AsyncServiceBrowser"),
    ):
        zc = mock_zc.return_value
        zc.async_add_service_listener = AsyncMock()
        zc.async_remove_service_listener = AsyncMock()
        zc.async_register_service = AsyncMock()
        zc.async_update_service = AsyncMock()
        zc.cache = DNSCache()
        yield mock_zc


@fixture
def _trigger_executor(
    _mn: None = Depends(mock_network),
    _mz: MagicMock = Depends(_mock_zeroconf),
) -> None:
    """Trigger the hook executor path."""
    return None


@test
async def standard_config_with_single_fireplace(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_apis_single_fp: tuple = Depends(mock_apis_single_fp),
) -> None:
    """Test standard flow with a user who has only a single fireplace."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    expect(result["step_id"]).to_equal("cloud_api")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "donJulio", CONF_PASSWORD: "Tequila0FD00m"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            "ip_address": "192.168.2.108",
            "api_key": "B5C4DA27AAEF31D1FB21AFF9BFA6BCD2",
            "serial": "3FB284769E4736F30C8973A7ED358123",
            "auth_cookie": "B984F21A6378560019F8A1CDE41B6782",
            "web_client_id": "FA2B1C3045601234D0AE17D72F8E975",
            "user_id": "52C3F9E8B9D3AC99F8E4D12345678901FE9A2BC7D85F7654E28BF98BCD123456",
            "username": "grumpypanda@china.cn",
            "password": "you-stole-my-pandas",
        }
    )


@test
async def standard_config_with_pre_configured_fireplace(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry_current: MockConfigEntry = Depends(mock_config_entry_current),
    _mock_apis_single_fp: tuple = Depends(mock_apis_single_fp),
) -> None:
    """What if we try to configure an already configured fireplace."""
    mock_config_entry_current.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    expect(result["step_id"]).to_equal("cloud_api")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "donJulio", CONF_PASSWORD: "Tequila0FD00m"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_available_devices")


@test
async def standard_config_with_single_fireplace_and_bad_credentials(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_apis_single_fp: tuple = Depends(mock_apis_single_fp),
) -> None:
    """Test bad credentials on a login."""
    _mock_local_interface, mock_cloud_interface, _mock_fp = mock_apis_single_fp
    mock_cloud_interface.login_with_credentials.side_effect = LoginError

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    expect(result["step_id"]).to_equal("cloud_api")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "donJulio", CONF_PASSWORD: "Tequila0FD00m"},
    )

    mock_cloud_interface.login_with_credentials.side_effect = None

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "api_error"})
    expect(result["step_id"]).to_equal("cloud_api")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "donJulio", CONF_PASSWORD: "Tequila0FD00m"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            "ip_address": "192.168.2.108",
            "api_key": "B5C4DA27AAEF31D1FB21AFF9BFA6BCD2",
            "serial": "3FB284769E4736F30C8973A7ED358123",
            "auth_cookie": "B984F21A6378560019F8A1CDE41B6782",
            "web_client_id": "FA2B1C3045601234D0AE17D72F8E975",
            "user_id": "52C3F9E8B9D3AC99F8E4D12345678901FE9A2BC7D85F7654E28BF98BCD123456",
            "username": "grumpypanda@china.cn",
            "password": "you-stole-my-pandas",
        }
    )


@test
async def standard_config_with_multiple_fireplace(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_apis_multifp: tuple = Depends(mock_apis_multifp),
) -> None:
    """Test multi-fireplace user who must be very rich."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    expect(result["step_id"]).to_equal("cloud_api")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "donJulio", CONF_PASSWORD: "Tequila0FD00m"},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("pick_cloud_device")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_SERIAL: "4GC295860E5837G40D9974B7FD459234"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            "ip_address": "192.168.2.109",
            "api_key": "D4C5EB28BBFF41E1FB21AFF9BFA6CD34",
            "serial": "4GC295860E5837G40D9974B7FD459234",
            "auth_cookie": "B984F21A6378560019F8A1CDE41B6782",
            "web_client_id": "FA2B1C3045601234D0AE17D72F8E975",
            "user_id": "52C3F9E8B9D3AC99F8E4D12345678901FE9A2BC7D85F7654E28BF98BCD123456",
            "username": "grumpypanda@china.cn",
            "password": "you-stole-my-pandas",
        }
    )


@test
async def dhcp_discovery_intellifire_device(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_apis_multifp: tuple = Depends(mock_apis_multifp),
) -> None:
    """Test successful DHCP Discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="1.1.1.1",
            macaddress="aabbcceeddff",
            hostname="zentrios-Test",
        ),
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("cloud_api")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "donJulio", CONF_PASSWORD: "Tequila0FD00m"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def dhcp_discovery_non_intellifire_device(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_apis_multifp: tuple = Depends(mock_apis_multifp),
) -> None:
    """Test successful DHCP Discovery of a non intellifire device."""
    mock_local_interface, _mock_cloud_interface, _mock_fp = mock_apis_multifp
    mock_local_interface.poll.side_effect = ConnectionError

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="1.1.1.1",
            macaddress="aabbcceeddff",
            hostname="zentrios-Evil",
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("not_intellifire_device")


@test
async def reauth_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry_current: MockConfigEntry = Depends(mock_config_entry_current),
    _mock_apis_single_fp: tuple = Depends(mock_apis_single_fp),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test reauth."""
    mock_config_entry_current.add_to_hass(hass)
    result = await mock_config_entry_current.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "donJulio", CONF_PASSWORD: "Tequila0FD00m"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
