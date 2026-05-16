"""Test the victron_gx init."""

from unittest.mock import MagicMock, patch

from tryke import Depends, expect, fixture, test
from victron_mqtt import (
    AuthenticationError,
    CannotConnectError,
    Hub as VictronVenusHub,
    MetricKind,
)
from victron_mqtt.testing import finalize_injection, inject_message

from homeassistant.components.victron_gx import async_remove_config_entry_device
from homeassistant.components.victron_gx.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from ._fixtures import (
    init_integration as init_integration_fx,
    mock_config_entry as mock_config_entry_fx,
    mock_victron_hub_library as mock_victron_hub_library_fx,
)
from .const import MOCK_INSTALLATION_ID

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    device_registry as device_registry_fx,
    hass as hass_fx,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
    return 0


@test
async def load_unload_entry(
    hass: HomeAssistant = Depends(hass_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    _hub_lib: MagicMock = Depends(mock_victron_hub_library_fx),
) -> None:
    """Test unload entry."""
    mock_config_entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(mock_config_entry.entry_id)).to_be(
        True
    )
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(mock_config_entry.entry_id)).to_be(
        True
    )
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def unload_entry_does_not_cleanup_on_platform_unload_failure(
    hass: HomeAssistant = Depends(hass_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    _hub_lib: MagicMock = Depends(mock_victron_hub_library_fx),
) -> None:
    """Test unload failure does not stop hub or clear callbacks."""
    mock_config_entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(mock_config_entry.entry_id)).to_be(
        True
    )
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)
    mock_config_entry.runtime_data.new_metric_callbacks[MetricKind.SENSOR] = MagicMock()
    hub_disconnect = mock_config_entry.runtime_data._hub.disconnect

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_unload_platforms",
        return_value=False,
    ):
        expect(
            await hass.config_entries.async_unload(mock_config_entry.entry_id)
        ).to_be(False)
        await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.FAILED_UNLOAD)
    hub_disconnect.assert_not_awaited()


@test
async def stop_on_homeassistant_stop(
    hass: HomeAssistant = Depends(hass_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    _hub_lib: MagicMock = Depends(mock_victron_hub_library_fx),
) -> None:
    """Test hub stops when Home Assistant stops."""
    mock_config_entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(mock_config_entry.entry_id)).to_be(
        True
    )
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)
    hub_disconnect = mock_config_entry.runtime_data._hub.disconnect
    hub_disconnect.assert_not_awaited()

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()

    hub_disconnect.assert_awaited_once()


@test.cases(
    test.case(
        "cannot_connect",
        connect_exception=CannotConnectError("Connection failed"),
        expected_state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "auth_error",
        connect_exception=AuthenticationError("Auth failed"),
        expected_state=ConfigEntryState.SETUP_ERROR,
    ),
)
async def setup_entry_start_failure_unloads_platforms_and_callbacks(
    connect_exception: Exception,
    expected_state: ConfigEntryState,
    hass: HomeAssistant = Depends(hass_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    mock_victron_hub_library: MagicMock = Depends(mock_victron_hub_library_fx),
) -> None:
    """Test setup cleanup when hub start fails after platform forwarding."""
    mock_config_entry.add_to_hass(hass)
    mock_victron_hub_library.return_value.connect.side_effect = connect_exception

    expect(await hass.config_entries.async_setup(mock_config_entry.entry_id)).to_be(
        False
    )
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(expected_state)
    expect(mock_config_entry.runtime_data.new_metric_callbacks).to_equal({})


@test
async def hub_start_connection_error(
    hass: HomeAssistant = Depends(hass_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    mock_victron_hub_library: MagicMock = Depends(mock_victron_hub_library_fx),
) -> None:
    """Test hub start with connection error."""
    mock_config_entry.add_to_hass(hass)

    mock_victron_hub_library.return_value.connect.side_effect = CannotConnectError(
        "Connection failed"
    )

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def hub_start_success(
    init_integration: tuple[VictronVenusHub, MockConfigEntry] = Depends(
        init_integration_fx
    ),
) -> None:
    """Test successful hub start."""
    victron_hub, mock_config_entry = init_integration

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(victron_hub.installation_id).to_equal(MOCK_INSTALLATION_ID)


@test
async def child_device_via_device_links_to_parent_in_registry(
    hass: HomeAssistant = Depends(hass_fx),
    init_integration: tuple[VictronVenusHub, MockConfigEntry] = Depends(
        init_integration_fx
    ),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
) -> None:
    """Test non-root device is linked to its parent device in the HA device registry."""
    victron_hub, _mock_config_entry = init_integration

    await inject_message(
        victron_hub,
        f"N/{MOCK_INSTALLATION_ID}/system/0/SystemState/State",
        '{"value": 9}',
    )
    await inject_message(
        victron_hub,
        f"N/{MOCK_INSTALLATION_ID}/battery/0/Dc/0/Current",
        '{"value": 10.5}',
    )
    await finalize_injection(victron_hub)
    await hass.async_block_till_done()

    system_device = device_registry.async_get_device(
        identifiers={(DOMAIN, f"{MOCK_INSTALLATION_ID}_system_0")}
    )
    expect(system_device).not_.to_be_none()
    expect(system_device.via_device_id).to_be_none()

    battery_device = device_registry.async_get_device(
        identifiers={(DOMAIN, f"{MOCK_INSTALLATION_ID}_battery_0")}
    )
    expect(battery_device).not_.to_be_none()
    expect(battery_device.via_device_id).to_equal(system_device.id)


@test
async def hub_start_authentication_error(
    hass: HomeAssistant = Depends(hass_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    mock_victron_hub_library: MagicMock = Depends(mock_victron_hub_library_fx),
) -> None:
    """Test hub start with authentication error."""
    mock_config_entry.add_to_hass(hass)

    mock_victron_hub_library.return_value.connect.side_effect = AuthenticationError(
        "Authentication failed"
    )

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)


@test
async def hub_stop(
    hass: HomeAssistant = Depends(hass_fx),
    init_integration: tuple[VictronVenusHub, MockConfigEntry] = Depends(
        init_integration_fx
    ),
) -> None:
    """Test hub stop."""
    _, mock_config_entry = init_integration

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(mock_config_entry.entry_id)).to_be(
        True
    )
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def hub_stop_disconnect_error(
    hass: HomeAssistant = Depends(hass_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    mock_victron_hub_library: MagicMock = Depends(mock_victron_hub_library_fx),
) -> None:
    """Test hub stop gracefully handles disconnect errors."""
    mock_config_entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(mock_config_entry.entry_id)).to_be(
        True
    )
    await hass.async_block_till_done()
    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    mock_victron_hub_library.return_value.disconnect.side_effect = Exception(
        "disconnect failed"
    )

    expect(await hass.config_entries.async_unload(mock_config_entry.entry_id)).to_be(
        True
    )
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def remove_config_entry_device(
    hass: HomeAssistant = Depends(hass_fx),
    init_integration: tuple[VictronVenusHub, MockConfigEntry] = Depends(
        init_integration_fx
    ),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
) -> None:
    """Test removing a device from the config entry."""
    victron_hub, mock_config_entry = init_integration

    device_entry = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry.entry_id,
        identifiers={(DOMAIN, f"{MOCK_INSTALLATION_ID}_test_device")},
    )

    result = await async_remove_config_entry_device(
        hass, mock_config_entry, device_entry
    )
    expect(result).to_be(True)

    await inject_message(
        victron_hub,
        f"N/{MOCK_INSTALLATION_ID}/battery/0/Dc/0/Current",
        '{"value": 10.5}',
    )
    await finalize_injection(victron_hub)
    await hass.async_block_till_done()

    connected_device = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry.entry_id,
        identifiers={(DOMAIN, f"{MOCK_INSTALLATION_ID}_battery_0")},
    )

    result = await async_remove_config_entry_device(
        hass, mock_config_entry, connected_device
    )
    expect(result).to_be(False)
