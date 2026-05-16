"""The tests for the hassio component."""

from http import HTTPStatus
from unittest.mock import MagicMock, patch

from aiohttp.hdrs import (
    CONTENT_TYPE,
    X_FORWARDED_FOR,
    X_FORWARDED_HOST,
    X_FORWARDED_PROTO,
)
from aiohttp.test_utils import TestClient
from multidict import CIMultiDict
from tryke import Depends, expect, fixture, test

from homeassistant.components.hassio.const import X_AUTH_TOKEN

from ._fixtures import hassio_noauth_client

from tests.hass_fixtures import (
    LogCapture,
    aioclient_mock as aioclient_mock_fixture,
    caplog as caplog_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _aiomock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> int:
    """Ensure mock_network and aioclient_mock patches are active."""
    return 0


@fixture
async def _hassio_noauth_client(
    _trigger: int = Depends(_trigger_executor),
    hassio_noauth_client: TestClient = Depends(hassio_noauth_client),
) -> TestClient:
    """Hassio no-auth client with patches guaranteed active."""
    return hassio_noauth_client


@test.cases(
    test.case("a3_vl", build_type=("a3_vl", "test/beer/ping?index=1")),
    test.case("core", build_type=("core", "index.html")),
    test.case("local", build_type=("local", "panel/config")),
    test.case("jk_921", build_type=("jk_921", "editor.php?idx=3&ping=5")),
    test.case("fsadjf10312", build_type=("fsadjf10312", "")),
)
async def ingress_request_get(
    build_type: tuple[str, str],
    hassio_noauth_client: TestClient = Depends(_hassio_noauth_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test no auth needed for ."""
    aioclient_mock.get(
        f"http://127.0.0.1/ingress/{build_type[0]}/{build_type[1]}",
        text="test",
        headers=CIMultiDict(
            [("Set-Cookie", "cookie1=value1"), ("Set-Cookie", "cookie2=value2")]
        ),
    )

    resp = await hassio_noauth_client.get(
        f"/api/hassio_ingress/{build_type[0]}/{build_type[1]}",
        headers=CIMultiDict(
            [("X-Test-Header", "beer"), ("X-Test-Header", "more beer")]
        ),
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(resp.headers["Set-Cookie"]).to_equal("cookie1=value1")
    expect(resp.headers.getall("Set-Cookie")).to_equal(
        ["cookie1=value1", "cookie2=value2"]
    )
    body = await resp.text()
    expect(body).to_equal("test")

    expect(len(aioclient_mock.mock_calls)).to_equal(1)
    expect(X_AUTH_TOKEN not in aioclient_mock.mock_calls[-1][3]).to_equal(True)
    expect(aioclient_mock.mock_calls[-1][3]["X-Hass-Source"]).to_equal("core.ingress")
    expect(aioclient_mock.mock_calls[-1][3]["X-Ingress-Path"]).to_equal(
        f"/api/hassio_ingress/{build_type[0]}"
    )
    expect(aioclient_mock.mock_calls[-1][3]["X-Test-Header"]).to_equal("beer")
    expect(aioclient_mock.mock_calls[-1][3].getall("X-Test-Header")).to_equal(
        ["beer", "more beer"]
    )
    expect(bool(aioclient_mock.mock_calls[-1][3][X_FORWARDED_FOR])).to_equal(True)
    expect(bool(aioclient_mock.mock_calls[-1][3][X_FORWARDED_HOST])).to_equal(True)
    expect(bool(aioclient_mock.mock_calls[-1][3][X_FORWARDED_PROTO])).to_equal(True)


@test.cases(
    test.case("a3_vl", build_type=("a3_vl", "test/beer/ping?index=1")),
    test.case("core", build_type=("core", "index.html")),
    test.case("local", build_type=("local", "panel/config")),
    test.case("jk_921", build_type=("jk_921", "editor.php?idx=3&ping=5")),
    test.case("fsadjf10312", build_type=("fsadjf10312", "")),
)
async def ingress_request_post(
    build_type: tuple[str, str],
    hassio_noauth_client: TestClient = Depends(_hassio_noauth_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test no auth needed for ."""
    aioclient_mock.post(
        f"http://127.0.0.1/ingress/{build_type[0]}/{build_type[1]}",
        text="test",
    )

    resp = await hassio_noauth_client.post(
        f"/api/hassio_ingress/{build_type[0]}/{build_type[1]}",
        headers={"X-Test-Header": "beer"},
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    body = await resp.text()
    expect(body).to_equal("test")

    expect(len(aioclient_mock.mock_calls)).to_equal(1)
    expect(X_AUTH_TOKEN not in aioclient_mock.mock_calls[-1][3]).to_equal(True)
    expect(aioclient_mock.mock_calls[-1][3]["X-Hass-Source"]).to_equal("core.ingress")
    expect(aioclient_mock.mock_calls[-1][3]["X-Ingress-Path"]).to_equal(
        f"/api/hassio_ingress/{build_type[0]}"
    )
    expect(aioclient_mock.mock_calls[-1][3]["X-Test-Header"]).to_equal("beer")
    expect(bool(aioclient_mock.mock_calls[-1][3][X_FORWARDED_FOR])).to_equal(True)
    expect(bool(aioclient_mock.mock_calls[-1][3][X_FORWARDED_HOST])).to_equal(True)
    expect(bool(aioclient_mock.mock_calls[-1][3][X_FORWARDED_PROTO])).to_equal(True)


@test.cases(
    test.case("a3_vl", build_type=("a3_vl", "test/beer/ping?index=1")),
    test.case("core", build_type=("core", "index.html")),
    test.case("local", build_type=("local", "panel/config")),
    test.case("jk_921", build_type=("jk_921", "editor.php?idx=3&ping=5")),
    test.case("fsadjf10312", build_type=("fsadjf10312", "")),
)
async def ingress_request_put(
    build_type: tuple[str, str],
    hassio_noauth_client: TestClient = Depends(_hassio_noauth_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test no auth needed for ."""
    aioclient_mock.put(
        f"http://127.0.0.1/ingress/{build_type[0]}/{build_type[1]}",
        text="test",
    )

    resp = await hassio_noauth_client.put(
        f"/api/hassio_ingress/{build_type[0]}/{build_type[1]}",
        headers={"X-Test-Header": "beer"},
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    body = await resp.text()
    expect(body).to_equal("test")

    expect(len(aioclient_mock.mock_calls)).to_equal(1)
    expect(X_AUTH_TOKEN not in aioclient_mock.mock_calls[-1][3]).to_equal(True)
    expect(aioclient_mock.mock_calls[-1][3]["X-Hass-Source"]).to_equal("core.ingress")
    expect(aioclient_mock.mock_calls[-1][3]["X-Ingress-Path"]).to_equal(
        f"/api/hassio_ingress/{build_type[0]}"
    )
    expect(aioclient_mock.mock_calls[-1][3]["X-Test-Header"]).to_equal("beer")
    expect(bool(aioclient_mock.mock_calls[-1][3][X_FORWARDED_FOR])).to_equal(True)
    expect(bool(aioclient_mock.mock_calls[-1][3][X_FORWARDED_HOST])).to_equal(True)
    expect(bool(aioclient_mock.mock_calls[-1][3][X_FORWARDED_PROTO])).to_equal(True)


@test.cases(
    test.case("a3_vl", build_type=("a3_vl", "test/beer/ping?index=1")),
    test.case("core", build_type=("core", "index.html")),
    test.case("local", build_type=("local", "panel/config")),
    test.case("jk_921", build_type=("jk_921", "editor.php?idx=3&ping=5")),
    test.case("fsadjf10312", build_type=("fsadjf10312", "")),
)
async def ingress_request_delete(
    build_type: tuple[str, str],
    hassio_noauth_client: TestClient = Depends(_hassio_noauth_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test no auth needed for ."""
    aioclient_mock.delete(
        f"http://127.0.0.1/ingress/{build_type[0]}/{build_type[1]}",
        text="test",
    )

    resp = await hassio_noauth_client.delete(
        f"/api/hassio_ingress/{build_type[0]}/{build_type[1]}",
        headers={"X-Test-Header": "beer"},
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    body = await resp.text()
    expect(body).to_equal("test")

    expect(len(aioclient_mock.mock_calls)).to_equal(1)
    expect(X_AUTH_TOKEN not in aioclient_mock.mock_calls[-1][3]).to_equal(True)
    expect(aioclient_mock.mock_calls[-1][3]["X-Hass-Source"]).to_equal("core.ingress")
    expect(aioclient_mock.mock_calls[-1][3]["X-Ingress-Path"]).to_equal(
        f"/api/hassio_ingress/{build_type[0]}"
    )
    expect(aioclient_mock.mock_calls[-1][3]["X-Test-Header"]).to_equal("beer")
    expect(bool(aioclient_mock.mock_calls[-1][3][X_FORWARDED_FOR])).to_equal(True)
    expect(bool(aioclient_mock.mock_calls[-1][3][X_FORWARDED_HOST])).to_equal(True)
    expect(bool(aioclient_mock.mock_calls[-1][3][X_FORWARDED_PROTO])).to_equal(True)


@test.cases(
    test.case("a3_vl", build_type=("a3_vl", "test/beer/ping?index=1")),
    test.case("core", build_type=("core", "index.html")),
    test.case("local", build_type=("local", "panel/config")),
    test.case("jk_921", build_type=("jk_921", "editor.php?idx=3&ping=5")),
    test.case("fsadjf10312", build_type=("fsadjf10312", "")),
)
async def ingress_request_patch(
    build_type: tuple[str, str],
    hassio_noauth_client: TestClient = Depends(_hassio_noauth_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test no auth needed for ."""
    aioclient_mock.patch(
        f"http://127.0.0.1/ingress/{build_type[0]}/{build_type[1]}",
        text="test",
    )

    resp = await hassio_noauth_client.patch(
        f"/api/hassio_ingress/{build_type[0]}/{build_type[1]}",
        headers={"X-Test-Header": "beer"},
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    body = await resp.text()
    expect(body).to_equal("test")

    expect(len(aioclient_mock.mock_calls)).to_equal(1)
    expect(X_AUTH_TOKEN not in aioclient_mock.mock_calls[-1][3]).to_equal(True)
    expect(aioclient_mock.mock_calls[-1][3]["X-Hass-Source"]).to_equal("core.ingress")
    expect(aioclient_mock.mock_calls[-1][3]["X-Ingress-Path"]).to_equal(
        f"/api/hassio_ingress/{build_type[0]}"
    )
    expect(aioclient_mock.mock_calls[-1][3]["X-Test-Header"]).to_equal("beer")
    expect(bool(aioclient_mock.mock_calls[-1][3][X_FORWARDED_FOR])).to_equal(True)
    expect(bool(aioclient_mock.mock_calls[-1][3][X_FORWARDED_HOST])).to_equal(True)
    expect(bool(aioclient_mock.mock_calls[-1][3][X_FORWARDED_PROTO])).to_equal(True)


@test.cases(
    test.case("a3_vl", build_type=("a3_vl", "test/beer/ping?index=1")),
    test.case("core", build_type=("core", "index.html")),
    test.case("local", build_type=("local", "panel/config")),
    test.case("jk_921", build_type=("jk_921", "editor.php?idx=3&ping=5")),
    test.case("fsadjf10312", build_type=("fsadjf10312", "")),
)
async def ingress_request_options(
    build_type: tuple[str, str],
    hassio_noauth_client: TestClient = Depends(_hassio_noauth_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test no auth needed for ."""
    aioclient_mock.options(
        f"http://127.0.0.1/ingress/{build_type[0]}/{build_type[1]}",
        text="test",
    )

    resp = await hassio_noauth_client.options(
        f"/api/hassio_ingress/{build_type[0]}/{build_type[1]}",
        headers={"X-Test-Header": "beer"},
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    body = await resp.text()
    expect(body).to_equal("test")

    expect(len(aioclient_mock.mock_calls)).to_equal(1)
    expect(X_AUTH_TOKEN not in aioclient_mock.mock_calls[-1][3]).to_equal(True)
    expect(aioclient_mock.mock_calls[-1][3]["X-Hass-Source"]).to_equal("core.ingress")
    expect(aioclient_mock.mock_calls[-1][3]["X-Ingress-Path"]).to_equal(
        f"/api/hassio_ingress/{build_type[0]}"
    )
    expect(aioclient_mock.mock_calls[-1][3]["X-Test-Header"]).to_equal("beer")
    expect(bool(aioclient_mock.mock_calls[-1][3][X_FORWARDED_FOR])).to_equal(True)
    expect(bool(aioclient_mock.mock_calls[-1][3][X_FORWARDED_HOST])).to_equal(True)
    expect(bool(aioclient_mock.mock_calls[-1][3][X_FORWARDED_PROTO])).to_equal(True)


@test.cases(
    test.case("a3_vl", build_type=("a3_vl", "test/beer/ping?index=1")),
    test.case("core", build_type=("core", "index.html")),
    test.case("local", build_type=("local", "panel/config")),
    test.case("jk_921", build_type=("jk_921", "editor.php?idx=3&ping=5")),
    test.case("fsadjf10312", build_type=("fsadjf10312", "")),
)
async def ingress_request_head(
    build_type: tuple[str, str],
    hassio_noauth_client: TestClient = Depends(_hassio_noauth_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test no auth needed for ."""
    aioclient_mock.head(
        f"http://127.0.0.1/ingress/{build_type[0]}/{build_type[1]}",
        text="test",
    )

    resp = await hassio_noauth_client.head(
        f"/api/hassio_ingress/{build_type[0]}/{build_type[1]}",
        headers={"X-Test-Header": "beer"},
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    body = await resp.text()
    expect(body).to_equal("")  # head does not return a body

    expect(len(aioclient_mock.mock_calls)).to_equal(1)
    expect(X_AUTH_TOKEN not in aioclient_mock.mock_calls[-1][3]).to_equal(True)
    expect(aioclient_mock.mock_calls[-1][3]["X-Hass-Source"]).to_equal("core.ingress")
    expect(aioclient_mock.mock_calls[-1][3]["X-Ingress-Path"]).to_equal(
        f"/api/hassio_ingress/{build_type[0]}"
    )
    expect(aioclient_mock.mock_calls[-1][3]["X-Test-Header"]).to_equal("beer")
    expect(bool(aioclient_mock.mock_calls[-1][3][X_FORWARDED_FOR])).to_equal(True)
    expect(bool(aioclient_mock.mock_calls[-1][3][X_FORWARDED_HOST])).to_equal(True)
    expect(bool(aioclient_mock.mock_calls[-1][3][X_FORWARDED_PROTO])).to_equal(True)


@test
async def ingress_request_head_with_content_type(
    hassio_noauth_client: TestClient = Depends(_hassio_noauth_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test HEAD request preserves content-type from upstream."""
    aioclient_mock.head(
        "http://127.0.0.1/ingress/core/index.html",
        text="",
        headers={"Content-Type": "text/html; charset=utf-8"},
    )

    resp = await hassio_noauth_client.head(
        "/api/hassio_ingress/core/index.html",
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    body = await resp.text()
    expect(body).to_equal("")
    expect(resp.headers[CONTENT_TYPE]).to_equal("text/html")


@test
async def ingress_request_head_without_content_type(
    hassio_noauth_client: TestClient = Depends(_hassio_noauth_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test HEAD request without upstream content-type omits it."""
    aioclient_mock.head(
        "http://127.0.0.1/ingress/core/index.html",
        text="",
    )

    resp = await hassio_noauth_client.head(
        "/api/hassio_ingress/core/index.html",
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    body = await resp.text()
    expect(body).to_equal("")
    expect(CONTENT_TYPE not in resp.headers).to_equal(True)


@test
async def ingress_request_304_no_content_type(
    hassio_noauth_client: TestClient = Depends(_hassio_noauth_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test 304 Not Modified does not include content-type when upstream omits it."""
    aioclient_mock.get(
        "http://127.0.0.1/ingress/core/index.html",
        text="",
        status=HTTPStatus.NOT_MODIFIED,
    )

    resp = await hassio_noauth_client.get(
        "/api/hassio_ingress/core/index.html",
    )

    expect(resp.status).to_equal(HTTPStatus.NOT_MODIFIED)
    body = await resp.text()
    expect(body).to_equal("")
    expect(CONTENT_TYPE not in resp.headers).to_equal(True)


@test
async def ingress_request_304_with_content_type(
    hassio_noauth_client: TestClient = Depends(_hassio_noauth_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test 304 Not Modified preserves content-type when upstream provides it."""
    aioclient_mock.get(
        "http://127.0.0.1/ingress/core/index.html",
        text="",
        status=HTTPStatus.NOT_MODIFIED,
        headers={"Content-Type": "text/html"},
    )

    resp = await hassio_noauth_client.get(
        "/api/hassio_ingress/core/index.html",
    )

    expect(resp.status).to_equal(HTTPStatus.NOT_MODIFIED)
    body = await resp.text()
    expect(body).to_equal("")
    expect(resp.headers[CONTENT_TYPE]).to_equal("text/html")


@test
async def ingress_request_204_no_content(
    hassio_noauth_client: TestClient = Depends(_hassio_noauth_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test 204 No Content does not include content-type."""
    aioclient_mock.get(
        "http://127.0.0.1/ingress/core/api/status",
        text="",
        status=HTTPStatus.NO_CONTENT,
    )

    resp = await hassio_noauth_client.get(
        "/api/hassio_ingress/core/api/status",
    )

    expect(resp.status).to_equal(HTTPStatus.NO_CONTENT)
    body = await resp.text()
    expect(body).to_equal("")
    expect(CONTENT_TYPE not in resp.headers).to_equal(True)


@test.cases(
    test.case("a3_vl", build_type=("a3_vl", "test/beer/ws")),
    test.case("core", build_type=("core", "ws.php")),
    test.case("local", build_type=("local", "panel/config/stream")),
    test.case("jk_921", build_type=("jk_921", "hulk")),
    test.case("demo", build_type=("demo", "ws/connection?id=9&token=SJAKWS283")),
)
async def ingress_websocket(
    build_type: tuple[str, str],
    hassio_noauth_client: TestClient = Depends(_hassio_noauth_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test no auth needed for ."""
    aioclient_mock.get(f"http://127.0.0.1/ingress/{build_type[0]}/{build_type[1]}")

    # Ignore error because we can setup a full IO infrastructure
    await hassio_noauth_client.ws_connect(
        f"/api/hassio_ingress/{build_type[0]}/{build_type[1]}",
        headers={"X-Test-Header": "beer"},
    )

    expect(len(aioclient_mock.mock_calls)).to_equal(1)
    expect(X_AUTH_TOKEN not in aioclient_mock.mock_calls[-1][3]).to_equal(True)
    expect(aioclient_mock.mock_calls[-1][3]["X-Hass-Source"]).to_equal("core.ingress")
    expect(aioclient_mock.mock_calls[-1][3]["X-Ingress-Path"]).to_equal(
        f"/api/hassio_ingress/{build_type[0]}"
    )
    expect(aioclient_mock.mock_calls[-1][3]["X-Test-Header"]).to_equal("beer")
    expect(bool(aioclient_mock.mock_calls[-1][3][X_FORWARDED_FOR])).to_equal(True)
    expect(bool(aioclient_mock.mock_calls[-1][3][X_FORWARDED_HOST])).to_equal(True)
    expect(bool(aioclient_mock.mock_calls[-1][3][X_FORWARDED_PROTO])).to_equal(True)


@test
async def ingress_missing_peername(
    hassio_noauth_client: TestClient = Depends(_hassio_noauth_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test handling of missing peername."""
    aioclient_mock.get(
        "http://127.0.0.1/ingress/lorem/ipsum",
        text="test",
    )

    def get_extra_info(_):
        return None

    with patch(
        "aiohttp.web_request.BaseRequest.transport",
        return_value=MagicMock(),
    ) as transport_mock:
        transport_mock.get_extra_info = get_extra_info
        resp = await hassio_noauth_client.get(
            "/api/hassio_ingress/lorem/ipsum",
            headers={"X-Test-Header": "beer"},
        )

    expect("Can't set forward_for header, missing peername" in caplog.text).to_equal(
        True
    )

    expect(resp.status).to_equal(HTTPStatus.BAD_REQUEST)


@test
async def forwarding_paths_as_requested(
    hassio_noauth_client: TestClient = Depends(_hassio_noauth_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test incomnig URLs with double encoding go out as dobule encoded."""
    # This double encoded string should be forwarded double-encoded too.
    aioclient_mock.get(
        "http://127.0.0.1/ingress/mock-token/hello/%252e./world",
        text="test",
    )

    resp = await hassio_noauth_client.get(
        "/api/hassio_ingress/mock-token/hello/%252e./world",
    )
    expect(await resp.text()).to_equal("test")


@test.cases(
    test.case("a3_vl", build_type=("a3_vl", "test/beer/ping?index=1")),
    test.case("core", build_type=("core", "index.html")),
    test.case("local", build_type=("local", "panel/config")),
    test.case("jk_921", build_type=("jk_921", "editor.php?idx=3&ping=5")),
    test.case("fsadjf10312", build_type=("fsadjf10312", "")),
)
async def ingress_request_get_compressed(
    build_type: tuple[str, str],
    hassio_noauth_client: TestClient = Depends(_hassio_noauth_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test ingress compressed."""
    body = "this_is_long_enough_to_be_compressed" * 100
    aioclient_mock.get(
        f"http://127.0.0.1/ingress/{build_type[0]}/{build_type[1]}",
        text=body,
        headers={"Content-Length": len(body), "Content-Type": "text/plain"},
    )

    resp = await hassio_noauth_client.get(
        f"/api/hassio_ingress/{build_type[0]}/{build_type[1]}",
        headers={"X-Test-Header": "beer", "Accept-Encoding": "gzip, deflate"},
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    resp_body = await resp.text()
    expect(resp_body).to_equal(body)
    expect(resp.headers["Content-Encoding"]).to_equal("deflate")

    expect(len(aioclient_mock.mock_calls)).to_equal(1)
    expect(X_AUTH_TOKEN not in aioclient_mock.mock_calls[-1][3]).to_equal(True)
    expect(aioclient_mock.mock_calls[-1][3]["X-Hass-Source"]).to_equal("core.ingress")
    expect(aioclient_mock.mock_calls[-1][3]["X-Ingress-Path"]).to_equal(
        f"/api/hassio_ingress/{build_type[0]}"
    )
    expect(aioclient_mock.mock_calls[-1][3]["X-Test-Header"]).to_equal("beer")
    expect(bool(aioclient_mock.mock_calls[-1][3][X_FORWARDED_FOR])).to_equal(True)
    expect(bool(aioclient_mock.mock_calls[-1][3][X_FORWARDED_HOST])).to_equal(True)
    expect(bool(aioclient_mock.mock_calls[-1][3][X_FORWARDED_PROTO])).to_equal(True)


@test.cases(
    test.case("image_png", content_type="image/png"),
    test.case("image_jpeg", content_type="image/jpeg"),
    test.case("font_woff2", content_type="font/woff2"),
    test.case("video_mp4", content_type="video/mp4"),
    test.case("application_tar", content_type="application/tar"),
)
async def ingress_request_not_compressed(
    content_type: str,
    hassio_noauth_client: TestClient = Depends(_hassio_noauth_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test ingress does not compress images."""
    body = b"this_is_long_enough_to_be_compressed" * 100
    aioclient_mock.get(
        "http://127.0.0.1/ingress/core/x.any",
        data=body,
        headers={"Content-Length": len(body), "Content-Type": content_type},
    )

    resp = await hassio_noauth_client.get(
        "/api/hassio_ingress/core/x.any",
        headers={"X-Test-Header": "beer", "Accept-Encoding": "gzip, deflate"},
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(resp.headers["Content-Type"]).to_equal(content_type)
    expect("Content-Encoding" not in resp.headers).to_equal(True)


@test
async def ingress_request_with_charset_in_content_type(
    hassio_noauth_client: TestClient = Depends(_hassio_noauth_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test ingress passes content type."""
    body = b"this_is_long_enough_to_be_compressed" * 100
    aioclient_mock.get(
        "http://127.0.0.1/ingress/core/x.any",
        data=body,
        headers={
            "Content-Length": len(body),
            "Content-Type": "text/html; charset=utf-8",
        },
    )

    resp = await hassio_noauth_client.get(
        "/api/hassio_ingress/core/x.any",
        headers={"X-Test-Header": "beer", "Accept-Encoding": "gzip, deflate"},
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(resp.headers["Content-Type"]).to_equal("text/html")


@test.cases(
    test.case("image_svg_xml", content_type="image/svg+xml"),
    test.case("text_html", content_type="text/html"),
    test.case("application_javascript", content_type="application/javascript"),
    test.case("text_plain", content_type="text/plain"),
    test.case("application_json", content_type="application/json"),
)
async def ingress_request_compressed(
    content_type: str,
    hassio_noauth_client: TestClient = Depends(_hassio_noauth_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test ingress compresses text."""
    body = b"this_is_long_enough_to_be_compressed" * 100
    aioclient_mock.get(
        "http://127.0.0.1/ingress/core/x.any",
        data=body,
        headers={"Content-Length": len(body), "Content-Type": content_type},
    )

    resp = await hassio_noauth_client.get(
        "/api/hassio_ingress/core/x.any",
        headers={"X-Test-Header": "beer", "Accept-Encoding": "gzip, deflate"},
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(resp.headers["Content-Type"]).to_equal(content_type)
    expect(resp.headers["Content-Encoding"]).to_equal("deflate")


@test.cases(
    test.case("a3_vl", build_type=("a3_vl", "test/beer/ping?index=1")),
    test.case("core", build_type=("core", "index.html")),
    test.case("local", build_type=("local", "panel/config")),
    test.case("jk_921", build_type=("jk_921", "editor.php?idx=3&ping=5")),
    test.case("fsadjf10312", build_type=("fsadjf10312", "")),
)
async def ingress_request_get_not_changed(
    build_type: tuple[str, str],
    hassio_noauth_client: TestClient = Depends(_hassio_noauth_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test ingress compressed and not modified."""
    aioclient_mock.get(
        f"http://127.0.0.1/ingress/{build_type[0]}/{build_type[1]}",
        text="test",
        status=HTTPStatus.NOT_MODIFIED,
    )

    resp = await hassio_noauth_client.get(
        f"/api/hassio_ingress/{build_type[0]}/{build_type[1]}",
        headers={"X-Test-Header": "beer", "Accept-Encoding": "gzip, deflate"},
    )

    expect(resp.status).to_equal(HTTPStatus.NOT_MODIFIED)
    body = await resp.text()
    expect(body).to_equal("")
    expect("Content-Encoding" not in resp.headers).to_equal(True)  # too small to compress

    expect(len(aioclient_mock.mock_calls)).to_equal(1)
    expect(X_AUTH_TOKEN not in aioclient_mock.mock_calls[-1][3]).to_equal(True)
    expect(aioclient_mock.mock_calls[-1][3]["X-Hass-Source"]).to_equal("core.ingress")
    expect(aioclient_mock.mock_calls[-1][3]["X-Ingress-Path"]).to_equal(
        f"/api/hassio_ingress/{build_type[0]}"
    )
    expect(aioclient_mock.mock_calls[-1][3]["X-Test-Header"]).to_equal("beer")
    expect(bool(aioclient_mock.mock_calls[-1][3][X_FORWARDED_FOR])).to_equal(True)
    expect(bool(aioclient_mock.mock_calls[-1][3][X_FORWARDED_HOST])).to_equal(True)
    expect(bool(aioclient_mock.mock_calls[-1][3][X_FORWARDED_PROTO])).to_equal(True)
