"""Test the Teltonika config flow."""

from unittest.mock import AsyncMock, MagicMock

from teltasync import TeltonikaAuthenticationError, TeltonikaConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.teltonika.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from ._fixtures import (
    mock_config_entry,
    mock_setup_entry,
    mock_teltasync,
    mock_teltasync_client,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form_user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _teltasync: MagicMock = Depends(mock_teltasync),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form and can create an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.1.1",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "password",
            CONF_VERIFY_SSL: False,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("RUTX50 Test")
    expect(dict(result["data"])).to_equal(
        {
            CONF_HOST: "https://192.168.1.1",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "password",
            CONF_VERIFY_SSL: False,
        }
    )
    expect(result["result"].unique_id).to_equal("1234567890")


@test.cases(
    test.case(
        "invalid_auth",
        exception=TeltonikaAuthenticationError("Invalid credentials"),
        error_key="invalid_auth",
    ),
    test.case(
        "cannot_connect",
        exception=TeltonikaConnectionError("Connection failed"),
        error_key="cannot_connect",
    ),
    test.case(
        "unknown",
        exception=ValueError("Unexpected error"),
        error_key="unknown",
    ),
)
async def form_error_with_recovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    teltasync_client: MagicMock = Depends(mock_teltasync_client),
    _setup: AsyncMock = Depends(mock_setup_entry),
    *,
    exception: Exception,
    error_key: str,
) -> None:
    """Test we handle errors in config form and can recover."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    teltasync_client.get_device_info.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.1.1",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "password",
            CONF_VERIFY_SSL: False,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_key})

    device_info = MagicMock()
    device_info.device_name = "RUTX50 Test"
    device_info.device_identifier = "1234567890"
    teltasync_client.get_device_info.side_effect = None
    teltasync_client.get_device_info.return_value = device_info
    teltasync_client.validate_credentials.return_value = True

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.1.1",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "password",
            CONF_VERIFY_SSL: False,
        },
    )

    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("RUTX50 Test")
    expect(result["data"][CONF_HOST]).to_equal("https://192.168.1.1")
    expect(result["result"].unique_id).to_equal("1234567890")


@test
async def form_duplicate_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _teltasync: MagicMock = Depends(mock_teltasync),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test duplicate config entry is handled."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.1.1",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "password",
            CONF_VERIFY_SSL: False,
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case(
        "ip",
        host_input="192.168.1.1",
        expected_base_url="https://192.168.1.1/api",
        expected_host="https://192.168.1.1",
    ),
    test.case(
        "with_http",
        host_input="http://192.168.1.1",
        expected_base_url="http://192.168.1.1/api",
        expected_host="http://192.168.1.1",
    ),
    test.case(
        "with_https",
        host_input="https://192.168.1.1",
        expected_base_url="https://192.168.1.1/api",
        expected_host="https://192.168.1.1",
    ),
    test.case(
        "with_https_and_api",
        host_input="https://192.168.1.1/api",
        expected_base_url="https://192.168.1.1/api",
        expected_host="https://192.168.1.1",
    ),
    test.case(
        "hostname",
        host_input="device.local",
        expected_base_url="https://device.local/api",
        expected_host="https://device.local",
    ),
)
async def host_url_construction(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    teltasync: MagicMock = Depends(mock_teltasync),
    teltasync_client: MagicMock = Depends(mock_teltasync_client),
    _setup: AsyncMock = Depends(mock_setup_entry),
    *,
    host_input: str,
    expected_base_url: str,
    expected_host: str,
) -> None:
    """Test that host URLs are constructed correctly."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: host_input,
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "password",
            CONF_VERIFY_SSL: False,
        },
    )

    expect(teltasync_client.get_device_info.call_count).to_equal(1)
    call_args = teltasync.call_args_list[0]
    expect(call_args.kwargs["base_url"]).to_equal(expected_base_url)
    expect(call_args.kwargs["verify_ssl"]).to_be(False)

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].data[CONF_HOST]).to_equal(expected_host)


@test
async def form_user_flow_http_fallback(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    teltasync_client: MagicMock = Depends(mock_teltasync_client),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we fall back to HTTP when HTTPS fails."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    teltasync_client.get_device_info.side_effect = [
        TeltonikaConnectionError("HTTPS unavailable"),
        teltasync_client.get_device_info.return_value,
    ]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.1.1",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "password",
            CONF_VERIFY_SSL: False,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"][CONF_HOST]).to_equal("http://192.168.1.1")
    expect(teltasync_client.get_device_info.call_count).to_equal(2)
    expect(teltasync_client.close.call_count).to_equal(2)


@test
async def dhcp_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    teltasync_client: MagicMock = Depends(mock_teltasync_client),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test DHCP discovery flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="192.168.1.50",
            macaddress="209727112233",
            hostname="teltonika",
        ),
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("dhcp_confirm")
    expect("name" in result["description_placeholders"]).to_be(True)
    expect("host" in result["description_placeholders"]).to_be(True)

    device_info = MagicMock()
    device_info.device_name = "RUTX50 Discovered"
    device_info.device_identifier = "DISCOVERED123"
    teltasync_client.get_device_info.return_value = device_info

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("RUTX50 Discovered")
    expect(result["data"][CONF_HOST]).to_equal("https://192.168.1.50")
    expect(result["data"][CONF_USERNAME]).to_equal("admin")
    expect(result["data"][CONF_PASSWORD]).to_equal("password")
    expect(result["result"].unique_id).to_equal("DISCOVERED123")


@test
async def dhcp_discovery_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _teltasync: MagicMock = Depends(mock_teltasync),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test DHCP discovery when device is already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="192.168.1.50",
            macaddress="209727112233",
            hostname="teltonika",
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(config_entry.data[CONF_HOST]).to_equal("192.168.1.50")


@test
async def dhcp_discovery_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    teltasync_client: MagicMock = Depends(mock_teltasync_client),
) -> None:
    """Test DHCP discovery when device is not reachable."""
    teltasync_client.get_device_info.side_effect = TeltonikaConnectionError(
        "Connection failed"
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="192.168.1.50",
            macaddress="209727112233",
            hostname="teltonika",
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test.cases(
    test.case(
        "invalid_auth",
        exception=TeltonikaAuthenticationError("Invalid credentials"),
        error_key="invalid_auth",
    ),
    test.case(
        "cannot_connect",
        exception=TeltonikaConnectionError("Connection failed"),
        error_key="cannot_connect",
    ),
    test.case(
        "unknown",
        exception=ValueError("Unexpected error"),
        error_key="unknown",
    ),
)
async def dhcp_confirm_error_with_recovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    teltasync_client: MagicMock = Depends(mock_teltasync_client),
    _setup: AsyncMock = Depends(mock_setup_entry),
    *,
    exception: Exception,
    error_key: str,
) -> None:
    """Test DHCP confirmation handles errors and can recover."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="192.168.1.50",
            macaddress="209727112233",
            hostname="teltonika",
        ),
    )

    teltasync_client.get_device_info.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_key})
    expect(result["step_id"]).to_equal("dhcp_confirm")

    device_info = MagicMock()
    device_info.device_name = "RUTX50 Discovered"
    device_info.device_identifier = "DISCOVERED123"
    teltasync_client.get_device_info.side_effect = None
    teltasync_client.get_device_info.return_value = device_info
    teltasync_client.validate_credentials.return_value = True

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "password",
        },
    )

    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("RUTX50 Discovered")
    expect(result["data"][CONF_HOST]).to_equal("https://192.168.1.50")
    expect(result["result"].unique_id).to_equal("DISCOVERED123")


@test
async def validate_credentials_false(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    teltasync_client: MagicMock = Depends(mock_teltasync_client),
) -> None:
    """Test config flow when validate_credentials returns False."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    device_info = MagicMock()
    device_info.device_name = "Test Device"
    device_info.device_identifier = "TEST123"

    teltasync_client.get_device_info.return_value = device_info
    teltasync_client.validate_credentials.return_value = False

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.1.1",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "password",
            CONF_VERIFY_SSL: False,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_auth"})


@test
async def reauth_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(mock_teltasync_client),
    _setup: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test successful reauth flow."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "new_password",
        },
    )

    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.data[CONF_USERNAME]).to_equal("admin")
    expect(config_entry.data[CONF_PASSWORD]).to_equal("new_password")
    expect(config_entry.data[CONF_HOST]).to_equal("192.168.1.1")


@test.cases(
    test.case(
        "invalid_auth",
        side_effect=TeltonikaAuthenticationError("Invalid credentials"),
        expected_error="invalid_auth",
    ),
    test.case(
        "cannot_connect",
        side_effect=TeltonikaConnectionError("Connection failed"),
        expected_error="cannot_connect",
    ),
    test.case(
        "unknown",
        side_effect=ValueError("Unexpected error"),
        expected_error="unknown",
    ),
)
async def reauth_flow_errors_with_recovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    teltasync_client: MagicMock = Depends(mock_teltasync_client),
    _setup: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    *,
    side_effect: Exception,
    expected_error: str,
) -> None:
    """Test reauth flow error handling with successful recovery."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)

    teltasync_client.get_device_info.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "bad_password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": expected_error})
    expect(result["step_id"]).to_equal("reauth_confirm")

    teltasync_client.get_device_info.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "new_password",
        },
    )

    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.data[CONF_USERNAME]).to_equal("admin")
    expect(config_entry.data[CONF_PASSWORD]).to_equal("new_password")
    expect(config_entry.data[CONF_HOST]).to_equal("192.168.1.1")


@test
async def reauth_flow_wrong_account(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    teltasync_client: MagicMock = Depends(mock_teltasync_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauth flow aborts when device serial doesn't match."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)

    device_info = MagicMock()
    device_info.device_name = "RUTX50 Different"
    device_info.device_identifier = "DIFFERENT1234567890"
    teltasync_client.get_device_info = AsyncMock(return_value=device_info)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "password",
        },
    )

    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("wrong_account")
