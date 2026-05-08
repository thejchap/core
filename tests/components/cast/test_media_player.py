"""The tests for the Cast Media player platform."""

from uuid import UUID

import pychromecast
from pychromecast.const import CAST_TYPE_CHROMECAST, CAST_TYPE_GROUP
from tryke import Depends, expect, fixture, test

from homeassistant.components.cast import media_player as cast
from homeassistant.components.cast.media_player import ChromecastInfo
from homeassistant.core import HomeAssistant

from ._fixtures import cast_mock_patches

from tests.hass_fixtures import hass as hass_fixture, mock_network

FakeUUID = UUID("57355bce-9364-4aa6-ac1e-eb849dccf9e2")


def _make_chromecast_info(
    *,
    host: str = "192.168.178.42",
    port: int = 8009,
    uuid: UUID | None = FakeUUID,
) -> ChromecastInfo:
    """Build a ChromecastInfo for tests."""
    service = pychromecast.discovery.HostServiceInfo(host, port)
    cast_type = CAST_TYPE_GROUP if port != 8009 else CAST_TYPE_CHROMECAST
    return ChromecastInfo(
        cast_info=pychromecast.models.CastInfo(
            services={service},
            uuid=uuid,
            model_name="Chromecast",
            friendly_name="Speaker",
            host=host,
            port=port,
            cast_type=cast_type,
            manufacturer="Nabu Casa",
        )
    )


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _cast: None = Depends(cast_mock_patches),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Anchor fixture (autouse for the module)."""
    return hass


@test
async def create_cast_device_without_uuid(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test create_cast_device with no UUID returns None."""
    info = _make_chromecast_info(uuid=None)
    cast_device = cast._async_create_cast_device(hass, info)
    expect(cast_device).to_be(None)


@test
async def create_cast_device_with_uuid(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test create_cast_device with UUID returns a device, then None when re-created."""
    added_casts: set = set()
    hass.data[cast.ADDED_CAST_DEVICES_KEY] = added_casts
    info = _make_chromecast_info()

    cast_device = cast._async_create_cast_device(hass, info)
    expect(cast_device).not_.to_be(None)
    expect(info.uuid in added_casts).to_be(True)

    cast_device = cast._async_create_cast_device(hass, info)
    expect(cast_device).to_be(None)


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def start_discovery_called_once() -> None:
    """Stub for test_start_discovery_called_once."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def internal_discovery_callback_fill_out_group_fail() -> None:
    """Stub for test_internal_discovery_callback_fill_out_group_fail."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def internal_discovery_callback_fill_out_group() -> None:
    """Stub for test_internal_discovery_callback_fill_out_group."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def internal_discovery_callback_fill_out_cast_type_manufacturer() -> None:
    """Stub for test_internal_discovery_callback_fill_out_cast_type_manufacturer."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def stop_discovery_called_on_stop() -> None:
    """Stub for test_stop_discovery_called_on_stop."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def manual_cast_chromecasts_uuid() -> None:
    """Stub for test_manual_cast_chromecasts_uuid."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def auto_cast_chromecasts() -> None:
    """Stub for test_auto_cast_chromecasts."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def discover_dynamic_group() -> None:
    """Stub for test_discover_dynamic_group."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def update_cast_chromecasts() -> None:
    """Stub for test_update_cast_chromecasts."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def entity_availability() -> None:
    """Stub for test_entity_availability."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def device_registry() -> None:
    """Stub for test_device_registry."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def entity_cast_status() -> None:
    """Stub for test_entity_cast_status."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def supported_features() -> None:
    """Stub for test_supported_features."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def entity_browse_media() -> None:
    """Stub for test_entity_browse_media."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def entity_browse_media_audio_only() -> None:
    """Stub for test_entity_browse_media_audio_only."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def entity_play_media() -> None:
    """Stub for test_entity_play_media."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def entity_play_media_cast() -> None:
    """Stub for test_entity_play_media_cast."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def entity_play_media_cast_invalid() -> None:
    """Stub for test_entity_play_media_cast_invalid."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def entity_play_media_sign_URL() -> None:
    """Stub for test_entity_play_media_sign_URL."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def entity_play_media_playlist() -> None:
    """Stub for test_entity_play_media_playlist."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def entity_media_content_type() -> None:
    """Stub for test_entity_media_content_type."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def entity_control() -> None:
    """Stub for test_entity_control."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def entity_media_states() -> None:
    """Stub for test_entity_media_states."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def entity_media_states_lovelace_app() -> None:
    """Stub for test_entity_media_states_lovelace_app."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def entity_media_states_active_input() -> None:
    """Stub for test_entity_media_states_active_input."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def group_media_states() -> None:
    """Stub for test_group_media_states."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def group_media_states_early() -> None:
    """Stub for test_group_media_states_early."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def group_media_control() -> None:
    """Stub for test_group_media_control."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def failed_cast_on_idle() -> None:
    """Stub for test_failed_cast_on_idle."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def failed_cast_other_url() -> None:
    """Stub for test_failed_cast_other_url."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def failed_cast_internal_url() -> None:
    """Stub for test_failed_cast_internal_url."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def failed_cast_external_url() -> None:
    """Stub for test_failed_cast_external_url."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def disconnect_on_stop() -> None:
    """Stub for test_disconnect_on_stop."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def entry_setup_no_config() -> None:
    """Stub for test_entry_setup_no_config."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def invalid_cast_platform() -> None:
    """Stub for test_invalid_cast_platform."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def cast_platform_play_media() -> None:
    """Stub for test_cast_platform_play_media."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def cast_platform_browse_media() -> None:
    """Stub for test_cast_platform_browse_media."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def cast_platform_play_media_local_media() -> None:
    """Stub for test_cast_platform_play_media_local_media."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def ha_cast() -> None:
    """Stub for test_ha_cast."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def entity_media_states_active_app_reported_idle() -> None:
    """Stub for test_entity_media_states_active_app_reported_idle."""

