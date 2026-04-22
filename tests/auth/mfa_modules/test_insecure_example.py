"""Test the example module auth module."""

from tryke import Depends, expect, fixture, test

from homeassistant import auth, data_entry_flow
from homeassistant.auth.mfa_modules import auth_mfa_module_from_config
from homeassistant.auth.models import Credentials
from homeassistant.core import HomeAssistant

from tests.common import MockUser
from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def validate(hass: HomeAssistant = Depends(hass)) -> None:
    """Test validating pin."""
    auth_module = await auth_mfa_module_from_config(
        hass,
        {
            "type": "insecure_example",
            "data": [{"user_id": "test-user", "pin": "123456"}],
        },
    )

    result = await auth_module.async_validate("test-user", {"pin": "123456"})
    expect(result).to_be(True)

    result = await auth_module.async_validate("test-user", {"pin": "invalid"})
    expect(result).to_be(False)

    result = await auth_module.async_validate("invalid-user", {"pin": "123456"})
    expect(result).to_be(False)


@test
async def setup_user(hass: HomeAssistant = Depends(hass)) -> None:
    """Test setup user."""
    auth_module = await auth_mfa_module_from_config(
        hass, {"type": "insecure_example", "data": []}
    )

    await auth_module.async_setup_user("test-user", {"pin": "123456"})
    expect(len(auth_module._data)).to_equal(1)

    result = await auth_module.async_validate("test-user", {"pin": "123456"})
    expect(result).to_be(True)


@test
async def depose_user(hass: HomeAssistant = Depends(hass)) -> None:
    """Test despose user."""
    auth_module = await auth_mfa_module_from_config(
        hass,
        {
            "type": "insecure_example",
            "data": [{"user_id": "test-user", "pin": "123456"}],
        },
    )
    expect(len(auth_module._data)).to_equal(1)

    await auth_module.async_depose_user("test-user")
    expect(len(auth_module._data)).to_equal(0)


@test
async def is_user_setup(hass: HomeAssistant = Depends(hass)) -> None:
    """Test is user setup."""
    auth_module = await auth_mfa_module_from_config(
        hass,
        {
            "type": "insecure_example",
            "data": [{"user_id": "test-user", "pin": "123456"}],
        },
    )
    expect(await auth_module.async_is_user_setup("test-user")).to_be(True)
    expect(await auth_module.async_is_user_setup("invalid-user")).to_be(False)


@test
async def login(hass: HomeAssistant = Depends(hass)) -> None:
    """Test login flow with auth module."""
    hass.auth = await auth.auth_manager_from_config(
        hass,
        [
            {
                "type": "insecure_example",
                "users": [{"username": "test-user", "password": "test-pass"}],
            }
        ],
        [
            {
                "type": "insecure_example",
                "data": [{"user_id": "mock-user", "pin": "123456"}],
            }
        ],
    )
    user = MockUser(
        id="mock-user", is_owner=False, is_active=False, name="Paulus"
    ).add_to_auth_manager(hass.auth)
    await hass.auth.async_link_user(
        user,
        Credentials(
            id="mock-id",
            auth_provider_type="insecure_example",
            auth_provider_id=None,
            data={"username": "test-user"},
            is_new=False,
        ),
    )

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
    expect(result["data_schema"].schema.get("pin") is str).to_be(True)

    result = await hass.auth.login_flow.async_configure(
        result["flow_id"], {"pin": "invalid-code"}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal("invalid_code")

    result = await hass.auth.login_flow.async_configure(
        result["flow_id"], {"pin": "123456"}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)
    expect(result["data"].id).to_equal("mock-id")


@test
async def setup_flow(hass: HomeAssistant = Depends(hass)) -> None:
    """Test validating pin."""
    auth_module = await auth_mfa_module_from_config(
        hass,
        {
            "type": "insecure_example",
            "data": [{"user_id": "test-user", "pin": "123456"}],
        },
    )

    flow = await auth_module.async_setup_flow("new-user")

    result = await flow.async_step_init()
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)

    result = await flow.async_step_init({"pin": "abcdefg"})
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)
    expect(auth_module._data[1]["user_id"]).to_equal("new-user")
    expect(auth_module._data[1]["pin"]).to_equal("abcdefg")
