"""Tests for Fritz!Tools services."""

from unittest.mock import MagicMock, patch

from fritzconnection.core.exceptions import (
    FritzActionFailedError,
    FritzConnectionException,
    FritzServiceError,
)
from fritzconnection.lib.fritzhosts import FritzHosts
from fritzconnection.lib.fritzstatus import FritzStatus
from tryke import Depends, expect, fixture, test
from voluptuous import MultipleInvalid

from homeassistant.components.fritz.const import DOMAIN
from homeassistant.components.fritz.services import (
    SERVICE_DIAL,
    SERVICE_SET_GUEST_WIFI_PW,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.setup import async_setup_component

from ._fixtures import (  # noqa: F401
    fc_class_mock,
    fc_data,
    fh_class_mock,
    fs_class_mock,
)
from .const import MOCK_SERIAL_NUMBER, MOCK_USER_DATA

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fx,
    device_registry as device_registry_fx,
    hass as hass_fx,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
    return 0


@test
async def setup_services(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Test setup of Fritz!Tools services."""
    expect(await async_setup_component(hass, DOMAIN, {})).to_be_truthy()
    await hass.async_block_till_done()

    services = hass.services.async_services_for_domain(DOMAIN)
    expect(services).to_be_truthy()
    expect(SERVICE_SET_GUEST_WIFI_PW in services).to_be(True)
    expect(SERVICE_DIAL in services).to_be(True)


@test
async def service_set_guest_wifi_password(
    hass: HomeAssistant = Depends(hass_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    caplog: LogCapture = Depends(caplog_fx),
    fc_class_mock: MagicMock = Depends(fc_class_mock),
    fh_class_mock: type[FritzHosts] = Depends(fh_class_mock),
) -> None:
    """Test service set_guest_wifi_password."""
    expect(await async_setup_component(hass, DOMAIN, {})).to_be_truthy()
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_DATA)
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    device = device_registry.async_get_device(
        identifiers={(DOMAIN, MOCK_SERIAL_NUMBER)}
    )
    expect(device).to_be_truthy()
    with patch(
        "homeassistant.components.fritz.coordinator.AvmWrapper.async_trigger_set_guest_password"
    ) as mock_async_trigger_set_guest_password:
        await hass.services.async_call(
            DOMAIN, SERVICE_SET_GUEST_WIFI_PW, {"device_id": device.id}
        )
        expect(mock_async_trigger_set_guest_password.called).to_be(True)


@test
async def service_set_guest_wifi_password_unknown_parameter(
    hass: HomeAssistant = Depends(hass_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    caplog: LogCapture = Depends(caplog_fx),
    fc_class_mock: MagicMock = Depends(fc_class_mock),
    fh_class_mock: type[FritzHosts] = Depends(fh_class_mock),
    fs_class_mock: type[FritzStatus] = Depends(fs_class_mock),
) -> None:
    """Test service set_guest_wifi_password with unknown parameter."""
    expect(await async_setup_component(hass, DOMAIN, {})).to_be_truthy()
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_DATA)
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    device = device_registry.async_get_device(
        identifiers={(DOMAIN, MOCK_SERIAL_NUMBER)}
    )
    expect(device).to_be_truthy()

    with patch(
        "homeassistant.components.fritz.coordinator.AvmWrapper.async_trigger_set_guest_password",
        side_effect=FritzServiceError("boom"),
    ) as mock_async_trigger_set_guest_password:
        await hass.services.async_call(
            DOMAIN, SERVICE_SET_GUEST_WIFI_PW, {"device_id": device.id}
        )
        await hass.async_block_till_done()
        expect(mock_async_trigger_set_guest_password.called).to_be(True)
        expect("HomeAssistantError: Action or parameter unknown" in caplog.text).to_be(
            True
        )


@test
async def service_set_guest_wifi_password_service_not_supported(
    hass: HomeAssistant = Depends(hass_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    caplog: LogCapture = Depends(caplog_fx),
    fc_class_mock: MagicMock = Depends(fc_class_mock),
    fh_class_mock: type[FritzHosts] = Depends(fh_class_mock),
    fs_class_mock: type[FritzStatus] = Depends(fs_class_mock),
) -> None:
    """Test service set_guest_wifi_password with connection error."""
    expect(await async_setup_component(hass, DOMAIN, {})).to_be_truthy()
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_DATA)
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    device = device_registry.async_get_device(
        identifiers={(DOMAIN, MOCK_SERIAL_NUMBER)}
    )
    expect(device).to_be_truthy()

    with patch(
        "homeassistant.components.fritz.coordinator.AvmWrapper.async_trigger_set_guest_password",
        side_effect=FritzConnectionException("boom"),
    ) as mock_async_trigger_set_guest_password:
        await hass.services.async_call(
            DOMAIN, SERVICE_SET_GUEST_WIFI_PW, {"device_id": device.id}
        )
        await hass.async_block_till_done()
        expect(mock_async_trigger_set_guest_password.called).to_be(True)
        expect("HomeAssistantError: Action not supported" in caplog.text).to_be(True)


@test
async def service_set_guest_wifi_password_unloaded(
    hass: HomeAssistant = Depends(hass_fx),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test service set_guest_wifi_password."""
    expect(await async_setup_component(hass, DOMAIN, {})).to_be_truthy()
    await hass.async_block_till_done()

    with patch(
        "homeassistant.components.fritz.coordinator.AvmWrapper.async_trigger_set_guest_password"
    ) as mock_async_trigger_set_guest_password:
        await hass.services.async_call(
            DOMAIN, SERVICE_SET_GUEST_WIFI_PW, {"device_id": "12345678"}
        )
        await hass.async_block_till_done()
        expect(mock_async_trigger_set_guest_password.called).to_be(False)
        expect(
            'ServiceValidationError: Failed to perform action "set_guest_wifi_password". Config entry for target not found'
            in caplog.text
        ).to_be(True)


@test
async def service_dial(
    hass: HomeAssistant = Depends(hass_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    caplog: LogCapture = Depends(caplog_fx),
    fc_class_mock: MagicMock = Depends(fc_class_mock),
    fh_class_mock: type[FritzHosts] = Depends(fh_class_mock),
    fs_class_mock: type[FritzStatus] = Depends(fs_class_mock),
) -> None:
    """Test service dial."""
    expect(await async_setup_component(hass, DOMAIN, {})).to_be_truthy()
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_DATA)
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    device = device_registry.async_get_device(
        identifiers={(DOMAIN, MOCK_SERIAL_NUMBER)}
    )
    expect(device).to_be_truthy()
    with patch(
        "homeassistant.components.fritz.coordinator.AvmWrapper.async_trigger_dial"
    ) as mock_async_trigger_dial:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_DIAL,
            {"device_id": device.id, "number": "1234567890", "max_ring_seconds": 10},
        )
        expect(mock_async_trigger_dial.called).to_be(True)
        expect(mock_async_trigger_dial.call_args.kwargs).to_equal(
            {"max_ring_seconds": 10}
        )
        expect(mock_async_trigger_dial.call_args.args).to_equal(("1234567890",))


@test
async def service_dial_unknown_parameter(
    hass: HomeAssistant = Depends(hass_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    caplog: LogCapture = Depends(caplog_fx),
    fc_class_mock: MagicMock = Depends(fc_class_mock),
    fh_class_mock: type[FritzHosts] = Depends(fh_class_mock),
    fs_class_mock: type[FritzStatus] = Depends(fs_class_mock),
) -> None:
    """Test service dial with unknown parameters."""
    expect(await async_setup_component(hass, DOMAIN, {})).to_be_truthy()
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_DATA)
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    device = device_registry.async_get_device(
        identifiers={(DOMAIN, MOCK_SERIAL_NUMBER)}
    )
    expect(device).to_be_truthy()

    with patch(
        "homeassistant.components.fritz.coordinator.AvmWrapper.async_trigger_dial",
        side_effect=FritzServiceError("boom"),
    ) as mock_async_trigger_dial:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_DIAL,
            {"device_id": device.id, "number": "1234567890", "max_ring_seconds": 10},
        )
        await hass.async_block_till_done()
        expect(mock_async_trigger_dial.called).to_be(True)
        expect("HomeAssistantError: Action or parameter unknown" in caplog.text).to_be(
            True
        )


@test
async def service_dial_wrong_parameter(
    hass: HomeAssistant = Depends(hass_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    caplog: LogCapture = Depends(caplog_fx),
    fc_class_mock: MagicMock = Depends(fc_class_mock),
    fh_class_mock: type[FritzHosts] = Depends(fh_class_mock),
    fs_class_mock: type[FritzStatus] = Depends(fs_class_mock),
) -> None:
    """Test service dial with unknown parameters."""
    expect(await async_setup_component(hass, DOMAIN, {})).to_be_truthy()
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_DATA)
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    device = device_registry.async_get_device(
        identifiers={(DOMAIN, MOCK_SERIAL_NUMBER)}
    )
    expect(device).to_be_truthy()

    with patch(
        "homeassistant.components.fritz.coordinator.AvmWrapper.async_trigger_dial",
    ) as mock_async_trigger_dial:
        async with expect_raises_async(MultipleInvalid):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_DIAL,
                {
                    "device_id": device.id,
                    "number": "1234567890",
                    "max_ring_seconds": "",
                },
            )
        expect(mock_async_trigger_dial.called).to_be(False)
    with patch(
        "homeassistant.components.fritz.coordinator.AvmWrapper.async_trigger_dial",
    ) as mock_async_trigger_dial:
        async with expect_raises_async(MultipleInvalid):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_DIAL,
                {
                    "device_id": device.id,
                    "number": "1234567890",
                    "max_ring_seconds": 0,
                },
            )
        expect(mock_async_trigger_dial.called).to_be(False)


@test
async def service_dial_service_not_supported(
    hass: HomeAssistant = Depends(hass_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    caplog: LogCapture = Depends(caplog_fx),
    fc_class_mock: MagicMock = Depends(fc_class_mock),
    fh_class_mock: type[FritzHosts] = Depends(fh_class_mock),
    fs_class_mock: type[FritzStatus] = Depends(fs_class_mock),
) -> None:
    """Test service dial with connection error."""
    expect(await async_setup_component(hass, DOMAIN, {})).to_be_truthy()
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_DATA)
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    device = device_registry.async_get_device(
        identifiers={(DOMAIN, MOCK_SERIAL_NUMBER)}
    )
    expect(device).to_be_truthy()

    with patch(
        "homeassistant.components.fritz.coordinator.AvmWrapper.async_trigger_dial",
        side_effect=FritzConnectionException("boom"),
    ) as mock_async_trigger_dial:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_DIAL,
            {"device_id": device.id, "number": "1234567890", "max_ring_seconds": 10},
        )
        await hass.async_block_till_done()
        expect(mock_async_trigger_dial.called).to_be(True)
        expect("HomeAssistantError: Action not supported" in caplog.text).to_be(True)


@test
async def service_dial_failed(
    hass: HomeAssistant = Depends(hass_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    caplog: LogCapture = Depends(caplog_fx),
    fc_class_mock: MagicMock = Depends(fc_class_mock),
    fh_class_mock: type[FritzHosts] = Depends(fh_class_mock),
    fs_class_mock: type[FritzStatus] = Depends(fs_class_mock),
) -> None:
    """Test dial service when the dial help is disabled."""
    expect(await async_setup_component(hass, DOMAIN, {})).to_be_truthy()
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_DATA)
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    device = device_registry.async_get_device(
        identifiers={(DOMAIN, MOCK_SERIAL_NUMBER)}
    )
    expect(device).to_be_truthy()

    with patch(
        "homeassistant.components.fritz.coordinator.AvmWrapper.async_trigger_dial",
        side_effect=FritzActionFailedError("boom"),
    ) as mock_async_trigger_dial:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_DIAL,
            {"device_id": device.id, "number": "1234567890", "max_ring_seconds": 10},
        )
        await hass.async_block_till_done()
        expect(mock_async_trigger_dial.called).to_be(True)
        expect(
            "HomeAssistantError: Failed to dial, check if the click to dial service of the FRITZ!Box is activated"
            in caplog.text
        ).to_be(True)


@test
async def service_dial_unloaded(
    hass: HomeAssistant = Depends(hass_fx),
    caplog: LogCapture = Depends(caplog_fx),
    fs_class_mock: type[FritzStatus] = Depends(fs_class_mock),
) -> None:
    """Test service dial."""
    expect(await async_setup_component(hass, DOMAIN, {})).to_be_truthy()
    await hass.async_block_till_done()

    with patch(
        "homeassistant.components.fritz.coordinator.AvmWrapper.async_trigger_dial"
    ) as mock_async_trigger_dial:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_DIAL,
            {"device_id": "12345678", "number": "1234567890", "max_ring_seconds": 10},
        )
        await hass.async_block_till_done()
        expect(mock_async_trigger_dial.called).to_be(False)
        expect(
            f'ServiceValidationError: Failed to perform action "{SERVICE_DIAL}". Config entry for target not found'
            in caplog.text
        ).to_be(True)
