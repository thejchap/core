"""Test the IntelliFire config flow."""

from unittest.mock import AsyncMock

from intellifire4py.exceptions import LoginError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.intellifire.const import (
    API_MODE_CLOUD,
    API_MODE_LOCAL,
    CONF_CONTROL_MODE,
    CONF_READ_MODE,
    CONF_SERIAL,
    DOMAIN,
)
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from ._fixtures import (
    mock_apis_multifp,
    mock_apis_single_fp,
    mock_config_entry_current,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def standard_config_with_single_fireplace(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _apis: tuple[AsyncMock, AsyncMock, AsyncMock] = Depends(mock_apis_single_fp),
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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry_current),
    _apis: tuple[AsyncMock, AsyncMock, AsyncMock] = Depends(mock_apis_single_fp),
) -> None:
    """What if we try to configure an already configured fireplace."""
    config_entry.add_to_hass(hass)

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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    apis: tuple[AsyncMock, AsyncMock, AsyncMock] = Depends(mock_apis_single_fp),
) -> None:
    """Test bad credentials on a login."""
    _mock_local_interface, mock_cloud_interface, _mock_fp = apis
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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _apis: tuple[AsyncMock, AsyncMock, AsyncMock] = Depends(mock_apis_multifp),
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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _apis: tuple[AsyncMock, AsyncMock, AsyncMock] = Depends(mock_apis_multifp),
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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    apis: tuple[AsyncMock, AsyncMock, AsyncMock] = Depends(mock_apis_multifp),
) -> None:
    """Test successful DHCP Discovery of a non intellifire device.."""
    mock_local_interface, _mock_cloud_interface, _mock_fp = apis
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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry_current),
    _apis: tuple[AsyncMock, AsyncMock, AsyncMock] = Depends(mock_apis_single_fp),
) -> None:
    """Test reauth."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    result["step_id"] = "cloud_api"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "donJulio", CONF_PASSWORD: "Tequila0FD00m"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry_current),
    apis: tuple[AsyncMock, AsyncMock, AsyncMock] = Depends(mock_apis_single_fp),
) -> None:
    """Test options flow for changing read/control modes."""
    _mock_local, _mock_cloud, mock_fp = apis

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    mock_fp.local_connectivity = True
    mock_fp.cloud_connectivity = True

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_READ_MODE: API_MODE_CLOUD, CONF_CONTROL_MODE: API_MODE_LOCAL},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            CONF_READ_MODE: API_MODE_CLOUD,
            CONF_CONTROL_MODE: API_MODE_LOCAL,
        }
    )


@test
async def options_flow_local_read_unavailable(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry_current),
    apis: tuple[AsyncMock, AsyncMock, AsyncMock] = Depends(mock_apis_single_fp),
) -> None:
    """Test options flow shows error when local connectivity unavailable for read mode."""
    _mock_local, _mock_cloud, mock_fp = apis

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    mock_fp.local_connectivity = False
    mock_fp.cloud_connectivity = True

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_READ_MODE: API_MODE_LOCAL, CONF_CONTROL_MODE: API_MODE_CLOUD},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({CONF_READ_MODE: "local_unavailable"})
    mock_fp.async_validate_connectivity.assert_called_once()


@test
async def options_flow_local_control_unavailable(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry_current),
    apis: tuple[AsyncMock, AsyncMock, AsyncMock] = Depends(mock_apis_single_fp),
) -> None:
    """Test options flow shows error when local connectivity unavailable for control mode."""
    _mock_local, _mock_cloud, mock_fp = apis

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    mock_fp.local_connectivity = False
    mock_fp.cloud_connectivity = True

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_READ_MODE: API_MODE_CLOUD, CONF_CONTROL_MODE: API_MODE_LOCAL},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({CONF_CONTROL_MODE: "local_unavailable"})


@test
async def options_flow_cloud_read_unavailable(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry_current),
    apis: tuple[AsyncMock, AsyncMock, AsyncMock] = Depends(mock_apis_single_fp),
) -> None:
    """Test options flow shows error when cloud connectivity unavailable for read mode."""
    _mock_local, _mock_cloud, mock_fp = apis

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    mock_fp.local_connectivity = True
    mock_fp.cloud_connectivity = False

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_READ_MODE: API_MODE_CLOUD, CONF_CONTROL_MODE: API_MODE_LOCAL},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({CONF_READ_MODE: "cloud_unavailable"})
    mock_fp.async_validate_connectivity.assert_called_once()


@test
async def options_flow_cloud_control_unavailable(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry_current),
    apis: tuple[AsyncMock, AsyncMock, AsyncMock] = Depends(mock_apis_single_fp),
) -> None:
    """Test options flow shows error when cloud connectivity unavailable for control mode."""
    _mock_local, _mock_cloud, mock_fp = apis

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    mock_fp.local_connectivity = True
    mock_fp.cloud_connectivity = False

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_READ_MODE: API_MODE_LOCAL, CONF_CONTROL_MODE: API_MODE_CLOUD},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({CONF_CONTROL_MODE: "cloud_unavailable"})
