"""Tests for Shelly services (tryke port)."""

from collections.abc import Generator
from contextlib import contextmanager, suppress
from typing import Any
from unittest.mock import Mock

from aioshelly.exceptions import DeviceConnectionError, RpcCallError
from tryke import Depends, expect, fixture, test

from homeassistant.components.shelly.const import ATTR_KEY, ATTR_VALUE, DOMAIN
from homeassistant.components.shelly.services import (
    SERVICE_GET_KVS_VALUE,
    SERVICE_SET_KVS_VALUE,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_DEVICE_ID
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import device_registry as dr

from tests.common import MockConfigEntry
from tests.components.shelly import init_integration
from tests.components.shelly._fixtures import (
    mock_block_device as mock_block_device_fixture,
    mock_rpc_device as mock_rpc_device_fixture,
)
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    hass as hass_fixture,
    mock_network,
)
_MISSING = object()


@contextmanager
def _patches() -> Generator[Any]:
    """Mimic pytest's monkeypatch for setattr/delattr."""

    undo: list[Any] = []

    class _Patcher:
        def setattr(self, target: Any, name: str, value: Any) -> None:
            original = getattr(target, name, _MISSING)
            undo.append(("attr", target, name, original))
            setattr(target, name, value)

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


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Anchor fixture so async Depends() fixtures resolve under tryke."""
    return 0


@test
async def service_get_kvs_value(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test get_kvs_value service."""
    entry = await init_integration(hass, 2)

    device = dr.async_entries_for_config_entry(device_registry, entry.entry_id)[0]

    mock_rpc_device.kvs_get.return_value = {
        "etag": "16mLia9TRt8lGhj9Zf5Dp6Hw==",
        "value": "test_value",
    }

    response = await hass.services.async_call(
        DOMAIN,
        SERVICE_GET_KVS_VALUE,
        {ATTR_DEVICE_ID: device.id, ATTR_KEY: "test_key"},
        blocking=True,
        return_response=True,
    )

    expect(response).to_equal({"value": "test_value"})
    mock_rpc_device.kvs_get.assert_called_once_with("test_key")


@test
async def service_get_kvs_value_invalid_device(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test get_kvs_value service with invalid device ID."""
    await init_integration(hass, 2)

    raised: ServiceValidationError | None = None
    try:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_GET_KVS_VALUE,
            {ATTR_DEVICE_ID: "invalid_device_id", ATTR_KEY: "test_key"},
            blocking=True,
            return_response=True,
        )
    except ServiceValidationError as exc:
        raised = exc

    expect(raised).to_be_truthy()
    expect(raised.translation_domain).to_equal(DOMAIN)
    expect(raised.translation_key).to_equal("invalid_device_id")
    expect(raised.translation_placeholders).to_equal(
        {ATTR_DEVICE_ID: "invalid_device_id"}
    )


@test
async def service_get_kvs_value_block_device(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test get_kvs_value service with non-RPC (Gen1) device."""
    entry = await init_integration(hass, 1)

    device = dr.async_entries_for_config_entry(device_registry, entry.entry_id)[0]

    raised: ServiceValidationError | None = None
    try:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_GET_KVS_VALUE,
            {ATTR_DEVICE_ID: device.id, ATTR_KEY: "test_key"},
            blocking=True,
            return_response=True,
        )
    except ServiceValidationError as exc:
        raised = exc

    expect(raised).to_be_truthy()
    expect(raised.translation_domain).to_equal(DOMAIN)
    expect(raised.translation_key).to_equal("kvs_not_supported")
    expect(raised.translation_placeholders).to_equal({"device": entry.title})


@test.cases(
    test.case("rpc_call_error", exc=RpcCallError(999), translation_key="rpc_call_error"),
    test.case(
        "device_connection_error",
        exc=DeviceConnectionError,
        translation_key="device_communication_error",
    ),
)
async def service_get_kvs_value_exc(
    exc: Exception,
    translation_key: str,
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test get_kvs_value service with exception."""
    entry = await init_integration(hass, 2)

    device = dr.async_entries_for_config_entry(device_registry, entry.entry_id)[0]

    mock_rpc_device.kvs_get.side_effect = exc

    raised: HomeAssistantError | None = None
    try:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_GET_KVS_VALUE,
            {ATTR_DEVICE_ID: device.id, ATTR_KEY: "test_key"},
            blocking=True,
            return_response=True,
        )
    except HomeAssistantError as caught:
        raised = caught

    expect(raised).to_be_truthy()
    expect(raised.translation_domain).to_equal(DOMAIN)
    expect(raised.translation_key).to_equal(translation_key)
    expect(raised.translation_placeholders).to_equal({"device": entry.title})


@test
async def config_entry_not_loaded(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test config entry not loaded."""
    entry = await init_integration(hass, 2)

    device = dr.async_entries_for_config_entry(device_registry, entry.entry_id)[0]

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state is ConfigEntryState.NOT_LOADED).to_be_truthy()

    raised: ServiceValidationError | None = None
    try:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_GET_KVS_VALUE,
            {ATTR_DEVICE_ID: device.id, ATTR_KEY: "test_key"},
            blocking=True,
            return_response=True,
        )
    except ServiceValidationError as exc:
        raised = exc

    expect(raised).to_be_truthy()
    expect(raised.translation_domain).to_equal(DOMAIN)
    expect(raised.translation_key).to_equal("entry_not_loaded")
    expect(raised.translation_placeholders).to_equal({"device": entry.title})


@test
async def service_get_kvs_value_sleeping_device(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test get_kvs_value service with RPC sleeping device."""
    entry = await init_integration(hass, 2, sleep_period=1000)

    mock_rpc_device.mock_online()
    await hass.async_block_till_done(wait_background_tasks=True)

    device = dr.async_entries_for_config_entry(device_registry, entry.entry_id)[0]

    raised: ServiceValidationError | None = None
    try:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_GET_KVS_VALUE,
            {ATTR_DEVICE_ID: device.id, ATTR_KEY: "test_key"},
            blocking=True,
            return_response=True,
        )
    except ServiceValidationError as exc:
        raised = exc

    expect(raised).to_be_truthy()
    expect(raised.translation_domain).to_equal(DOMAIN)
    expect(raised.translation_key).to_equal("kvs_not_supported")
    expect(raised.translation_placeholders).to_equal({"device": entry.title})


@test
async def service_set_kvs_value(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test set_kvs_value service."""
    entry = await init_integration(hass, 2)

    device = dr.async_entries_for_config_entry(device_registry, entry.entry_id)[0]

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_KVS_VALUE,
        {ATTR_DEVICE_ID: device.id, ATTR_KEY: "test_key", ATTR_VALUE: "test_value"},
        blocking=True,
    )

    mock_rpc_device.kvs_set.assert_called_once_with("test_key", "test_value")


@test
async def service_get_kvs_value_config_entry_not_found(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test device with no config entries."""
    entry = await init_integration(hass, 2)

    device = dr.async_entries_for_config_entry(device_registry, entry.entry_id)[0]

    device_registry.devices[device.id].config_entries.clear()

    raised: ServiceValidationError | None = None
    try:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_GET_KVS_VALUE,
            {ATTR_DEVICE_ID: device.id, ATTR_KEY: "test_key"},
            blocking=True,
            return_response=True,
        )
    except ServiceValidationError as exc:
        raised = exc

    expect(raised).to_be_truthy()
    expect(raised.translation_domain).to_equal(DOMAIN)
    expect(raised.translation_key).to_equal("config_entry_not_found")
    expect(raised.translation_placeholders).to_equal({"device_id": device.id})


@test
async def service_get_kvs_value_device_not_initialized(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test get_kvs_value if runtime_data.rpc is None."""
    entry = await init_integration(hass, 2)

    device = dr.async_entries_for_config_entry(device_registry, entry.entry_id)[0]

    with _patches() as monkeypatch:
        monkeypatch.delattr(entry.runtime_data, "rpc")

        raised: ServiceValidationError | None = None
        try:
            await hass.services.async_call(
                DOMAIN,
                SERVICE_GET_KVS_VALUE,
                {ATTR_DEVICE_ID: device.id, ATTR_KEY: "test_key"},
                blocking=True,
                return_response=True,
            )
        except ServiceValidationError as exc:
            raised = exc

        expect(raised).to_be_truthy()
        expect(raised.translation_domain).to_equal(DOMAIN)
        expect(raised.translation_key).to_equal("device_not_initialized")
        expect(raised.translation_placeholders).to_equal({"device": entry.title})


@test
async def service_get_kvs_value_wrong_domain(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test get_kvs_value when device has config entries from different domains."""
    entry = await init_integration(hass, 2)

    device = dr.async_entries_for_config_entry(device_registry, entry.entry_id)[0]

    other_entry = MockConfigEntry(
        domain="other_domain",
        data={},
    )
    other_entry.add_to_hass(hass)

    device_registry.async_update_device(
        device.id, add_config_entry_id=other_entry.entry_id
    )

    device_registry.async_update_device(
        device.id, remove_config_entry_id=entry.entry_id
    )

    raised: ServiceValidationError | None = None
    try:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_GET_KVS_VALUE,
            {ATTR_DEVICE_ID: device.id, ATTR_KEY: "test_key"},
            blocking=True,
            return_response=True,
        )
    except ServiceValidationError as exc:
        raised = exc

    expect(raised).to_be_truthy()
    expect(raised.translation_domain).to_equal(DOMAIN)
    expect(raised.translation_key).to_equal("config_entry_not_found")
    expect(raised.translation_placeholders).to_equal({"device_id": device.id})
