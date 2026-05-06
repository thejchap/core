"""Test the Trusted Networks auth provider."""

from ipaddress import ip_address, ip_network
from unittest.mock import Mock, patch

from hass_nabucasa import remote
import voluptuous as vol
from tryke import Depends, expect, fixture, test

from homeassistant import auth
from homeassistant.auth import auth_store
from homeassistant.auth.providers import trusted_networks as tn_auth
from homeassistant.components.http import CONF_TRUSTED_PROXIES, CONF_USE_X_FORWARDED_FOR
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass


@fixture
async def store(hass: HomeAssistant = Depends(hass)) -> auth_store.AuthStore:
    """Mock store."""
    store = auth_store.AuthStore(hass)
    await store.async_load()
    return store


@fixture
def provider(
    hass: HomeAssistant = Depends(hass),
    store: auth_store.AuthStore = Depends(store),
) -> tn_auth.TrustedNetworksAuthProvider:
    """Mock provider."""
    return tn_auth.TrustedNetworksAuthProvider(
        hass,
        store,
        tn_auth.CONFIG_SCHEMA(
            {
                "type": "trusted_networks",
                "trusted_networks": [
                    "192.168.0.1",
                    "192.168.128.0/24",
                    "::1",
                    "fd00::/8",
                ],
            }
        ),
    )


@fixture
def provider_with_user(
    hass: HomeAssistant = Depends(hass),
    store: auth_store.AuthStore = Depends(store),
) -> tn_auth.TrustedNetworksAuthProvider:
    """Mock provider with trusted users config."""
    return tn_auth.TrustedNetworksAuthProvider(
        hass,
        store,
        tn_auth.CONFIG_SCHEMA(
            {
                "type": "trusted_networks",
                "trusted_networks": [
                    "192.168.0.1",
                    "192.168.128.0/24",
                    "::1",
                    "fd00::/8",
                ],
                # user_id will be injected in test.
                "trusted_users": {
                    "192.168.0.1": [],
                    "192.168.128.0/24": [],
                    "fd00::/8": [],
                },
            }
        ),
    )


@fixture
def provider_bypass_login(
    hass: HomeAssistant = Depends(hass),
    store: auth_store.AuthStore = Depends(store),
) -> tn_auth.TrustedNetworksAuthProvider:
    """Mock provider with allow_bypass_login config."""
    return tn_auth.TrustedNetworksAuthProvider(
        hass,
        store,
        tn_auth.CONFIG_SCHEMA(
            {
                "type": "trusted_networks",
                "trusted_networks": [
                    "192.168.0.1",
                    "192.168.128.0/24",
                    "::1",
                    "fd00::/8",
                ],
                "allow_bypass_login": True,
            }
        ),
    )


@fixture
def manager(
    hass: HomeAssistant = Depends(hass),
    store: auth_store.AuthStore = Depends(store),
    provider: tn_auth.TrustedNetworksAuthProvider = Depends(provider),
) -> auth.AuthManager:
    """Mock manager."""
    return auth.AuthManager(hass, store, {(provider.type, provider.id): provider}, {})


@fixture
def manager_with_user(
    hass: HomeAssistant = Depends(hass),
    store: auth_store.AuthStore = Depends(store),
    provider_with_user: tn_auth.TrustedNetworksAuthProvider = Depends(provider_with_user),
) -> auth.AuthManager:
    """Mock manager with trusted user."""
    return auth.AuthManager(
        hass,
        store,
        {(provider_with_user.type, provider_with_user.id): provider_with_user},
        {},
    )


@fixture
def manager_bypass_login(
    hass: HomeAssistant = Depends(hass),
    store: auth_store.AuthStore = Depends(store),
    provider_bypass_login: tn_auth.TrustedNetworksAuthProvider = Depends(
        provider_bypass_login
    ),
) -> auth.AuthManager:
    """Mock manager with allow bypass login."""
    return auth.AuthManager(
        hass,
        store,
        {(provider_bypass_login.type, provider_bypass_login.id): provider_bypass_login},
        {},
    )


@test
async def config_schema() -> None:
    """Test CONFIG_SCHEMA."""
    tn_auth.CONFIG_SCHEMA(
        {
            "type": "trusted_networks",
            "trusted_networks": ["192.168.0.1"],
            "trusted_users": {
                "192.168.0.1": [
                    "a1ab982744b64757bf80515589258924",
                    {"group": "system-group"},
                ]
            },
        }
    )
    expect(
        lambda: tn_auth.CONFIG_SCHEMA(
            {
                "type": "trusted_networks",
                "trusted_networks": ["192.168.0.1"],
                "trusted_users": {"192.168.0.1": ["abcde"]},
            }
        )
    ).to_raise(vol.Invalid)


@test
async def trusted_networks_credentials(
    manager: auth.AuthManager = Depends(manager),
    provider: tn_auth.TrustedNetworksAuthProvider = Depends(provider),
) -> None:
    """Test trusted_networks credentials related functions."""
    owner = await manager.async_create_user("test-owner")
    tn_owner_cred = await provider.async_get_or_create_credentials({"user": owner.id})
    expect(tn_owner_cred.is_new).to_be(False)
    expect(any(cred.id == tn_owner_cred.id for cred in owner.credentials)).to_be(True)

    user = await manager.async_create_user("test-user")
    tn_user_cred = await provider.async_get_or_create_credentials({"user": user.id})
    expect(tn_user_cred.id != tn_owner_cred.id).to_be(True)
    expect(tn_user_cred.is_new).to_be(False)
    expect(any(cred.id == tn_user_cred.id for cred in user.credentials)).to_be(True)

    try:
        await provider.async_get_or_create_credentials({"user": "invalid-user"})
    except tn_auth.InvalidUserError:
        pass
    else:
        raise AssertionError("Expected InvalidUserError to be raised")


@test
async def validate_access(
    provider: tn_auth.TrustedNetworksAuthProvider = Depends(provider),
) -> None:
    """Test validate access from trusted networks."""
    provider.async_validate_access(ip_address("192.168.0.1"))
    provider.async_validate_access(ip_address("192.168.128.10"))
    provider.async_validate_access(ip_address("::1"))
    provider.async_validate_access(ip_address("fd01:db8::ff00:42:8329"))

    expect(lambda: provider.async_validate_access(ip_address("192.168.0.2"))).to_raise(
        auth.InvalidAuthError
    )
    expect(lambda: provider.async_validate_access(ip_address("127.0.0.1"))).to_raise(
        auth.InvalidAuthError
    )
    expect(
        lambda: provider.async_validate_access(ip_address("2001:db8::ff00:42:8329"))
    ).to_raise(auth.InvalidAuthError)


@test
async def validate_access_proxy(
    hass: HomeAssistant = Depends(hass),
    provider: tn_auth.TrustedNetworksAuthProvider = Depends(provider),
) -> None:
    """Test validate access from trusted networks are blocked from proxy."""
    await async_setup_component(
        hass,
        "http",
        {
            "http": {
                CONF_TRUSTED_PROXIES: ["192.168.128.0/31", "fd00::1"],
                CONF_USE_X_FORWARDED_FOR: True,
            }
        },
    )
    provider.async_validate_access(ip_address("192.168.128.2"))
    provider.async_validate_access(ip_address("fd00::2"))
    expect(
        lambda: provider.async_validate_access(ip_address("192.168.128.0"))
    ).to_raise(auth.InvalidAuthError)
    expect(
        lambda: provider.async_validate_access(ip_address("192.168.128.1"))
    ).to_raise(auth.InvalidAuthError)
    expect(lambda: provider.async_validate_access(ip_address("fd00::1"))).to_raise(
        auth.InvalidAuthError
    )


@test
async def validate_access_cloud(
    hass: HomeAssistant = Depends(hass),
    provider: tn_auth.TrustedNetworksAuthProvider = Depends(provider),
) -> None:
    """Test validate access from trusted networks are blocked from cloud."""
    await async_setup_component(
        hass,
        "http",
        {
            "http": {
                CONF_TRUSTED_PROXIES: ["192.168.128.0/31", "fd00::1"],
                CONF_USE_X_FORWARDED_FOR: True,
            }
        },
    )
    hass.config.components.add("cloud")

    provider.async_validate_access(ip_address("192.168.128.2"))

    remote.is_cloud_request.set(True)
    expect(
        lambda: provider.async_validate_access(ip_address("192.168.128.2"))
    ).to_raise(auth.InvalidAuthError)


@test
async def validate_refresh_token(
    provider: tn_auth.TrustedNetworksAuthProvider = Depends(provider),
) -> None:
    """Verify re-validation of refresh token."""
    with patch.object(provider, "async_validate_access") as mock:
        expect(
            lambda: provider.async_validate_refresh_token(Mock(), None)
        ).to_raise(auth.InvalidAuthError)

        provider.async_validate_refresh_token(Mock(), "127.0.0.1")
        mock.assert_called_once_with(ip_address("127.0.0.1"))


@test
async def login_flow(
    manager: auth.AuthManager = Depends(manager),
    provider: tn_auth.TrustedNetworksAuthProvider = Depends(provider),
) -> None:
    """Test login flow."""
    owner = await manager.async_create_user("test-owner")
    user = await manager.async_create_user("test-user")

    flow = await provider.async_login_flow({"ip_address": ip_address("127.0.0.1")})
    step = await flow.async_step_init()
    expect(step["type"] is FlowResultType.ABORT).to_be(True)
    expect(step["reason"]).to_equal("not_allowed")

    flow = await provider.async_login_flow({"ip_address": ip_address("192.168.0.1")})
    step = await flow.async_step_init()
    expect(step["step_id"]).to_equal("init")

    schema = step["data_schema"]
    expect(bool(schema({"user": owner.id}))).to_be(True)
    expect(lambda: schema({"user": "invalid-user"})).to_raise(vol.Invalid)

    step = await flow.async_step_init({"user": user.id})
    expect(step["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(step["data"]["user"]).to_equal(user.id)


@test
async def trusted_users_login(
    manager_with_user: auth.AuthManager = Depends(manager_with_user),
    provider_with_user: tn_auth.TrustedNetworksAuthProvider = Depends(provider_with_user),
) -> None:
    """Test available user list changed per different IP."""
    owner = await manager_with_user.async_create_user("test-owner")
    sys_user = await manager_with_user.async_create_system_user("test-sys-user")
    user = await manager_with_user.async_create_user("test-user")

    config = provider_with_user.config["trusted_users"]
    expect(ip_network("192.168.0.1") in config).to_be(True)
    config[ip_network("192.168.0.1")] = [owner.id]
    expect(ip_network("192.168.128.0/24") in config).to_be(True)
    config[ip_network("192.168.128.0/24")] = [sys_user.id, user.id]

    flow = await provider_with_user.async_login_flow(
        {"ip_address": ip_address("127.0.0.1")}
    )
    step = await flow.async_step_init()
    expect(step["type"] is FlowResultType.ABORT).to_be(True)
    expect(step["reason"]).to_equal("not_allowed")

    flow = await provider_with_user.async_login_flow(
        {"ip_address": ip_address("192.168.0.1")}
    )
    step = await flow.async_step_init()
    expect(step["step_id"]).to_equal("init")

    schema = step["data_schema"]
    expect(bool(schema({"user": owner.id}))).to_be(True)
    expect(lambda: schema({"user": user.id})).to_raise(vol.Invalid)

    flow = await provider_with_user.async_login_flow(
        {"ip_address": ip_address("192.168.128.1")}
    )
    step = await flow.async_step_init()
    expect(step["step_id"]).to_equal("init")

    schema = step["data_schema"]
    expect(bool(schema({"user": user.id}))).to_be(True)
    expect(lambda: schema({"user": owner.id})).to_raise(vol.Invalid)
    expect(lambda: schema({"user": sys_user.id})).to_raise(vol.Invalid)

    flow = await provider_with_user.async_login_flow({"ip_address": ip_address("::1")})
    step = await flow.async_step_init()
    expect(step["step_id"]).to_equal("init")

    schema = step["data_schema"]
    expect(bool(schema({"user": owner.id}))).to_be(True)
    expect(bool(schema({"user": user.id}))).to_be(True)
    expect(lambda: schema({"user": sys_user.id})).to_raise(vol.Invalid)

    flow = await provider_with_user.async_login_flow(
        {"ip_address": ip_address("fd00::1")}
    )
    step = await flow.async_step_init()
    expect(step["step_id"]).to_equal("init")

    schema = step["data_schema"]
    expect(lambda: schema({"user": owner.id})).to_raise(vol.Invalid)
    expect(lambda: schema({"user": user.id})).to_raise(vol.Invalid)
    expect(lambda: schema({"user": sys_user.id})).to_raise(vol.Invalid)


@test
async def trusted_group_login(
    manager_with_user: auth.AuthManager = Depends(manager_with_user),
    provider_with_user: tn_auth.TrustedNetworksAuthProvider = Depends(provider_with_user),
) -> None:
    """Test config trusted_user with group_id."""
    owner = await manager_with_user.async_create_user("test-owner")
    user = await manager_with_user.async_create_user("test-user")
    await manager_with_user.async_update_user(
        user, group_ids=[auth.const.GROUP_ID_USER]
    )

    config = provider_with_user.config["trusted_users"]
    expect(ip_network("192.168.0.1") in config).to_be(True)
    config[ip_network("192.168.0.1")] = [{"group": [auth.const.GROUP_ID_USER]}]
    expect(ip_network("192.168.128.0/24") in config).to_be(True)
    config[ip_network("192.168.128.0/24")] = [
        owner.id,
        {"group": [auth.const.GROUP_ID_USER]},
    ]

    flow = await provider_with_user.async_login_flow(
        {"ip_address": ip_address("127.0.0.1")}
    )
    step = await flow.async_step_init()
    expect(step["type"] is FlowResultType.ABORT).to_be(True)
    expect(step["reason"]).to_equal("not_allowed")

    flow = await provider_with_user.async_login_flow(
        {"ip_address": ip_address("192.168.0.1")}
    )
    step = await flow.async_step_init()
    expect(step["step_id"]).to_equal("init")

    schema = step["data_schema"]
    expect(bool(schema({"user": user.id}))).to_be(True)
    expect(lambda: schema({"user": owner.id})).to_raise(vol.Invalid)

    flow = await provider_with_user.async_login_flow(
        {"ip_address": ip_address("192.168.128.1")}
    )
    step = await flow.async_step_init()
    expect(step["step_id"]).to_equal("init")

    schema = step["data_schema"]
    expect(bool(schema({"user": owner.id}))).to_be(True)
    expect(bool(schema({"user": user.id}))).to_be(True)


@test
async def bypass_login_flow(
    manager_bypass_login: auth.AuthManager = Depends(manager_bypass_login),
    provider_bypass_login: tn_auth.TrustedNetworksAuthProvider = Depends(
        provider_bypass_login
    ),
) -> None:
    """Test login flow can be bypass if only one user available."""
    owner = await manager_bypass_login.async_create_user("test-owner")

    flow = await provider_bypass_login.async_login_flow(
        {"ip_address": ip_address("127.0.0.1")}
    )
    step = await flow.async_step_init()
    expect(step["type"] is FlowResultType.ABORT).to_be(True)
    expect(step["reason"]).to_equal("not_allowed")

    flow = await provider_bypass_login.async_login_flow(
        {"ip_address": ip_address("192.168.0.1")}
    )
    step = await flow.async_step_init()
    expect(step["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(step["data"]["user"]).to_equal(owner.id)

    user = await manager_bypass_login.async_create_user("test-user")

    flow = await provider_bypass_login.async_login_flow(
        {"ip_address": ip_address("192.168.0.1")}
    )
    step = await flow.async_step_init()
    schema = step["data_schema"]
    expect(bool(schema({"user": owner.id}))).to_be(True)
    expect(bool(schema({"user": user.id}))).to_be(True)
