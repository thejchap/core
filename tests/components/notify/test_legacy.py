"""The tests for legacy notify services."""

import asyncio
from collections.abc import Callable, Coroutine, Mapping
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import voluptuous as vol
import yaml

from tryke import Depends, expect, fixture, test

from homeassistant import config as hass_config
from homeassistant.components import notify
from homeassistant.const import SERVICE_RELOAD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.reload import async_setup_reload_service
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.setup import async_setup_component

from tests.common import MockPlatform, mock_platform
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    hass as hass_fixture,
    mock_network,
    tmp_path as tmp_path_fixture,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
    return 0


class NotificationService(notify.BaseNotificationService):
    """A test class for legacy notification services."""

    def __init__(
        self,
        hass: HomeAssistant,
        target_list: dict[str, Any] | None = None,
        name="notify",
    ) -> None:
        """Initialize the service."""

        async def _async_make_reloadable(hass: HomeAssistant) -> None:
            """Initialize the reload service."""
            await async_setup_reload_service(hass, name, [notify.DOMAIN])

        self.hass = hass
        self.target_list = target_list or {"a": 1, "b": 2}
        hass.async_create_task(_async_make_reloadable(hass))

    @property
    def targets(self):
        """Return a dictionary of devices."""
        return self.target_list


class MockNotifyPlatform(MockPlatform):
    """Help to set up a legacy test notify service."""

    def __init__(self, async_get_service: Any = None, get_service: Any = None) -> None:
        """Return a legacy notify service."""
        super().__init__()
        if get_service:
            self.get_service = get_service
        if async_get_service:
            self.async_get_service = async_get_service


def mock_notify_platform(
    hass: HomeAssistant,
    tmp_path: Path,
    integration: str = "notify",
    async_get_service: Callable[
        [HomeAssistant, ConfigType, DiscoveryInfoType | None],
        Coroutine[Any, Any, notify.BaseNotificationService],
    ]
    | None = None,
    get_service: Callable[
        [HomeAssistant, ConfigType, DiscoveryInfoType | None],
        notify.BaseNotificationService,
    ]
    | None = None,
):
    """Specialize the mock platform for legacy notify service."""
    loaded_platform = MockNotifyPlatform(async_get_service, get_service)
    mock_platform(hass, f"{integration}.notify", loaded_platform)

    return loaded_platform


async def help_setup_notify(
    hass: HomeAssistant, tmp_path: Path, targets: dict[str, None] | None = None
) -> MagicMock:
    """Help set up a platform notify service."""
    send_message_mock = MagicMock()

    class _TestNotifyService(notify.BaseNotificationService):
        def __init__(self, targets: dict[str, None] | None) -> None:
            """Initialize service."""
            self._targets = targets
            super().__init__()

        @property
        def targets(self) -> Mapping[str, Any] | None:
            """Return a dictionary of registered targets."""
            return self._targets

        def send_message(self, message: str, **kwargs: Any) -> None:
            """Send a message."""
            send_message_mock(message, kwargs)

    async def async_get_service(
        hass: HomeAssistant,
        config: ConfigType,
        discovery_info: DiscoveryInfoType | None = None,
    ) -> notify.BaseNotificationService:
        """Get notify service for mocked platform."""
        return _TestNotifyService(targets)

    mock_notify_platform(hass, tmp_path, "test", async_get_service=async_get_service)
    await async_setup_component(hass, "notify", {"notify": [{"platform": "test"}]})
    await hass.async_block_till_done()

    return send_message_mock


@test
async def same_targets(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test not changing the targets in a legacy notify service."""
    svc = NotificationService(hass)
    await svc.async_setup(hass, "notify", "test")
    await svc.async_register_services()
    await hass.async_block_till_done()

    expect(hasattr(svc, "registered_targets")).to_be_truthy()
    expect(svc.registered_targets).to_equal({"test_a": 1, "test_b": 2})

    await svc.async_register_services()
    await hass.async_block_till_done()
    expect(svc.registered_targets).to_equal({"test_a": 1, "test_b": 2})


@test
async def change_targets(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test changing the targets in a legacy notify service."""
    svc = NotificationService(hass)
    await svc.async_setup(hass, "notify", "test")
    await svc.async_register_services()
    await hass.async_block_till_done()

    expect(hasattr(svc, "registered_targets")).to_be_truthy()
    expect(svc.registered_targets).to_equal({"test_a": 1, "test_b": 2})

    svc.target_list = {"a": 0}
    await svc.async_register_services()
    await hass.async_block_till_done()
    expect(svc.target_list).to_equal({"a": 0})
    expect(svc.registered_targets).to_equal({"test_a": 0})


@test
async def add_targets(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test adding the targets in a legacy notify service."""
    svc = NotificationService(hass)
    await svc.async_setup(hass, "notify", "test")
    await svc.async_register_services()
    await hass.async_block_till_done()

    expect(hasattr(svc, "registered_targets")).to_be_truthy()
    expect(svc.registered_targets).to_equal({"test_a": 1, "test_b": 2})

    svc.target_list = {"a": 1, "b": 2, "c": 3}
    await svc.async_register_services()
    await hass.async_block_till_done()
    expect(svc.target_list).to_equal({"a": 1, "b": 2, "c": 3})
    expect(svc.registered_targets).to_equal({"test_a": 1, "test_b": 2, "test_c": 3})


@test
async def remove_targets(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test removing targets from the targets in a legacy notify service."""
    svc = NotificationService(hass)
    await svc.async_setup(hass, "notify", "test")
    await svc.async_register_services()
    await hass.async_block_till_done()

    expect(hasattr(svc, "registered_targets")).to_be_truthy()
    expect(svc.registered_targets).to_equal({"test_a": 1, "test_b": 2})

    svc.target_list = {"c": 1}
    await svc.async_register_services()
    await hass.async_block_till_done()
    expect(svc.target_list).to_equal({"c": 1})
    expect(svc.registered_targets).to_equal({"test_c": 1})


@test
async def invalid_platform(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test service setup with an invalid platform."""
    mock_notify_platform(hass, tmp_path, "testnotify1")
    await async_setup_component(
        hass, "notify", {"notify": [{"platform": "testnotify1"}]}
    )
    await hass.async_block_till_done()
    expect("Invalid notify platform" in caplog.text).to_be_truthy()
    caplog.clear()
    mock_notify_platform(hass, tmp_path, "testnotify2")
    await async_load_platform(
        hass,
        "notify",
        "testnotify2",
        {},
        hass_config={"notify": [{"platform": "testnotify2"}]},
    )
    await hass.async_block_till_done()
    expect("Invalid notify platform" in caplog.text).to_be_truthy()


@test
async def invalid_service(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test service setup with an invalid service object or platform."""

    def get_service(
        hass: HomeAssistant,
        config: ConfigType,
        discovery_info: DiscoveryInfoType | None = None,
    ) -> notify.BaseNotificationService | None:
        """Return None for an invalid notify service."""
        return None

    mock_notify_platform(hass, tmp_path, "testnotify", get_service=get_service)
    await async_load_platform(
        hass,
        "notify",
        "testnotify",
        {},
        hass_config={"notify": [{"platform": "testnotify"}]},
    )
    await hass.async_block_till_done()
    expect(
        "Failed to initialize notification service testnotify" in caplog.text
    ).to_be_truthy()
    caplog.clear()

    await async_load_platform(
        hass,
        "notify",
        "testnotifyinvalid",
        {"notify": [{"platform": "testnotifyinvalid"}]},
        hass_config={"notify": [{"platform": "testnotifyinvalid"}]},
    )
    await hass.async_block_till_done()
    expect("Unknown notification service specified" in caplog.text).to_be_truthy()


@test
async def platform_setup_with_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test service setup with an invalid setup."""

    async def async_get_service(
        hass: HomeAssistant,
        config: ConfigType,
        discovery_info: DiscoveryInfoType | None = None,
    ) -> notify.BaseNotificationService | None:
        """Return None for an invalid notify service."""
        raise Exception("Setup error")  # noqa: TRY002

    mock_notify_platform(
        hass, tmp_path, "testnotify", async_get_service=async_get_service
    )
    await async_load_platform(
        hass,
        "notify",
        "testnotify",
        {},
        hass_config={"notify": [{"platform": "testnotify"}]},
    )
    await hass.async_block_till_done()
    expect("Error setting up platform testnotify" in caplog.text).to_be_truthy()


@test
async def reload_with_notify_builtin_platform_reload(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test reload using the legacy notify platform reload method."""

    async def async_get_service(
        hass: HomeAssistant,
        config: ConfigType,
        discovery_info: DiscoveryInfoType | None = None,
    ) -> NotificationService:
        """Get notify service for mocked platform."""
        targetlist = {"a": 1, "b": 2}
        return NotificationService(hass, targetlist, "testnotify")

    mock_notify_platform(
        hass, tmp_path, "testnotify", async_get_service=async_get_service
    )

    await notify.async_reload(hass, "testnotify")

    await async_setup_component(
        hass, "notify", {"notify": [{"platform": "testnotify"}]}
    )
    await hass.async_block_till_done()
    expect(hass.services.has_service(notify.DOMAIN, "testnotify_a")).to_be_truthy()
    expect(hass.services.has_service(notify.DOMAIN, "testnotify_b")).to_be_truthy()

    await notify.async_reload(hass, "testnotify")
    expect(hass.services.has_service(notify.DOMAIN, "testnotify_a")).to_be_truthy()
    expect(hass.services.has_service(notify.DOMAIN, "testnotify_b")).to_be_truthy()


@test
async def setup_platform_and_reload(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test service setup and reload."""
    get_service_called = Mock()

    async def async_get_service(
        hass: HomeAssistant,
        config: ConfigType,
        discovery_info: DiscoveryInfoType | None = None,
    ) -> NotificationService:
        """Get notify service for mocked platform."""
        get_service_called(config, discovery_info)
        targetlist = {"a": 1, "b": 2}
        return NotificationService(hass, targetlist, "testnotify")

    async def async_get_service2(
        hass: HomeAssistant,
        config: ConfigType,
        discovery_info: DiscoveryInfoType | None = None,
    ) -> NotificationService:
        """Get legacy notify service for mocked platform."""
        get_service_called(config, discovery_info)
        targetlist = {"c": 3, "d": 4}
        return NotificationService(hass, targetlist, "testnotify2")

    mock_notify_platform(
        hass, tmp_path, "testnotify", async_get_service=async_get_service
    )

    mock_notify_platform(
        hass, tmp_path, "testnotify2", async_get_service=async_get_service2
    )

    await async_setup_component(
        hass, "notify", {"notify": [{"platform": "testnotify"}]}
    )
    await hass.async_block_till_done()
    expect(hass.services.has_service("testnotify", SERVICE_RELOAD)).to_be_truthy()
    expect(hass.services.has_service(notify.DOMAIN, "testnotify_a")).to_be_truthy()
    expect(hass.services.has_service(notify.DOMAIN, "testnotify_b")).to_be_truthy()
    expect(get_service_called.call_count).to_equal(1)
    expect(get_service_called.call_args[0][0]).to_equal({"platform": "testnotify"})
    expect(get_service_called.call_args[0][1]).to_be(None)
    get_service_called.reset_mock()

    await async_load_platform(
        hass,
        "notify",
        "testnotify2",
        {},
        hass_config={"notify": [{"platform": "testnotify"}]},
    )
    await hass.async_block_till_done()
    expect(hass.services.has_service("testnotify2", SERVICE_RELOAD)).to_be_truthy()
    expect(hass.services.has_service(notify.DOMAIN, "testnotify2_c")).to_be_truthy()
    expect(hass.services.has_service(notify.DOMAIN, "testnotify2_d")).to_be_truthy()
    expect(get_service_called.call_count).to_equal(1)
    expect(get_service_called.call_args[0][0]).to_equal({})
    expect(get_service_called.call_args[0][1]).to_equal({})
    get_service_called.reset_mock()

    new_yaml_config_file = tmp_path / "configuration.yaml"
    new_yaml_config = yaml.dump({"notify": [{"platform": "testnotify"}]})
    new_yaml_config_file.write_text(new_yaml_config)

    with patch.object(hass_config, "YAML_CONFIG_FILE", new_yaml_config_file):
        await hass.services.async_call(
            "testnotify",
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await hass.services.async_call(
            "testnotify2",
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await hass.async_block_till_done()

    expect(hass.services.has_service(notify.DOMAIN, "testnotify_a")).to_be_truthy()
    expect(hass.services.has_service(notify.DOMAIN, "testnotify_b")).to_be_truthy()
    expect(get_service_called.call_count).to_equal(1)
    expect(get_service_called.call_args[0][0]).to_equal({"platform": "testnotify"})
    expect(get_service_called.call_args[0][1]).to_be(None)

    expect(hass.services.has_service(notify.DOMAIN, "testnotify2_c")).to_be_falsy()
    expect(hass.services.has_service(notify.DOMAIN, "testnotify2_d")).to_be_falsy()


@test
async def setup_platform_before_notify_setup(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test trying to setup a platform before legacy notify service is setup."""
    get_service_called = Mock()

    async def async_get_service(
        hass: HomeAssistant,
        config: ConfigType,
        discovery_info: DiscoveryInfoType | None = None,
    ) -> NotificationService:
        """Get notify service for mocked platform."""
        get_service_called(config, discovery_info)
        targetlist = {"a": 1, "b": 2}
        return NotificationService(hass, targetlist, "testnotify")

    async def async_get_service2(
        hass: HomeAssistant,
        config: ConfigType,
        discovery_info: DiscoveryInfoType | None = None,
    ) -> NotificationService:
        """Get notify service for mocked platform."""
        get_service_called(config, discovery_info)
        targetlist = {"c": 3, "d": 4}
        return NotificationService(hass, targetlist, "testnotify2")

    mock_notify_platform(
        hass, tmp_path, "testnotify", async_get_service=async_get_service
    )

    mock_notify_platform(
        hass, tmp_path, "testnotify2", async_get_service=async_get_service2
    )

    hass_config_dict = {"notify": [{"platform": "testnotify"}]}

    load_coro = async_load_platform(
        hass, Platform.NOTIFY, "testnotify2", {}, hass_config=hass_config_dict
    )

    setup_coro = async_setup_component(hass, "notify", hass_config_dict)

    load_task = asyncio.create_task(load_coro)
    setup_task = asyncio.create_task(setup_coro)

    await asyncio.gather(load_task, setup_task)

    await hass.async_block_till_done()
    expect(hass.services.has_service(notify.DOMAIN, "testnotify_a")).to_be_truthy()
    expect(hass.services.has_service(notify.DOMAIN, "testnotify_b")).to_be_truthy()
    expect(hass.services.has_service(notify.DOMAIN, "testnotify2_c")).to_be_truthy()
    expect(hass.services.has_service(notify.DOMAIN, "testnotify2_d")).to_be_truthy()


@test
async def setup_platform_after_notify_setup(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test trying to setup a platform after legacy notify service is set up."""
    get_service_called = Mock()

    async def async_get_service(
        hass: HomeAssistant,
        config: ConfigType,
        discovery_info: DiscoveryInfoType | None = None,
    ) -> NotificationService:
        """Get notify service for mocked platform."""
        get_service_called(config, discovery_info)
        targetlist = {"a": 1, "b": 2}
        return NotificationService(hass, targetlist, "testnotify")

    async def async_get_service2(
        hass: HomeAssistant,
        config: ConfigType,
        discovery_info: DiscoveryInfoType | None = None,
    ) -> NotificationService:
        """Get notify service for mocked platform."""
        get_service_called(config, discovery_info)
        targetlist = {"c": 3, "d": 4}
        return NotificationService(hass, targetlist, "testnotify2")

    mock_notify_platform(
        hass, tmp_path, "testnotify", async_get_service=async_get_service
    )

    mock_notify_platform(
        hass, tmp_path, "testnotify2", async_get_service=async_get_service2
    )

    hass_config_dict = {"notify": [{"platform": "testnotify"}]}

    load_coro = async_load_platform(
        hass, Platform.NOTIFY, "testnotify2", {}, hass_config=hass_config_dict
    )

    setup_coro = async_setup_component(hass, "notify", hass_config_dict)

    setup_task = asyncio.create_task(setup_coro)
    load_task = asyncio.create_task(load_coro)

    await asyncio.gather(load_task, setup_task)

    await hass.async_block_till_done()
    expect(hass.services.has_service(notify.DOMAIN, "testnotify_a")).to_be_truthy()
    expect(hass.services.has_service(notify.DOMAIN, "testnotify_b")).to_be_truthy()
    expect(hass.services.has_service(notify.DOMAIN, "testnotify2_c")).to_be_truthy()
    expect(hass.services.has_service(notify.DOMAIN, "testnotify2_d")).to_be_truthy()


@test
async def sending_none_message(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test send with None as message."""
    send_message_mock = await help_setup_notify(hass, tmp_path)
    async with expect_raises_async(
        vol.Invalid,
        match="string value is None for dictionary value @ data\\['message'\\]",
    ):
        await hass.services.async_call(
            notify.DOMAIN, notify.SERVICE_NOTIFY, {notify.ATTR_MESSAGE: None}
        )
    send_message_mock.assert_not_called()


@test
async def method_forwards_correct_data(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test that all data from the service gets forwarded to service."""
    send_message_mock = await help_setup_notify(hass, tmp_path)
    data = {
        notify.ATTR_MESSAGE: "my message",
        notify.ATTR_TITLE: "my title",
        notify.ATTR_DATA: {"hello": "world"},
    }
    await hass.services.async_call(notify.DOMAIN, notify.SERVICE_NOTIFY, data)
    await hass.async_block_till_done()
    send_message_mock.assert_called_once_with(
        "my message", {"title": "my title", "data": {"hello": "world"}}
    )


@test
async def calling_notify_from_script_loaded_from_yaml_without_title(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test if we can call a notify from a script."""
    send_message_mock = await help_setup_notify(hass, tmp_path)
    step = {
        "service": "notify.notify",
        "data": {
            "data": {"push": {"sound": "US-EN-Morgan-Freeman-Roommate-Is-Arriving.wav"}}
        },
        "data_template": {"message": "Test 123 {{ 2 + 2 }}\n"},
    }
    await async_setup_component(
        hass, "script", {"script": {"test": {"sequence": step}}}
    )
    await hass.services.async_call("script", "test")
    await hass.async_block_till_done()
    send_message_mock.assert_called_once_with(
        "Test 123 4",
        {"data": {"push": {"sound": "US-EN-Morgan-Freeman-Roommate-Is-Arriving.wav"}}},
    )


@test
async def calling_notify_from_script_loaded_from_yaml_with_title(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test if we can call a notify from a script."""
    send_message_mock = await help_setup_notify(hass, tmp_path)
    step = {
        "service": "notify.notify",
        "data": {
            "data": {"push": {"sound": "US-EN-Morgan-Freeman-Roommate-Is-Arriving.wav"}}
        },
        "data_template": {"message": "Test 123 {{ 2 + 2 }}\n", "title": "Test"},
    }
    await async_setup_component(
        hass, "script", {"script": {"test": {"sequence": step}}}
    )
    await hass.services.async_call("script", "test")
    await hass.async_block_till_done()
    send_message_mock.assert_called_once_with(
        "Test 123 4",
        {
            "title": "Test",
            "data": {
                "push": {"sound": "US-EN-Morgan-Freeman-Roommate-Is-Arriving.wav"}
            },
        },
    )


@test
async def targets_are_services(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test that all targets are exposed as individual services."""
    await help_setup_notify(hass, tmp_path, targets={"a": 1, "b": 2})
    expect(hass.services.has_service("notify", "notify") is not None).to_be_truthy()
    expect(hass.services.has_service("notify", "test_a") is not None).to_be_truthy()
    expect(hass.services.has_service("notify", "test_b") is not None).to_be_truthy()


@test
async def messages_to_targets_route(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test message routing to specific target services."""
    send_message_mock = await help_setup_notify(
        hass, tmp_path, targets={"target_name": "test target id"}
    )

    await hass.services.async_call(
        "notify",
        "test_target_name",
        {"message": "my message", "title": "my title", "data": {"hello": "world"}},
    )
    await hass.async_block_till_done()

    send_message_mock.assert_called_once_with(
        "my message",
        {"target": ["test target id"], "title": "my title", "data": {"hello": "world"}},
    )
