"""The tests for the Home Assistant HTTP component."""

from http import HTTPStatus
from ipaddress import ip_address
import logging
import os
from unittest.mock import Mock, mock_open, patch

from aiohttp import web
from aiohttp.web_exceptions import HTTPUnauthorized
from aiohttp.web_middlewares import middleware
from tryke import Depends, expect, fixture, test

from homeassistant.components import http
from homeassistant.components.http.ban import (
    IP_BANS_FILE,
    KEY_BAN_MANAGER,
    KEY_FAILED_LOGIN_ATTEMPTS,
    process_success_login,
    setup_bans,
)
from homeassistant.components.http.view import request_handler_factory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.http import KEY_AUTHENTICATED, KEY_HASS
from homeassistant.setup import async_setup_component

from ._fixtures import (
    gethostbyaddr_mock,
    hassio_bundle,
)

from tests.common import async_get_persistent_notifications
from tests.hass_fixtures import (
    LogCapture,
    aiohttp_client as aiohttp_client_fixture,
    caplog as caplog_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.test_util import mock_real_ip
from tests.typing import ClientSessionGenerator

SUPERVISOR_IP = "1.2.3.4"
BANNED_IPS = ["200.201.202.203", "100.64.0.2"]
BANNED_IPS_WITH_SUPERVISOR = [*BANNED_IPS, SUPERVISOR_IP]


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _gethostbyaddr: None = Depends(gethostbyaddr_mock),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def access_from_banned_ip(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fixture),
) -> None:
    """Test accessing to server from banned IP. Both trusted and not."""
    app = web.Application()
    app[KEY_HASS] = hass
    setup_bans(hass, app, 5)
    set_real_ip = mock_real_ip(app)

    with patch(
        "homeassistant.components.http.ban.load_yaml_config_file",
        return_value={
            banned_ip: {"banned_at": "2016-11-16T19:20:03"} for banned_ip in BANNED_IPS
        },
    ):
        client = await aiohttp_client(app)

    for remote_addr in BANNED_IPS:
        set_real_ip(remote_addr)
        resp = await client.get("/")
        expect(resp.status).to_equal(HTTPStatus.FORBIDDEN)


@test
async def access_from_banned_ip_with_partially_broken_yaml_file(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test accessing to server from banned IP. Both trusted and not.

    We inject some garbage into the yaml file to make sure it can
    still load the bans.
    """
    app = web.Application()
    app[KEY_HASS] = hass
    setup_bans(hass, app, 5)
    set_real_ip = mock_real_ip(app)

    data = {banned_ip: {"banned_at": "2016-11-16T19:20:03"} for banned_ip in BANNED_IPS}
    data["5.3.3.3"] = {"banned_at": "garbage"}

    with patch(
        "homeassistant.components.http.ban.load_yaml_config_file",
        return_value=data,
    ):
        client = await aiohttp_client(app)

    for remote_addr in BANNED_IPS:
        set_real_ip(remote_addr)
        resp = await client.get("/")
        expect(resp.status).to_equal(HTTPStatus.FORBIDDEN)

    set_real_ip("5.3.3.3")
    resp = await client.get("/")
    expect(resp.status).to_equal(HTTPStatus.NOT_FOUND)

    expect("Failed to load IP ban" in caplog.text).to_be(True)


@test
async def access_from_banned_ip_with_invalid_ip_entry(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that invalid IP addresses in ban file are skipped gracefully.

    An invalid IP entry (e.g., with typo like "Eo128.199.160.243") should
    be logged as an error and skipped, allowing valid bans to still load.
    The test ensures that valid IPs after invalid ones are still processed.
    """
    app = web.Application()
    app[KEY_HASS] = hass
    setup_bans(hass, app, 5)
    set_real_ip = mock_real_ip(app)

    data = {
        "Eo128.199.160.243": {"banned_at": "2024-07-06T14:07:46"},
        BANNED_IPS[0]: {"banned_at": "2016-11-16T19:20:03"},
        "invalidip": {"banned_at": "2024-07-06T14:07:46"},
        BANNED_IPS[1]: {"banned_at": "2016-11-16T19:20:03"},
    }

    with patch(
        "homeassistant.components.http.ban.load_yaml_config_file",
        return_value=data,
    ):
        client = await aiohttp_client(app)

    manager = app[KEY_BAN_MANAGER]
    expect(len(manager.ip_bans_lookup)).to_equal(len(BANNED_IPS))

    for remote_addr in BANNED_IPS:
        set_real_ip(remote_addr)
        resp = await client.get("/")
        expect(resp.status).to_equal(HTTPStatus.FORBIDDEN)

    set_real_ip("192.168.1.1")
    resp = await client.get("/")
    expect(resp.status).to_equal(HTTPStatus.NOT_FOUND)

    record_tuples = [
        (record.name, record.levelno, record.getMessage())
        for record in caplog.records
    ]
    for ip in ("Eo128.199.160.243", "invalidip"):
        expect(
            (
                "homeassistant.components.http.ban",
                logging.ERROR,
                f"Failed to load IP ban: invalid IP address {ip}",
            )
            in record_tuples
        ).to_be(True)


@test
async def no_ip_bans_file(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fixture),
) -> None:
    """Test no ip bans file."""
    app = web.Application()
    app[KEY_HASS] = hass
    setup_bans(hass, app, 5)
    set_real_ip = mock_real_ip(app)

    with patch(
        "homeassistant.components.http.ban.load_yaml_config_file",
        side_effect=FileNotFoundError,
    ):
        client = await aiohttp_client(app)

    set_real_ip("4.3.2.1")
    resp = await client.get("/")
    expect(resp.status).to_equal(HTTPStatus.NOT_FOUND)


@test
async def failure_loading_ip_bans_file(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fixture),
) -> None:
    """Test failure loading ip bans file."""
    app = web.Application()
    app[KEY_HASS] = hass
    setup_bans(hass, app, 5)
    set_real_ip = mock_real_ip(app)

    with patch(
        "homeassistant.components.http.ban.load_yaml_config_file",
        side_effect=HomeAssistantError,
    ):
        client = await aiohttp_client(app)

    set_real_ip("4.3.2.1")
    resp = await client.get("/")
    expect(resp.status).to_equal(HTTPStatus.NOT_FOUND)


@test
async def ip_ban_manager_never_started(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test we handle the ip ban manager not being started."""
    app = web.Application()
    app[KEY_HASS] = hass
    setup_bans(hass, app, 5)
    set_real_ip = mock_real_ip(app)

    with patch(
        "homeassistant.components.http.ban.load_yaml_config_file",
        side_effect=FileNotFoundError,
    ):
        client = await aiohttp_client(app)

    del app[KEY_BAN_MANAGER]

    set_real_ip("4.3.2.1")
    resp = await client.get("/")
    expect(resp.status).to_equal(HTTPStatus.NOT_FOUND)
    expect(
        "IP Ban middleware loaded but banned IPs not loaded" in caplog.text
    ).to_be(True)


@test.cases(
    test.case(
        "supervisor_ip_first_banned",
        remote_addr=BANNED_IPS_WITH_SUPERVISOR[0],
        bans=1,
        status=HTTPStatus.FORBIDDEN,
    ),
    test.case(
        "supervisor_ip_second_banned",
        remote_addr=BANNED_IPS_WITH_SUPERVISOR[1],
        bans=1,
        status=HTTPStatus.FORBIDDEN,
    ),
    test.case(
        "supervisor_ip_not_banned",
        remote_addr=BANNED_IPS_WITH_SUPERVISOR[2],
        bans=0,
        status=HTTPStatus.UNAUTHORIZED,
    ),
)
async def access_from_supervisor_ip(
    remote_addr: str,
    bans: int,
    status: HTTPStatus,
    _t: None = Depends(_trigger_executor),
    _hassio: None = Depends(hassio_bundle),
    hass: HomeAssistant = Depends(hass_fixture),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fixture),
) -> None:
    """Test accessing to server from supervisor IP."""
    app = web.Application()
    app[KEY_HASS] = hass

    async def unauth_handler(request):
        """Return a mock web response."""
        raise HTTPUnauthorized

    app.router.add_get("/", unauth_handler)
    setup_bans(hass, app, 1)
    mock_real_ip(app)(remote_addr)

    with patch(
        "homeassistant.components.http.ban.load_yaml_config_file",
        return_value={},
    ):
        client = await aiohttp_client(app)

    manager = app[KEY_BAN_MANAGER]

    expect(await async_setup_component(hass, "hassio", {"hassio": {}})).to_be_truthy()

    m_open = mock_open()

    with (
        patch.dict(os.environ, {"SUPERVISOR": SUPERVISOR_IP}),
        patch("homeassistant.components.http.ban.open", m_open, create=True),
    ):
        resp = await client.get("/")
        expect(resp.status).to_equal(HTTPStatus.UNAUTHORIZED)
        expect(len(manager.ip_bans_lookup)).to_equal(bans)
        expect(m_open.call_count).to_equal(bans)

        resp = await client.get("/")
        expect(resp.status).to_equal(status)
        expect(len(manager.ip_bans_lookup)).to_equal(bans)


@test
async def ban_middleware_not_loaded_by_config(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test accessing to server from banned IP when feature is off."""
    with patch("homeassistant.components.http.setup_bans") as mock_setup:
        await async_setup_component(
            hass, "http", {"http": {http.CONF_IP_BAN_ENABLED: False}}
        )

    expect(len(mock_setup.mock_calls)).to_equal(0)


@test
async def ban_middleware_loaded_by_default(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test accessing to server from banned IP when feature is off."""
    with patch("homeassistant.components.http.setup_bans") as mock_setup:
        await async_setup_component(hass, "http", {"http": {}})

    expect(len(mock_setup.mock_calls)).to_equal(1)


@test
async def ip_bans_file_creation(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Testing if banned IP file created."""
    app = web.Application()
    app[KEY_HASS] = hass

    async def unauth_handler(request):
        """Return a mock web response."""
        raise HTTPUnauthorized

    app.router.add_get("/example", unauth_handler)
    setup_bans(hass, app, 2)
    mock_real_ip(app)("200.201.202.204")

    with patch(
        "homeassistant.components.http.ban.load_yaml_config_file",
        return_value={
            banned_ip: {"banned_at": "2016-11-16T19:20:03"} for banned_ip in BANNED_IPS
        },
    ):
        client = await aiohttp_client(app)

    manager = app[KEY_BAN_MANAGER]
    m_open = mock_open()

    with patch("homeassistant.components.http.ban.open", m_open, create=True):
        resp = await client.get("/example")
        expect(resp.status).to_equal(HTTPStatus.UNAUTHORIZED)
        expect(len(manager.ip_bans_lookup)).to_equal(len(BANNED_IPS))
        expect(m_open.call_count).to_equal(0)

        resp = await client.get("/example")
        expect(resp.status).to_equal(HTTPStatus.UNAUTHORIZED)
        expect(len(manager.ip_bans_lookup)).to_equal(len(BANNED_IPS) + 1)
        m_open.assert_called_once_with(
            hass.config.path(IP_BANS_FILE), "a", encoding="utf8"
        )

        resp = await client.get("/example")
        expect(resp.status).to_equal(HTTPStatus.FORBIDDEN)
        expect(m_open.call_count).to_equal(1)

        notifications = async_get_persistent_notifications(hass)
        expect(len(notifications)).to_equal(2)
        expect(notifications["http-login"]["message"]).to_equal(
            "Login attempt or request with invalid authentication from example.com (200.201.202.204). See the log for details."
        )

        expect(
            "Login attempt or request with invalid authentication from example.com (200.201.202.204). Requested URL: '/example'."
            in caplog.text
        ).to_be(True)


@test
async def failed_login_attempts_counter(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fixture),
) -> None:
    """Testing if failed login attempts counter increased."""
    app = web.Application()
    app[KEY_HASS] = hass

    async def auth_handler(request):
        """Return 200 status code."""
        return None, 200

    async def auth_true_handler(request):
        """Return 200 status code."""
        process_success_login(request)
        return None, 200

    app.router.add_get(
        "/auth_true",
        request_handler_factory(hass, Mock(requires_auth=True), auth_true_handler),
    )
    app.router.add_get(
        "/auth_false",
        request_handler_factory(hass, Mock(requires_auth=True), auth_handler),
    )
    app.router.add_get(
        "/", request_handler_factory(hass, Mock(requires_auth=False), auth_handler)
    )

    setup_bans(hass, app, 5)
    remote_ip = ip_address("200.201.202.204")
    mock_real_ip(app)("200.201.202.204")

    @middleware
    async def mock_auth(request, handler):
        """Mock auth middleware."""
        if "auth_true" in request.path:
            request[KEY_AUTHENTICATED] = True
        else:
            request[KEY_AUTHENTICATED] = False
        return await handler(request)

    app.middlewares.append(mock_auth)

    client = await aiohttp_client(app)

    resp = await client.get("/auth_false")
    expect(resp.status).to_equal(HTTPStatus.UNAUTHORIZED)
    expect(app[KEY_FAILED_LOGIN_ATTEMPTS][remote_ip]).to_equal(1)

    resp = await client.get("/auth_false")
    expect(resp.status).to_equal(HTTPStatus.UNAUTHORIZED)
    expect(app[KEY_FAILED_LOGIN_ATTEMPTS][remote_ip]).to_equal(2)

    resp = await client.get("/")
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(app[KEY_FAILED_LOGIN_ATTEMPTS][remote_ip]).to_equal(2)

    resp = await client.get("/auth_true")
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(app[KEY_FAILED_LOGIN_ATTEMPTS][remote_ip]).to_equal(0)

    resp = await client.get("/auth_false")
    expect(resp.status).to_equal(HTTPStatus.UNAUTHORIZED)
    expect(app[KEY_FAILED_LOGIN_ATTEMPTS][remote_ip]).to_equal(1)

    resp = await client.get("/auth_false")
    expect(resp.status).to_equal(HTTPStatus.UNAUTHORIZED)
    expect(app[KEY_FAILED_LOGIN_ATTEMPTS][remote_ip]).to_equal(2)


@test
async def single_ban_file_entry(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that only one item is added to ban file."""
    app = web.Application()
    app[KEY_HASS] = hass

    async def unauth_handler(request):
        """Return a mock web response."""
        raise HTTPUnauthorized

    app.router.add_get("/example", unauth_handler)
    setup_bans(hass, app, 2)
    mock_real_ip(app)("200.201.202.204")

    manager = app[KEY_BAN_MANAGER]
    m_open = mock_open()

    with patch("homeassistant.components.http.ban.open", m_open, create=True):
        remote_ip = ip_address("200.201.202.204")
        await manager.async_add_ban(remote_ip)
        await manager.async_add_ban(remote_ip)

    expect(m_open.call_count).to_equal(1)


@test
async def unix_socket_skips_ban_check(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fixture),
) -> None:
    """Test that Unix socket requests bypass ban middleware."""
    app = web.Application()
    app[KEY_HASS] = hass
    setup_bans(hass, app, 5)
    set_real_ip = mock_real_ip(app)

    with patch(
        "homeassistant.components.http.ban.load_yaml_config_file",
        return_value={
            banned_ip: {"banned_at": "2016-11-16T19:20:03"} for banned_ip in BANNED_IPS
        },
    ):
        client = await aiohttp_client(app)

    set_real_ip(BANNED_IPS[0])
    resp = await client.get("/")
    expect(resp.status).to_equal(HTTPStatus.FORBIDDEN)

    with patch(
        "homeassistant.components.http.ban.is_supervisor_unix_socket_request",
        return_value=True,
    ):
        resp = await client.get("/")
    expect(resp.status).to_equal(HTTPStatus.NOT_FOUND)
