"""Tests for Overkiz config flow."""

from __future__ import annotations

from ipaddress import ip_address
from unittest.mock import AsyncMock, Mock, patch

from aiohttp import ClientConnectorCertificateError, ClientError
from pyoverkiz.exceptions import (
    BadCredentialsException,
    MaintenanceException,
    NotSuchTokenException,
    TooManyAttemptsBannedException,
    TooManyRequestsException,
    UnknownUserException,
)
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.overkiz.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

from ._fixtures import (
    mock_async_zeroconf as mock_async_zeroconf_fx,
    mock_setup_entry as mock_setup_entry_fx,
)

TEST_EMAIL = "test@testdomain.com"
TEST_EMAIL2 = "test@testdomain.nl"
TEST_PASSWORD = "test-password"
TEST_PASSWORD2 = "test-password2"
TEST_SERVER = "somfy_europe"
TEST_SERVER2 = "hi_kumo_europe"
TEST_SERVER_COZYTOUCH = "atlantic_cozytouch"
TEST_GATEWAY_ID = "1234-5678-9123"
TEST_GATEWAY_ID2 = "4321-5678-9123"
TEST_GATEWAY_ID3 = "SOMFY_PROTECT-v0NT53occUBPyuJRzx59kalW1hFfzimN"

TEST_HOST = "gateway-1234-5678-9123.local:8443"
TEST_HOST2 = "192.168.11.104:8443"
TEST_TOKEN = "1234123412341234"

MOCK_GATEWAY_RESPONSE = [Mock(id=TEST_GATEWAY_ID)]
MOCK_GATEWAY2_RESPONSE = [Mock(id=TEST_GATEWAY_ID3), Mock(id=TEST_GATEWAY_ID2)]

FAKE_ZERO_CONF_INFO = ZeroconfServiceInfo(
    ip_address=ip_address("192.168.0.51"),
    ip_addresses=[ip_address("192.168.0.51")],
    port=443,
    hostname=f"gateway-{TEST_GATEWAY_ID}.local.",
    type="_kizbox._tcp.local.",
    name=f"gateway-{TEST_GATEWAY_ID}._kizbox._tcp.local.",
    properties={
        "api_version": "1",
        "gateway_pin": TEST_GATEWAY_ID,
        "fw_version": "2021.5.4-29",
    },
)

FAKE_ZERO_CONF_INFO_LOCAL = ZeroconfServiceInfo(
    ip_address=ip_address("192.168.0.51"),
    ip_addresses=[ip_address("192.168.0.51")],
    port=8443,
    hostname=f"gateway-{TEST_GATEWAY_ID}.local.",
    type="_kizboxdev._tcp.local.",
    name=f"gateway-{TEST_GATEWAY_ID}._kizboxdev._tcp.local.",
    properties={
        "api_version": "1",
        "gateway_pin": TEST_GATEWAY_ID,
        "fw_version": "2021.5.4-29",
    },
)


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _mock_setup: AsyncMock = Depends(mock_setup_entry_fx),
    _mock_zc=Depends(mock_async_zeroconf_fx),
) -> None:
    """Wire mock_network, mock_setup_entry, and zeroconf mock for every test."""


@test
async def form_cloud(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"hub": TEST_SERVER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("local_or_cloud")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"api_type": "cloud"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("cloud")

    with (
        patch("pyoverkiz.client.OverkizClient.login", return_value=True),
        patch(
            "pyoverkiz.client.OverkizClient.get_gateways",
            return_value=MOCK_GATEWAY_RESPONSE,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": TEST_EMAIL, "password": TEST_PASSWORD},
        )

    await hass.async_block_till_done()

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_only_cloud_supported(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"hub": TEST_SERVER2},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("cloud")

    with (
        patch("pyoverkiz.client.OverkizClient.login", return_value=True),
        patch(
            "pyoverkiz.client.OverkizClient.get_gateways",
            return_value=MOCK_GATEWAY_RESPONSE,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": TEST_EMAIL, "password": TEST_PASSWORD},
        )

    await hass.async_block_till_done()

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_local_happy_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test local API configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"hub": TEST_SERVER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("local_or_cloud")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"api_type": "local"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("local")

    with patch.multiple(
        "pyoverkiz.client.OverkizClient",
        login=AsyncMock(return_value=True),
        get_gateways=AsyncMock(return_value=MOCK_GATEWAY_RESPONSE),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "gateway-1234-5678-1234.local:8443",
                "token": TEST_TOKEN,
                "verify_ssl": True,
            },
        )

    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("gateway-1234-5678-1234.local:8443")
    expect(result["data"]).to_equal(
        {
            "host": "gateway-1234-5678-1234.local:8443",
            "token": TEST_TOKEN,
            "verify_ssl": True,
            "hub": TEST_SERVER,
            "api_type": "local",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("bad_credentials", BadCredentialsException, "invalid_auth"),
    test.case("too_many_requests", TooManyRequestsException, "too_many_requests"),
    test.case("timeout", TimeoutError, "cannot_connect"),
    test.case("client_error", ClientError, "cannot_connect"),
    test.case("maintenance", MaintenanceException, "server_in_maintenance"),
    test.case(
        "too_many_attempts", TooManyAttemptsBannedException, "too_many_attempts"
    ),
    test.case("unknown_user", UnknownUserException, "unsupported_hardware"),
    test.case("unknown", Exception, "unknown"),
)
async def form_invalid_auth_cloud(
    side_effect: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid auth (cloud)."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"hub": TEST_SERVER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("local_or_cloud")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"api_type": "cloud"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("cloud")

    with patch("pyoverkiz.client.OverkizClient.login", side_effect=side_effect):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": TEST_EMAIL, "password": TEST_PASSWORD},
        )

    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})


@test.cases(
    test.case(
        "cozytouch", UnknownUserException, "CozyTouch", TEST_SERVER_COZYTOUCH
    ),
    test.case("unknown", UnknownUserException, "Unknown", TEST_SERVER2),
)
async def form_invalid_hardware_cloud(
    side_effect: type[Exception],
    description_placeholder: str,
    server: str,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle unsupported hardware (cloud)."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"hub": server},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("cloud")

    with patch("pyoverkiz.client.OverkizClient.login", side_effect=side_effect):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": TEST_EMAIL, "password": TEST_PASSWORD},
        )

    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "unsupported_hardware"})
    expect(result["description_placeholders"]).to_equal(
        {"unsupported_device": description_placeholder}
    )


@test.cases(
    test.case(
        "somfy_protect", UnknownUserException, "Somfy Protect", TEST_SERVER
    ),
)
async def form_invalid_hardware_cloud_local(
    side_effect: type[Exception],
    description_placeholder: str,
    server: str,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle unsupported hardware (cloud and local)."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"hub": server},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"api_type": "cloud"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("cloud")

    with patch("pyoverkiz.client.OverkizClient.login", side_effect=side_effect):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": TEST_EMAIL, "password": TEST_PASSWORD},
        )

    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "unsupported_hardware"})
    expect(result["description_placeholders"]).to_equal(
        {"unsupported_device": description_placeholder}
    )


@test.cases(
    test.case("bad_credentials", BadCredentialsException, "invalid_auth"),
    test.case("too_many_requests", TooManyRequestsException, "too_many_requests"),
    test.case(
        "certificate_verify_failed",
        ClientConnectorCertificateError(Mock(host=TEST_HOST), Exception),
        "certificate_verify_failed",
    ),
    test.case("timeout", TimeoutError, "cannot_connect"),
    test.case("client_error", ClientError, "cannot_connect"),
    test.case("maintenance", MaintenanceException, "server_in_maintenance"),
    test.case(
        "too_many_attempts", TooManyAttemptsBannedException, "too_many_attempts"
    ),
    test.case("unknown_user", UnknownUserException, "unsupported_hardware"),
    test.case("no_such_token", NotSuchTokenException, "invalid_auth"),
    test.case("unknown", Exception, "unknown"),
)
async def form_invalid_auth_local(
    side_effect,
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid auth (local)."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"hub": TEST_SERVER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("local_or_cloud")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"api_type": "local"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("local")

    with patch("pyoverkiz.client.OverkizClient.login", side_effect=side_effect):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": TEST_HOST,
                "token": TEST_TOKEN,
                "verify_ssl": True,
            },
        )

    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})


@test.cases(
    test.case("bad_credentials", BadCredentialsException, "unsupported_hardware"),
)
async def form_invalid_cozytouch_auth(
    side_effect: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid auth (cloud)."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"hub": TEST_SERVER_COZYTOUCH},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("cloud")

    with patch("pyoverkiz.client.OverkizClient.login", side_effect=side_effect):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": TEST_EMAIL, "password": TEST_PASSWORD},
        )

    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})
    expect(result["step_id"]).to_equal("cloud")


@test
async def cloud_abort_on_duplicate_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test we get the form."""
    MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_GATEWAY_ID,
        data={"username": TEST_EMAIL, "password": TEST_PASSWORD, "hub": TEST_SERVER},
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"hub": TEST_SERVER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("local_or_cloud")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"api_type": "cloud"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("cloud")

    with (
        patch("pyoverkiz.client.OverkizClient.login", return_value=True),
        patch(
            "pyoverkiz.client.OverkizClient.get_gateways",
            return_value=MOCK_GATEWAY_RESPONSE,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": TEST_EMAIL, "password": TEST_PASSWORD},
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def local_abort_on_duplicate_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test local API configuration is aborted if gateway already exists."""
    MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_GATEWAY_ID,
        version=2,
        data={
            "host": TEST_HOST,
            "token": TEST_TOKEN,
            "verify_ssl": True,
            "hub": TEST_SERVER,
            "api_type": "local",
        },
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"hub": TEST_SERVER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("local_or_cloud")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"api_type": "local"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("local")

    with patch.multiple(
        "pyoverkiz.client.OverkizClient",
        login=AsyncMock(return_value=True),
        get_gateways=AsyncMock(return_value=MOCK_GATEWAY_RESPONSE),
        get_setup_option=AsyncMock(return_value=True),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": TEST_HOST,
                "token": TEST_TOKEN,
                "verify_ssl": True,
            },
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def cloud_allow_multiple_unique_entries(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test we get the form."""
    MockConfigEntry(
        version=1,
        domain=DOMAIN,
        unique_id=TEST_GATEWAY_ID2,
        data={"username": TEST_EMAIL, "password": TEST_PASSWORD, "hub": TEST_SERVER},
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"hub": TEST_SERVER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("local_or_cloud")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"api_type": "cloud"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("cloud")

    with (
        patch("pyoverkiz.client.OverkizClient.login", return_value=True),
        patch(
            "pyoverkiz.client.OverkizClient.get_gateways",
            return_value=MOCK_GATEWAY_RESPONSE,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": TEST_EMAIL, "password": TEST_PASSWORD},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_EMAIL)
    expect(result["data"]).to_equal(
        {
            "api_type": "cloud",
            "username": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "hub": TEST_SERVER,
        }
    )


@test
async def cloud_reauth_success(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test reauthentication flow."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_GATEWAY_ID,
        version=2,
        data={
            "username": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "hub": TEST_SERVER2,
            "api_type": "cloud",
        },
    )
    mock_entry.add_to_hass(hass)

    result = await mock_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("cloud")

    with (
        patch("pyoverkiz.client.OverkizClient.login", return_value=True),
        patch(
            "pyoverkiz.client.OverkizClient.get_gateways",
            return_value=MOCK_GATEWAY_RESPONSE,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                "username": TEST_EMAIL,
                "password": TEST_PASSWORD2,
            },
        )

        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("reauth_successful")
        expect(mock_entry.data["username"]).to_equal(TEST_EMAIL)
        expect(mock_entry.data["password"]).to_equal(TEST_PASSWORD2)


@test
async def cloud_reauth_wrong_account(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reauthentication flow."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_GATEWAY_ID,
        version=2,
        data={
            "username": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "hub": TEST_SERVER2,
            "api_type": "cloud",
        },
    )
    mock_entry.add_to_hass(hass)

    result = await mock_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("cloud")

    with (
        patch("pyoverkiz.client.OverkizClient.login", return_value=True),
        patch(
            "pyoverkiz.client.OverkizClient.get_gateways",
            return_value=MOCK_GATEWAY2_RESPONSE,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                "username": TEST_EMAIL,
                "password": TEST_PASSWORD2,
            },
        )

        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("reauth_wrong_account")


@test
async def local_reauth_legacy(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test legacy reauthentication flow with username/password."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_GATEWAY_ID,
        version=2,
        data={
            "host": TEST_HOST,
            "username": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "verify_ssl": True,
            "hub": TEST_SERVER,
            "api_type": "local",
        },
    )
    mock_entry.add_to_hass(hass)

    result = await mock_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("local_or_cloud")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"api_type": "local"},
    )

    expect(result2["step_id"]).to_equal("local")

    with patch.multiple(
        "pyoverkiz.client.OverkizClient",
        login=AsyncMock(return_value=True),
        get_gateways=AsyncMock(return_value=MOCK_GATEWAY_RESPONSE),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": TEST_HOST,
                "token": "new_token",
                "verify_ssl": True,
            },
        )

        expect(result3["type"]).to_be(FlowResultType.ABORT)
        expect(result3["reason"]).to_equal("reauth_successful")
        expect(mock_entry.data["host"]).to_equal(TEST_HOST)
        expect(mock_entry.data["token"]).to_equal("new_token")
        expect(mock_entry.data["verify_ssl"]).to_be(True)


@test
async def local_reauth_success(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test modern local reauth flow."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_GATEWAY_ID,
        version=2,
        data={
            "host": TEST_HOST,
            "token": "old_token",
            "verify_ssl": True,
            "hub": TEST_SERVER,
            "api_type": "local",
        },
    )
    mock_entry.add_to_hass(hass)

    result = await mock_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("local_or_cloud")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"api_type": "local"},
    )

    expect(result2["step_id"]).to_equal("local")

    with patch.multiple(
        "pyoverkiz.client.OverkizClient",
        login=AsyncMock(return_value=True),
        get_gateways=AsyncMock(return_value=MOCK_GATEWAY_RESPONSE),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": TEST_HOST,
                "token": "new_token",
                "verify_ssl": True,
            },
        )

        expect(result3["type"]).to_be(FlowResultType.ABORT)
        expect(result3["reason"]).to_equal("reauth_successful")
        expect(mock_entry.data["host"]).to_equal(TEST_HOST)
        expect(mock_entry.data["token"]).to_equal("new_token")
        expect(mock_entry.data["verify_ssl"]).to_be(True)
        expect("username" in mock_entry.data).to_be(False)
        expect("password" in mock_entry.data).to_be(False)


@test
async def local_reauth_wrong_account(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test local reauth flow with wrong gateway account."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_GATEWAY_ID2,
        version=2,
        data={
            "host": TEST_HOST,
            "token": "old_token",
            "verify_ssl": True,
            "hub": TEST_SERVER,
            "api_type": "local",
        },
    )
    mock_entry.add_to_hass(hass)

    result = await mock_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("local_or_cloud")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"api_type": "local"},
    )

    expect(result2["step_id"]).to_equal("local")

    with patch.multiple(
        "pyoverkiz.client.OverkizClient",
        login=AsyncMock(return_value=True),
        get_gateways=AsyncMock(return_value=MOCK_GATEWAY_RESPONSE),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": TEST_HOST,
                "token": "new_token",
                "verify_ssl": True,
            },
        )

        expect(result3["type"]).to_be(FlowResultType.ABORT)
        expect(result3["reason"]).to_equal("reauth_wrong_account")


@test
async def dhcp_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test that DHCP discovery for new bridge works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=DhcpServiceInfo(
            hostname="gateway-1234-5678-9123",
            ip="192.168.1.4",
            macaddress="f8811a000000",
        ),
        context={"source": config_entries.SOURCE_DHCP},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(config_entries.SOURCE_USER)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"hub": TEST_SERVER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("local_or_cloud")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"api_type": "cloud"},
    )

    with (
        patch("pyoverkiz.client.OverkizClient.login", return_value=True),
        patch("pyoverkiz.client.OverkizClient.get_gateways", return_value=None),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": TEST_EMAIL,
                "password": TEST_PASSWORD,
            },
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_EMAIL)
    expect(result["data"]).to_equal(
        {
            "username": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "hub": TEST_SERVER,
            "api_type": "cloud",
        }
    )

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def dhcp_flow_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that DHCP doesn't setup already configured gateways."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_GATEWAY_ID,
        data={"username": TEST_EMAIL, "password": TEST_PASSWORD, "hub": TEST_SERVER},
    )
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=DhcpServiceInfo(
            hostname="gateway-1234-5678-9123",
            ip="192.168.1.4",
            macaddress="f8811a000000",
        ),
        context={"source": config_entries.SOURCE_DHCP},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def zeroconf_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test that zeroconf discovery for new bridge works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=FAKE_ZERO_CONF_INFO,
        context={"source": config_entries.SOURCE_ZEROCONF},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(config_entries.SOURCE_USER)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"hub": TEST_SERVER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("local_or_cloud")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"api_type": "cloud"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("cloud")

    with (
        patch("pyoverkiz.client.OverkizClient.login", return_value=True),
        patch(
            "pyoverkiz.client.OverkizClient.get_gateways",
            return_value=MOCK_GATEWAY_RESPONSE,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": TEST_EMAIL, "password": TEST_PASSWORD},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_EMAIL)
    expect(result["data"]).to_equal(
        {
            "username": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "hub": TEST_SERVER,
            "api_type": "cloud",
        }
    )

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def local_zeroconf_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test that zeroconf discovery for new local bridge works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=FAKE_ZERO_CONF_INFO_LOCAL,
        context={"source": config_entries.SOURCE_ZEROCONF},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(config_entries.SOURCE_USER)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"hub": TEST_SERVER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("local_or_cloud")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"api_type": "local"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("local")

    with patch.multiple(
        "pyoverkiz.client.OverkizClient",
        login=AsyncMock(return_value=True),
        get_gateways=AsyncMock(return_value=MOCK_GATEWAY_RESPONSE),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "gateway-1234-5678-9123.local:8443",
                "token": TEST_TOKEN,
                "verify_ssl": False,
            },
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("gateway-1234-5678-9123.local:8443")

    expect(result["data"]).to_equal(
        {
            "host": "gateway-1234-5678-9123.local:8443",
            "token": TEST_TOKEN,
            "verify_ssl": False,
            "hub": TEST_SERVER,
            "api_type": "local",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def zeroconf_flow_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that zeroconf doesn't setup already configured gateways."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_GATEWAY_ID,
        data={"username": TEST_EMAIL, "password": TEST_PASSWORD, "hub": TEST_SERVER},
    )
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=FAKE_ZERO_CONF_INFO,
        context={"source": config_entries.SOURCE_ZEROCONF},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
