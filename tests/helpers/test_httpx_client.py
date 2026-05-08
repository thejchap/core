"""Test the httpx client helper."""

from unittest.mock import Mock, patch

import httpx
from tryke import Depends, expect, fixture, test

from homeassistant.const import EVENT_HOMEASSISTANT_CLOSE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import httpx_client as client
from homeassistant.util.ssl import SSL_ALPN_HTTP11, SSL_ALPN_HTTP11_HTTP2

from tests.common import MockModule, extract_stack_to_frame, mock_integration
from tests.hass_fixtures import LogCapture, caplog as caplog_fixture, hass as hass_fixture
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor() -> None:
    """Force tryke to build a per-module HookExecutor for this file."""


@test
async def get_async_client_with_ssl(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test init async client with ssl."""
    client.get_async_client(hass)

    expect(
        isinstance(
            hass.data[client.DATA_ASYNC_CLIENT][(True, SSL_ALPN_HTTP11)],
            httpx.AsyncClient,
        )
    ).to_be(True)


@test
async def get_async_client_without_ssl(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test init async client without ssl."""
    client.get_async_client(hass, verify_ssl=False)

    expect(
        isinstance(
            hass.data[client.DATA_ASYNC_CLIENT][(False, SSL_ALPN_HTTP11)],
            httpx.AsyncClient,
        )
    ).to_be(True)


@test
async def create_async_httpx_client_with_ssl_and_cookies(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test init async client with ssl and cookies."""
    client.get_async_client(hass)

    httpx_client = client.create_async_httpx_client(hass, cookies={"bla": True})
    expect(isinstance(httpx_client, httpx.AsyncClient)).to_be(True)
    expect(
        hass.data[client.DATA_ASYNC_CLIENT][(True, SSL_ALPN_HTTP11)] is httpx_client
    ).to_be(False)


@test
async def create_async_httpx_client_without_ssl_and_cookies(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test init async client without ssl and cookies."""
    client.get_async_client(hass, verify_ssl=False)

    httpx_client = client.create_async_httpx_client(
        hass, verify_ssl=False, cookies={"bla": True}
    )
    expect(isinstance(httpx_client, httpx.AsyncClient)).to_be(True)
    expect(
        hass.data[client.DATA_ASYNC_CLIENT][(False, SSL_ALPN_HTTP11)] is httpx_client
    ).to_be(False)


@test
async def create_async_httpx_client_default_headers(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test init async client with default headers."""
    httpx_client = client.create_async_httpx_client(hass)
    expect(isinstance(httpx_client, httpx.AsyncClient)).to_be(True)
    expect(httpx_client.headers[client.USER_AGENT]).to_equal(client.SERVER_SOFTWARE)


@test
async def create_async_httpx_client_with_headers(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test init async client with headers."""
    httpx_client = client.create_async_httpx_client(hass, headers={"x-test": "true"})
    expect(isinstance(httpx_client, httpx.AsyncClient)).to_be(True)
    expect(httpx_client.headers["x-test"]).to_equal("true")
    # Default headers are preserved
    expect(httpx_client.headers[client.USER_AGENT]).to_equal(client.SERVER_SOFTWARE)


@test
async def get_async_client_cleanup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test init async client with ssl."""
    client.get_async_client(hass)

    expect(
        isinstance(
            hass.data[client.DATA_ASYNC_CLIENT][(True, SSL_ALPN_HTTP11)],
            httpx.AsyncClient,
        )
    ).to_be(True)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_CLOSE)
    await hass.async_block_till_done()

    expect(
        hass.data[client.DATA_ASYNC_CLIENT][(True, SSL_ALPN_HTTP11)].is_closed
    ).to_be(True)


@test
async def get_async_client_cleanup_without_ssl(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test init async client without ssl."""
    client.get_async_client(hass, verify_ssl=False)

    expect(
        isinstance(
            hass.data[client.DATA_ASYNC_CLIENT][(False, SSL_ALPN_HTTP11)],
            httpx.AsyncClient,
        )
    ).to_be(True)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_CLOSE)
    await hass.async_block_till_done()

    expect(
        hass.data[client.DATA_ASYNC_CLIENT][(False, SSL_ALPN_HTTP11)].is_closed
    ).to_be(True)


@test
async def get_async_client_patched_close(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test closing the async client does not work."""
    with patch("httpx.AsyncClient.aclose") as mock_aclose:
        httpx_session = client.get_async_client(hass)
        expect(
            isinstance(
                hass.data[client.DATA_ASYNC_CLIENT][(True, SSL_ALPN_HTTP11)],
                httpx.AsyncClient,
            )
        ).to_be(True)

        async with expect_raises_async(RuntimeError):
            await httpx_session.aclose()

        expect(mock_aclose.call_count).to_equal(0)


@test
async def get_async_client_context_manager(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test using the async client with a context manager does not close the session."""
    with patch("httpx.AsyncClient.aclose") as mock_aclose:
        httpx_session = client.get_async_client(hass)
        expect(
            isinstance(
                hass.data[client.DATA_ASYNC_CLIENT][(True, SSL_ALPN_HTTP11)],
                httpx.AsyncClient,
            )
        ).to_be(True)

        async with httpx_session:
            pass

        expect(mock_aclose.call_count).to_equal(0)


@test
async def get_async_client_http2(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test init async client with HTTP/2 support."""
    http1_client = client.get_async_client(hass)
    http2_client = client.get_async_client(hass, alpn_protocols=SSL_ALPN_HTTP11_HTTP2)

    expect(http1_client is http2_client).to_be(False)
    expect(
        isinstance(
            hass.data[client.DATA_ASYNC_CLIENT][(True, SSL_ALPN_HTTP11)],
            httpx.AsyncClient,
        )
    ).to_be(True)
    expect(
        isinstance(
            hass.data[client.DATA_ASYNC_CLIENT][(True, SSL_ALPN_HTTP11_HTTP2)],
            httpx.AsyncClient,
        )
    ).to_be(True)

    expect(client.get_async_client(hass) is http1_client).to_be(True)
    expect(
        client.get_async_client(hass, alpn_protocols=SSL_ALPN_HTTP11_HTTP2)
        is http2_client
    ).to_be(True)


@test
async def get_async_client_http2_cleanup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test cleanup of HTTP/2 async client."""
    client.get_async_client(hass, alpn_protocols=SSL_ALPN_HTTP11_HTTP2)

    expect(
        isinstance(
            hass.data[client.DATA_ASYNC_CLIENT][(True, SSL_ALPN_HTTP11_HTTP2)],
            httpx.AsyncClient,
        )
    ).to_be(True)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_CLOSE)
    await hass.async_block_till_done()

    expect(
        hass.data[client.DATA_ASYNC_CLIENT][(True, SSL_ALPN_HTTP11_HTTP2)].is_closed
    ).to_be(True)


@test
async def get_async_client_http2_without_ssl(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test init async client with HTTP/2 and without SSL."""
    http2_client = client.get_async_client(
        hass, verify_ssl=False, alpn_protocols=SSL_ALPN_HTTP11_HTTP2
    )

    expect(
        isinstance(
            hass.data[client.DATA_ASYNC_CLIENT][(False, SSL_ALPN_HTTP11_HTTP2)],
            httpx.AsyncClient,
        )
    ).to_be(True)

    expect(
        client.get_async_client(
            hass, verify_ssl=False, alpn_protocols=SSL_ALPN_HTTP11_HTTP2
        )
        is http2_client
    ).to_be(True)


@test
async def create_async_httpx_client_http2(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test create async client with HTTP/2 uses correct ALPN protocols."""
    http1_client = client.create_async_httpx_client(hass)
    http2_client = client.create_async_httpx_client(
        hass, alpn_protocols=SSL_ALPN_HTTP11_HTTP2
    )

    expect(http1_client is http2_client).to_be(False)
    expect(isinstance(http1_client, httpx.AsyncClient)).to_be(True)
    expect(isinstance(http2_client, httpx.AsyncClient)).to_be(True)


@test
async def warning_close_session_integration(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test log warning message when closing the session from integration context."""
    with (
        patch(
            "homeassistant.helpers.frame.linecache.getline",
            return_value="await session.aclose()",
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
                        line="await session.aclose()",
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
        httpx_session = client.get_async_client(hass)
        await httpx_session.aclose()

    expect(
        "Detected that integration 'hue' closes the Home Assistant httpx client at "
        "homeassistant/components/hue/light.py, line 23: await session.aclose(). "
        "Please create a bug report at https://github.com/home-assistant/core/issues?"
        "q=is%3Aopen+is%3Aissue+label%3A%22integration%3A+hue%22"
        in caplog.text
    ).to_be(True)


@test
async def warning_close_session_custom(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test log warning message when closing the session from custom context."""
    mock_integration(hass, MockModule("hue"), built_in=False)
    with (
        patch(
            "homeassistant.helpers.frame.linecache.getline",
            return_value="await session.aclose()",
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
                        line="await session.aclose()",
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
        httpx_session = client.get_async_client(hass)
        await httpx_session.aclose()
    expect(
        "Detected that custom integration 'hue' closes the Home Assistant httpx client "
        "at custom_components/hue/light.py, line 23: await session.aclose(). "
        "Please report it to the author of the 'hue' custom integration"
        in caplog.text
    ).to_be(True)
