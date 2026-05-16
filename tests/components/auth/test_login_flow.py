"""Tests for the login flow."""

from http import HTTPStatus
from typing import Any
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.core_config import async_process_ha_core_config

from ._fixtures import aiohttp_client as aiohttp_client_fx, current_request_with_host

from . import BASE_CONFIG, async_setup_auth

from tests.common import CLIENT_ID, CLIENT_REDIRECT_URI
from tests.hass_fixtures import hass as hass_fixture
from tests.typing import ClientSessionGenerator


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0

_TRUSTED_NETWORKS_CONFIG = {
    "type": "trusted_networks",
    "trusted_networks": ["192.168.0.1"],
    "trusted_users": {
        "192.168.0.1": [
            "a1ab982744b64757bf80515589258924",
            {"group": "system-group"},
        ]
    },
}


_HA_PROVIDER_EXPECTED = [
    {
        "name": "Home Assistant Local",
        "type": "homeassistant",
        "id": None,
    }
]
_EXAMPLE_PROVIDER_EXPECTED = [
    {"name": "Example", "type": "insecure_example", "id": None}
]


@test.cases(
    test.case(
        "base-192.168.1.10",
        provider_configs=BASE_CONFIG,
        expected=_EXAMPLE_PROVIDER_EXPECTED,
        ip="192.168.1.10",
        preselect_remember_me=True,
    ),
    test.case(
        "base-ipv6-mapped-ipv4",
        provider_configs=BASE_CONFIG,
        expected=_EXAMPLE_PROVIDER_EXPECTED,
        ip="::ffff:192.168.0.10",
        preselect_remember_me=True,
    ),
    test.case(
        "base-public-ipv4",
        provider_configs=BASE_CONFIG,
        expected=_EXAMPLE_PROVIDER_EXPECTED,
        ip="1.2.3.4",
        preselect_remember_me=False,
    ),
    test.case(
        "base-public-ipv6",
        provider_configs=BASE_CONFIG,
        expected=_EXAMPLE_PROVIDER_EXPECTED,
        ip="2001:db8::1",
        preselect_remember_me=False,
    ),
    test.case(
        "ha-192.168.1.10",
        provider_configs=[{"type": "homeassistant"}],
        expected=_HA_PROVIDER_EXPECTED,
        ip="192.168.1.10",
        preselect_remember_me=True,
    ),
    test.case(
        "ha-ipv6-mapped-ipv4",
        provider_configs=[{"type": "homeassistant"}],
        expected=_HA_PROVIDER_EXPECTED,
        ip="::ffff:192.168.0.10",
        preselect_remember_me=True,
    ),
    test.case(
        "ha-public-ipv4",
        provider_configs=[{"type": "homeassistant"}],
        expected=_HA_PROVIDER_EXPECTED,
        ip="1.2.3.4",
        preselect_remember_me=False,
    ),
    test.case(
        "ha-public-ipv6",
        provider_configs=[{"type": "homeassistant"}],
        expected=_HA_PROVIDER_EXPECTED,
        ip="2001:db8::1",
        preselect_remember_me=False,
    ),
)
async def fetch_auth_providers(
    provider_configs: list[dict[str, Any]],
    expected: list[dict[str, Any]],
    ip: str,
    preselect_remember_me: bool,
    hass: HomeAssistant = Depends(hass_fixture),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fx),
) -> None:
    """Test fetching auth providers."""
    client = await async_setup_auth(
        hass, aiohttp_client, provider_configs, custom_ip=ip
    )
    resp = await client.get("/auth/providers")
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(await resp.json()).to_equal(
        {
            "providers": expected,
            "preselect_remember_me": preselect_remember_me,
        }
    )


@test.cases(
    test.case(
        "trusted",
        ip="192.168.0.1",
        expected=[
            {"name": "Trusted Networks", "type": "trusted_networks", "id": None}
        ],
    ),
    test.case("ipv6-mapped", ip="::ffff:192.168.0.10", expected=[]),
    test.case("public-ipv4", ip="1.2.3.4", expected=[]),
    test.case("public-ipv6", ip="2001:db8::1", expected=[]),
)
async def fetch_auth_providers_trusted_network(
    ip: str,
    expected: list[dict[str, Any]],
    hass: HomeAssistant = Depends(hass_fixture),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fx),
) -> None:
    """Test fetching auth providers."""
    client = await async_setup_auth(
        hass, aiohttp_client, [_TRUSTED_NETWORKS_CONFIG], custom_ip=ip
    )
    resp = await client.get("/auth/providers")
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect((await resp.json())["providers"]).to_equal(expected)


@test
async def fetch_auth_providers_onboarding(
    hass: HomeAssistant = Depends(hass_fixture),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fx),
) -> None:
    """Test fetching auth providers."""
    client = await async_setup_auth(hass, aiohttp_client)
    with patch(
        "homeassistant.components.onboarding.async_is_user_onboarded",
        return_value=False,
    ):
        resp = await client.get("/auth/providers")
    expect(resp.status).to_equal(HTTPStatus.BAD_REQUEST)
    expect(await resp.json()).to_equal(
        {
            "message": "Onboarding not finished",
            "code": "onboarding_required",
        }
    )


@test
async def cannot_get_flows_in_progress(
    hass: HomeAssistant = Depends(hass_fixture),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fx),
) -> None:
    """Test we cannot get flows in progress."""
    client = await async_setup_auth(hass, aiohttp_client, [])
    resp = await client.get("/auth/login_flow")
    expect(resp.status).to_equal(HTTPStatus.METHOD_NOT_ALLOWED)


@test
async def invalid_username_password(
    hass: HomeAssistant = Depends(hass_fixture),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fx),
) -> None:
    """Test we cannot get flows in progress."""
    client = await async_setup_auth(hass, aiohttp_client)
    resp = await client.post(
        "/auth/login_flow",
        json={
            "client_id": CLIENT_ID,
            "handler": ["insecure_example", None],
            "redirect_uri": CLIENT_REDIRECT_URI,
        },
    )
    expect(resp.status).to_equal(HTTPStatus.OK)
    step = await resp.json()

    # Incorrect username
    with patch(
        "homeassistant.components.auth.login_flow.process_wrong_login"
    ) as mock_process_wrong_login:
        resp = await client.post(
            f"/auth/login_flow/{step['flow_id']}",
            json={
                "client_id": CLIENT_ID,
                "username": "wrong-user",
                "password": "test-pass",
            },
        )

    expect(resp.status).to_equal(HTTPStatus.OK)
    step = await resp.json()
    expect(len(mock_process_wrong_login.mock_calls)).to_equal(1)

    expect(step["step_id"]).to_equal("init")
    expect(step["errors"]["base"]).to_equal("invalid_auth")

    # Incorrect password
    with patch(
        "homeassistant.components.auth.login_flow.process_wrong_login"
    ) as mock_process_wrong_login:
        resp = await client.post(
            f"/auth/login_flow/{step['flow_id']}",
            json={
                "client_id": CLIENT_ID,
                "username": "test-user",
                "password": "wrong-pass",
            },
        )

    expect(resp.status).to_equal(HTTPStatus.OK)
    step = await resp.json()
    expect(len(mock_process_wrong_login.mock_calls)).to_equal(1)

    expect(step["step_id"]).to_equal("init")
    expect(step["errors"]["base"]).to_equal("invalid_auth")

    # Incorrect username and invalid redirect URI fails on wrong login
    with patch(
        "homeassistant.components.auth.login_flow.process_wrong_login"
    ) as mock_process_wrong_login:
        resp = await client.post(
            f"/auth/login_flow/{step['flow_id']}",
            json={
                "client_id": CLIENT_ID,
                "username": "wrong-user",
                "password": "test-pass",
            },
        )

    expect(resp.status).to_equal(HTTPStatus.OK)
    step = await resp.json()
    expect(len(mock_process_wrong_login.mock_calls)).to_equal(1)

    expect(step["step_id"]).to_equal("init")
    expect(step["errors"]["base"]).to_equal("invalid_auth")


@test
async def invalid_redirect_uri(
    hass: HomeAssistant = Depends(hass_fixture),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fx),
) -> None:
    """Test invalid redirect URI."""
    client = await async_setup_auth(hass, aiohttp_client)
    resp = await client.post(
        "/auth/login_flow",
        json={
            "client_id": CLIENT_ID,
            "handler": ["insecure_example", None],
            "redirect_uri": "https://some-other-domain.com",
        },
    )
    expect(resp.status).to_equal(HTTPStatus.OK)
    step = await resp.json()

    with (
        patch(
            "homeassistant.components.auth.indieauth.fetch_redirect_uris",
            return_value=[],
        ),
        patch(
            "homeassistant.components.http.ban.process_wrong_login"
        ) as mock_process_wrong_login,
    ):
        resp = await client.post(
            f"/auth/login_flow/{step['flow_id']}",
            json={
                "client_id": CLIENT_ID,
                "username": "test-user",
                "password": "test-pass",
            },
        )

    expect(resp.status).to_equal(HTTPStatus.FORBIDDEN)
    data = await resp.json()
    expect(len(mock_process_wrong_login.mock_calls)).to_equal(1)

    expect(data["message"]).to_equal("Invalid redirect URI")


@test
async def login_exist_user(
    hass: HomeAssistant = Depends(hass_fixture),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fx),
) -> None:
    """Test logging in with exist user."""
    client = await async_setup_auth(hass, aiohttp_client, setup_api=True)
    cred = await hass.auth.auth_providers[0].async_get_or_create_credentials(
        {"username": "test-user"}
    )
    await hass.auth.async_get_or_create_user(cred)

    resp = await client.post(
        "/auth/login_flow",
        json={
            "client_id": CLIENT_ID,
            "handler": ["insecure_example", None],
            "redirect_uri": CLIENT_REDIRECT_URI,
        },
    )
    expect(resp.status).to_equal(HTTPStatus.OK)
    step = await resp.json()

    with patch(
        "homeassistant.components.auth.login_flow.process_success_login"
    ) as mock_process_success_login:
        resp = await client.post(
            f"/auth/login_flow/{step['flow_id']}",
            json={
                "client_id": CLIENT_ID,
                "username": "test-user",
                "password": "test-pass",
            },
        )

    expect(resp.status).to_equal(HTTPStatus.OK)
    step = await resp.json()
    expect(step["type"]).to_equal("create_entry")
    expect(len(step["result"]) > 1).to_be(True)
    expect(len(mock_process_success_login.mock_calls)).to_equal(1)


@test
async def login_local_only_user(
    hass: HomeAssistant = Depends(hass_fixture),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fx),
) -> None:
    """Test logging in with local only user."""
    client = await async_setup_auth(hass, aiohttp_client, setup_api=True)
    cred = await hass.auth.auth_providers[0].async_get_or_create_credentials(
        {"username": "test-user"}
    )
    user = await hass.auth.async_get_or_create_user(cred)
    await hass.auth.async_update_user(user, local_only=True)

    resp = await client.post(
        "/auth/login_flow",
        json={
            "client_id": CLIENT_ID,
            "handler": ["insecure_example", None],
            "redirect_uri": CLIENT_REDIRECT_URI,
        },
    )
    expect(resp.status).to_equal(HTTPStatus.OK)
    step = await resp.json()

    with patch(
        "homeassistant.components.auth.login_flow.async_user_not_allowed_do_auth",
        return_value="User is local only",
    ) as mock_not_allowed_do_auth:
        resp = await client.post(
            f"/auth/login_flow/{step['flow_id']}",
            json={
                "client_id": CLIENT_ID,
                "username": "test-user",
                "password": "test-pass",
            },
        )

    expect(resp.status).to_equal(HTTPStatus.FORBIDDEN)
    expect(len(mock_not_allowed_do_auth.mock_calls)).to_equal(1)
    expect(await resp.json()).to_equal({"message": "Login blocked: User is local only"})


@test
async def login_exist_user_ip_changes(
    hass: HomeAssistant = Depends(hass_fixture),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fx),
) -> None:
    """Test logging in and the ip address changes results in an rejection."""
    client = await async_setup_auth(hass, aiohttp_client, setup_api=True)
    cred = await hass.auth.auth_providers[0].async_get_or_create_credentials(
        {"username": "test-user"}
    )
    await hass.auth.async_get_or_create_user(cred)

    resp = await client.post(
        "/auth/login_flow",
        json={
            "client_id": CLIENT_ID,
            "handler": ["insecure_example", None],
            "redirect_uri": CLIENT_REDIRECT_URI,
        },
    )
    expect(resp.status).to_equal(200)
    step = await resp.json()

    #
    # Here we modify the ip_address in the context to make sure
    # when ip address changes in the middle of the login flow we prevent logins.
    #
    # This method was chosen because it seemed less likely to break
    # vs patching aiohttp internals to fake the ip address
    #
    for flow_id, flow in hass.auth.login_flow._progress.items():
        expect(flow_id).to_equal(step["flow_id"])
        flow.context["ip_address"] = "10.2.3.1"

    resp = await client.post(
        f"/auth/login_flow/{step['flow_id']}",
        json={
            "client_id": CLIENT_ID,
            "redirect_uri": CLIENT_REDIRECT_URI,
            "username": "test-user",
            "password": "test-pass",
        },
    )

    expect(resp.status).to_equal(400)
    response = await resp.json()
    expect(response).to_equal({"message": "IP address changed"})


@test.cases(
    test.case(
        "external_url",
        config={
            "internal_url": "http://192.168.1.100:8123",
            "external_url": "https://example.com",
        },
        expected_url_prefix="https://example.com",
        extra_response_data={"issuer": "https://example.com"},
    ),
    test.case(
        "internal_url",
        config={
            "internal_url": "https://example.com",
            "external_url": "https://other.com",
        },
        expected_url_prefix="https://example.com",
        extra_response_data={"issuer": "https://example.com"},
    ),
    test.case(
        "no_match",
        config={
            "internal_url": "https://other.com",
            "external_url": "https://again.com",
        },
        expected_url_prefix="",
        extra_response_data={},
    ),
)
async def well_known_auth_info(
    config: dict[str, str],
    expected_url_prefix: str,
    extra_response_data: dict[str, str],
    _request_with_host: None = Depends(current_request_with_host),
    hass: HomeAssistant = Depends(hass_fixture),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fx),
) -> None:
    """Test the well-known OAuth authorization server endpoint with different URL configurations."""
    await async_process_ha_core_config(hass, config)
    client = await async_setup_auth(hass, aiohttp_client, setup_api=True)
    resp = await client.get(
        "/.well-known/oauth-authorization-server",
    )
    expect(resp.status).to_equal(200)
    expect(await resp.json()).to_equal(
        {
            **extra_response_data,
            "authorization_endpoint": f"{expected_url_prefix}/auth/authorize",
            "token_endpoint": f"{expected_url_prefix}/auth/token",
            "revocation_endpoint": f"{expected_url_prefix}/auth/revoke",
            "client_id_metadata_document_supported": True,
            "response_types_supported": ["code"],
            "service_documentation": "https://developers.home-assistant.io/docs/auth_api",
        }
    )


@test.cases(
    test.case(
        "external_url",
        config={
            "internal_url": "http://192.168.1.100:8123",
            "external_url": "https://example.com",
        },
        expected_response={
            "resource": "https://example.com",
            "authorization_servers": ["https://example.com"],
            "resource_documentation": "https://developers.home-assistant.io/docs/auth_api",
        },
    ),
    test.case(
        "internal_url",
        config={
            "internal_url": "https://example.com",
            "external_url": "https://other.com",
        },
        expected_response={
            "resource": "https://example.com",
            "authorization_servers": ["https://example.com"],
            "resource_documentation": "https://developers.home-assistant.io/docs/auth_api",
        },
    ),
)
async def well_known_protected_resource(
    config: dict[str, str],
    expected_response: dict[str, Any],
    _request_with_host: None = Depends(current_request_with_host),
    hass: HomeAssistant = Depends(hass_fixture),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fx),
) -> None:
    """Test the well-known OAuth protected resource metadata endpoint per RFC9728."""
    await async_process_ha_core_config(hass, config)
    client = await async_setup_auth(hass, aiohttp_client, setup_api=True)
    resp = await client.get(
        "/.well-known/oauth-protected-resource",
    )
    expect(resp.status).to_equal(200)
    expect(await resp.json()).to_equal(expected_response)


@test
async def well_known_protected_resource_no_url(
    _request_with_host: None = Depends(current_request_with_host),
    hass: HomeAssistant = Depends(hass_fixture),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fx),
) -> None:
    """Test the protected resource metadata returns 404 when no URL is configured."""
    await async_process_ha_core_config(
        hass,
        {
            "internal_url": "https://other.com",
            "external_url": "https://again.com",
        },
    )
    client = await async_setup_auth(hass, aiohttp_client, setup_api=True)
    resp = await client.get(
        "/.well-known/oauth-protected-resource",
    )
    expect(resp.status).to_equal(404)
