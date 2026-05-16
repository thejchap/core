"""The tests for Shelly device triggers (tryke port)."""

from collections.abc import Generator
from contextlib import contextmanager, suppress
from typing import Any
from unittest.mock import Mock

from aioshelly.const import MODEL_BUTTON1
from pytest_unordered import unordered
from tryke import Depends, expect, fixture, test

from homeassistant.components import automation
from homeassistant.components.device_automation import (
    DeviceAutomationType,
    InvalidDeviceAutomationConfig,
)
from homeassistant.components.shelly.const import (
    ATTR_CHANNEL,
    ATTR_CLICK_TYPE,
    CONF_SUBTYPE,
    DOMAIN,
    EVENT_SHELLY_CLICK,
)
from homeassistant.const import CONF_DEVICE_ID, CONF_DOMAIN, CONF_PLATFORM, CONF_TYPE
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import (
    device_registry as dr,
    translation as translation_helper,
)
from homeassistant.setup import async_setup_component

from tests.common import async_get_device_automations
from tests.components.shelly import init_integration
from tests.components.shelly._fixtures import (
    mock_block_device as mock_block_device_fixture,
    mock_rpc_device as mock_rpc_device_fixture,
    service_calls as service_calls_fixture,
)
from tests.hass_fixtures import (
    caplog as caplog_fixture,
    device_registry as device_registry_fixture,
    hass as hass_fixture,
)
from tests.hass_tryke_helpers import expect_raises_async

_MISSING = object()


def _preload_strings_translations(hass: HomeAssistant, domain: str) -> None:
    """Load strings.json into the translation cache.

    The dev tree lacks ``translations/en.json`` files, so the real translation
    loader returns no data. Read ``strings.json`` directly and seed the cache
    so messages with ``translation_key`` resolve to their English template.
    """
    import json  # noqa: PLC0415
    from pathlib import Path  # noqa: PLC0415

    strings_path = (
        Path(__file__).resolve().parents[3]
        / "homeassistant"
        / "components"
        / domain
        / "strings.json"
    )
    data: dict[str, Any] = json.loads(strings_path.read_text())
    cache = translation_helper._async_get_translations_cache(hass)
    translation_data = {"en": {domain: data}}
    cache._build_category_cache("en", {domain}, translation_data["en"])
    cache.cache_data.loaded.setdefault("en", set()).add(domain)


@contextmanager
def _patches() -> Generator[Any]:
    """Mimic pytest's monkeypatch for setattr/setitem/delattr."""

    undo: list[Any] = []

    class _Patcher:
        def setattr(self, target: Any, name: str, value: Any) -> None:
            original = getattr(target, name, _MISSING)
            undo.append(("attr", target, name, original))
            setattr(target, name, value)

        def setitem(self, mapping: Any, key: Any, value: Any) -> None:
            original = mapping.get(key, _MISSING)
            undo.append(("item", mapping, key, original))
            mapping[key] = value

        def delattr(self, target: Any, name: str) -> None:
            original = getattr(target, name, _MISSING)
            undo.append(("attr", target, name, original))
            try:
                del target.__dict__[name]
            except (AttributeError, KeyError):
                with suppress(AttributeError):
                    delattr(target, name)

    try:
        yield _Patcher()
    finally:
        for kind, obj, key, original in reversed(undo):
            if kind == "attr":
                if original is _MISSING:
                    with suppress(AttributeError):
                        delattr(obj, key)
                else:
                    setattr(obj, key, original)
            elif original is _MISSING:
                obj.pop(key, None)
            else:
                obj[key] = original


@fixture
def _trigger_executor() -> int:
    """Anchor fixture so async Depends() fixtures resolve under tryke."""
    return 0


@test.cases(
    test.case("momentary", button_type="momentary", is_valid=True),
    test.case("momentary_on_release", button_type="momentary_on_release", is_valid=True),
    test.case("detached", button_type="detached", is_valid=True),
    test.case("toggle", button_type="toggle", is_valid=False),
)
async def get_triggers_block_device(
    button_type: str,
    is_valid: bool,
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test we get the expected triggers from a shelly block device."""
    with _patches() as monkeypatch:
        monkeypatch.setitem(
            mock_block_device.settings,
            "relays",
            [
                {"btn_type": button_type},
                {"btn_type": "toggle"},
            ],
        )
        entry = await init_integration(hass, 1)
        device = dr.async_entries_for_config_entry(device_registry, entry.entry_id)[0]

        expected_triggers: list[dict[str, Any]] = []
        if is_valid:
            expected_triggers = [
                {
                    CONF_PLATFORM: "device",
                    CONF_DEVICE_ID: device.id,
                    CONF_DOMAIN: DOMAIN,
                    CONF_TYPE: type_,
                    CONF_SUBTYPE: "button1",
                    "metadata": {},
                }
                for type_ in ("single", "long")
            ]

        triggers = await async_get_device_automations(
            hass, DeviceAutomationType.TRIGGER, device.id
        )
        triggers = [value for value in triggers if value["domain"] == DOMAIN]
        expect(triggers == unordered(expected_triggers)).to_be(True)


@test
async def get_triggers_rpc_device(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test we get the expected triggers from a shelly RPC device."""
    entry = await init_integration(hass, 2)
    device = dr.async_entries_for_config_entry(device_registry, entry.entry_id)[0]

    expected_triggers = [
        {
            CONF_PLATFORM: "device",
            CONF_DEVICE_ID: device.id,
            CONF_DOMAIN: DOMAIN,
            CONF_TYPE: trigger_type,
            CONF_SUBTYPE: "button1",
            "metadata": {},
        }
        for trigger_type in (
            "btn_down",
            "btn_up",
            "single_push",
            "double_push",
            "triple_push",
            "long_push",
        )
    ]

    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device.id
    )
    triggers = [value for value in triggers if value["domain"] == DOMAIN]
    expect(triggers == unordered(expected_triggers)).to_be(True)


@test
async def get_triggers_button(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test we get the expected triggers from a shelly button."""
    entry = await init_integration(hass, 1, model=MODEL_BUTTON1)
    device = dr.async_entries_for_config_entry(device_registry, entry.entry_id)[0]

    expected_triggers = [
        {
            CONF_PLATFORM: "device",
            CONF_DEVICE_ID: device.id,
            CONF_DOMAIN: DOMAIN,
            CONF_TYPE: trigger_type,
            CONF_SUBTYPE: "button",
            "metadata": {},
        }
        for trigger_type in ("single", "double", "triple", "long")
    ]

    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device.id
    )
    triggers = [value for value in triggers if value["domain"] == DOMAIN]
    expect(triggers == unordered(expected_triggers)).to_be(True)


@test
async def get_triggers_non_initialized_devices(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test we get the empty triggers for non-initialized devices."""
    with _patches() as monkeypatch:
        monkeypatch.setattr(mock_block_device, "initialized", False)
        entry = await init_integration(hass, 1)
        device = dr.async_entries_for_config_entry(device_registry, entry.entry_id)[0]

        triggers = await async_get_device_automations(
            hass, DeviceAutomationType.TRIGGER, device.id
        )
        triggers = [value for value in triggers if value["domain"] == DOMAIN]
        expect(triggers == unordered([])).to_be(True)


@test
async def get_triggers_for_invalid_device_id(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test error raised for invalid shelly device_id."""
    await init_integration(hass, 1)
    config_entry = await init_integration(hass, 1, data={}, skip_setup=True)
    invalid_device = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    _preload_strings_translations(hass, DOMAIN)

    async with expect_raises_async(
        InvalidDeviceAutomationConfig,
        match="not found while configuring device automation triggers",
    ):
        await async_get_device_automations(
            hass, DeviceAutomationType.TRIGGER, invalid_device.id
        )


@test
async def if_fires_on_click_event_block_device(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test for click_event trigger firing for block device."""
    entry = await init_integration(hass, 1)
    device = dr.async_entries_for_config_entry(device_registry, entry.entry_id)[0]

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: [
                    {
                        "trigger": {
                            CONF_PLATFORM: "device",
                            CONF_DOMAIN: DOMAIN,
                            CONF_DEVICE_ID: device.id,
                            CONF_TYPE: "single",
                            CONF_SUBTYPE: "button1",
                        },
                        "action": {
                            "service": "test.automation",
                            "data_template": {"some": "test_trigger_single_click"},
                        },
                    },
                ]
            },
        )
    ).to_be(True)

    message = {
        CONF_DEVICE_ID: device.id,
        ATTR_CLICK_TYPE: "single",
        ATTR_CHANNEL: 1,
    }
    hass.bus.async_fire(EVENT_SHELLY_CLICK, message)
    await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal("test_trigger_single_click")


@test
async def if_fires_on_click_event_rpc_device(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test for click_event trigger firing for rpc device."""
    entry = await init_integration(hass, 2)
    device = dr.async_entries_for_config_entry(device_registry, entry.entry_id)[0]

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: [
                    {
                        "trigger": {
                            CONF_PLATFORM: "device",
                            CONF_DOMAIN: DOMAIN,
                            CONF_DEVICE_ID: device.id,
                            CONF_TYPE: "single_push",
                            CONF_SUBTYPE: "button1",
                        },
                        "action": {
                            "service": "test.automation",
                            "data_template": {"some": "test_trigger_single_push"},
                        },
                    },
                ]
            },
        )
    ).to_be(True)

    message = {
        CONF_DEVICE_ID: device.id,
        ATTR_CLICK_TYPE: "single_push",
        ATTR_CHANNEL: 1,
    }
    hass.bus.async_fire(EVENT_SHELLY_CLICK, message)
    await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal("test_trigger_single_push")


@test
async def validate_trigger_block_device_not_ready(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test validate trigger config when block device is not ready."""
    with _patches() as monkeypatch:
        monkeypatch.setattr(mock_block_device, "initialized", False)
        entry = await init_integration(hass, 1)
        device = dr.async_entries_for_config_entry(device_registry, entry.entry_id)[0]

        expect(
            await async_setup_component(
                hass,
                automation.DOMAIN,
                {
                    automation.DOMAIN: [
                        {
                            "trigger": {
                                CONF_PLATFORM: "device",
                                CONF_DOMAIN: DOMAIN,
                                CONF_DEVICE_ID: device.id,
                                CONF_TYPE: "single",
                                CONF_SUBTYPE: "button1",
                            },
                            "action": {
                                "service": "test.automation",
                                "data_template": {
                                    "some": "test_trigger_single_click"
                                },
                            },
                        },
                    ]
                },
            )
        ).to_be(True)
        message = {
            CONF_DEVICE_ID: device.id,
            ATTR_CLICK_TYPE: "single",
            ATTR_CHANNEL: 1,
        }
        hass.bus.async_fire(EVENT_SHELLY_CLICK, message)
        await hass.async_block_till_done()

        expect(len(service_calls)).to_equal(1)
        expect(service_calls[0].data["some"]).to_equal("test_trigger_single_click")


@test
async def validate_trigger_rpc_device_not_ready(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test validate trigger config when RPC device is not ready."""
    with _patches() as monkeypatch:
        monkeypatch.setattr(mock_rpc_device, "initialized", False)
        entry = await init_integration(hass, 2)
        device = dr.async_entries_for_config_entry(device_registry, entry.entry_id)[0]

        expect(
            await async_setup_component(
                hass,
                automation.DOMAIN,
                {
                    automation.DOMAIN: [
                        {
                            "trigger": {
                                CONF_PLATFORM: "device",
                                CONF_DOMAIN: DOMAIN,
                                CONF_DEVICE_ID: device.id,
                                CONF_TYPE: "single_push",
                                CONF_SUBTYPE: "button1",
                            },
                            "action": {
                                "service": "test.automation",
                                "data_template": {
                                    "some": "test_trigger_single_push"
                                },
                            },
                        },
                    ]
                },
            )
        ).to_be(True)
        message = {
            CONF_DEVICE_ID: device.id,
            ATTR_CLICK_TYPE: "single_push",
            ATTR_CHANNEL: 1,
        }
        hass.bus.async_fire(EVENT_SHELLY_CLICK, message)
        await hass.async_block_till_done()

        expect(len(service_calls)).to_equal(1)
        expect(service_calls[0].data["some"]).to_equal("test_trigger_single_push")


@test
async def validate_trigger_invalid_triggers(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    caplog: Any = Depends(caplog_fixture),
) -> None:
    """Test for click_event with invalid triggers."""
    entry = await init_integration(hass, 1)
    device = dr.async_entries_for_config_entry(device_registry, entry.entry_id)[0]
    _preload_strings_translations(hass, DOMAIN)

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: [
                    {
                        "trigger": {
                            CONF_PLATFORM: "device",
                            CONF_DOMAIN: DOMAIN,
                            CONF_DEVICE_ID: device.id,
                            CONF_TYPE: "single",
                            CONF_SUBTYPE: "button3",
                        },
                        "action": {
                            "service": "test.automation",
                            "data_template": {"some": "test_trigger_single_click"},
                        },
                    },
                ]
            },
        )
    ).to_be(True)

    expect(
        "Invalid device automation trigger (type, subtype): ('single', 'button3')"
        in caplog.text
    ).to_be(True)


@test
async def rpc_no_runtime_data(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test device trigger for RPC device when there is no runtime_data in the entry."""
    entry = await init_integration(hass, 2)
    runtime_data = entry.runtime_data
    with _patches() as monkeypatch:
        monkeypatch.delattr(entry, "runtime_data")
        device = dr.async_entries_for_config_entry(device_registry, entry.entry_id)[0]

        expect(
            await async_setup_component(
                hass,
                automation.DOMAIN,
                {
                    automation.DOMAIN: [
                        {
                            "trigger": {
                                CONF_PLATFORM: "device",
                                CONF_DOMAIN: DOMAIN,
                                CONF_DEVICE_ID: device.id,
                                CONF_TYPE: "single_push",
                                CONF_SUBTYPE: "button1",
                            },
                            "action": {
                                "service": "test.automation",
                                "data_template": {
                                    "some": "test_trigger_single_push"
                                },
                            },
                        },
                    ]
                },
            )
        ).to_be(True)
        message = {
            CONF_DEVICE_ID: device.id,
            ATTR_CLICK_TYPE: "single_push",
            ATTR_CHANNEL: 1,
        }
        hass.bus.async_fire(EVENT_SHELLY_CLICK, message)
        await hass.async_block_till_done()

        expect(len(service_calls)).to_equal(1)
        expect(service_calls[0].data["some"]).to_equal("test_trigger_single_push")

    # Restore runtime_data to avoid issues on cleanup
    entry.runtime_data = runtime_data


@test
async def block_no_runtime_data(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test device trigger for block device when there is no runtime_data in the entry."""
    entry = await init_integration(hass, 1)
    runtime_data = entry.runtime_data
    with _patches() as monkeypatch:
        monkeypatch.delattr(entry, "runtime_data")
        device = dr.async_entries_for_config_entry(device_registry, entry.entry_id)[0]

        expect(
            await async_setup_component(
                hass,
                automation.DOMAIN,
                {
                    automation.DOMAIN: [
                        {
                            "trigger": {
                                CONF_PLATFORM: "device",
                                CONF_DOMAIN: DOMAIN,
                                CONF_DEVICE_ID: device.id,
                                CONF_TYPE: "single",
                                CONF_SUBTYPE: "button1",
                            },
                            "action": {
                                "service": "test.automation",
                                "data_template": {"some": "test_trigger_single"},
                            },
                        },
                    ]
                },
            )
        ).to_be(True)
        message = {
            CONF_DEVICE_ID: device.id,
            ATTR_CLICK_TYPE: "single",
            ATTR_CHANNEL: 1,
        }
        hass.bus.async_fire(EVENT_SHELLY_CLICK, message)
        await hass.async_block_till_done()

        expect(len(service_calls)).to_equal(1)
        expect(service_calls[0].data["some"]).to_equal("test_trigger_single")

    # Restore runtime_data to avoid issues on cleanup
    entry.runtime_data = runtime_data
