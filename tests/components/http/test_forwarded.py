"""Test real forwarded middleware."""

from http import HTTPStatus
from ipaddress import ip_network
from unittest.mock import Mock, patch

from aiohttp import web
from aiohttp.hdrs import X_FORWARDED_FOR, X_FORWARDED_HOST, X_FORWARDED_PROTO
from tryke import Depends, expect, fixture, test

from homeassistant.components.http.forwarded import async_setup_forwarded

from tests.hass_fixtures import (
    LogCapture,
    aiohttp_client as aiohttp_client_fixture,
    caplog as caplog_fixture,
    mock_network,
)
from tests.typing import ClientSessionGenerator


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


async def mock_handler(request):
    """Return the real IP as text."""
    return web.Response(text=request.remote)


@test
async def x_forwarded_for_without_trusted_proxy(
    _t: None = Depends(_trigger_executor),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that we get the IP from the transport."""

    async def handler(request):
        url = mock_api_client.make_url("/")
        expect(request.host).to_equal(f"{url.host}:{url.port}")
        expect(request.scheme).to_equal("http")
        expect(request.secure).to_be(False)
        expect(request.remote).to_equal("127.0.0.1")

        return web.Response()

    app = web.Application()
    app.router.add_get("/", handler)

    async_setup_forwarded(app, True, [])

    mock_api_client = await aiohttp_client(app)
    resp = await mock_api_client.get("/", headers={X_FORWARDED_FOR: "255.255.255.255"})

    expect(resp.status).to_equal(HTTPStatus.BAD_REQUEST)
    expect(
        "Received X-Forwarded-For header from an untrusted proxy 127.0.0.1"
        in caplog.text
    ).to_be(True)


@test.cases(
    test.case(
        "subnet_match",
        trusted_proxies=["127.0.0.0/24", "1.1.1.1", "10.10.10.0/24"],
        x_forwarded_for="10.10.10.10, 1.1.1.1",
        remote="10.10.10.10",
    ),
    test.case(
        "three_chained_with_space",
        trusted_proxies=["127.0.0.0/24", "1.1.1.1"],
        x_forwarded_for="123.123.123.123, 2.2.2.2, 1.1.1.1",
        remote="2.2.2.2",
    ),
    test.case(
        "three_chained_no_space",
        trusted_proxies=["127.0.0.0/24", "1.1.1.1"],
        x_forwarded_for="123.123.123.123,2.2.2.2,1.1.1.1",
        remote="2.2.2.2",
    ),
    test.case(
        "single_trusted_subnet",
        trusted_proxies=["127.0.0.0/24"],
        x_forwarded_for="123.123.123.123, 2.2.2.2, 1.1.1.1",
        remote="1.1.1.1",
    ),
    test.case(
        "loopback_only",
        trusted_proxies=["127.0.0.0/24"],
        x_forwarded_for="127.0.0.1",
        remote="127.0.0.1",
    ),
    test.case(
        "two_trusted_first_match",
        trusted_proxies=["127.0.0.1", "1.1.1.1"],
        x_forwarded_for="123.123.123.123, 1.1.1.1",
        remote="123.123.123.123",
    ),
    test.case(
        "two_trusted_second_match",
        trusted_proxies=["127.0.0.1", "1.1.1.1"],
        x_forwarded_for="123.123.123.123, 2.2.2.2, 1.1.1.1",
        remote="2.2.2.2",
    ),
    test.case(
        "single_untrusted",
        trusted_proxies=["127.0.0.1"],
        x_forwarded_for="255.255.255.255",
        remote="255.255.255.255",
    ),
)
async def x_forwarded_for_with_trusted_proxy(
    trusted_proxies: list[str],
    x_forwarded_for: str,
    remote: str,
    _t: None = Depends(_trigger_executor),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fixture),
) -> None:
    """Test that we get the IP from the forwarded for header."""

    async def handler(request):
        url = mock_api_client.make_url("/")
        expect(request.host).to_equal(f"{url.host}:{url.port}")
        expect(request.scheme).to_equal("http")
        expect(request.secure).to_be(False)
        expect(request.remote).to_equal(remote)

        return web.Response()

    app = web.Application()
    app.router.add_get("/", handler)
    async_setup_forwarded(
        app, True, [ip_network(trusted_proxy) for trusted_proxy in trusted_proxies]
    )

    mock_api_client = await aiohttp_client(app)
    resp = await mock_api_client.get("/", headers={X_FORWARDED_FOR: x_forwarded_for})

    expect(resp.status).to_equal(HTTPStatus.OK)


@test.cases(
    test.case(
        "subnet_match",
        trusted_proxies=["127.0.0.0/24", "1.1.1.1", "10.10.10.0/24"],
        x_forwarded_for=["10.10.10.10", "1.1.1.1"],
        remote="10.10.10.10",
    ),
    test.case(
        "three_chained",
        trusted_proxies=["127.0.0.0/24", "1.1.1.1"],
        x_forwarded_for=["123.123.123.123", "2.2.2.2", "1.1.1.1"],
        remote="2.2.2.2",
    ),
    test.case(
        "single_trusted_subnet",
        trusted_proxies=["127.0.0.0/24"],
        x_forwarded_for=["123.123.123.123", "2.2.2.2", "1.1.1.1"],
        remote="1.1.1.1",
    ),
    test.case(
        "two_trusted_first_match",
        trusted_proxies=["127.0.0.1", "1.1.1.1"],
        x_forwarded_for=["123.123.123.123", "1.1.1.1"],
        remote="123.123.123.123",
    ),
    test.case(
        "two_trusted_second_match",
        trusted_proxies=["127.0.0.1", "1.1.1.1"],
        x_forwarded_for=["123.123.123.123", "2.2.2.2", "1.1.1.1"],
        remote="2.2.2.2",
    ),
)
async def x_multiple_forwarded_for_with_trusted_proxy(
    trusted_proxies: list[str],
    x_forwarded_for: list[str],
    remote: str,
    _t: None = Depends(_trigger_executor),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fixture),
) -> None:
    """Test that we get the IP from multiple forwarded for headers."""

    async def handler(request):
        url = mock_api_client.make_url("/")
        expect(request.host).to_equal(f"{url.host}:{url.port}")
        expect(request.scheme).to_equal("http")
        expect(request.secure).to_be(False)
        expect(request.remote).to_equal(remote)

        return web.Response()

    app = web.Application()
    app.router.add_get("/", handler)
    async_setup_forwarded(
        app, True, [ip_network(trusted_proxy) for trusted_proxy in trusted_proxies]
    )

    mock_api_client = await aiohttp_client(app)
    resp = await mock_api_client.get(
        "/", headers=[(X_FORWARDED_FOR, addr) for addr in x_forwarded_for]
    )

    expect(resp.status).to_equal(HTTPStatus.OK)


@test
async def x_forwarded_for_disabled_with_proxy(
    _t: None = Depends(_trigger_executor),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that we warn when processing is disabled, but proxy has been detected."""

    async def handler(request):
        url = mock_api_client.make_url("/")
        expect(request.host).to_equal(f"{url.host}:{url.port}")
        expect(request.scheme).to_equal("http")
        expect(request.secure).to_be(False)
        expect(request.remote).to_equal("127.0.0.1")

        return web.Response()

    app = web.Application()
    app.router.add_get("/", handler)

    async_setup_forwarded(app, False, [])

    mock_api_client = await aiohttp_client(app)
    resp = await mock_api_client.get("/", headers={X_FORWARDED_FOR: "255.255.255.255"})

    expect(resp.status).to_equal(HTTPStatus.BAD_REQUEST)
    expect(
        "A request from a reverse proxy was received from 127.0.0.1, but your HTTP "
        "integration is not set-up for reverse proxies" in caplog.text
    ).to_be(True)


@test
async def x_forwarded_for_with_spoofed_header(
    _t: None = Depends(_trigger_executor),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fixture),
) -> None:
    """Test that we get the IP from the transport with a spoofed header."""

    async def handler(request):
        url = mock_api_client.make_url("/")
        expect(request.host).to_equal(f"{url.host}:{url.port}")
        expect(request.scheme).to_equal("http")
        expect(request.secure).to_be(False)
        expect(request.remote).to_equal("255.255.255.255")

        return web.Response()

    app = web.Application()
    app.router.add_get("/", handler)
    async_setup_forwarded(app, True, [ip_network("127.0.0.1")])

    mock_api_client = await aiohttp_client(app)
    resp = await mock_api_client.get(
        "/", headers={X_FORWARDED_FOR: "222.222.222.222, 255.255.255.255"}
    )

    expect(resp.status).to_equal(HTTPStatus.OK)


@test.cases(
    test.case("invalid_text", x_forwarded_for="This value is invalid"),
    test.case("empty_middle_spaces", x_forwarded_for="1.1.1.1, , 1.2.3.4"),
    test.case("empty_middle_no_space", x_forwarded_for="1.1.1.1,,1.2.3.4"),
    test.case("invalid_word", x_forwarded_for="1.1.1.1, batman, 1.2.3.4"),
    test.case("cidr_only", x_forwarded_for="192.168.0.0/24"),
    test.case("cidr_and_ip", x_forwarded_for="192.168.0.0/24, 1.1.1.1"),
    test.case("only_comma", x_forwarded_for=","),
    test.case("empty_string", x_forwarded_for=""),
)
async def x_forwarded_for_with_malformed_header(
    x_forwarded_for: str,
    _t: None = Depends(_trigger_executor),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that we get a HTTP 400 bad request with a malformed header."""
    app = web.Application()
    app.router.add_get("/", mock_handler)
    async_setup_forwarded(app, True, [ip_network("127.0.0.1")])

    mock_api_client = await aiohttp_client(app)

    resp = await mock_api_client.get("/", headers={X_FORWARDED_FOR: x_forwarded_for})

    expect(resp.status).to_equal(HTTPStatus.BAD_REQUEST)
    expect("Invalid IP address in X-Forwarded-For" in caplog.text).to_be(True)


@test.cases(
    test.case(
        "https_http_http",
        x_forwarded_for="10.10.10.10, 127.0.0.1, 127.0.0.2",
        remote="10.10.10.10",
        x_forwarded_proto="https, http, http",
        secure=True,
    ),
    test.case(
        "https_http_http_no_space",
        x_forwarded_for="10.10.10.10, 127.0.0.1, 127.0.0.2",
        remote="10.10.10.10",
        x_forwarded_proto="https,http,http",
        secure=True,
    ),
    test.case(
        "single_http",
        x_forwarded_for="10.10.10.10, 127.0.0.1, 127.0.0.2",
        remote="10.10.10.10",
        x_forwarded_proto="http",
        secure=False,
    ),
    test.case(
        "http_https_https",
        x_forwarded_for="10.10.10.10, 127.0.0.1, 127.0.0.2",
        remote="10.10.10.10",
        x_forwarded_proto="http, https, https",
        secure=False,
    ),
    test.case(
        "single_https",
        x_forwarded_for="10.10.10.10, 127.0.0.1, 127.0.0.2",
        remote="10.10.10.10",
        x_forwarded_proto="https",
        secure=True,
    ),
    test.case(
        "spoofed_http_https_http",
        x_forwarded_for="255.255.255.255, 10.10.10.10, 127.0.0.1",
        remote="10.10.10.10",
        x_forwarded_proto="http, https, http",
        secure=True,
    ),
    test.case(
        "spoofed_https_http_https",
        x_forwarded_for="255.255.255.255, 10.10.10.10, 127.0.0.1",
        remote="10.10.10.10",
        x_forwarded_proto="https, http, https",
        secure=False,
    ),
    test.case(
        "spoofed_single_https",
        x_forwarded_for="255.255.255.255, 10.10.10.10, 127.0.0.1",
        remote="10.10.10.10",
        x_forwarded_proto="https",
        secure=True,
    ),
)
async def x_forwarded_proto_with_trusted_proxy(
    x_forwarded_for: str,
    remote: str,
    x_forwarded_proto: str,
    secure: bool,
    _t: None = Depends(_trigger_executor),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fixture),
) -> None:
    """Test that we get the proto header if proxy is trusted."""

    async def handler(request):
        expect(request.remote).to_equal(remote)
        expect(request.scheme).to_equal("https" if secure else "http")
        expect(request.secure).to_be(secure)

        return web.Response()

    app = web.Application()
    app.router.add_get("/", handler)
    async_setup_forwarded(app, True, [ip_network("127.0.0.0/24")])

    mock_api_client = await aiohttp_client(app)
    resp = await mock_api_client.get(
        "/",
        headers={
            X_FORWARDED_FOR: x_forwarded_for,
            X_FORWARDED_PROTO: x_forwarded_proto,
        },
    )

    expect(resp.status).to_equal(HTTPStatus.OK)


@test.cases(
    test.case(
        "https_http_http",
        x_forwarded_for="10.10.10.10, 127.0.0.1, 127.0.0.2",
        remote="10.10.10.10",
        x_forwarded_proto=["https", "http", "http"],
        secure=True,
    ),
    test.case(
        "http_https_https",
        x_forwarded_for="10.10.10.10, 127.0.0.1, 127.0.0.2",
        remote="10.10.10.10",
        x_forwarded_proto=["http", "https", "https"],
        secure=False,
    ),
    test.case(
        "spoofed_http_https_http",
        x_forwarded_for="255.255.255.255, 10.10.10.10, 127.0.0.1",
        remote="10.10.10.10",
        x_forwarded_proto=["http", "https", "http"],
        secure=True,
    ),
    test.case(
        "spoofed_https_http_https",
        x_forwarded_for="255.255.255.255, 10.10.10.10, 127.0.0.1",
        remote="10.10.10.10",
        x_forwarded_proto=["https", "http", "https"],
        secure=False,
    ),
)
async def x_multiple_forwarded_proto_with_trusted_proxy(
    x_forwarded_for: str,
    remote: str,
    x_forwarded_proto: list[str],
    secure: bool,
    _t: None = Depends(_trigger_executor),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fixture),
) -> None:
    """Test that we get the proto header if proxy is trusted."""

    async def handler(request):
        expect(request.remote).to_equal(remote)
        expect(request.scheme).to_equal("https" if secure else "http")
        expect(request.secure).to_be(secure)

        return web.Response()

    app = web.Application()
    app.router.add_get("/", handler)
    async_setup_forwarded(app, True, [ip_network("127.0.0.0/24")])

    mock_api_client = await aiohttp_client(app)
    resp = await mock_api_client.get(
        "/",
        headers=[(X_FORWARDED_FOR, x_forwarded_for)]
        + [(X_FORWARDED_PROTO, proto) for proto in x_forwarded_proto],
    )

    expect(resp.status).to_equal(HTTPStatus.OK)


@test
async def x_forwarded_proto_with_trusted_proxy_multiple_for(
    _t: None = Depends(_trigger_executor),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fixture),
) -> None:
    """Test that we get the proto with 1 element in the proto, multiple in the for."""

    async def handler(request):
        url = mock_api_client.make_url("/")
        expect(request.host).to_equal(f"{url.host}:{url.port}")
        expect(request.scheme).to_equal("https")
        expect(request.secure).to_be(True)
        expect(request.remote).to_equal("255.255.255.255")

        return web.Response()

    app = web.Application()
    app.router.add_get("/", handler)
    async_setup_forwarded(app, True, [ip_network("127.0.0.0/24")])

    mock_api_client = await aiohttp_client(app)
    resp = await mock_api_client.get(
        "/",
        headers={
            X_FORWARDED_FOR: "255.255.255.255, 127.0.0.1, 127.0.0.2",
            X_FORWARDED_PROTO: "https",
        },
    )

    expect(resp.status).to_equal(HTTPStatus.OK)


@test
async def x_forwarded_proto_with_trusted_proxy_multiple_for_2(
    _t: None = Depends(_trigger_executor),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fixture),
) -> None:
    """Test that we get the proto with 1 element in the proto, multiple in the for."""

    async def handler(request):
        url = mock_api_client.make_url("/")
        expect(request.host).to_equal(f"{url.host}:{url.port}")
        expect(request.scheme).to_equal("https")
        expect(request.secure).to_be(True)
        expect(request.remote).to_equal("255.255.255.255")

        return web.Response()

    app = web.Application()
    app.router.add_get("/", handler)
    async_setup_forwarded(app, True, [ip_network("127.0.0.0/24")])

    mock_api_client = await aiohttp_client(app)
    resp = await mock_api_client.get(
        "/",
        headers=[
            (X_FORWARDED_FOR, "255.255.255.255"),
            (X_FORWARDED_FOR, "127.0.0.1"),
            (X_FORWARDED_FOR, "127.0.0.2"),
            (X_FORWARDED_PROTO, "https"),
        ],
    )

    expect(resp.status).to_equal(HTTPStatus.OK)


@test
async def x_forwarded_proto_not_processed_without_for(
    _t: None = Depends(_trigger_executor),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fixture),
) -> None:
    """Test that proto header isn't processed without a for header."""

    async def handler(request):
        url = mock_api_client.make_url("/")
        expect(request.host).to_equal(f"{url.host}:{url.port}")
        expect(request.scheme).to_equal("http")
        expect(request.secure).to_be(False)
        expect(request.remote).to_equal("127.0.0.1")

        return web.Response()

    app = web.Application()
    app.router.add_get("/", handler)
    async_setup_forwarded(app, True, [ip_network("127.0.0.1")])

    mock_api_client = await aiohttp_client(app)
    resp = await mock_api_client.get("/", headers={X_FORWARDED_PROTO: "https"})

    expect(resp.status).to_equal(HTTPStatus.OK)


@test.cases(
    test.case("empty_string", x_forwarded_proto=""),
    test.case("only_comma", x_forwarded_proto=","),
    test.case("empty_middle_spaces", x_forwarded_proto="https, , https"),
    test.case("trailing_empty", x_forwarded_proto="https, https, "),
)
async def x_forwarded_proto_empty_element(
    x_forwarded_proto: str,
    _t: None = Depends(_trigger_executor),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that we get a HTTP 400 bad request with empty proto."""
    app = web.Application()
    app.router.add_get("/", mock_handler)
    async_setup_forwarded(app, True, [ip_network("127.0.0.1")])

    mock_api_client = await aiohttp_client(app)
    resp = await mock_api_client.get(
        "/",
        headers={X_FORWARDED_FOR: "1.1.1.1", X_FORWARDED_PROTO: x_forwarded_proto},
    )

    expect(resp.status).to_equal(HTTPStatus.BAD_REQUEST)
    expect("Empty item received in X-Forward-Proto header" in caplog.text).to_be(True)


@test.cases(
    test.case(
        "two_for_three_proto",
        x_forwarded_for="1.1.1.1, 2.2.2.2",
        x_forwarded_proto="https, https, https",
        expected=2,
        got=3,
    ),
    test.case(
        "four_for_three_proto",
        x_forwarded_for="1.1.1.1, 2.2.2.2, 3.3.3.3, 4.4.4.4",
        x_forwarded_proto="https, https, https",
        expected=4,
        got=3,
    ),
)
async def x_forwarded_proto_incorrect_number_of_elements(
    x_forwarded_for: str,
    x_forwarded_proto: str,
    expected: int,
    got: int,
    _t: None = Depends(_trigger_executor),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that we get a HTTP 400 bad request with incorrect number of elements."""
    app = web.Application()
    app.router.add_get("/", mock_handler)
    async_setup_forwarded(app, True, [ip_network("127.0.0.1")])

    mock_api_client = await aiohttp_client(app)
    resp = await mock_api_client.get(
        "/",
        headers={
            X_FORWARDED_FOR: x_forwarded_for,
            X_FORWARDED_PROTO: x_forwarded_proto,
        },
    )

    expect(resp.status).to_equal(HTTPStatus.BAD_REQUEST)
    expect(
        f"Incorrect number of elements in X-Forward-Proto. Expected 1 or {expected}, got {got}"
        in caplog.text
    ).to_be(True)


@test
async def x_forwarded_host_with_trusted_proxy(
    _t: None = Depends(_trigger_executor),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fixture),
) -> None:
    """Test that we get the host header if proxy is trusted."""

    async def handler(request):
        expect(request.host).to_equal("example.com")
        expect(request.scheme).to_equal("http")
        expect(request.secure).to_be(False)
        expect(request.remote).to_equal("255.255.255.255")

        return web.Response()

    app = web.Application()
    app.router.add_get("/", handler)
    async_setup_forwarded(app, True, [ip_network("127.0.0.1")])

    mock_api_client = await aiohttp_client(app)
    resp = await mock_api_client.get(
        "/",
        headers={X_FORWARDED_FOR: "255.255.255.255", X_FORWARDED_HOST: "example.com"},
    )

    expect(resp.status).to_equal(HTTPStatus.OK)


@test
async def x_forwarded_host_not_processed_without_for(
    _t: None = Depends(_trigger_executor),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fixture),
) -> None:
    """Test that host header isn't processed without a for header."""

    async def handler(request):
        url = mock_api_client.make_url("/")
        expect(request.host).to_equal(f"{url.host}:{url.port}")
        expect(request.scheme).to_equal("http")
        expect(request.secure).to_be(False)
        expect(request.remote).to_equal("127.0.0.1")

        return web.Response()

    app = web.Application()
    app.router.add_get("/", handler)
    async_setup_forwarded(app, True, [ip_network("127.0.0.1")])

    mock_api_client = await aiohttp_client(app)
    resp = await mock_api_client.get("/", headers={X_FORWARDED_HOST: "example.com"})

    expect(resp.status).to_equal(HTTPStatus.OK)


@test
async def x_forwarded_host_with_multiple_headers(
    _t: None = Depends(_trigger_executor),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that we get a HTTP 200 OK with multiple headers."""
    app = web.Application()
    app.router.add_get("/", mock_handler)
    async_setup_forwarded(app, True, [ip_network("127.0.0.1")])

    mock_api_client = await aiohttp_client(app)
    resp = await mock_api_client.get(
        "/",
        headers=[
            (X_FORWARDED_FOR, "222.222.222.222"),
            (X_FORWARDED_HOST, "example.com"),
            (X_FORWARDED_HOST, "example.spoof"),
        ],
    )

    expect(resp.status).to_equal(HTTPStatus.OK)


@test
async def x_forwarded_host_with_empty_header(
    _t: None = Depends(_trigger_executor),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that we get a HTTP 400 bad request with empty host value."""
    app = web.Application()
    app.router.add_get("/", mock_handler)
    async_setup_forwarded(app, True, [ip_network("127.0.0.1")])

    mock_api_client = await aiohttp_client(app)
    resp = await mock_api_client.get(
        "/", headers={X_FORWARDED_FOR: "222.222.222.222", X_FORWARDED_HOST: ""}
    )

    expect(resp.status).to_equal(HTTPStatus.BAD_REQUEST)
    expect("Empty value received in X-Forward-Host header" in caplog.text).to_be(True)


@test
async def x_forwarded_cloud(
    _t: None = Depends(_trigger_executor),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that cloud requests are not processed."""
    app = web.Application()
    app.router.add_get("/", mock_handler)
    async_setup_forwarded(app, True, [ip_network("127.0.0.1")])

    mock_api_client = await aiohttp_client(app)

    with patch(
        "hass_nabucasa.remote.is_cloud_request", Mock(get=Mock(return_value=True))
    ):
        resp = await mock_api_client.get(
            "/", headers={X_FORWARDED_FOR: "222.222.222.222", X_FORWARDED_HOST: ""}
        )

    # This request would normally fail because it's invalid, now it works.
    expect(resp.status).to_equal(HTTPStatus.OK)
