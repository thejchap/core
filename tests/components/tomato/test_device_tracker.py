"""The tests for the Tomato device tracker platform."""

from unittest import mock

import requests
import requests_mock
from tryke import Depends, expect, fixture, test
import voluptuous as vol

from homeassistant.components.device_tracker import DOMAIN as DEVICE_TRACKER_DOMAIN
from homeassistant.components.tomato import device_tracker as tomato
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PLATFORM,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant

from ._fixtures import mock_exception_logger, mock_session_send

from tests.hass_fixtures import hass as hass_fixture


@fixture
def _trigger_executor() -> int:
    """Anchor for tryke fixture resolution."""
    return 0


def mock_session_response(*args, **kwargs):
    """Mock data generation for session response."""

    class MockSessionResponse:
        def __init__(self, text, status_code) -> None:
            self.text = text
            self.status_code = status_code

    # Username: foo
    # Password: bar
    if args[0].headers["Authorization"] != "Basic Zm9vOmJhcg==":
        return MockSessionResponse(None, 401)
    if "gimmie_bad_data" in args[0].body:
        return MockSessionResponse("This shouldn't (wldev = be here.;", 200)
    if "gimmie_good_data" in args[0].body:
        return MockSessionResponse(
            "wldev = [ ['eth1','F4:F5:D8:AA:AA:AA',"
            "-42,5500,1000,7043,0],['eth1','58:EF:68:00:00:00',"
            "-42,5500,1000,7043,0]];\n"
            "dhcpd_lease = [ ['chromecast','172.10.10.5','F4:F5:D8:AA:AA:AA',"
            "'0 days, 16:17:08'],['wemo','172.10.10.6','58:EF:68:00:00:00',"
            "'0 days, 12:09:08']];",
            200,
        )

    return MockSessionResponse(None, 200)


@test
async def config_missing_optional_params(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_session_send: mock.MagicMock = Depends(mock_session_send),
) -> None:
    """Test the setup without optional parameters."""
    config = {
        DEVICE_TRACKER_DOMAIN: tomato.PLATFORM_SCHEMA(
            {
                CONF_PLATFORM: DEVICE_TRACKER_DOMAIN,
                CONF_HOST: "tomato-router",
                CONF_USERNAME: "foo",
                CONF_PASSWORD: "password",
                tomato.CONF_HTTP_ID: "1234567890",
            }
        )
    }
    result = tomato.get_scanner(hass, config)
    expect(result.req.url).to_equal("http://tomato-router:80/update.cgi")
    expect(result.req.headers).to_equal(
        {
            "Content-Length": "32",
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic Zm9vOnBhc3N3b3Jk",
        }
    )
    expect("_http_id=1234567890" in result.req.body).to_be(True)
    expect("exec=devlist" in result.req.body).to_be(True)


@test
async def config_default_nonssl_port(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_session_send: mock.MagicMock = Depends(mock_session_send),
) -> None:
    """Test the setup without a default port set without ssl enabled."""
    with (
        mock.patch("os.access", return_value=True),
        mock.patch("os.path.isfile", mock.Mock(return_value=True)),
    ):
        config = {
            DEVICE_TRACKER_DOMAIN: tomato.PLATFORM_SCHEMA(
                {
                    CONF_PLATFORM: DEVICE_TRACKER_DOMAIN,
                    CONF_HOST: "tomato-router",
                    CONF_USERNAME: "foo",
                    CONF_PASSWORD: "password",
                    tomato.CONF_HTTP_ID: "1234567890",
                }
            )
        }
        result = tomato.get_scanner(hass, config)
        expect(result.req.url).to_equal("http://tomato-router:80/update.cgi")


@test
async def config_default_ssl_port(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_session_send: mock.MagicMock = Depends(mock_session_send),
) -> None:
    """Test the setup without a default port set with ssl enabled."""
    with (
        mock.patch("os.access", return_value=True),
        mock.patch("os.path.isfile", mock.Mock(return_value=True)),
    ):
        config = {
            DEVICE_TRACKER_DOMAIN: tomato.PLATFORM_SCHEMA(
                {
                    CONF_PLATFORM: DEVICE_TRACKER_DOMAIN,
                    CONF_HOST: "tomato-router",
                    CONF_SSL: True,
                    CONF_USERNAME: "foo",
                    CONF_PASSWORD: "password",
                    tomato.CONF_HTTP_ID: "1234567890",
                }
            )
        }
        result = tomato.get_scanner(hass, config)
        expect(result.req.url).to_equal("https://tomato-router:443/update.cgi")


@test
async def config_verify_ssl_but_no_ssl_enabled(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_session_send: mock.MagicMock = Depends(mock_session_send),
) -> None:
    """Test the setup with a string with ssl_verify but ssl not enabled."""
    with (
        mock.patch("os.access", return_value=True),
        mock.patch("os.path.isfile", mock.Mock(return_value=True)),
    ):
        config = {
            DEVICE_TRACKER_DOMAIN: tomato.PLATFORM_SCHEMA(
                {
                    CONF_PLATFORM: DEVICE_TRACKER_DOMAIN,
                    CONF_HOST: "tomato-router",
                    CONF_PORT: 1234,
                    CONF_SSL: False,
                    CONF_VERIFY_SSL: "/test/tomato.crt",
                    CONF_USERNAME: "foo",
                    CONF_PASSWORD: "password",
                    tomato.CONF_HTTP_ID: "1234567890",
                }
            )
        }
        result = tomato.get_scanner(hass, config)
        expect(result.req.url).to_equal("http://tomato-router:1234/update.cgi")
        expect(result.req.headers).to_equal(
            {
                "Content-Length": "32",
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": "Basic Zm9vOnBhc3N3b3Jk",
            }
        )
        expect("_http_id=1234567890" in result.req.body).to_be(True)
        expect("exec=devlist" in result.req.body).to_be(True)
        expect(mock_session_send.call_count).to_equal(1)
        expect(mock_session_send.mock_calls[0]).to_equal(
            mock.call(result.req, timeout=60)
        )


@test
async def config_valid_verify_ssl_path(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_session_send: mock.MagicMock = Depends(mock_session_send),
) -> None:
    """Test the setup with a string for ssl_verify.

    Representing the absolute path to a CA certificate bundle.
    """
    with (
        mock.patch("os.access", return_value=True),
        mock.patch("os.path.isfile", mock.Mock(return_value=True)),
    ):
        config = {
            DEVICE_TRACKER_DOMAIN: tomato.PLATFORM_SCHEMA(
                {
                    CONF_PLATFORM: DEVICE_TRACKER_DOMAIN,
                    CONF_HOST: "tomato-router",
                    CONF_PORT: 1234,
                    CONF_SSL: True,
                    CONF_VERIFY_SSL: "/test/tomato.crt",
                    CONF_USERNAME: "bar",
                    CONF_PASSWORD: "foo",
                    tomato.CONF_HTTP_ID: "0987654321",
                }
            )
        }
        result = tomato.get_scanner(hass, config)
        expect(result.req.url).to_equal("https://tomato-router:1234/update.cgi")
        expect(result.req.headers).to_equal(
            {
                "Content-Length": "32",
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": "Basic YmFyOmZvbw==",
            }
        )
        expect("_http_id=0987654321" in result.req.body).to_be(True)
        expect("exec=devlist" in result.req.body).to_be(True)
        expect(mock_session_send.call_count).to_equal(1)
        expect(mock_session_send.mock_calls[0]).to_equal(
            mock.call(result.req, timeout=60, verify="/test/tomato.crt")
        )


@test
async def config_valid_verify_ssl_bool(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_session_send: mock.MagicMock = Depends(mock_session_send),
) -> None:
    """Test the setup with a bool for ssl_verify."""
    config = {
        DEVICE_TRACKER_DOMAIN: tomato.PLATFORM_SCHEMA(
            {
                CONF_PLATFORM: DEVICE_TRACKER_DOMAIN,
                CONF_HOST: "tomato-router",
                CONF_PORT: 1234,
                CONF_SSL: True,
                CONF_VERIFY_SSL: "False",
                CONF_USERNAME: "bar",
                CONF_PASSWORD: "foo",
                tomato.CONF_HTTP_ID: "0987654321",
            }
        )
    }
    result = tomato.get_scanner(hass, config)
    expect(result.req.url).to_equal("https://tomato-router:1234/update.cgi")
    expect(result.req.headers).to_equal(
        {
            "Content-Length": "32",
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic YmFyOmZvbw==",
        }
    )
    expect("_http_id=0987654321" in result.req.body).to_be(True)
    expect("exec=devlist" in result.req.body).to_be(True)
    expect(mock_session_send.call_count).to_equal(1)
    expect(mock_session_send.mock_calls[0]).to_equal(
        mock.call(result.req, timeout=60, verify=False)
    )


@test
def config_errors() -> None:
    """Test for configuration errors."""
    expect(
        lambda: tomato.PLATFORM_SCHEMA(
            {
                CONF_PLATFORM: DEVICE_TRACKER_DOMAIN,
                # No Host,
                CONF_PORT: 1234,
                CONF_SSL: True,
                CONF_VERIFY_SSL: "False",
                CONF_USERNAME: "bar",
                CONF_PASSWORD: "foo",
                tomato.CONF_HTTP_ID: "0987654321",
            }
        )
    ).to_raise(vol.Invalid)
    expect(
        lambda: tomato.PLATFORM_SCHEMA(
            {
                CONF_PLATFORM: DEVICE_TRACKER_DOMAIN,
                CONF_HOST: "tomato-router",
                CONF_PORT: -123456789,  # Bad Port
                CONF_SSL: True,
                CONF_VERIFY_SSL: "False",
                CONF_USERNAME: "bar",
                CONF_PASSWORD: "foo",
                tomato.CONF_HTTP_ID: "0987654321",
            }
        )
    ).to_raise(vol.Invalid)
    expect(
        lambda: tomato.PLATFORM_SCHEMA(
            {
                CONF_PLATFORM: DEVICE_TRACKER_DOMAIN,
                CONF_HOST: "tomato-router",
                CONF_PORT: 1234,
                CONF_SSL: True,
                CONF_VERIFY_SSL: "False",
                # No Username
                CONF_PASSWORD: "foo",
                tomato.CONF_HTTP_ID: "0987654321",
            }
        )
    ).to_raise(vol.Invalid)
    expect(
        lambda: tomato.PLATFORM_SCHEMA(
            {
                CONF_PLATFORM: DEVICE_TRACKER_DOMAIN,
                CONF_HOST: "tomato-router",
                CONF_PORT: 1234,
                CONF_SSL: True,
                CONF_VERIFY_SSL: "False",
                CONF_USERNAME: "bar",
                # No Password
                tomato.CONF_HTTP_ID: "0987654321",
            }
        )
    ).to_raise(vol.Invalid)
    expect(
        lambda: tomato.PLATFORM_SCHEMA(
            {
                CONF_PLATFORM: DEVICE_TRACKER_DOMAIN,
                CONF_HOST: "tomato-router",
                CONF_PORT: 1234,
                CONF_SSL: True,
                CONF_VERIFY_SSL: "False",
                CONF_USERNAME: "bar",
                CONF_PASSWORD: "foo",
                # No HTTP_ID
            }
        )
    ).to_raise(vol.Invalid)


@test
async def config_bad_credentials(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_exception_logger: mock.MagicMock = Depends(mock_exception_logger),
) -> None:
    """Test the setup with bad credentials."""
    with mock.patch("requests.Session.send", side_effect=mock_session_response):
        config = {
            DEVICE_TRACKER_DOMAIN: tomato.PLATFORM_SCHEMA(
                {
                    CONF_PLATFORM: DEVICE_TRACKER_DOMAIN,
                    CONF_HOST: "tomato-router",
                    CONF_USERNAME: "i_am",
                    CONF_PASSWORD: "an_imposter",
                    tomato.CONF_HTTP_ID: "1234",
                }
            )
        }

        tomato.get_scanner(hass, config)

        expect(mock_exception_logger.call_count).to_equal(1)
        expect(mock_exception_logger.mock_calls[0]).to_equal(
            mock.call(
                "Failed to authenticate, please check your username and password"
            )
        )


@test
async def bad_response(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_exception_logger: mock.MagicMock = Depends(mock_exception_logger),
) -> None:
    """Test the setup with bad response from router."""
    with mock.patch("requests.Session.send", side_effect=mock_session_response):
        config = {
            DEVICE_TRACKER_DOMAIN: tomato.PLATFORM_SCHEMA(
                {
                    CONF_PLATFORM: DEVICE_TRACKER_DOMAIN,
                    CONF_HOST: "tomato-router",
                    CONF_USERNAME: "foo",
                    CONF_PASSWORD: "bar",
                    tomato.CONF_HTTP_ID: "gimmie_bad_data",
                }
            )
        }

        tomato.get_scanner(hass, config)

        expect(mock_exception_logger.call_count).to_equal(1)
        expect(mock_exception_logger.mock_calls[0]).to_equal(
            mock.call("Failed to parse response from router")
        )


@test
async def scan_devices(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_exception_logger: mock.MagicMock = Depends(mock_exception_logger),
) -> None:
    """Test scanning for new devices."""
    with mock.patch("requests.Session.send", side_effect=mock_session_response):
        config = {
            DEVICE_TRACKER_DOMAIN: tomato.PLATFORM_SCHEMA(
                {
                    CONF_PLATFORM: DEVICE_TRACKER_DOMAIN,
                    CONF_HOST: "tomato-router",
                    CONF_USERNAME: "foo",
                    CONF_PASSWORD: "bar",
                    tomato.CONF_HTTP_ID: "gimmie_good_data",
                }
            )
        }

        scanner = tomato.get_scanner(hass, config)
        expect(scanner.scan_devices()).to_equal(
            ["F4:F5:D8:AA:AA:AA", "58:EF:68:00:00:00"]
        )


@test
async def bad_connection(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_exception_logger: mock.MagicMock = Depends(mock_exception_logger),
) -> None:
    """Test the router with a connection error."""
    with mock.patch("requests.Session.send", side_effect=mock_session_response):
        config = {
            DEVICE_TRACKER_DOMAIN: tomato.PLATFORM_SCHEMA(
                {
                    CONF_PLATFORM: DEVICE_TRACKER_DOMAIN,
                    CONF_HOST: "tomato-router",
                    CONF_USERNAME: "foo",
                    CONF_PASSWORD: "bar",
                    tomato.CONF_HTTP_ID: "gimmie_good_data",
                }
            )
        }

        with requests_mock.Mocker() as adapter:
            adapter.register_uri(
                "POST",
                "http://tomato-router:80/update.cgi",
                exc=requests.exceptions.ConnectionError,
            )
            tomato.get_scanner(hass, config)
        expect(mock_exception_logger.call_count).to_equal(1)
        expect(mock_exception_logger.mock_calls[0]).to_equal(
            mock.call(
                "Failed to connect to the router or invalid http_id supplied"
            )
        )


@test
async def router_timeout(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_exception_logger: mock.MagicMock = Depends(mock_exception_logger),
) -> None:
    """Test the router with a timeout error."""
    with mock.patch("requests.Session.send", side_effect=mock_session_response):
        config = {
            DEVICE_TRACKER_DOMAIN: tomato.PLATFORM_SCHEMA(
                {
                    CONF_PLATFORM: DEVICE_TRACKER_DOMAIN,
                    CONF_HOST: "tomato-router",
                    CONF_USERNAME: "foo",
                    CONF_PASSWORD: "bar",
                    tomato.CONF_HTTP_ID: "gimmie_good_data",
                }
            )
        }

        with requests_mock.Mocker() as adapter:
            adapter.register_uri(
                "POST",
                "http://tomato-router:80/update.cgi",
                exc=requests.exceptions.Timeout,
            )
            tomato.get_scanner(hass, config)
        expect(mock_exception_logger.call_count).to_equal(1)
        expect(mock_exception_logger.mock_calls[0]).to_equal(
            mock.call("Connection to the router timed out")
        )


@test
async def get_device_name(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_exception_logger: mock.MagicMock = Depends(mock_exception_logger),
) -> None:
    """Test getting device names."""
    with mock.patch("requests.Session.send", side_effect=mock_session_response):
        config = {
            DEVICE_TRACKER_DOMAIN: tomato.PLATFORM_SCHEMA(
                {
                    CONF_PLATFORM: DEVICE_TRACKER_DOMAIN,
                    CONF_HOST: "tomato-router",
                    CONF_USERNAME: "foo",
                    CONF_PASSWORD: "bar",
                    tomato.CONF_HTTP_ID: "gimmie_good_data",
                }
            )
        }

        scanner = tomato.get_scanner(hass, config)
        expect(scanner.get_device_name("F4:F5:D8:AA:AA:AA")).to_equal("chromecast")
        expect(scanner.get_device_name("58:EF:68:00:00:00")).to_equal("wemo")
        expect(scanner.get_device_name("AA:BB:CC:00:00:00")).to_be(None)
