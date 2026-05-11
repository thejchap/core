"""Test Fully Kiosk Browser services."""

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.fully_kiosk.const import (
    ATTR_APPLICATION,
    ATTR_KEY,
    ATTR_URL,
    ATTR_VALUE,
    DOMAIN,
    SERVICE_LOAD_URL,
    SERVICE_SET_CONFIG,
    SERVICE_START_APPLICATION,
)
from homeassistant.const import ATTR_DEVICE_ID
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr

from ._fixtures import (
    init_integration as init_integration_fixture,
    mock_fully_kiosk as mock_fully_kiosk_fixture,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async


@test
def module_importable() -> None:
    """Smoke test: the fully_kiosk.services module imports cleanly."""
    from homeassistant.components.fully_kiosk import services  # noqa: PLC0415

    expect(services).not_.to_be(None)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def services(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    mock_fully_kiosk: MagicMock = Depends(mock_fully_kiosk_fixture),
    _init_integration: MockConfigEntry = Depends(init_integration_fixture),
) -> None:
    """Test the Fully Kiosk Browser services."""
    device_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, "abcdef-123456")}
    )

    expect(device_entry is not None).to_be(True)

    url = "https://example.com"
    await hass.services.async_call(
        DOMAIN,
        SERVICE_LOAD_URL,
        {ATTR_DEVICE_ID: [device_entry.id], ATTR_URL: url},
        blocking=True,
    )

    mock_fully_kiosk.loadUrl.assert_called_once_with(url)

    app = "de.ozerov.fully"
    await hass.services.async_call(
        DOMAIN,
        SERVICE_START_APPLICATION,
        {ATTR_DEVICE_ID: [device_entry.id], ATTR_APPLICATION: app},
        blocking=True,
    )

    mock_fully_kiosk.startApplication.assert_called_once_with(app)

    key = "test_key"
    value = "test_value"

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_CONFIG,
        {
            ATTR_DEVICE_ID: [device_entry.id],
            ATTR_KEY: key,
            ATTR_VALUE: value,
        },
        blocking=True,
    )

    mock_fully_kiosk.setConfigurationString.assert_called_once_with(key, value)

    key = "test_key"
    value = 1234

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_CONFIG,
        {
            ATTR_DEVICE_ID: [device_entry.id],
            ATTR_KEY: key,
            ATTR_VALUE: value,
        },
        blocking=True,
    )

    mock_fully_kiosk.setConfigurationString.assert_called_with(key, str(value))

    key = "test_key"
    value = "true"
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_CONFIG,
        {
            ATTR_DEVICE_ID: [device_entry.id],
            ATTR_KEY: key,
            ATTR_VALUE: value,
        },
        blocking=True,
    )

    mock_fully_kiosk.setConfigurationBool.assert_called_once_with(key, value)

    key = "test_key"
    value = True
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_CONFIG,
        {
            ATTR_DEVICE_ID: [device_entry.id],
            ATTR_KEY: key,
            ATTR_VALUE: value,
        },
        blocking=True,
    )

    mock_fully_kiosk.setConfigurationBool.assert_called_with(key, value)


@test
async def service_unloaded_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    mock_fully_kiosk: MagicMock = Depends(mock_fully_kiosk_fixture),
    init_integration: MockConfigEntry = Depends(init_integration_fixture),
) -> None:
    """Test service not called when config entry unloaded."""
    await hass.config_entries.async_unload(init_integration.entry_id)

    device_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, "abcdef-123456")}
    )

    expect(device_entry is not None).to_be(True)

    async with expect_raises_async(HomeAssistantError, match="Test device is not loaded"):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_LOAD_URL,
            {ATTR_DEVICE_ID: [device_entry.id], ATTR_URL: "https://nabucasa.com"},
            blocking=True,
        )
    mock_fully_kiosk.loadUrl.assert_not_called()

    async with expect_raises_async(HomeAssistantError, match="Test device is not loaded"):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_START_APPLICATION,
            {ATTR_DEVICE_ID: [device_entry.id], ATTR_APPLICATION: "de.ozerov.fully"},
            blocking=True,
        )
    mock_fully_kiosk.startApplication.assert_not_called()


@test
async def service_bad_device_id(
    hass: HomeAssistant = Depends(_trigger_executor),
    _mock_fully_kiosk: MagicMock = Depends(mock_fully_kiosk_fixture),
    _init_integration: MockConfigEntry = Depends(init_integration_fixture),
) -> None:
    """Test Fully Kiosk Browser service invocation with bad device id."""
    async with expect_raises_async(
        HomeAssistantError, match="Device 'bad-device_id' not found in device registry"
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_LOAD_URL,
            {ATTR_DEVICE_ID: ["bad-device_id"], ATTR_URL: "https://example.com"},
            blocking=True,
        )


@test
async def service_called_with_non_fkb_target_devices(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    _mock_fully_kiosk: MagicMock = Depends(mock_fully_kiosk_fixture),
    _init_integration: MockConfigEntry = Depends(init_integration_fixture),
) -> None:
    """Services raise exception when no valid devices provided."""
    other_domain = "NotFullyKiosk"
    other_config_id = "555"
    other_mock_config_entry = MockConfigEntry(
        title="Not Fully Kiosk", domain=other_domain, entry_id=other_config_id
    )
    other_mock_config_entry.add_to_hass(hass)

    device_entry = device_registry.async_get_or_create(
        config_entry_id=other_config_id,
        identifiers={
            (other_domain, 1),
        },
    )

    async with expect_raises_async(
        HomeAssistantError,
        match=f"Device '{device_entry.id}' is not a fully_kiosk device",
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_LOAD_URL,
            {
                ATTR_DEVICE_ID: [device_entry.id],
                ATTR_URL: "https://example.com",
            },
            blocking=True,
        )
