"""The tests for the hassio component."""

from http import HTTPStatus

from aiohttp import StreamReader
from aiohttp.test_utils import TestClient
from tryke import Depends, expect, fixture, test

from ._fixtures import hassio_client, hassio_noauth_client

from tests.common import MockUser
from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fixture,
    hass_admin_user as hass_admin_user_fixture,
)
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(
    _aiomock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> int:
    """Ensure aioclient_mock patch is active before HA sessions are created."""
    return 0


@fixture
async def _hassio_client(
    _trigger: int = Depends(_trigger_executor),
    hassio_client: TestClient = Depends(hassio_client),
) -> TestClient:
    """Hassio admin client with aioclient_mock patch guaranteed active."""
    return hassio_client


@fixture
async def _hassio_noauth_client(
    _trigger: int = Depends(_trigger_executor),
    hassio_noauth_client: TestClient = Depends(hassio_noauth_client),
) -> TestClient:
    """Hassio no-auth client with aioclient_mock patch guaranteed active."""
    return hassio_noauth_client


def _strip_admin(user: MockUser) -> None:
    """Demote a user to non-admin by emptying their groups."""
    user.groups = []


@test.cases(
    test.case("logo", path="addons/bl_b392/logo"),
    test.case("icon", path="addons/bl_b392/icon"),
)
async def forward_request_onboarded_user_get(
    path: str,
    hassio_client: TestClient = Depends(_hassio_client),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test fetching normal path."""
    _strip_admin(hass_admin_user)
    aioclient_mock.get(f"http://127.0.0.1/{path}", text="response")

    resp = await hassio_client.get(f"/api/hassio/{path}")

    expect(resp.status).to_equal(HTTPStatus.OK)
    body = await resp.text()
    expect(body).to_equal("response")

    expect(len(aioclient_mock.mock_calls)).to_equal(1)
    expect(aioclient_mock.mock_calls[0][3]).to_equal({"X-Hass-Source": "core.http"})


@test.cases(
    test.case("POST", method="POST"),
    test.case("PUT", method="PUT"),
    test.case("DELETE", method="DELETE"),
)
async def forward_request_onboarded_user_unallowed_methods(
    method: str,
    hassio_client: TestClient = Depends(_hassio_client),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test fetching normal path."""
    _strip_admin(hass_admin_user)
    resp = await hassio_client.request(method, "/api/hassio/addons/bl_b392/icon")

    expect(resp.status).to_equal(HTTPStatus.METHOD_NOT_ALLOWED)
    expect(len(aioclient_mock.mock_calls)).to_equal(0)


@test.cases(
    test.case(
        "bullshit_filter",
        bad_path="addons/bl_b392/%252E./icon",
        expected_status=HTTPStatus.BAD_REQUEST,
    ),
    test.case(
        "supervisor_info",
        bad_path="supervisor/info",
        expected_status=HTTPStatus.UNAUTHORIZED,
    ),
    test.case(
        "supervisor_logs",
        bad_path="supervisor/logs",
        expected_status=HTTPStatus.UNAUTHORIZED,
    ),
    test.case(
        "supervisor_logs_follow",
        bad_path="supervisor/logs/follow",
        expected_status=HTTPStatus.UNAUTHORIZED,
    ),
    test.case(
        "addon_logs",
        bad_path="addons/bl_b392/logs",
        expected_status=HTTPStatus.UNAUTHORIZED,
    ),
    test.case(
        "addon_logs_follow",
        bad_path="addons/bl_b392/logs/follow",
        expected_status=HTTPStatus.UNAUTHORIZED,
    ),
)
async def forward_request_onboarded_user_unallowed_paths(
    bad_path: str,
    expected_status: int,
    hassio_client: TestClient = Depends(_hassio_client),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test fetching normal path."""
    _strip_admin(hass_admin_user)
    resp = await hassio_client.get(f"/api/hassio/{bad_path}")

    expect(resp.status).to_equal(expected_status)
    expect(len(aioclient_mock.mock_calls)).to_equal(0)


@test.cases(
    test.case("logo", path="addons/bl_b392/logo"),
    test.case("icon", path="addons/bl_b392/icon"),
)
async def forward_request_onboarded_noauth_get(
    path: str,
    hassio_noauth_client: TestClient = Depends(_hassio_noauth_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test fetching normal path."""
    aioclient_mock.get(f"http://127.0.0.1/{path}", text="response")

    resp = await hassio_noauth_client.get(f"/api/hassio/{path}")

    expect(resp.status).to_equal(HTTPStatus.OK)
    body = await resp.text()
    expect(body).to_equal("response")

    expect(len(aioclient_mock.mock_calls)).to_equal(1)
    expect(aioclient_mock.mock_calls[0][3]).to_equal({"X-Hass-Source": "core.http"})


@test.cases(
    test.case("POST", method="POST"),
    test.case("PUT", method="PUT"),
    test.case("DELETE", method="DELETE"),
)
async def forward_request_onboarded_noauth_unallowed_methods(
    method: str,
    hassio_noauth_client: TestClient = Depends(_hassio_noauth_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test fetching normal path."""
    resp = await hassio_noauth_client.request(method, "/api/hassio/addons/bl_b392/icon")

    expect(resp.status).to_equal(HTTPStatus.METHOD_NOT_ALLOWED)
    expect(len(aioclient_mock.mock_calls)).to_equal(0)


@test.cases(
    test.case(
        "bullshit_filter",
        bad_path="addons/bl_b392/%252E./icon",
        expected_status=HTTPStatus.BAD_REQUEST,
    ),
    test.case(
        "supervisor_info",
        bad_path="supervisor/info",
        expected_status=HTTPStatus.UNAUTHORIZED,
    ),
    test.case(
        "supervisor_logs",
        bad_path="supervisor/logs",
        expected_status=HTTPStatus.UNAUTHORIZED,
    ),
    test.case(
        "supervisor_logs_follow",
        bad_path="supervisor/logs/follow",
        expected_status=HTTPStatus.UNAUTHORIZED,
    ),
    test.case(
        "addon_logs",
        bad_path="addons/bl_b392/logs",
        expected_status=HTTPStatus.UNAUTHORIZED,
    ),
    test.case(
        "addon_logs_follow",
        bad_path="addons/bl_b392/logs/follow",
        expected_status=HTTPStatus.UNAUTHORIZED,
    ),
)
async def forward_request_onboarded_noauth_unallowed_paths(
    bad_path: str,
    expected_status: int,
    hassio_noauth_client: TestClient = Depends(_hassio_noauth_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test fetching normal path."""
    resp = await hassio_noauth_client.get(f"/api/hassio/{bad_path}")

    expect(resp.status).to_equal(expected_status)
    expect(len(aioclient_mock.mock_calls)).to_equal(0)


@test.cases(
    test.case("get_info", method="GET", path="backups/1234abcd/info"),
    test.case("get_download", method="GET", path="backups/1234abcd/download"),
    test.case("post_restore_full", method="POST", path="backups/1234abcd/restore/full"),
    test.case(
        "post_restore_partial", method="POST", path="backups/1234abcd/restore/partial"
    ),
    test.case("post_new_upload", method="POST", path="backups/new/upload"),
)
async def forward_request_backup_unauthenticated_rejected(
    method: str,
    path: str,
    hassio_noauth_client: TestClient = Depends(_hassio_noauth_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test backup endpoints reject unauthenticated requests."""
    resp = await hassio_noauth_client.request(method, f"/api/hassio/{path}")

    expect(resp.status).to_equal(HTTPStatus.UNAUTHORIZED)
    expect(len(aioclient_mock.mock_calls)).to_equal(0)


@test.cases(
    test.case("get_info", method="GET", path="backups/1234abcd/info"),
    test.case("get_download", method="GET", path="backups/1234abcd/download"),
    test.case("post_restore_full", method="POST", path="backups/1234abcd/restore/full"),
    test.case(
        "post_restore_partial", method="POST", path="backups/1234abcd/restore/partial"
    ),
    test.case("post_new_upload", method="POST", path="backups/new/upload"),
)
async def forward_request_backup_non_admin_rejected(
    method: str,
    path: str,
    hassio_client: TestClient = Depends(_hassio_client),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test backup endpoints reject authenticated non-admin requests."""
    _strip_admin(hass_admin_user)
    resp = await hassio_client.request(method, f"/api/hassio/{path}")

    expect(resp.status).to_equal(HTTPStatus.UNAUTHORIZED)
    expect(len(aioclient_mock.mock_calls)).to_equal(0)


@test.cases(
    test.case("logo", path="addons/bl_b392/logo", authenticated=False),
    test.case("icon", path="addons/bl_b392/icon", authenticated=False),
    test.case("backup_info", path="backups/1234abcd/info", authenticated=True),
    test.case("supervisor_logs", path="supervisor/logs", authenticated=True),
    test.case(
        "supervisor_logs_follow", path="supervisor/logs/follow", authenticated=True
    ),
    test.case("addon_logs", path="addons/bl_b392/logs", authenticated=True),
    test.case(
        "addon_logs_follow", path="addons/bl_b392/logs/follow", authenticated=True
    ),
    test.case("addon_changelog", path="addons/bl_b392/changelog", authenticated=True),
    test.case(
        "addon_documentation", path="addons/bl_b392/documentation", authenticated=True
    ),
)
async def forward_request_admin_get(
    path: str,
    authenticated: bool,
    hassio_client: TestClient = Depends(_hassio_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test fetching normal path."""
    aioclient_mock.get(f"http://127.0.0.1/{path}", text="response")

    resp = await hassio_client.get(f"/api/hassio/{path}")

    expect(resp.status).to_equal(HTTPStatus.OK)
    body = await resp.text()
    expect(body).to_equal("response")

    expect(len(aioclient_mock.mock_calls)).to_equal(1)
    expected_headers = {
        "X-Hass-Source": "core.http",
    }
    if authenticated:
        expected_headers["Authorization"] = "Bearer 123456"

    expect(aioclient_mock.mock_calls[0][3]).to_equal(expected_headers)


@test.cases(
    test.case("new_upload", path="backups/new/upload"),
    test.case("restore_full", path="backups/1234abcd/restore/full"),
    test.case("restore_partial", path="backups/1234abcd/restore/partial"),
)
async def forward_request_admin_post(
    path: str,
    hassio_client: TestClient = Depends(_hassio_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test fetching normal path."""
    aioclient_mock.get(f"http://127.0.0.1/{path}", text="response")

    resp = await hassio_client.get(f"/api/hassio/{path}")

    expect(resp.status).to_equal(HTTPStatus.OK)
    body = await resp.text()
    expect(body).to_equal("response")

    expect(len(aioclient_mock.mock_calls)).to_equal(1)
    expect(aioclient_mock.mock_calls[0][3]).to_equal(
        {
            "X-Hass-Source": "core.http",
            "Authorization": "Bearer 123456",
        }
    )


@test.cases(
    test.case("POST", method="POST"),
    test.case("PUT", method="PUT"),
    test.case("DELETE", method="DELETE"),
)
async def forward_request_admin_unallowed_methods(
    method: str,
    hassio_client: TestClient = Depends(_hassio_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test fetching normal path."""
    resp = await hassio_client.request(method, "/api/hassio/addons/bl_b392/icon")

    expect(resp.status).to_equal(HTTPStatus.METHOD_NOT_ALLOWED)
    expect(len(aioclient_mock.mock_calls)).to_equal(0)


@test.cases(
    test.case(
        "bullshit_filter",
        bad_path="addons/bl_b392/%252E./icon",
        expected_status=HTTPStatus.BAD_REQUEST,
    ),
    test.case(
        "supervisor_info",
        bad_path="supervisor/info",
        expected_status=HTTPStatus.UNAUTHORIZED,
    ),
)
async def forward_request_admin_unallowed_paths(
    bad_path: str,
    expected_status: int,
    hassio_client: TestClient = Depends(_hassio_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test fetching normal path."""
    resp = await hassio_client.get(f"/api/hassio/{bad_path}")

    expect(resp.status).to_equal(expected_status)
    expect(len(aioclient_mock.mock_calls)).to_equal(0)


@test
async def bad_gateway_when_cannot_find_supervisor(
    hassio_client: TestClient = Depends(_hassio_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test we get a bad gateway error if we can't find supervisor."""
    aioclient_mock.get("http://127.0.0.1/addons/bl_b392/icon", exc=TimeoutError)

    resp = await hassio_client.get("/api/hassio/addons/bl_b392/icon")
    expect(resp.status).to_equal(HTTPStatus.BAD_GATEWAY)


@test
async def backup_upload_headers(
    hassio_client: TestClient = Depends(_hassio_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test that we forward the full header for backup upload."""
    content_type = "multipart/form-data; boundary='--webkit'"
    aioclient_mock.post("http://127.0.0.1/backups/new/upload")

    resp = await hassio_client.post(
        "/api/hassio/backups/new/upload", headers={"Content-Type": content_type}
    )

    expect(resp.status).to_equal(HTTPStatus.OK)

    expect(len(aioclient_mock.mock_calls)).to_equal(1)

    req_headers = aioclient_mock.mock_calls[0][-1]
    expect(req_headers["Content-Type"]).to_equal(content_type)


@test
async def backup_download_headers(
    hassio_client: TestClient = Depends(_hassio_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test that we forward the full header for backup download."""
    content_disposition = "attachment; filename=test.tar"
    aioclient_mock.get(
        "http://127.0.0.1/backups/1234abcd/download",
        headers={
            "Content-Length": "50000000",
            "Content-Disposition": content_disposition,
        },
    )

    resp = await hassio_client.get("/api/hassio/backups/1234abcd/download")

    expect(resp.status).to_equal(HTTPStatus.OK)

    expect(len(aioclient_mock.mock_calls)).to_equal(1)

    expect(resp.headers["Content-Disposition"]).to_equal(content_disposition)


@test
async def stream(
    hassio_client: TestClient = Depends(_hassio_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Verify that the request is a stream."""
    content_type = "multipart/form-data; boundary='--webkit'"
    aioclient_mock.post("http://127.0.0.1/backups/new/upload")
    resp = await hassio_client.post(
        "/api/hassio/backups/new/upload", headers={"Content-Type": content_type}
    )
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(isinstance(aioclient_mock.mock_calls[-1][2], StreamReader)).to_be(True)


@test
async def simple_get_no_stream(
    hassio_client: TestClient = Depends(_hassio_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Verify that a simple GET request is not a stream."""
    aioclient_mock.get("http://127.0.0.1/addons/bl_b392/icon")
    resp = await hassio_client.get("/api/hassio/addons/bl_b392/icon")
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(aioclient_mock.mock_calls[-1][2]).to_be_none()


@test
async def no_follow_logs_compress(
    hassio_client: TestClient = Depends(_hassio_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test that we do not compress follow logs."""
    aioclient_mock.get(
        "http://127.0.0.1/supervisor/logs/follow",
        headers={"Content-Type": "text/plain"},
    )
    aioclient_mock.get(
        "http://127.0.0.1/supervisor/logs",
        headers={"Content-Type": "text/plain"},
    )

    resp1 = await hassio_client.get("/api/hassio/supervisor/logs/follow")
    resp2 = await hassio_client.get("/api/hassio/supervisor/logs")

    expect(resp1.status).to_equal(HTTPStatus.OK)
    expect(resp1.headers.get("Content-Encoding")).to_be_none()

    expect(resp2.status).to_equal(HTTPStatus.OK)
    expect(resp2.headers.get("Content-Encoding")).to_equal("deflate")


@test
async def no_event_stream_compress(
    hassio_client: TestClient = Depends(_hassio_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test that we do not compress SSE (Server-Sent Events) streams."""
    aioclient_mock.get(
        "http://127.0.0.1/backups/1234abcd/info",
        headers={"Content-Type": "text/event-stream"},
    )
    aioclient_mock.get(
        "http://127.0.0.1/addons/bl_b392/changelog",
        headers={"Content-Type": "application/json"},
    )

    resp1 = await hassio_client.get("/api/hassio/backups/1234abcd/info")
    resp2 = await hassio_client.get("/api/hassio/addons/bl_b392/changelog")

    expect(resp1.status).to_equal(HTTPStatus.OK)
    # SSE (text/event-stream) should not be compressed to allow streaming
    expect(resp1.headers.get("Content-Encoding")).to_be_none()

    expect(resp2.status).to_equal(HTTPStatus.OK)
    # Regular JSON should be compressed
    expect(resp2.headers.get("Content-Encoding")).to_equal("deflate")


@test
async def forward_range_header_for_logs(
    hassio_client: TestClient = Depends(_hassio_client),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test that we forward the Range header for logs."""
    aioclient_mock.get("http://127.0.0.1/host/logs")
    aioclient_mock.get("http://127.0.0.1/host/logs/boots/-1")
    aioclient_mock.get("http://127.0.0.1/host/logs/boots/-2/follow?lines=100")
    aioclient_mock.get("http://127.0.0.1/addons/123abc_esphome/logs")
    aioclient_mock.get("http://127.0.0.1/addons/123abc_esphome/logs/follow")
    aioclient_mock.get("http://127.0.0.1/backups/1234abcd/download")

    test_range = ":-100:50"

    host_resp = await hassio_client.get(
        "/api/hassio/host/logs", headers={"Range": test_range}
    )
    host_resp2 = await hassio_client.get(
        "/api/hassio/host/logs/boots/-1", headers={"Range": test_range}
    )
    host_resp3 = await hassio_client.get(
        "/api/hassio/host/logs/boots/-2/follow?lines=100", headers={"Range": test_range}
    )
    addon_resp = await hassio_client.get(
        "/api/hassio/addons/123abc_esphome/logs", headers={"Range": test_range}
    )
    addon_resp2 = await hassio_client.get(
        "/api/hassio/addons/123abc_esphome/logs/follow", headers={"Range": test_range}
    )
    backup_resp = await hassio_client.get(
        "/api/hassio/backups/1234abcd/download", headers={"Range": test_range}
    )

    expect(host_resp.status).to_equal(HTTPStatus.OK)
    expect(host_resp2.status).to_equal(HTTPStatus.OK)
    expect(host_resp3.status).to_equal(HTTPStatus.OK)
    expect(addon_resp.status).to_equal(HTTPStatus.OK)
    expect(addon_resp2.status).to_equal(HTTPStatus.OK)
    expect(backup_resp.status).to_equal(HTTPStatus.OK)

    expect(len(aioclient_mock.mock_calls)).to_equal(6)

    expect(aioclient_mock.mock_calls[0][-1].get("Range")).to_equal(test_range)
    expect(aioclient_mock.mock_calls[1][-1].get("Range")).to_equal(test_range)
    expect(aioclient_mock.mock_calls[2][-1].get("Range")).to_equal(test_range)
    expect(aioclient_mock.mock_calls[3][-1].get("Range")).to_equal(test_range)
    expect(aioclient_mock.mock_calls[4][-1].get("Range")).to_equal(test_range)
    expect(aioclient_mock.mock_calls[5][-1].get("Range")).to_be_none()
