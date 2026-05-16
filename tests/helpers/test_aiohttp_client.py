"""Test the aiohttp client helper."""

import socket
from unittest.mock import Mock, patch

import aiohttp
from tryke import Depends, expect, fixture, test

from homeassistant.components.mjpeg import (
    CONF_MJPEG_URL,
    CONF_STILL_IMAGE_URL,
    DOMAIN as MJPEG_DOMAIN,
)
from homeassistant.const import (
    CONF_AUTHENTICATION,
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
    EVENT_HOMEASSISTANT_CLOSE,
    HTTP_BASIC_AUTHENTICATION,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client as client
from homeassistant.util import ssl as ssl_util
from homeassistant.util.color import RGBColor
from homeassistant.util.ssl import SSLCipherList

from tests.common import (
    MockConfigEntry,
    MockModule,
    extract_stack_to_frame,
    mock_integration,
)
from tests.hass_fixtures import (
    ClientSessionGenerator,
    LogCapture,
    aioclient_mock as aioclient_mock_fixture,
    caplog as caplog_fixture,
    hass as hass_fixture,
    hass_client as hass_client_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Force tryke to build a per-module HookExecutor for this file."""
    return 0


@fixture
async def camera_client(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
):
    """Fixture to fetch camera streams."""
    mock_config_entry = MockConfigEntry(
        title="MJPEG Camera",
        domain=MJPEG_DOMAIN,
        options={
            CONF_AUTHENTICATION: HTTP_BASIC_AUTHENTICATION,
            CONF_MJPEG_URL: "http://example.com/mjpeg_stream",
            CONF_PASSWORD: None,
            CONF_STILL_IMAGE_URL: None,
            CONF_USERNAME: None,
            CONF_VERIFY_SSL: True,
        },
    )
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    return await hass_client()


@test
async def get_clientsession_with_ssl(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test init clientsession with ssl."""
    client.async_get_clientsession(hass)
    verify_ssl = True
    ssl_cipher = SSLCipherList.PYTHON_DEFAULT
    family = 0

    client_session = hass.data[client.DATA_CLIENTSESSION][
        (verify_ssl, family, ssl_cipher)
    ]
    expect(isinstance(client_session, aiohttp.ClientSession)).to_be(True)
    connector = hass.data[client.DATA_CONNECTOR][(verify_ssl, family, ssl_cipher)]
    expect(isinstance(connector, aiohttp.TCPConnector)).to_be(True)


@test
async def get_clientsession_without_ssl(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test init clientsession without ssl."""
    client.async_get_clientsession(hass, verify_ssl=False)
    verify_ssl = False
    ssl_cipher = SSLCipherList.PYTHON_DEFAULT
    family = 0

    client_session = hass.data[client.DATA_CLIENTSESSION][
        (verify_ssl, family, ssl_cipher)
    ]
    expect(isinstance(client_session, aiohttp.ClientSession)).to_be(True)
    connector = hass.data[client.DATA_CONNECTOR][(verify_ssl, family, ssl_cipher)]
    expect(isinstance(connector, aiohttp.TCPConnector)).to_be(True)


@test.cases(
    test.case("ssl_unspec_default", verify_ssl=True, expected_family=socket.AF_UNSPEC, ssl_cipher=SSLCipherList.PYTHON_DEFAULT),
    test.case("ssl_inet_default", verify_ssl=True, expected_family=socket.AF_INET, ssl_cipher=SSLCipherList.PYTHON_DEFAULT),
    test.case("ssl_inet6_default", verify_ssl=True, expected_family=socket.AF_INET6, ssl_cipher=SSLCipherList.PYTHON_DEFAULT),
    test.case("ssl_unspec_intermediate", verify_ssl=True, expected_family=socket.AF_UNSPEC, ssl_cipher=SSLCipherList.INTERMEDIATE),
    test.case("ssl_inet_intermediate", verify_ssl=True, expected_family=socket.AF_INET, ssl_cipher=SSLCipherList.INTERMEDIATE),
    test.case("ssl_inet6_intermediate", verify_ssl=True, expected_family=socket.AF_INET6, ssl_cipher=SSLCipherList.INTERMEDIATE),
    test.case("ssl_unspec_modern", verify_ssl=True, expected_family=socket.AF_UNSPEC, ssl_cipher=SSLCipherList.MODERN),
    test.case("ssl_inet_modern", verify_ssl=True, expected_family=socket.AF_INET, ssl_cipher=SSLCipherList.MODERN),
    test.case("ssl_inet6_modern", verify_ssl=True, expected_family=socket.AF_INET6, ssl_cipher=SSLCipherList.MODERN),
    test.case("ssl_unspec_insecure", verify_ssl=True, expected_family=socket.AF_UNSPEC, ssl_cipher=SSLCipherList.INSECURE),
    test.case("ssl_inet_insecure", verify_ssl=True, expected_family=socket.AF_INET, ssl_cipher=SSLCipherList.INSECURE),
    test.case("ssl_inet6_insecure", verify_ssl=True, expected_family=socket.AF_INET6, ssl_cipher=SSLCipherList.INSECURE),
    test.case("nossl_unspec_default", verify_ssl=False, expected_family=socket.AF_UNSPEC, ssl_cipher=SSLCipherList.PYTHON_DEFAULT),
    test.case("nossl_inet_default", verify_ssl=False, expected_family=socket.AF_INET, ssl_cipher=SSLCipherList.PYTHON_DEFAULT),
    test.case("nossl_inet6_default", verify_ssl=False, expected_family=socket.AF_INET6, ssl_cipher=SSLCipherList.PYTHON_DEFAULT),
    test.case("nossl_unspec_intermediate", verify_ssl=False, expected_family=socket.AF_UNSPEC, ssl_cipher=SSLCipherList.INTERMEDIATE),
    test.case("nossl_inet_intermediate", verify_ssl=False, expected_family=socket.AF_INET, ssl_cipher=SSLCipherList.INTERMEDIATE),
    test.case("nossl_inet6_intermediate", verify_ssl=False, expected_family=socket.AF_INET6, ssl_cipher=SSLCipherList.INTERMEDIATE),
    test.case("nossl_unspec_modern", verify_ssl=False, expected_family=socket.AF_UNSPEC, ssl_cipher=SSLCipherList.MODERN),
    test.case("nossl_inet_modern", verify_ssl=False, expected_family=socket.AF_INET, ssl_cipher=SSLCipherList.MODERN),
    test.case("nossl_inet6_modern", verify_ssl=False, expected_family=socket.AF_INET6, ssl_cipher=SSLCipherList.MODERN),
    test.case("nossl_unspec_insecure", verify_ssl=False, expected_family=socket.AF_UNSPEC, ssl_cipher=SSLCipherList.INSECURE),
    test.case("nossl_inet_insecure", verify_ssl=False, expected_family=socket.AF_INET, ssl_cipher=SSLCipherList.INSECURE),
    test.case("nossl_inet6_insecure", verify_ssl=False, expected_family=socket.AF_INET6, ssl_cipher=SSLCipherList.INSECURE),
)
async def get_clientsession(
    verify_ssl: bool,
    expected_family: int,
    ssl_cipher: SSLCipherList,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test init clientsession combinations."""
    client.async_get_clientsession(
        hass, verify_ssl=verify_ssl, family=expected_family, ssl_cipher=ssl_cipher
    )
    client_session = hass.data[client.DATA_CLIENTSESSION][
        (verify_ssl, expected_family, ssl_cipher)
    ]
    expect(isinstance(client_session, aiohttp.ClientSession)).to_be(True)
    connector = hass.data[client.DATA_CONNECTOR][
        (verify_ssl, expected_family, ssl_cipher)
    ]
    expect(isinstance(connector, aiohttp.TCPConnector)).to_be(True)


@test
async def create_clientsession_with_ssl_and_cookies(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test create clientsession with ssl."""
    session = client.async_create_clientsession(hass, cookies={"bla": True})
    expect(isinstance(session, aiohttp.ClientSession)).to_be(True)

    verify_ssl = True
    ssl_cipher = SSLCipherList.PYTHON_DEFAULT
    family = 0

    expect(client.DATA_CLIENTSESSION not in hass.data).to_be(True)
    connector = hass.data[client.DATA_CONNECTOR][(verify_ssl, family, ssl_cipher)]
    expect(isinstance(connector, aiohttp.TCPConnector)).to_be(True)


@test
async def create_clientsession_without_ssl_and_cookies(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test create clientsession without ssl."""
    session = client.async_create_clientsession(hass, False, cookies={"bla": True})
    expect(isinstance(session, aiohttp.ClientSession)).to_be(True)

    verify_ssl = False
    ssl_cipher = SSLCipherList.PYTHON_DEFAULT
    family = 0

    expect(client.DATA_CLIENTSESSION not in hass.data).to_be(True)
    connector = hass.data[client.DATA_CONNECTOR][(verify_ssl, family, ssl_cipher)]
    expect(isinstance(connector, aiohttp.TCPConnector)).to_be(True)


@test.cases(
    test.case("ssl_0_default", verify_ssl=True, expected_family=0, ssl_cipher=SSLCipherList.PYTHON_DEFAULT),
    test.case("ssl_4_default", verify_ssl=True, expected_family=4, ssl_cipher=SSLCipherList.PYTHON_DEFAULT),
    test.case("ssl_6_default", verify_ssl=True, expected_family=6, ssl_cipher=SSLCipherList.PYTHON_DEFAULT),
    test.case("ssl_0_intermediate", verify_ssl=True, expected_family=0, ssl_cipher=SSLCipherList.INTERMEDIATE),
    test.case("ssl_4_intermediate", verify_ssl=True, expected_family=4, ssl_cipher=SSLCipherList.INTERMEDIATE),
    test.case("ssl_6_intermediate", verify_ssl=True, expected_family=6, ssl_cipher=SSLCipherList.INTERMEDIATE),
    test.case("ssl_0_modern", verify_ssl=True, expected_family=0, ssl_cipher=SSLCipherList.MODERN),
    test.case("ssl_4_modern", verify_ssl=True, expected_family=4, ssl_cipher=SSLCipherList.MODERN),
    test.case("ssl_6_modern", verify_ssl=True, expected_family=6, ssl_cipher=SSLCipherList.MODERN),
    test.case("ssl_0_insecure", verify_ssl=True, expected_family=0, ssl_cipher=SSLCipherList.INSECURE),
    test.case("ssl_4_insecure", verify_ssl=True, expected_family=4, ssl_cipher=SSLCipherList.INSECURE),
    test.case("ssl_6_insecure", verify_ssl=True, expected_family=6, ssl_cipher=SSLCipherList.INSECURE),
    test.case("nossl_0_default", verify_ssl=False, expected_family=0, ssl_cipher=SSLCipherList.PYTHON_DEFAULT),
    test.case("nossl_4_default", verify_ssl=False, expected_family=4, ssl_cipher=SSLCipherList.PYTHON_DEFAULT),
    test.case("nossl_6_default", verify_ssl=False, expected_family=6, ssl_cipher=SSLCipherList.PYTHON_DEFAULT),
    test.case("nossl_0_intermediate", verify_ssl=False, expected_family=0, ssl_cipher=SSLCipherList.INTERMEDIATE),
    test.case("nossl_4_intermediate", verify_ssl=False, expected_family=4, ssl_cipher=SSLCipherList.INTERMEDIATE),
    test.case("nossl_6_intermediate", verify_ssl=False, expected_family=6, ssl_cipher=SSLCipherList.INTERMEDIATE),
    test.case("nossl_0_modern", verify_ssl=False, expected_family=0, ssl_cipher=SSLCipherList.MODERN),
    test.case("nossl_4_modern", verify_ssl=False, expected_family=4, ssl_cipher=SSLCipherList.MODERN),
    test.case("nossl_6_modern", verify_ssl=False, expected_family=6, ssl_cipher=SSLCipherList.MODERN),
    test.case("nossl_0_insecure", verify_ssl=False, expected_family=0, ssl_cipher=SSLCipherList.INSECURE),
    test.case("nossl_4_insecure", verify_ssl=False, expected_family=4, ssl_cipher=SSLCipherList.INSECURE),
    test.case("nossl_6_insecure", verify_ssl=False, expected_family=6, ssl_cipher=SSLCipherList.INSECURE),
)
async def get_clientsession_cleanup(
    verify_ssl: bool,
    expected_family: int,
    ssl_cipher: SSLCipherList,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test init clientsession cleanup."""
    client.async_get_clientsession(
        hass, verify_ssl=verify_ssl, family=expected_family, ssl_cipher=ssl_cipher
    )

    client_session = hass.data[client.DATA_CLIENTSESSION][
        (verify_ssl, expected_family, ssl_cipher)
    ]
    expect(isinstance(client_session, aiohttp.ClientSession)).to_be(True)
    connector = hass.data[client.DATA_CONNECTOR][
        (verify_ssl, expected_family, ssl_cipher)
    ]
    expect(isinstance(connector, aiohttp.TCPConnector)).to_be(True)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_CLOSE)
    await hass.async_block_till_done()

    expect(client_session.closed).to_be(True)
    expect(connector.closed).to_be(True)


@test
async def get_clientsession_patched_close(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test closing clientsession does not work."""
    verify_ssl = True
    ssl_cipher = SSLCipherList.PYTHON_DEFAULT
    family = 0

    with patch("aiohttp.ClientSession.close") as mock_close:
        session = client.async_get_clientsession(hass)

        expect(
            isinstance(
                hass.data[client.DATA_CLIENTSESSION][(verify_ssl, family, ssl_cipher)],
                aiohttp.ClientSession,
            )
        ).to_be(True)
        expect(
            isinstance(
                hass.data[client.DATA_CONNECTOR][(verify_ssl, family, ssl_cipher)],
                aiohttp.TCPConnector,
            )
        ).to_be(True)

        async with expect_raises_async(RuntimeError):
            await session.close()

        expect(mock_close.call_count).to_equal(0)


@test
async def warning_close_session_integration(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test log warning message when closing the session from integration context."""
    with (
        patch(
            "homeassistant.helpers.frame.linecache.getline",
            return_value="await session.close()",
        ),
        patch(
            "homeassistant.helpers.frame.get_current_frame",
            return_value=extract_stack_to_frame(
                [
                    Mock(
                        filename="/home/paulus/homeassistant/core.py",
                        lineno="23",
                        line="do_something()",
                    ),
                    Mock(
                        filename="/home/paulus/homeassistant/components/hue/light.py",
                        lineno="23",
                        line="await session.close()",
                    ),
                    Mock(
                        filename="/home/paulus/aiohue/lights.py",
                        lineno="2",
                        line="something()",
                    ),
                ]
            ),
        ),
    ):
        session = client.async_get_clientsession(hass)
        await session.close()
    expect(
        "Detected that integration 'hue' closes the Home Assistant aiohttp session at "
        "homeassistant/components/hue/light.py, line 23: await session.close(). "
        "Please create a bug report at https://github.com/home-assistant/core/issues?"
        "q=is%3Aopen+is%3Aissue+label%3A%22integration%3A+hue%22"
        in caplog.text
    ).to_be(True)


@test
async def warning_close_session_custom(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test log warning message when closing the session from custom context."""
    mock_integration(hass, MockModule("hue"), built_in=False)
    with (
        patch(
            "homeassistant.helpers.frame.linecache.getline",
            return_value="await session.close()",
        ),
        patch(
            "homeassistant.helpers.frame.get_current_frame",
            return_value=extract_stack_to_frame(
                [
                    Mock(
                        filename="/home/paulus/homeassistant/core.py",
                        lineno="23",
                        line="do_something()",
                    ),
                    Mock(
                        filename="/home/paulus/config/custom_components/hue/light.py",
                        lineno="23",
                        line="await session.close()",
                    ),
                    Mock(
                        filename="/home/paulus/aiohue/lights.py",
                        lineno="2",
                        line="something()",
                    ),
                ]
            ),
        ),
    ):
        session = client.async_get_clientsession(hass)
        await session.close()
    expect(
        "Detected that custom integration 'hue' closes the Home Assistant aiohttp "
        "session at custom_components/hue/light.py, line 23: await session.close(). "
        "Please report it to the author of the 'hue' custom integration"
        in caplog.text
    ).to_be(True)


@test
async def async_aiohttp_proxy_stream(
    _trigger: int = Depends(_trigger_executor),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    camera_client=Depends(camera_client),
) -> None:
    """Test that it fetches the given url."""
    aioclient_mock.get("http://example.com/mjpeg_stream", content=b"Frame1Frame2Frame3")

    resp = await camera_client.get("/api/camera_proxy_stream/camera.mjpeg_camera")

    expect(resp.status).to_equal(200)
    expect(aioclient_mock.call_count).to_equal(1)
    body = await resp.text()
    expect(body).to_equal("Frame1Frame2Frame3")


@test
async def async_aiohttp_proxy_stream_timeout(
    _trigger: int = Depends(_trigger_executor),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    camera_client=Depends(camera_client),
) -> None:
    """Test that it fetches the given url."""
    aioclient_mock.get("http://example.com/mjpeg_stream", exc=TimeoutError())

    resp = await camera_client.get("/api/camera_proxy_stream/camera.mjpeg_camera")
    expect(resp.status).to_equal(504)


@test
async def async_aiohttp_proxy_stream_client_err(
    _trigger: int = Depends(_trigger_executor),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    camera_client=Depends(camera_client),
) -> None:
    """Test that it fetches the given url."""
    aioclient_mock.get("http://example.com/mjpeg_stream", exc=aiohttp.ClientError())

    resp = await camera_client.get("/api/camera_proxy_stream/camera.mjpeg_camera")
    expect(resp.status).to_equal(502)


@test
async def sending_named_tuple(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test sending a named tuple in json."""
    resp = aioclient_mock.post("http://127.0.0.1/rgb", json={"rgb": RGBColor(4, 3, 2)})
    session = client.async_create_clientsession(hass)
    resp = await session.post("http://127.0.0.1/rgb", json={"rgb": RGBColor(4, 3, 2)})
    expect(resp.status).to_equal(200)
    expect(await resp.json()).to_equal({"rgb": [4, 3, 2]})
    expect(aioclient_mock.mock_calls[0][2]["rgb"]).to_equal(RGBColor(4, 3, 2))


@test
async def client_session_immutable_headers(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can't mutate headers."""
    session = client.async_get_clientsession(hass)

    def _set_header() -> None:
        session.headers["user-agent"] = "bla"

    expect(_set_header).to_raise(TypeError)

    def _update_headers() -> None:
        session.headers.update({"user-agent": "bla"})

    expect(_update_headers).to_raise(AttributeError)


@test.skip("requires disable_mock_zeroconf_resolver + mock_async_zeroconf fixtures")
async def async_mdnsresolver() -> None:
    """Test async_mdnsresolver."""


@test
async def resolver_is_singleton(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the resolver is a singleton."""
    session = client.async_get_clientsession(hass)
    session2 = client.async_get_clientsession(hass)
    session3 = client.async_create_clientsession(hass)
    expect(isinstance(session._connector, aiohttp.TCPConnector)).to_be(True)
    expect(isinstance(session2._connector, aiohttp.TCPConnector)).to_be(True)
    expect(isinstance(session3._connector, aiohttp.TCPConnector)).to_be(True)
    expect(session._connector._resolver is session2._connector._resolver).to_be(True)
    expect(session._connector._resolver is session3._connector._resolver).to_be(True)


@test
async def connector_uses_http11_alpn(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that connector uses HTTP/1.1 ALPN protocols."""
    with patch.object(
        ssl_util, "client_context", wraps=ssl_util.client_context
    ) as mock_client_context:
        client.async_get_clientsession(hass)

        mock_client_context.assert_called_once_with(
            SSLCipherList.PYTHON_DEFAULT, ssl_util.SSL_ALPN_HTTP11
        )


@test
async def connector_no_verify_uses_http11_alpn(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that connector without SSL verification uses HTTP/1.1 ALPN protocols."""
    with patch.object(
        ssl_util, "client_context_no_verify", wraps=ssl_util.client_context_no_verify
    ) as mock_client_context_no_verify:
        client.async_get_clientsession(hass, verify_ssl=False)

        mock_client_context_no_verify.assert_called_once_with(
            SSLCipherList.PYTHON_DEFAULT, ssl_util.SSL_ALPN_HTTP11
        )


@test.skip("requires socket_enabled fixture for live aiohttp TestServer")
async def redirect_loopback_to_loopback_allowed() -> None:
    """Test that redirects from loopback to loopback are allowed."""


@test.skip("requires socket_enabled fixture for live aiohttp TestServer")
async def redirect_relative_url_allowed() -> None:
    """Test that relative redirects are allowed (they stay on the same host)."""


@test.skip("requires socket_enabled fixture for live aiohttp TestServer")
async def redirect_to_non_loopback_allowed() -> None:
    """Test that redirects to non-loopback addresses are allowed."""


@test.skip("requires socket_enabled fixture for live aiohttp TestServer")
async def redirect_to_custom_scheme_not_blocked() -> None:
    """Test that redirects to custom (non-HTTP/S) URI schemes are not blocked."""


@test.skip("requires socket_enabled fixture for live aiohttp TestServer")
async def redirect_to_blocked_address() -> None:
    """Test that redirects to blocked addresses are blocked."""
