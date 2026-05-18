"""The tests for the Home Assistant HTTP component."""

import asyncio
from collections.abc import Callable
from datetime import timedelta
from http import HTTPStatus
from ipaddress import ip_network
import logging
import os
from pathlib import Path
import socket
from unittest.mock import ANY, Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.auth.providers.homeassistant import HassAuthProvider
from homeassistant.components import cloud, http
from homeassistant.components.cloud import CloudNotAvailable
from homeassistant.const import HASSIO_USER_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.http import KEY_HASS
from homeassistant.helpers.network import NoURLAvailableError
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from homeassistant.util.ssl import server_context_intermediate, server_context_modern

from tests.common import async_call_logger_set_level, async_fire_time_changed
from tests.hass_fixtures import (
    ClientSessionGenerator,
    LogCapture,
    aiohttp_client as aiohttp_client_fixture,
    caplog as caplog_fixture,
    hass as hass_fixture,
    hass_client as hass_client_fixture,
    hass_client_no_auth as hass_client_no_auth_fixture,
    issue_registry as issue_registry_fixture,
    local_auth as local_auth_fixture,
    mock_network,
    tmp_path as tmp_path_fixture,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Anchor for tryke fixture resolution."""
    return 0


def _unused_tcp_port() -> int:
    """Return a free TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _setup_broken_ssl_pem_files(tmp_path: Path) -> tuple[Path, Path]:
    test_dir = tmp_path / "test_broken_ssl"
    test_dir.mkdir()
    cert_path = test_dir / "cert.pem"
    cert_path.write_text("garbage")
    key_path = test_dir / "key.pem"
    key_path.write_text("garbage")
    return cert_path, key_path


def _setup_empty_ssl_pem_files(tmp_path: Path) -> tuple[Path, Path, Path]:
    test_dir = tmp_path / "test_empty_ssl"
    test_dir.mkdir()
    cert_path = test_dir / "cert.pem"
    cert_path.write_text("-")
    peer_cert_path = test_dir / "peer_cert.pem"
    peer_cert_path.write_text("-")
    key_path = test_dir / "key.pem"
    key_path.write_text("-")
    return cert_path, key_path, peer_cert_path


class TestView(http.HomeAssistantView):
    """Test the HTTP views."""

    name = "test"
    url = "/hello"

    async def get(self, request):
        """Return a get request."""
        return "hello"


@test
async def registering_view_while_running(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fixture),
) -> None:
    """Test that we can register a view while the server is running."""
    await async_setup_component(
        hass,
        http.DOMAIN,
        {http.DOMAIN: {http.CONF_SERVER_PORT: _unused_tcp_port()}},
    )

    await hass.async_start()
    # This raises a RuntimeError if app is frozen
    hass.http.register_view(TestView)


@test
async def homeassistant_assigned_to_app(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test HomeAssistant instance is assigned to HomeAssistantApp."""
    expect(await async_setup_component(hass, "api", {"http": {}})).to_be_truthy()
    await hass.async_start()
    expect(hass.http.app[KEY_HASS]).to_equal(hass)
    expect(hass.http.app["hass"]).to_equal(hass)  # For backwards compatibility
    await hass.async_stop()


@test
async def not_log_password(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
    local_auth: HassAuthProvider = Depends(local_auth_fixture),
) -> None:
    """Test access with password doesn't get logged."""
    expect(await async_setup_component(hass, "api", {"http": {}})).to_be_truthy()
    client = await hass_client_no_auth()
    logging.getLogger("aiohttp.access").setLevel(logging.INFO)

    resp = await client.get("/api/", params={"api_password": "test-password"})

    expect(resp.status).to_equal(HTTPStatus.UNAUTHORIZED)
    logs = caplog.text

    # Ensure we don't log API passwords
    expect("/api/" in logs).to_be(True)
    expect("some-pass" not in logs).to_be(True)


@test
async def proxy_config(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test use_x_forwarded_for must config together with trusted_proxies."""
    expect(
        await async_setup_component(
            hass,
            "http",
            {
                "http": {
                    http.CONF_USE_X_FORWARDED_FOR: True,
                    http.CONF_TRUSTED_PROXIES: ["127.0.0.1"],
                }
            },
        )
    ).to_be(True)


@test
async def proxy_config_only_use_xff(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test use_x_forwarded_for must config together with trusted_proxies."""
    result = await async_setup_component(
        hass, "http", {"http": {http.CONF_USE_X_FORWARDED_FOR: True}}
    )
    expect(result is not True).to_be(True)


@test
async def proxy_config_only_trust_proxies(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test use_x_forwarded_for must config together with trusted_proxies."""
    result = await async_setup_component(
        hass, "http", {"http": {http.CONF_TRUSTED_PROXIES: ["127.0.0.1"]}}
    )
    expect(result is not True).to_be(True)


@test
async def ssl_profile_defaults_modern(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test default ssl profile."""
    cert_path, key_path, _ = await hass.async_add_executor_job(
        _setup_empty_ssl_pem_files, tmp_path
    )

    with (
        patch("ssl.SSLContext.load_cert_chain"),
        patch(
            "homeassistant.util.ssl.server_context_modern",
            side_effect=server_context_modern,
        ) as mock_context,
    ):
        expect(
            await async_setup_component(
                hass,
                "http",
                {"http": {"ssl_certificate": cert_path, "ssl_key": key_path}},
            )
        ).to_be(True)
        await hass.async_start()
        await hass.async_block_till_done()

    expect(len(mock_context.mock_calls)).to_equal(1)


@test
async def ssl_profile_change_intermediate(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test setting ssl profile to intermediate."""
    cert_path, key_path, _ = await hass.async_add_executor_job(
        _setup_empty_ssl_pem_files, tmp_path
    )

    with (
        patch("ssl.SSLContext.load_cert_chain"),
        patch(
            "homeassistant.util.ssl.server_context_intermediate",
            side_effect=server_context_intermediate,
        ) as mock_context,
    ):
        expect(
            await async_setup_component(
                hass,
                "http",
                {
                    "http": {
                        "ssl_profile": "intermediate",
                        "ssl_certificate": cert_path,
                        "ssl_key": key_path,
                    }
                },
            )
        ).to_be(True)
        await hass.async_start()
        await hass.async_block_till_done()

    expect(len(mock_context.mock_calls)).to_equal(1)


@test
async def ssl_profile_change_modern(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test setting ssl profile to modern."""
    cert_path, key_path, _ = await hass.async_add_executor_job(
        _setup_empty_ssl_pem_files, tmp_path
    )

    with (
        patch("ssl.SSLContext.load_cert_chain"),
        patch(
            "homeassistant.util.ssl.server_context_modern",
            side_effect=server_context_modern,
        ) as mock_context,
    ):
        expect(
            await async_setup_component(
                hass,
                "http",
                {
                    "http": {
                        "ssl_profile": "modern",
                        "ssl_certificate": cert_path,
                        "ssl_key": key_path,
                    }
                },
            )
        ).to_be(True)
        await hass.async_start()
        await hass.async_block_till_done()

    expect(len(mock_context.mock_calls)).to_equal(1)


@test
async def peer_cert(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test required peer cert."""
    cert_path, key_path, peer_cert_path = await hass.async_add_executor_job(
        _setup_empty_ssl_pem_files, tmp_path
    )

    with (
        patch("ssl.SSLContext.load_cert_chain"),
        patch("ssl.SSLContext.load_verify_locations") as mock_load_verify_locations,
        patch(
            "homeassistant.util.ssl.server_context_modern",
            side_effect=server_context_modern,
        ) as mock_context,
    ):
        expect(
            await async_setup_component(
                hass,
                "http",
                {
                    "http": {
                        "ssl_peer_certificate": peer_cert_path,
                        "ssl_profile": "modern",
                        "ssl_certificate": cert_path,
                        "ssl_key": key_path,
                    }
                },
            )
        ).to_be(True)
        await hass.async_start()
        await hass.async_block_till_done()

    expect(len(mock_context.mock_calls)).to_equal(1)
    expect(len(mock_load_verify_locations.mock_calls)).to_equal(1)


@test
async def emergency_ssl_certificate_when_invalid(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test http can startup with an emergency self signed cert when the current one is broken."""
    cert_path, key_path = await hass.async_add_executor_job(
        _setup_broken_ssl_pem_files, tmp_path
    )

    hass.config.recovery_mode = True
    expect(
        await async_setup_component(
            hass,
            "http",
            {"http": {"ssl_certificate": cert_path, "ssl_key": key_path}},
        )
    ).to_be(True)

    await hass.async_start()
    await hass.async_block_till_done()
    expect(
        "Home Assistant is running in recovery mode with an emergency self signed ssl certificate because the configured SSL certificate was not usable"
        in caplog.text
    ).to_be(True)

    expect(hass.http.site is not None).to_be(True)


@test
async def emergency_ssl_certificate_not_used_when_not_recovery_mode(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test an emergency cert is only used in recovery mode."""
    cert_path, key_path = await hass.async_add_executor_job(
        _setup_broken_ssl_pem_files, tmp_path
    )

    expect(
        await async_setup_component(
            hass, "http", {"http": {"ssl_certificate": cert_path, "ssl_key": key_path}}
        )
    ).to_be(False)


@test
async def emergency_ssl_certificate_when_invalid_get_url_fails(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test http falls back to no ssl when an emergency cert cannot be created when the configured one is broken."""
    cert_path, key_path = await hass.async_add_executor_job(
        _setup_broken_ssl_pem_files, tmp_path
    )
    hass.config.recovery_mode = True

    with patch(
        "homeassistant.components.http.get_url", side_effect=NoURLAvailableError
    ) as mock_get_url:
        expect(
            await async_setup_component(
                hass,
                "http",
                {"http": {"ssl_certificate": cert_path, "ssl_key": key_path}},
            )
        ).to_be(True)
        await hass.async_start()
        await hass.async_block_till_done()

    expect(len(mock_get_url.mock_calls)).to_equal(1)
    expect(
        "Home Assistant is running in recovery mode with an emergency self signed ssl certificate because the configured SSL certificate was not usable"
        in caplog.text
    ).to_be(True)

    expect(hass.http.site is not None).to_be(True)


@test
async def invalid_ssl_and_cannot_create_emergency_cert(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test http falls back to no ssl when an emergency cert cannot be created when the configured one is broken."""
    cert_path, key_path = await hass.async_add_executor_job(
        _setup_broken_ssl_pem_files, tmp_path
    )
    hass.config.recovery_mode = True

    with patch(
        "homeassistant.components.http.x509.CertificateBuilder", side_effect=OSError
    ) as mock_builder:
        expect(
            await async_setup_component(
                hass,
                "http",
                {"http": {"ssl_certificate": cert_path, "ssl_key": key_path}},
            )
        ).to_be(True)
        await hass.async_start()
        await hass.async_block_till_done()
    expect(
        "Could not create an emergency self signed ssl certificate" in caplog.text
    ).to_be(True)
    expect(len(mock_builder.mock_calls)).to_equal(1)

    expect(hass.http.site is not None).to_be(True)


@test
async def invalid_ssl_and_cannot_create_emergency_cert_with_ssl_peer_cert(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test http falls back to no ssl when an emergency cert cannot be created when the configured one is broken."""
    cert_path, key_path = await hass.async_add_executor_job(
        _setup_broken_ssl_pem_files, tmp_path
    )
    hass.config.recovery_mode = True

    with patch(
        "homeassistant.components.http.x509.CertificateBuilder", side_effect=OSError
    ) as mock_builder:
        expect(
            await async_setup_component(
                hass,
                "http",
                {
                    "http": {
                        "ssl_certificate": cert_path,
                        "ssl_key": key_path,
                        "ssl_peer_certificate": cert_path,
                    }
                },
            )
        ).to_be(False)
        await hass.async_start()
        await hass.async_block_till_done()
    expect(
        "Could not create an emergency self signed ssl certificate" in caplog.text
    ).to_be(True)
    expect(len(mock_builder.mock_calls)).to_equal(1)


@test
async def cors_defaults(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the CORS default settings."""
    with patch("homeassistant.components.http.setup_cors") as mock_setup:
        expect(await async_setup_component(hass, "http", {})).to_be_truthy()

    expect(len(mock_setup.mock_calls)).to_equal(1)
    expect(mock_setup.mock_calls[0][1][1]).to_equal(["https://cast.home-assistant.io"])


@test
async def storing_config(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fixture),
) -> None:
    """Test that we store last working config."""
    config = {
        http.CONF_SERVER_PORT: _unused_tcp_port(),
        "use_x_forwarded_for": True,
        "trusted_proxies": ["192.168.1.100"],
    }

    expect(
        await async_setup_component(hass, http.DOMAIN, {http.DOMAIN: config})
    ).to_be_truthy()

    await hass.async_start()

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=200))
    await hass.async_block_till_done()

    restored = await http.async_get_last_config(hass)
    restored["trusted_proxies"][0] = ip_network(restored["trusted_proxies"][0])

    expect(restored).to_equal(http.HTTP_SCHEMA(config))


@test
async def logging_test(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Testing the access log works."""
    await asyncio.gather(
        *(
            async_setup_component(hass, component, {})
            for component in ("http", "logger", "api")
        )
    )
    hass.states.async_set("logging.entity", "hello")
    async with async_call_logger_set_level(
        "aiohttp.access", "INFO", hass=hass, caplog=caplog
    ):
        client = await hass_client()
        response = await client.get("/api/states/logging.entity")
        expect(response.status).to_equal(HTTPStatus.OK)

        expect("GET /api/states/logging.entity" in caplog.text).to_be(True)
        caplog.clear()
    async with async_call_logger_set_level(
        "aiohttp.access", "WARNING", hass=hass, caplog=caplog
    ):
        response = await client.get("/api/states/logging.entity")
        expect(response.status).to_equal(HTTPStatus.OK)
        expect("GET /api/states/logging.entity" in caplog.text).to_be(False)


@test
async def ssl_issue_if_no_urls_configured(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test raising SSL issue if no external or internal URL is configured."""
    expect(hass.config.external_url is None).to_be(True)
    expect(hass.config.internal_url is None).to_be(True)

    cert_path, key_path, _ = await hass.async_add_executor_job(
        _setup_empty_ssl_pem_files, tmp_path
    )

    with (
        patch("ssl.SSLContext.load_cert_chain"),
        patch(
            "homeassistant.util.ssl.server_context_modern",
            side_effect=server_context_modern,
        ),
    ):
        expect(
            await async_setup_component(
                hass,
                "http",
                {"http": {"ssl_certificate": cert_path, "ssl_key": key_path}},
            )
        ).to_be_truthy()
        await hass.async_start()
        await hass.async_block_till_done()

    expect(
        ("http", "ssl_configured_without_configured_urls") in issue_registry.issues
    ).to_be(True)


@test
async def ssl_issue_if_using_cloud(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test raising no SSL issue if not right configured but using cloud."""
    expect(hass.config.external_url is None).to_be(True)
    expect(hass.config.internal_url is None).to_be(True)

    cert_path, key_path, _ = await hass.async_add_executor_job(
        _setup_empty_ssl_pem_files, tmp_path
    )

    with (
        patch("ssl.SSLContext.load_cert_chain"),
        patch.object(cloud, "async_remote_ui_url", return_value="https://example.com"),
        patch(
            "homeassistant.util.ssl.server_context_modern",
            side_effect=server_context_modern,
        ),
    ):
        expect(
            await async_setup_component(
                hass,
                "http",
                {"http": {"ssl_certificate": cert_path, "ssl_key": key_path}},
            )
        ).to_be_truthy()
        await hass.async_start()
        await hass.async_block_till_done()

    expect(
        ("http", "ssl_configured_without_configured_urls") in issue_registry.issues
    ).to_be(False)


@test
async def ssl_issue_if_not_connected_to_cloud(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test raising no SSL issue if not right configured and not connected to cloud."""
    expect(hass.config.external_url is None).to_be(True)
    expect(hass.config.internal_url is None).to_be(True)

    cert_path, key_path, _ = await hass.async_add_executor_job(
        _setup_empty_ssl_pem_files, tmp_path
    )

    with (
        patch("ssl.SSLContext.load_cert_chain"),
        patch(
            "homeassistant.util.ssl.server_context_modern",
            side_effect=server_context_modern,
        ),
        patch(
            "homeassistant.components.cloud.async_remote_ui_url",
            side_effect=CloudNotAvailable,
        ),
    ):
        expect(
            await async_setup_component(
                hass,
                "http",
                {"http": {"ssl_certificate": cert_path, "ssl_key": key_path}},
            )
        ).to_be_truthy()
        await hass.async_start()
        await hass.async_block_till_done()

    expect(
        ("http", "ssl_configured_without_configured_urls") in issue_registry.issues
    ).to_be(True)


@test.cases(
    test.case(
        "both_urls",
        external_url="https://example.com",
        internal_url="https://example.local",
    ),
    test.case("internal_only", external_url=None, internal_url="http://example.local"),
    test.case("external_only", external_url="https://example.com", internal_url=None),
)
async def ssl_issue_urls_configured(
    external_url: str | None,
    internal_url: str | None,
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test raising SSL issue if no external or internal URL is configured."""
    cert_path, key_path, _ = await hass.async_add_executor_job(
        _setup_empty_ssl_pem_files, tmp_path
    )

    hass.config.external_url = external_url
    hass.config.internal_url = internal_url

    with (
        patch("ssl.SSLContext.load_cert_chain"),
        patch(
            "homeassistant.util.ssl.server_context_modern",
            side_effect=server_context_modern,
        ),
    ):
        expect(
            await async_setup_component(
                hass,
                "http",
                {"http": {"ssl_certificate": cert_path, "ssl_key": key_path}},
            )
        ).to_be_truthy()
        await hass.async_start()
        await hass.async_block_till_done()

    expect(
        ("http", "ssl_configured_without_configured_urls") in issue_registry.issues
    ).to_be(False)


@test.cases(
    test.case(
        "no_hassio_no_host",
        hassio=False,
        http_config={},
        expected_serverhost=["0.0.0.0", "::"],
        expected_issues=set(),
    ),
    test.case(
        "no_hassio_with_host",
        hassio=False,
        http_config={"server_host": "0.0.0.0"},
        expected_serverhost=["0.0.0.0"],
        expected_issues=set(),
    ),
    test.case(
        "hassio_no_host",
        hassio=True,
        http_config={},
        expected_serverhost=["0.0.0.0", "::"],
        expected_issues=set(),
    ),
    test.case(
        "hassio_with_host",
        hassio=True,
        http_config={"server_host": "0.0.0.0"},
        expected_serverhost=["0.0.0.0"],
        expected_issues={("http", "server_host_deprecated_hassio")},
    ),
)
async def server_host(
    hassio: bool,
    http_config: dict,
    expected_serverhost: list,
    expected_issues: set[tuple[str, str]],
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test server_host behavior."""
    mock_server = Mock()
    with (
        patch("homeassistant.components.http.is_hassio", return_value=hassio),
        patch(
            "asyncio.BaseEventLoop.create_server", return_value=mock_server
        ) as mock_create_server,
    ):
        expect(
            await async_setup_component(hass, "http", {"http": http_config})
        ).to_be_truthy()
        await hass.async_start()
        await hass.async_block_till_done()

    mock_create_server.assert_called_once_with(
        ANY,
        expected_serverhost,
        8123,
        ssl=None,
        backlog=128,
        reuse_address=None,
        reuse_port=None,
    )

    expect(set(issue_registry.issues)).to_equal(expected_issues)


@test.skip("Race between start_server and start_supervisor_unix_socket under tryke")
async def unix_socket_started_with_supervisor(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test unix socket is started when running under Supervisor."""
    await hass.auth.async_create_system_user(
        HASSIO_USER_NAME, group_ids=["system-admin"]
    )
    socket_path = tmp_path / "core.sock"
    loop = asyncio.get_running_loop()
    mock_sock = Mock()
    with (
        patch.dict(
            os.environ, {"SUPERVISOR_CORE_API_SOCKET": str(socket_path)}, clear=False
        ),
        patch("asyncio.BaseEventLoop.create_server", return_value=Mock()),
        patch(
            "homeassistant.components.http.web_runner.HomeAssistantUnixSite"
            "._create_unix_socket",
            return_value=mock_sock,
        ) as mock_create_sock,
        patch.object(
            loop, "create_unix_server", return_value=Mock()
        ) as mock_create_unix,
    ):
        expect(
            await async_setup_component(hass, "http", {"http": {}})
        ).to_be_truthy()
        await hass.async_start()
        await hass.async_block_till_done()

    mock_create_sock.assert_called_once()
    mock_create_unix.assert_called_once_with(ANY, sock=mock_sock, backlog=128)
    expect(hass.http.supervisor_site is not None).to_be(True)


@test
async def unix_socket_not_started_without_supervisor(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test unix socket is not started when not running under Supervisor."""
    with (
        patch.dict(os.environ, {}, clear=False),
        patch("asyncio.BaseEventLoop.create_server", return_value=Mock()),
    ):
        os.environ.pop("SUPERVISOR_CORE_API_SOCKET", None)
        expect(
            await async_setup_component(hass, "http", {"http": {}})
        ).to_be_truthy()
        await hass.async_start()
        await hass.async_block_till_done()

    expect(hass.http.supervisor_site is None).to_be(True)


@test
async def unix_socket_rejected_relative_path(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test unix socket is rejected when path is relative."""
    with (
        patch.dict(
            os.environ,
            {"SUPERVISOR_CORE_API_SOCKET": "relative/path.sock"},
            clear=False,
        ),
        patch("asyncio.BaseEventLoop.create_server", return_value=Mock()),
    ):
        expect(
            await async_setup_component(hass, "http", {"http": {}})
        ).to_be_truthy()
        await hass.async_start()
        await hass.async_block_till_done()

    expect(hass.http.supervisor_site is None).to_be(True)
    expect("path must be absolute" in caplog.text).to_be(True)
