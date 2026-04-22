"""Test the HMAC-based One Time Password (MFA) auth module."""

import asyncio
from unittest.mock import patch

import voluptuous_serialize
from tryke import Depends, expect, fixture, test

from homeassistant import data_entry_flow
from homeassistant.auth import auth_manager_from_config, models as auth_models
from homeassistant.auth.mfa_modules import auth_mfa_module_from_config
from homeassistant.components.notify import NOTIFY_SERVICE_SCHEMA
from homeassistant.core import HomeAssistant

from tests.common import MockUser, async_mock_service
from tests.hass_fixtures import hass

MOCK_CODE = "123456"
MOCK_CODE_2 = "654321"


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def validating_mfa(hass: HomeAssistant = Depends(hass)) -> None:
    """Test validating mfa code."""
    notify_auth_module = await auth_mfa_module_from_config(hass, {"type": "notify"})
    await notify_auth_module.async_setup_user("test-user", {"notify_service": "dummy"})

    with patch("pyotp.HOTP.verify", return_value=True):
        expect(
            await notify_auth_module.async_validate("test-user", {"code": MOCK_CODE})
        ).to_be(True)


@test
async def validating_mfa_invalid_code(hass: HomeAssistant = Depends(hass)) -> None:
    """Test validating an invalid mfa code."""
    notify_auth_module = await auth_mfa_module_from_config(hass, {"type": "notify"})
    await notify_auth_module.async_setup_user("test-user", {"notify_service": "dummy"})

    with patch("pyotp.HOTP.verify", return_value=False):
        expect(
            await notify_auth_module.async_validate("test-user", {"code": MOCK_CODE})
        ).to_be(False)


@test
async def validating_mfa_invalid_user(hass: HomeAssistant = Depends(hass)) -> None:
    """Test validating an mfa code with invalid user."""
    notify_auth_module = await auth_mfa_module_from_config(hass, {"type": "notify"})
    await notify_auth_module.async_setup_user("test-user", {"notify_service": "dummy"})

    expect(
        await notify_auth_module.async_validate("invalid-user", {"code": MOCK_CODE})
    ).to_be(False)


@test
async def validating_mfa_counter(hass: HomeAssistant = Depends(hass)) -> None:
    """Test counter will move only after generate code."""
    notify_auth_module = await auth_mfa_module_from_config(hass, {"type": "notify"})
    await notify_auth_module.async_setup_user(
        "test-user", {"counter": 0, "notify_service": "dummy"}
    )
    async_mock_service(hass, "notify", "dummy")

    expect(bool(notify_auth_module._user_settings)).to_be(True)
    notify_setting = list(notify_auth_module._user_settings.values())[0]
    init_count = notify_setting.counter
    expect(init_count is not None).to_be(True)

    with patch("pyotp.HOTP.at", return_value=MOCK_CODE):
        await notify_auth_module.async_initialize_login_mfa_step("test-user")

    notify_setting = list(notify_auth_module._user_settings.values())[0]
    after_generate_count = notify_setting.counter
    expect(after_generate_count != init_count).to_be(True)

    with patch("pyotp.HOTP.verify", return_value=True):
        expect(
            await notify_auth_module.async_validate("test-user", {"code": MOCK_CODE})
        ).to_be(True)

    notify_setting = list(notify_auth_module._user_settings.values())[0]
    expect(after_generate_count).to_equal(notify_setting.counter)

    with patch("pyotp.HOTP.verify", return_value=False):
        expect(
            await notify_auth_module.async_validate("test-user", {"code": MOCK_CODE})
        ).to_be(False)

    notify_setting = list(notify_auth_module._user_settings.values())[0]
    expect(after_generate_count).to_equal(notify_setting.counter)


@test
async def setup_depose_user(hass: HomeAssistant = Depends(hass)) -> None:
    """Test set up and despose user."""
    notify_auth_module = await auth_mfa_module_from_config(hass, {"type": "notify"})
    await notify_auth_module.async_setup_user("test-user", {})
    expect(len(notify_auth_module._user_settings)).to_equal(1)
    await notify_auth_module.async_setup_user("test-user", {})
    expect(len(notify_auth_module._user_settings)).to_equal(1)

    await notify_auth_module.async_depose_user("test-user")
    expect(len(notify_auth_module._user_settings)).to_equal(0)

    await notify_auth_module.async_setup_user("test-user2", {"secret": "secret-code"})
    expect(len(notify_auth_module._user_settings)).to_equal(1)


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
        [{"type": "notify"}],
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

    notify_calls = async_mock_service(
        hass, "notify", "test-notify", NOTIFY_SERVICE_SCHEMA
    )

    await hass.auth.async_enable_user_mfa(
        user, "notify", {"notify_service": "test-notify"}
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

    with patch("pyotp.HOTP.at", return_value=MOCK_CODE):
        result = await hass.auth.login_flow.async_configure(
            result["flow_id"], {"username": "test-user", "password": "test-pass"}
        )
        expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
        expect(result["step_id"]).to_equal("mfa")
        expect(result["data_schema"].schema.get("code") is str).to_be(True)

    await hass.async_block_till_done()

    expect(len(notify_calls)).to_equal(1)
    notify_call = notify_calls[0]
    expect(notify_call.domain).to_equal("notify")
    expect(notify_call.service).to_equal("test-notify")
    message = notify_call.data["message"]
    expect(MOCK_CODE in message).to_be(True)

    with patch("pyotp.HOTP.verify", return_value=False):
        result = await hass.auth.login_flow.async_configure(
            result["flow_id"], {"code": "invalid-code"}
        )
        expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
        expect(result["step_id"]).to_equal("mfa")
        expect(result["errors"]["base"]).to_equal("invalid_code")

    await hass.async_block_till_done()

    expect(len(notify_calls)).to_equal(1)

    with (
        patch("pyotp.HOTP.verify", return_value=False),
        patch("pyotp.HOTP.at", return_value=MOCK_CODE_2),
    ):
        result = await hass.auth.login_flow.async_configure(
            result["flow_id"], {"code": "invalid-code"}
        )
        expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
        expect(result["step_id"]).to_equal("mfa")
        expect(result["errors"]["base"]).to_equal("invalid_code")

        result = await hass.auth.login_flow.async_configure(
            result["flow_id"], {"code": "invalid-code"}
        )
        expect(result["type"]).to_equal(data_entry_flow.FlowResultType.ABORT)
        expect(result["reason"]).to_equal("too_many_retry")

    await hass.async_block_till_done()

    result = await hass.auth.login_flow.async_init((provider.type, provider.id))
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)

    with patch("pyotp.HOTP.at", return_value=MOCK_CODE):
        result = await hass.auth.login_flow.async_configure(
            result["flow_id"], {"username": "test-user", "password": "test-pass"}
        )
        expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
        expect(result["step_id"]).to_equal("mfa")
        expect(result["data_schema"].schema.get("code") is str).to_be(True)

    await hass.async_block_till_done()

    expect(len(notify_calls)).to_equal(2)
    notify_call = notify_calls[1]
    expect(notify_call.domain).to_equal("notify")
    expect(notify_call.service).to_equal("test-notify")
    message = notify_call.data["message"]
    expect(MOCK_CODE in message).to_be(True)

    with patch("pyotp.HOTP.verify", return_value=True):
        result = await hass.auth.login_flow.async_configure(
            result["flow_id"], {"code": MOCK_CODE}
        )
        expect(result["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)
        expect(result["data"].id).to_equal("mock-id")


@test
async def setup_user_notify_service(hass: HomeAssistant = Depends(hass)) -> None:
    """Test allow select notify service during mfa setup."""
    notify_calls = async_mock_service(hass, "notify", "test1", NOTIFY_SERVICE_SCHEMA)
    async_mock_service(hass, "notify", "test2", NOTIFY_SERVICE_SCHEMA)
    notify_auth_module = await auth_mfa_module_from_config(hass, {"type": "notify"})

    services = notify_auth_module.aync_get_available_notify_services()
    expect(services).to_equal(["test1", "test2"])

    flow = await notify_auth_module.async_setup_flow("test-user")
    step = await flow.async_step_init()
    expect(step["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(step["step_id"]).to_equal("init")
    schema = step["data_schema"]
    schema({"notify_service": "test2"})
    expect(voluptuous_serialize.convert(schema)).to_equal(
        [
            {
                "name": "notify_service",
                "options": [
                    ("test1", "test1"),
                    ("test2", "test2"),
                ],
                "required": True,
                "type": "select",
            },
            {
                "name": "target",
                "optional": True,
                "required": False,
                "type": "string",
            },
        ]
    )

    with patch("pyotp.HOTP.at", return_value=MOCK_CODE):
        step = await flow.async_step_init({"notify_service": "test1"})
        expect(step["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
        expect(step["step_id"]).to_equal("setup")

    await hass.async_block_till_done()

    expect(len(notify_calls)).to_equal(1)
    notify_call = notify_calls[0]
    expect(notify_call.domain).to_equal("notify")
    expect(notify_call.service).to_equal("test1")
    message = notify_call.data["message"]
    expect(MOCK_CODE in message).to_be(True)

    with patch("pyotp.HOTP.at", return_value=MOCK_CODE_2):
        step = await flow.async_step_setup({"code": "invalid"})
        expect(step["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
        expect(step["step_id"]).to_equal("setup")
        expect(step["errors"]["base"]).to_equal("invalid_code")

    await hass.async_block_till_done()

    expect(len(notify_calls)).to_equal(2)
    notify_call = notify_calls[1]
    expect(notify_call.domain).to_equal("notify")
    expect(notify_call.service).to_equal("test1")
    message = notify_call.data["message"]
    expect(MOCK_CODE_2 in message).to_be(True)

    with patch("pyotp.HOTP.verify", return_value=True):
        step = await flow.async_step_setup({"code": MOCK_CODE_2})
        expect(step["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)


@test
async def include_exclude_config(hass: HomeAssistant = Depends(hass)) -> None:
    """Test allow include exclude config."""
    async_mock_service(hass, "notify", "include1", NOTIFY_SERVICE_SCHEMA)
    async_mock_service(hass, "notify", "include2", NOTIFY_SERVICE_SCHEMA)
    async_mock_service(hass, "notify", "exclude1", NOTIFY_SERVICE_SCHEMA)
    async_mock_service(hass, "notify", "exclude2", NOTIFY_SERVICE_SCHEMA)
    async_mock_service(hass, "other", "include3", NOTIFY_SERVICE_SCHEMA)
    async_mock_service(hass, "other", "exclude3", NOTIFY_SERVICE_SCHEMA)

    notify_auth_module = await auth_mfa_module_from_config(
        hass, {"type": "notify", "exclude": ["exclude1", "exclude2", "exclude3"]}
    )
    services = notify_auth_module.aync_get_available_notify_services()
    expect(services).to_equal(["include1", "include2"])

    notify_auth_module = await auth_mfa_module_from_config(
        hass, {"type": "notify", "include": ["include1", "include2", "include3"]}
    )
    services = notify_auth_module.aync_get_available_notify_services()
    expect(services).to_equal(["include1", "include2"])

    # Exclude has high priority than include.
    notify_auth_module = await auth_mfa_module_from_config(
        hass,
        {
            "type": "notify",
            "include": ["include1", "include2", "include3"],
            "exclude": ["exclude1", "exclude2", "include2"],
        },
    )
    services = notify_auth_module.aync_get_available_notify_services()
    expect(services).to_equal(["include1"])


@test
async def setup_user_no_notify_service(hass: HomeAssistant = Depends(hass)) -> None:
    """Test setup flow abort if there is no available notify service."""
    async_mock_service(hass, "notify", "test1", NOTIFY_SERVICE_SCHEMA)
    notify_auth_module = await auth_mfa_module_from_config(
        hass, {"type": "notify", "exclude": "test1"}
    )

    services = notify_auth_module.aync_get_available_notify_services()
    expect(services).to_equal([])

    flow = await notify_auth_module.async_setup_flow("test-user")
    step = await flow.async_step_init()
    expect(step["type"]).to_equal(data_entry_flow.FlowResultType.ABORT)
    expect(step["reason"]).to_equal("no_available_service")


@test
async def not_raise_exception_when_service_not_exist(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test login flow will not raise exception when notify service error."""
    hass.auth = await auth_manager_from_config(
        hass,
        [
            {
                "type": "insecure_example",
                "users": [{"username": "test-user", "password": "test-pass"}],
            }
        ],
        [{"type": "notify"}],
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

    await hass.auth.async_enable_user_mfa(
        user, "notify", {"notify_service": "invalid-notify"}
    )

    provider = hass.auth.auth_providers[0]

    result = await hass.auth.login_flow.async_init((provider.type, provider.id))
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)

    with patch("pyotp.HOTP.at", return_value=MOCK_CODE):
        result = await hass.auth.login_flow.async_configure(
            result["flow_id"], {"username": "test-user", "password": "test-pass"}
        )
        expect(result["type"]).to_equal(data_entry_flow.FlowResultType.ABORT)
        expect(result["reason"]).to_equal("unknown_error")

    await hass.async_block_till_done()


@test
async def race_condition_in_data_loading(hass: HomeAssistant = Depends(hass)) -> None:
    """Test race condition in the data loading."""
    counter = 0

    async def mock_load(_):
        """Mock homeassistant.helpers.storage.Store.async_load."""
        nonlocal counter
        counter += 1
        await asyncio.sleep(0)

    notify_auth_module = await auth_mfa_module_from_config(hass, {"type": "notify"})
    with patch("homeassistant.helpers.storage.Store.async_load", new=mock_load):
        task1 = notify_auth_module.async_validate("user", {"code": "value"})
        task2 = notify_auth_module.async_validate("user", {"code": "value"})
        results = await asyncio.gather(task1, task2, return_exceptions=True)
        expect(counter).to_equal(1)
        expect(results[0]).to_be(False)
        expect(results[1]).to_be(False)
