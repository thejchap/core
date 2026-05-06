"""Test the httpx client helper."""

from unittest.mock import Mock, patch

import httpx
from tryke import Depends, expect, fixture, test

from homeassistant.const import EVENT_HOMEASSISTANT_CLOSE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import httpx_client as client
from homeassistant.util.ssl import SSL_ALPN_HTTP11, SSL_ALPN_HTTP11_HTTP2

from tests.common import MockModule, extract_stack_to_frame, mock_integration
from tests.hass_fixtures import LogCapture, caplog, hass


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def get_async_client_with_ssl(hass: HomeAssistant = Depends(hass)) -> None:
    """Test init async client with ssl."""
    client.get_async_client(hass)

    expect(
        isinstance(
            hass.data[client.DATA_ASYNC_CLIENT][(True, SSL_ALPN_HTTP11)],
            httpx.AsyncClient,
        )
    ).to_be(True)


@test
async def get_async_client_without_ssl(hass: HomeAssistant = Depends(hass)) -> None:
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
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test init async client with ssl and cookies."""
    client.get_async_client(hass)

    httpx_client = client.create_async_httpx_client(hass, cookies={"bla": True})
    expect(isinstance(httpx_client, httpx.AsyncClient)).to_be(True)
    expect(
        hass.data[client.DATA_ASYNC_CLIENT][(True, SSL_ALPN_HTTP11)] != httpx_client
    ).to_be(True)


@test
async def create_async_httpx_client_without_ssl_and_cookies(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test init async client without ssl and cookies."""
    client.get_async_client(hass, verify_ssl=False)

    httpx_client = client.create_async_httpx_client(
        hass, verify_ssl=False, cookies={"bla": True}
    )
    expect(isinstance(httpx_client, httpx.AsyncClient)).to_be(True)
    expect(
        hass.data[client.DATA_ASYNC_CLIENT][(False, SSL_ALPN_HTTP11)] != httpx_client
    ).to_be(True)


@test
async def create_async_httpx_client_default_headers(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test init async client with default headers."""
    httpx_client = client.create_async_httpx_client(hass)
    expect(isinstance(httpx_client, httpx.AsyncClient)).to_be(True)
    expect(httpx_client.headers[client.USER_AGENT]).to_equal(client.SERVER_SOFTWARE)


@test
async def create_async_httpx_client_with_headers(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test init async client with headers."""
    httpx_client = client.create_async_httpx_client(hass, headers={"x-test": "true"})
    expect(isinstance(httpx_client, httpx.AsyncClient)).to_be(True)
    expect(httpx_client.headers["x-test"]).to_equal("true")
    # Default headers are preserved
    expect(httpx_client.headers[client.USER_AGENT]).to_equal(client.SERVER_SOFTWARE)


@test
async def get_async_client_cleanup(hass: HomeAssistant = Depends(hass)) -> None:
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
    hass: HomeAssistant = Depends(hass),
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
async def get_async_client_patched_close(hass: HomeAssistant = Depends(hass)) -> None:
    """Test closing the async client does not work."""
    with patch("httpx.AsyncClient.aclose") as mock_aclose:
        httpx_session = client.get_async_client(hass)
        expect(
            isinstance(
                hass.data[client.DATA_ASYNC_CLIENT][(True, SSL_ALPN_HTTP11)],
                httpx.AsyncClient,
            )
        ).to_be(True)

        caught: Exception | None = None
        try:
            await httpx_session.aclose()
        except RuntimeError as exc:
            caught = exc
        expect(caught).not_.to_be_none()

        expect(mock_aclose.call_count).to_equal(0)


@test
async def get_async_client_context_manager(
    hass: HomeAssistant = Depends(hass),
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
async def get_async_client_http2(hass: HomeAssistant = Depends(hass)) -> None:
    """Test init async client with HTTP/2 support."""
    http1_client = client.get_async_client(hass)
    http2_client = client.get_async_client(hass, alpn_protocols=SSL_ALPN_HTTP11_HTTP2)

    # HTTP/1.1 and HTTP/2 clients should be different (different SSL contexts)
    expect(http1_client is not http2_client).to_be(True)
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

    # Same parameters should return cached client
    expect(client.get_async_client(hass) is http1_client).to_be(True)
    expect(
        client.get_async_client(hass, alpn_protocols=SSL_ALPN_HTTP11_HTTP2)
        is http2_client
    ).to_be(True)


@test
async def get_async_client_http2_cleanup(hass: HomeAssistant = Depends(hass)) -> None:
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
    hass: HomeAssistant = Depends(hass),
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

    # Same parameters should return cached client
    expect(
        client.get_async_client(
            hass, verify_ssl=False, alpn_protocols=SSL_ALPN_HTTP11_HTTP2
        )
        is http2_client
    ).to_be(True)


@test
async def create_async_httpx_client_http2(hass: HomeAssistant = Depends(hass)) -> None:
    """Test create async client with HTTP/2 uses correct ALPN protocols."""
    http1_client = client.create_async_httpx_client(hass)
    http2_client = client.create_async_httpx_client(
        hass, alpn_protocols=SSL_ALPN_HTTP11_HTTP2
    )

    # Different clients (not cached)
    expect(http1_client is not http2_client).to_be(True)

    # Both should be valid clients
    expect(isinstance(http1_client, httpx.AsyncClient)).to_be(True)
    expect(isinstance(http2_client, httpx.AsyncClient)).to_be(True)


@test
async def warning_close_session_integration(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
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
        (
            "Detected that integration 'hue' closes the Home Assistant httpx client at "
            "homeassistant/components/hue/light.py, line 23: await session.aclose(). "
            "Please create a bug report at https://github.com/home-assistant/core/issues?"
            "q=is%3Aopen+is%3Aissue+label%3A%22integration%3A+hue%22"
        )
        in caplog.text
    ).to_be(True)


@test
async def warning_close_session_custom(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
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
        (
            "Detected that custom integration 'hue' closes the Home Assistant httpx client "
            "at custom_components/hue/light.py, line 23: await session.aclose(). "
            "Please report it to the author of the 'hue' custom integration"
        )
        in caplog.text
    ).to_be(True)
