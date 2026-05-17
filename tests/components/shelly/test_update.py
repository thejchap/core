"""Tests for Shelly update platform (tryke port)."""

from collections.abc import Generator
from contextlib import contextmanager, suppress
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from aioshelly.exceptions import DeviceConnectionError, InvalidAuthError, RpcCallError
from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test

from homeassistant.components.shelly import (
    BLOCK_SLEEPING_PLATFORMS,
    PLATFORMS,
    RPC_SLEEPING_PLATFORMS,
)
from homeassistant.components.shelly.const import (
    DOMAIN,
    GEN1_RELEASE_URL,
    GEN2_BETA_RELEASE_URL,
    GEN2_RELEASE_URL,
)
from homeassistant.components.update import (
    ATTR_IN_PROGRESS,
    ATTR_INSTALLED_VERSION,
    ATTR_LATEST_VERSION,
    ATTR_RELEASE_URL,
    ATTR_UPDATE_PERCENTAGE,
    DOMAIN as UPDATE_DOMAIN,
    SERVICE_INSTALL,
    UpdateEntityFeature,
)
from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_SUPPORTED_FEATURES,
    STATE_OFF,
    STATE_ON,
    STATE_UNKNOWN,
    Platform,
)
from homeassistant.core import HomeAssistant, State
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceRegistry
from homeassistant.helpers.entity_registry import EntityRegistry

from tests.common import mock_restore_cache
from tests.components.shelly import (
    init_integration,
    inject_rpc_device_event,
    mock_rest_update,
    register_device,
    register_entity,
)
from tests.components.shelly._fixtures import (
    mock_block_device as mock_block_device_fixture,
    mock_bluetooth as mock_bluetooth_fixture,
    mock_coap as mock_coap_fixture,
    mock_rpc_device as mock_rpc_device_fixture,
    mock_ws_server as mock_ws_server_fixture,
)
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import (
    entity_registry_enabled_by_default as entity_registry_enabled_by_default_fixture,
    expect_raises_async,
)


_MISSING = object()


def _load_translations(hass: HomeAssistant) -> None:
    """Preload shelly + update strings.json into the translation cache.

    The dev tree lacks ``translations/en.json`` files, so the real translation
    loader returns no entity data. Seed the cache from ``strings.json`` so
    ``has_entity_name`` entities resolve to the expected entity IDs
    (e.g. ``update.test_name_firmware``).
    """
    import json  # noqa: PLC0415
    from pathlib import Path  # noqa: PLC0415

    from homeassistant.helpers import translation as translation_helper  # noqa: PLC0415

    cache = translation_helper._async_get_translations_cache(hass)
    components_root = Path(__file__).resolve().parents[3] / "homeassistant" / "components"
    for component in ("shelly", "update"):
        strings_path = components_root / component / "strings.json"
        data: dict = json.loads(strings_path.read_text())
        translation_data = {"en": {component: data}}
        cache._build_category_cache("en", {component}, translation_data["en"])
        cache.cache_data.loaded.setdefault("en", set()).add(component)


@contextmanager
def _patches() -> Generator[Any]:
    """Mimic pytest's monkeypatch for setattr/setitem."""

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

        def delitem(self, mapping: Any, key: Any) -> None:
            original = mapping.get(key, _MISSING)
            undo.append(("item", mapping, key, original))
            mapping.pop(key, None)

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


@contextmanager
def _patch_platforms(platforms: list[Platform]) -> Generator[None]:
    """Only allow given platforms to be loaded."""
    with (
        patch(
            "homeassistant.components.shelly.PLATFORMS",
            list(set(PLATFORMS) & set(platforms)),
        ),
        patch(
            "homeassistant.components.shelly.BLOCK_SLEEPING_PLATFORMS",
            list(set(BLOCK_SLEEPING_PLATFORMS) & set(platforms)),
        ),
        patch(
            "homeassistant.components.shelly.RPC_SLEEPING_PLATFORMS",
            list(set(RPC_SLEEPING_PLATFORMS) & set(platforms)),
        ),
    ):
        yield


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _coap: None = Depends(mock_coap_fixture),
    _ws: None = Depends(mock_ws_server_fixture),
    _bt: None = Depends(mock_bluetooth_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
) -> int:
    """Anchor fixture so async Depends() fixtures resolve under tryke."""
    _load_translations(hass)
    return 0


@fixture
def fixture_platforms() -> Generator[None]:
    """Limit platforms under test."""
    with _patch_platforms([Platform.UPDATE]):
        yield


@test
async def block_update(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    _enabled: Any = Depends(entity_registry_enabled_by_default_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test block device update entity."""
    entity_id = "update.test_name_firmware"
    with _patches() as monkeypatch:
        monkeypatch.setitem(mock_block_device.status["update"], "old_version", "1.0.0")
        monkeypatch.setitem(mock_block_device.status["update"], "new_version", "2.0.0")
        monkeypatch.setitem(mock_block_device.status, "cloud", {"connected": False})
        await init_integration(hass, 1)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes[ATTR_INSTALLED_VERSION]).to_equal("1.0.0")
        expect(state.attributes[ATTR_LATEST_VERSION]).to_equal("2.0.0")
        expect(state.attributes[ATTR_IN_PROGRESS]).to_equal(False)
        expect(state.attributes[ATTR_UPDATE_PERCENTAGE]).to_be_none()
        expect(state.attributes[ATTR_SUPPORTED_FEATURES]).to_equal(
            UpdateEntityFeature.INSTALL | UpdateEntityFeature.PROGRESS
        )

        await hass.services.async_call(
            UPDATE_DOMAIN,
            SERVICE_INSTALL,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        expect(mock_block_device.trigger_ota_update.call_count).to_equal(1)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes[ATTR_INSTALLED_VERSION]).to_equal("1.0.0")
        expect(state.attributes[ATTR_LATEST_VERSION]).to_equal("2.0.0")
        expect(state.attributes[ATTR_IN_PROGRESS]).to_equal(True)
        expect(state.attributes[ATTR_UPDATE_PERCENTAGE]).to_be_none()
        expect(state.attributes[ATTR_RELEASE_URL]).to_equal(GEN1_RELEASE_URL)

        monkeypatch.setitem(mock_block_device.status["update"], "old_version", "2.0.0")
        await mock_rest_update(hass, freezer)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)
        expect(state.attributes[ATTR_INSTALLED_VERSION]).to_equal("2.0.0")
        expect(state.attributes[ATTR_LATEST_VERSION]).to_equal("2.0.0")
        expect(state.attributes[ATTR_IN_PROGRESS]).to_equal(False)
        expect(state.attributes[ATTR_UPDATE_PERCENTAGE]).to_be_none()

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-fwupdate")


@test
async def block_beta_update(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    _enabled: Any = Depends(entity_registry_enabled_by_default_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test block device beta update entity."""
    entity_id = "update.test_name_beta_firmware"
    with _patches() as monkeypatch:
        monkeypatch.setitem(mock_block_device.status["update"], "old_version", "1.0.0")
        monkeypatch.setitem(mock_block_device.status["update"], "new_version", "2.0.0")
        monkeypatch.setitem(mock_block_device.status["update"], "beta_version", "")
        monkeypatch.setitem(mock_block_device.status, "cloud", {"connected": False})
        await init_integration(hass, 1)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)
        expect(state.attributes[ATTR_INSTALLED_VERSION]).to_equal("1.0.0")
        expect(state.attributes[ATTR_LATEST_VERSION]).to_equal("1.0.0")
        expect(state.attributes[ATTR_IN_PROGRESS]).to_equal(False)
        expect(state.attributes[ATTR_UPDATE_PERCENTAGE]).to_be_none()

        monkeypatch.setitem(
            mock_block_device.status["update"], "beta_version", "2.0.0-beta"
        )
        await mock_rest_update(hass, freezer)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes[ATTR_INSTALLED_VERSION]).to_equal("1.0.0")
        expect(state.attributes[ATTR_LATEST_VERSION]).to_equal("2.0.0-beta")
        expect(state.attributes[ATTR_IN_PROGRESS]).to_equal(False)
        expect(state.attributes[ATTR_UPDATE_PERCENTAGE]).to_be_none()
        expect(state.attributes[ATTR_RELEASE_URL]).to_be_none()

        await hass.services.async_call(
            UPDATE_DOMAIN,
            SERVICE_INSTALL,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        expect(mock_block_device.trigger_ota_update.call_count).to_equal(1)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes[ATTR_INSTALLED_VERSION]).to_equal("1.0.0")
        expect(state.attributes[ATTR_LATEST_VERSION]).to_equal("2.0.0-beta")
        expect(state.attributes[ATTR_IN_PROGRESS]).to_equal(True)
        expect(state.attributes[ATTR_UPDATE_PERCENTAGE]).to_be_none()

        monkeypatch.setitem(
            mock_block_device.status["update"], "old_version", "2.0.0-beta"
        )
        await mock_rest_update(hass, freezer)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)
        expect(state.attributes[ATTR_INSTALLED_VERSION]).to_equal("2.0.0-beta")
        expect(state.attributes[ATTR_LATEST_VERSION]).to_equal("2.0.0-beta")
        expect(state.attributes[ATTR_IN_PROGRESS]).to_equal(False)
        expect(state.attributes[ATTR_UPDATE_PERCENTAGE]).to_be_none()

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-fwupdate_beta")


@test
async def block_update_connection_error(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    _enabled: Any = Depends(entity_registry_enabled_by_default_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test block device update connection error."""
    with _patches() as monkeypatch:
        monkeypatch.setitem(mock_block_device.status["update"], "old_version", "1.0.0")
        monkeypatch.setitem(mock_block_device.status["update"], "new_version", "2.0.0")
        monkeypatch.setattr(
            mock_block_device,
            "trigger_ota_update",
            AsyncMock(side_effect=DeviceConnectionError),
        )
        await init_integration(hass, 1)

        async with expect_raises_async(
            HomeAssistantError,
            match=(
                "Device communication error occurred while "
                "triggering OTA update for Test name"
            ),
        ):
            await hass.services.async_call(
                UPDATE_DOMAIN,
                SERVICE_INSTALL,
                {ATTR_ENTITY_ID: "update.test_name_firmware"},
                blocking=True,
            )


@test
async def block_update_auth_error(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    _enabled: Any = Depends(entity_registry_enabled_by_default_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test block device update authentication error."""
    with _patches() as monkeypatch:
        monkeypatch.setitem(mock_block_device.status["update"], "old_version", "1.0.0")
        monkeypatch.setitem(mock_block_device.status["update"], "new_version", "2.0.0")
        monkeypatch.setattr(
            mock_block_device,
            "trigger_ota_update",
            AsyncMock(side_effect=InvalidAuthError),
        )
        entry = await init_integration(hass, 1)

        expect(entry.state).to_be(ConfigEntryState.LOADED)

        await hass.services.async_call(
            UPDATE_DOMAIN,
            SERVICE_INSTALL,
            {ATTR_ENTITY_ID: "update.test_name_firmware"},
            blocking=True,
        )

        expect(entry.state).to_be(ConfigEntryState.LOADED)

        flows = hass.config_entries.flow.async_progress()
        expect(len(flows)).to_equal(1)

        flow = flows[0]
        expect(flow.get("step_id")).to_equal("reauth_confirm")
        expect(flow.get("handler")).to_equal(DOMAIN)

        expect("context" in flow).to_equal(True)
        expect(flow["context"].get("source")).to_equal(SOURCE_REAUTH)
        expect(flow["context"].get("entry_id")).to_equal(entry.entry_id)


@test
async def block_version_compare(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    _enabled: Any = Depends(entity_registry_enabled_by_default_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test block device custom firmware version comparison."""

    STABLE = "20230913-111730/v1.14.0-gcb84623"
    BETA = "20231107-162609/v1.14.1-rc1-g0617c15"

    entity_id_beta = "update.test_name_beta_firmware"
    entity_id_latest = "update.test_name_firmware"
    with _patches() as monkeypatch:
        monkeypatch.setitem(mock_block_device.status["update"], "old_version", STABLE)
        monkeypatch.setitem(mock_block_device.status["update"], "new_version", "")
        monkeypatch.setitem(mock_block_device.status["update"], "beta_version", BETA)
        monkeypatch.setitem(mock_block_device.status, "cloud", {"connected": False})
        await init_integration(hass, 1)

        state = hass.states.get(entity_id_latest)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)
        expect(state.attributes[ATTR_INSTALLED_VERSION]).to_equal(STABLE)
        expect(state.attributes[ATTR_LATEST_VERSION]).to_equal(STABLE)

        state = hass.states.get(entity_id_beta)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes[ATTR_INSTALLED_VERSION]).to_equal(STABLE)
        expect(state.attributes[ATTR_LATEST_VERSION]).to_equal(BETA)

        monkeypatch.setitem(mock_block_device.status["update"], "old_version", BETA)
        monkeypatch.setitem(mock_block_device.status["update"], "new_version", STABLE)
        monkeypatch.setitem(mock_block_device.status["update"], "beta_version", BETA)
        await mock_rest_update(hass, freezer)

        state = hass.states.get(entity_id_latest)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)
        expect(state.attributes[ATTR_INSTALLED_VERSION]).to_equal(BETA)
        expect(state.attributes[ATTR_LATEST_VERSION]).to_equal(STABLE)

        state = hass.states.get(entity_id_beta)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)
        expect(state.attributes[ATTR_INSTALLED_VERSION]).to_equal(BETA)
        expect(state.attributes[ATTR_LATEST_VERSION]).to_equal(BETA)


@test
async def rpc_update(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test RPC device update entity."""
    entity_id = "update.test_name_firmware"
    with _patches() as monkeypatch:
        monkeypatch.setitem(mock_rpc_device.shelly, "ver", "1")
        monkeypatch.setitem(
            mock_rpc_device.status["sys"],
            "available_updates",
            {
                "stable": {"version": "2"},
            },
        )
        await init_integration(hass, 2)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes[ATTR_INSTALLED_VERSION]).to_equal("1")
        expect(state.attributes[ATTR_LATEST_VERSION]).to_equal("2")
        expect(state.attributes[ATTR_IN_PROGRESS]).to_equal(False)
        expect(state.attributes[ATTR_UPDATE_PERCENTAGE]).to_be_none()
        expect(state.attributes[ATTR_SUPPORTED_FEATURES]).to_equal(
            UpdateEntityFeature.INSTALL | UpdateEntityFeature.PROGRESS
        )

        await hass.services.async_call(
            UPDATE_DOMAIN,
            SERVICE_INSTALL,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

        expect(mock_rpc_device.trigger_ota_update.call_count).to_equal(1)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes[ATTR_INSTALLED_VERSION]).to_equal("1")
        expect(state.attributes[ATTR_LATEST_VERSION]).to_equal("2")
        expect(state.attributes[ATTR_IN_PROGRESS]).to_equal(True)
        expect(state.attributes[ATTR_UPDATE_PERCENTAGE]).to_be_none()
        expect(state.attributes[ATTR_RELEASE_URL]).to_equal(GEN2_RELEASE_URL)

        inject_rpc_device_event(
            monkeypatch,
            mock_rpc_device,
            {
                "events": [
                    {
                        "event": "ota_begin",
                        "id": 1,
                        "ts": 1668522399.2,
                    }
                ],
                "ts": 1668522399.2,
            },
        )

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.attributes[ATTR_IN_PROGRESS]).to_equal(True)
        expect(state.attributes[ATTR_UPDATE_PERCENTAGE]).to_equal(0)

        inject_rpc_device_event(
            monkeypatch,
            mock_rpc_device,
            {
                "events": [
                    {
                        "event": "ota_progress",
                        "id": 1,
                        "ts": 1668522399.2,
                        "progress_percent": 50,
                    }
                ],
                "ts": 1668522399.2,
            },
        )

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.attributes[ATTR_IN_PROGRESS]).to_equal(True)
        expect(state.attributes[ATTR_UPDATE_PERCENTAGE]).to_equal(50)

        inject_rpc_device_event(
            monkeypatch,
            mock_rpc_device,
            {
                "events": [
                    {
                        "event": "ota_success",
                        "id": 1,
                        "ts": 1668522399.2,
                    }
                ],
                "ts": 1668522399.2,
            },
        )
        monkeypatch.setitem(mock_rpc_device.shelly, "ver", "2")
        mock_rpc_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)
        expect(state.attributes[ATTR_INSTALLED_VERSION]).to_equal("2")
        expect(state.attributes[ATTR_LATEST_VERSION]).to_equal("2")
        expect(state.attributes[ATTR_IN_PROGRESS]).to_equal(False)
        expect(state.attributes[ATTR_UPDATE_PERCENTAGE]).to_be_none()

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-sys-fwupdate")


@test
async def rpc_sleeping_update(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test RPC sleeping device update entity."""
    with _patches() as monkeypatch:
        monkeypatch.setattr(mock_rpc_device, "connected", False)
        monkeypatch.setitem(mock_rpc_device.status["sys"], "wakeup_period", 1000)
        monkeypatch.setitem(mock_rpc_device.shelly, "ver", "1")
        monkeypatch.setitem(
            mock_rpc_device.status["sys"],
            "available_updates",
            {
                "stable": {"version": "2"},
            },
        )
        entity_id = f"{UPDATE_DOMAIN}.test_name_firmware"
        with patch.object(
            mock_rpc_device,
            "initialize",
            new_callable=AsyncMock,
            side_effect=DeviceConnectionError,
        ):
            await init_integration(hass, 2, sleep_period=1000)

        # Entity should be created when device is online
        expect(hass.states.get(entity_id)).to_be_none()

        # Make device online
        mock_rpc_device.mock_online()
        await hass.async_block_till_done(wait_background_tasks=True)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes[ATTR_INSTALLED_VERSION]).to_equal("1")
        expect(state.attributes[ATTR_LATEST_VERSION]).to_equal("2")
        expect(state.attributes[ATTR_IN_PROGRESS]).to_equal(False)
        expect(state.attributes[ATTR_UPDATE_PERCENTAGE]).to_be_none()
        expect(state.attributes[ATTR_SUPPORTED_FEATURES]).to_equal(
            UpdateEntityFeature(0)
        )
        expect(state.attributes[ATTR_RELEASE_URL]).to_equal(GEN2_RELEASE_URL)

        monkeypatch.setitem(mock_rpc_device.shelly, "ver", "2")
        mock_rpc_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)
        expect(state.attributes[ATTR_INSTALLED_VERSION]).to_equal("2")
        expect(state.attributes[ATTR_LATEST_VERSION]).to_equal("2")
        expect(state.attributes[ATTR_IN_PROGRESS]).to_equal(False)
        expect(state.attributes[ATTR_UPDATE_PERCENTAGE]).to_be_none()
        expect(state.attributes[ATTR_SUPPORTED_FEATURES]).to_equal(
            UpdateEntityFeature(0)
        )

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-sys-fwupdate")


@test
async def rpc_restored_sleeping_update(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test RPC restored update entity."""
    with _patches() as monkeypatch:
        entry = await init_integration(hass, 2, sleep_period=1000, skip_setup=True)
        device = register_device(device_registry, entry)
        entity_id = register_entity(
            hass,
            UPDATE_DOMAIN,
            "test_name_firmware",
            "sys-fwupdate",
            entry,
            device_id=device.id,
        )

        attr = {ATTR_INSTALLED_VERSION: "1", ATTR_LATEST_VERSION: "2"}
        mock_restore_cache(hass, [State(entity_id, STATE_ON, attributes=attr)])
        monkeypatch.setitem(mock_rpc_device.shelly, "ver", "2")
        monkeypatch.setitem(mock_rpc_device.status["sys"], "available_updates", {})
        monkeypatch.setattr(mock_rpc_device, "initialized", False)

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes[ATTR_INSTALLED_VERSION]).to_equal("1")
        expect(state.attributes[ATTR_LATEST_VERSION]).to_equal("2")
        expect(state.attributes[ATTR_IN_PROGRESS]).to_equal(False)
        expect(state.attributes[ATTR_UPDATE_PERCENTAGE]).to_be_none()
        expect(state.attributes[ATTR_SUPPORTED_FEATURES]).to_equal(
            UpdateEntityFeature(0)
        )

        # Make device online
        monkeypatch.setattr(mock_rpc_device, "initialized", True)
        mock_rpc_device.mock_online()
        await hass.async_block_till_done(wait_background_tasks=True)

        # Mock update
        mock_rpc_device.mock_update()
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)
        expect(state.attributes[ATTR_INSTALLED_VERSION]).to_equal("2")
        expect(state.attributes[ATTR_LATEST_VERSION]).to_equal("2")
        expect(state.attributes[ATTR_IN_PROGRESS]).to_equal(False)
        expect(state.attributes[ATTR_UPDATE_PERCENTAGE]).to_be_none()
        expect(state.attributes[ATTR_SUPPORTED_FEATURES]).to_equal(
            UpdateEntityFeature(0)
        )


@test
async def rpc_restored_sleeping_update_no_last_state(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test RPC restored update entity missing last state."""
    with _patches() as monkeypatch:
        monkeypatch.setitem(mock_rpc_device.shelly, "ver", "1")
        monkeypatch.setitem(
            mock_rpc_device.status["sys"],
            "available_updates",
            {
                "stable": {"version": "2"},
            },
        )
        entry = await init_integration(hass, 2, sleep_period=1000, skip_setup=True)
        device = register_device(device_registry, entry)
        entity_id = register_entity(
            hass,
            UPDATE_DOMAIN,
            "test_name_firmware",
            "sys-fwupdate",
            entry,
            device_id=device.id,
        )

        monkeypatch.setattr(mock_rpc_device, "initialized", False)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_UNKNOWN)

        # Make device online
        monkeypatch.setattr(mock_rpc_device, "initialized", True)
        mock_rpc_device.mock_online()
        await hass.async_block_till_done(wait_background_tasks=True)

        # Mock update
        mock_rpc_device.mock_update()
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes[ATTR_INSTALLED_VERSION]).to_equal("1")
        expect(state.attributes[ATTR_LATEST_VERSION]).to_equal("2")
        expect(state.attributes[ATTR_IN_PROGRESS]).to_equal(False)
        expect(state.attributes[ATTR_UPDATE_PERCENTAGE]).to_be_none()
        expect(state.attributes[ATTR_SUPPORTED_FEATURES]).to_equal(
            UpdateEntityFeature(0)
        )


@test
async def rpc_beta_update(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    _enabled: Any = Depends(entity_registry_enabled_by_default_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test RPC device beta update entity."""
    entity_id = "update.test_name_beta_firmware"
    with _patches() as monkeypatch:
        monkeypatch.setitem(mock_rpc_device.shelly, "ver", "1")
        monkeypatch.setitem(
            mock_rpc_device.status["sys"],
            "available_updates",
            {
                "stable": {"version": "2"},
                "beta": {"version": ""},
            },
        )
        await init_integration(hass, 2)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)
        expect(state.attributes[ATTR_INSTALLED_VERSION]).to_equal("1")
        expect(state.attributes[ATTR_LATEST_VERSION]).to_equal("1")
        expect(state.attributes[ATTR_IN_PROGRESS]).to_equal(False)
        expect(state.attributes[ATTR_UPDATE_PERCENTAGE]).to_be_none()

        monkeypatch.setitem(
            mock_rpc_device.status["sys"],
            "available_updates",
            {
                "stable": {"version": "2"},
                "beta": {"version": "2b"},
            },
        )
        await mock_rest_update(hass, freezer)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes[ATTR_INSTALLED_VERSION]).to_equal("1")
        expect(state.attributes[ATTR_LATEST_VERSION]).to_equal("2b")
        expect(state.attributes[ATTR_IN_PROGRESS]).to_equal(False)
        expect(state.attributes[ATTR_RELEASE_URL]).to_equal(GEN2_BETA_RELEASE_URL)

        await hass.services.async_call(
            UPDATE_DOMAIN,
            SERVICE_INSTALL,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        inject_rpc_device_event(
            monkeypatch,
            mock_rpc_device,
            {
                "events": [
                    {
                        "event": "ota_begin",
                        "id": 1,
                        "ts": 1668522399.2,
                    }
                ],
                "ts": 1668522399.2,
            },
        )

        expect(mock_rpc_device.trigger_ota_update.call_count).to_equal(1)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes[ATTR_INSTALLED_VERSION]).to_equal("1")
        expect(state.attributes[ATTR_LATEST_VERSION]).to_equal("2b")
        expect(state.attributes[ATTR_IN_PROGRESS]).to_equal(True)
        expect(state.attributes[ATTR_UPDATE_PERCENTAGE]).to_equal(0)

        inject_rpc_device_event(
            monkeypatch,
            mock_rpc_device,
            {
                "events": [
                    {
                        "event": "ota_progress",
                        "id": 1,
                        "ts": 1668522399.2,
                        "progress_percent": 40,
                    }
                ],
                "ts": 1668522399.2,
            },
        )

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.attributes[ATTR_IN_PROGRESS]).to_equal(True)
        expect(state.attributes[ATTR_UPDATE_PERCENTAGE]).to_equal(40)

        inject_rpc_device_event(
            monkeypatch,
            mock_rpc_device,
            {
                "events": [
                    {
                        "event": "ota_success",
                        "id": 1,
                        "ts": 1668522399.2,
                    }
                ],
                "ts": 1668522399.2,
            },
        )
        monkeypatch.setitem(mock_rpc_device.shelly, "ver", "2b")
        await mock_rest_update(hass, freezer)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)
        expect(state.attributes[ATTR_INSTALLED_VERSION]).to_equal("2b")
        expect(state.attributes[ATTR_LATEST_VERSION]).to_equal("2b")
        expect(state.attributes[ATTR_IN_PROGRESS]).to_equal(False)
        expect(state.attributes[ATTR_UPDATE_PERCENTAGE]).to_be_none()

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-sys-fwupdate_beta")


@test.cases(
    test.case(
        "device_connection_error",
        exc=DeviceConnectionError,
        error=(
            "Device communication error occurred while "
            "triggering OTA update for Test name"
        ),
    ),
    test.case(
        "rpc_call_error",
        exc=RpcCallError(-1, "error"),
        error=(
            "RPC call error occurred while triggering OTA update for Test name"
        ),
    ),
)
async def rpc_update_errors(
    exc: Exception,
    error: str,
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    _enabled: Any = Depends(entity_registry_enabled_by_default_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test RPC device update connection/call errors."""
    with _patches() as monkeypatch:
        monkeypatch.setitem(mock_rpc_device.shelly, "ver", "1")
        monkeypatch.setitem(
            mock_rpc_device.status["sys"],
            "available_updates",
            {
                "stable": {"version": "2"},
                "beta": {"version": ""},
            },
        )
        monkeypatch.setattr(
            mock_rpc_device, "trigger_ota_update", AsyncMock(side_effect=exc)
        )
        await init_integration(hass, 2)

        async with expect_raises_async(HomeAssistantError, match=error):
            await hass.services.async_call(
                UPDATE_DOMAIN,
                SERVICE_INSTALL,
                {ATTR_ENTITY_ID: "update.test_name_firmware"},
                blocking=True,
            )


@test
async def rpc_update_auth_error(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    _enabled: Any = Depends(entity_registry_enabled_by_default_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test RPC device update authentication error."""
    with _patches() as monkeypatch:
        monkeypatch.setitem(mock_rpc_device.shelly, "ver", "1")
        monkeypatch.setitem(
            mock_rpc_device.status["sys"],
            "available_updates",
            {
                "stable": {"version": "2"},
                "beta": {"version": ""},
            },
        )
        monkeypatch.setattr(
            mock_rpc_device,
            "trigger_ota_update",
            AsyncMock(side_effect=InvalidAuthError),
        )
        entry = await init_integration(hass, 2)

        expect(entry.state).to_be(ConfigEntryState.LOADED)

        await hass.services.async_call(
            UPDATE_DOMAIN,
            SERVICE_INSTALL,
            {ATTR_ENTITY_ID: "update.test_name_firmware"},
            blocking=True,
        )

        expect(entry.state).to_be(ConfigEntryState.LOADED)

        flows = hass.config_entries.flow.async_progress()
        expect(len(flows)).to_equal(1)

        flow = flows[0]
        expect(flow.get("step_id")).to_equal("reauth_confirm")
        expect(flow.get("handler")).to_equal(DOMAIN)

        expect("context" in flow).to_equal(True)
        expect(flow["context"].get("source")).to_equal(SOURCE_REAUTH)
        expect(flow["context"].get("entry_id")).to_equal(entry.entry_id)
