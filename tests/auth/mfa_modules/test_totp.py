"""Test the Time-based One Time Password (MFA) auth module."""

import asyncio
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import data_entry_flow
from homeassistant.auth import auth_manager_from_config, models as auth_models
from homeassistant.auth.mfa_modules import auth_mfa_module_from_config
from homeassistant.core import HomeAssistant

from tests.common import MockUser
from tests.hass_fixtures import hass

MOCK_CODE = "123456"


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def validating_mfa(hass: HomeAssistant = Depends(hass)) -> None:
    """Test validating mfa code."""
    totp_auth_module = await auth_mfa_module_from_config(hass, {"type": "totp"})
    await totp_auth_module.async_setup_user("test-user", {})

    with patch("pyotp.TOTP.verify", return_value=True):
        expect(
            await totp_auth_module.async_validate("test-user", {"code": MOCK_CODE})
        ).to_be(True)


@test
async def validating_mfa_invalid_code(hass: HomeAssistant = Depends(hass)) -> None:
    """Test validating an invalid mfa code."""
    totp_auth_module = await auth_mfa_module_from_config(hass, {"type": "totp"})
    await totp_auth_module.async_setup_user("test-user", {})

    with patch("pyotp.TOTP.verify", return_value=False):
        expect(
            await totp_auth_module.async_validate("test-user", {"code": MOCK_CODE})
        ).to_be(False)


@test
async def validating_mfa_invalid_user(hass: HomeAssistant = Depends(hass)) -> None:
    """Test validating an mfa code with invalid user."""
    totp_auth_module = await auth_mfa_module_from_config(hass, {"type": "totp"})
    await totp_auth_module.async_setup_user("test-user", {})

    expect(
        await totp_auth_module.async_validate("invalid-user", {"code": MOCK_CODE})
    ).to_be(False)


@test
async def setup_depose_user(hass: HomeAssistant = Depends(hass)) -> None:
    """Test despose user."""
    totp_auth_module = await auth_mfa_module_from_config(hass, {"type": "totp"})
    result = await totp_auth_module.async_setup_user("test-user", {})
    expect(len(totp_auth_module._users)).to_equal(1)
    result2 = await totp_auth_module.async_setup_user("test-user", {})
    expect(len(totp_auth_module._users)).to_equal(1)
    expect(result != result2).to_be(True)

    await totp_auth_module.async_depose_user("test-user")
    expect(len(totp_auth_module._users)).to_equal(0)

    result = await totp_auth_module.async_setup_user(
        "test-user2", {"secret": "secret-code"}
    )
    expect(result).to_equal("secret-code")
    expect(len(totp_auth_module._users)).to_equal(1)


@test
async def login_flow_validates_mfa(hass: HomeAssistant = Depends(hass)) -> None:
    """Test login flow with mfa enabled."""
    hass.auth = await auth_manager_from_config(
        hass,
        [
            {
                "type": "insecure_example",
                "users": [{"username": "test-user", "password": "test-pass"}],
            }
        ],
        [{"type": "totp"}],
    )
    user = MockUser(
        id="mock-user", is_owner=False, is_active=False, name="Paulus"
    ).add_to_auth_manager(hass.auth)
    await hass.auth.async_link_user(
        user,
        auth_models.Credentials(
            id="mock-id",
            auth_provider_type="insecure_example",
            auth_provider_id=None,
            data={"username": "test-user"},
            is_new=False,
        ),
    )

    await hass.auth.async_enable_user_mfa(user, "totp", {})

    provider = hass.auth.auth_providers[0]

    result = await hass.auth.login_flow.async_init((provider.type, provider.id))
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)

    result = await hass.auth.login_flow.async_configure(
        result["flow_id"], {"username": "incorrect-user", "password": "test-pass"}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal("invalid_auth")

    result = await hass.auth.login_flow.async_configure(
        result["flow_id"], {"username": "test-user", "password": "incorrect-pass"}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal("invalid_auth")

    result = await hass.auth.login_flow.async_configure(
        result["flow_id"], {"username": "test-user", "password": "test-pass"}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(result["step_id"]).to_equal("mfa")
    expect(result["data_schema"].schema.get("code") is str).to_be(True)

    with patch("pyotp.TOTP.verify", return_value=False):
        result = await hass.auth.login_flow.async_configure(
            result["flow_id"], {"code": "invalid-code"}
        )
        expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
        expect(result["step_id"]).to_equal("mfa")
        expect(result["errors"]["base"]).to_equal("invalid_code")

    with patch("pyotp.TOTP.verify", return_value=True):
        result = await hass.auth.login_flow.async_configure(
            result["flow_id"], {"code": MOCK_CODE}
        )
        expect(result["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)
        expect(result["data"].id).to_equal("mock-id")


@test
async def race_condition_in_data_loading(hass: HomeAssistant = Depends(hass)) -> None:
    """Test race condition in the data loading."""
    counter = 0

    async def mock_load(_):
        """Mock of homeassistant.helpers.storage.Store.async_load."""
        nonlocal counter
        counter += 1
        await asyncio.sleep(0)

    totp_auth_module = await auth_mfa_module_from_config(hass, {"type": "totp"})
    with patch("homeassistant.helpers.storage.Store.async_load", new=mock_load):
        task1 = totp_auth_module.async_validate("user", {"code": "value"})
        task2 = totp_auth_module.async_validate("user", {"code": "value"})
        results = await asyncio.gather(task1, task2, return_exceptions=True)
        expect(counter).to_equal(1)
        expect(results[0]).to_be(False)
        expect(results[1]).to_be(False)
