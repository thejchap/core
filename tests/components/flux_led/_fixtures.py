"""Tryke fixtures for the flux_led integration."""

from collections.abc import Generator
from unittest.mock import patch

from tryke import fixture

_FAKE_TRANSLATIONS = {
    "component.flux_led.entity.sensor.paired_remotes.name": "Paired remotes",
    "component.flux_led.entity.switch.remote_access.name": "Remote access",
    "component.flux_led.entity.switch.music.name": "Music",
}


async def _fake_get_translations(
    hass_arg, language, category, integrations=None, config_flow=None
):
    return _FAKE_TRANSLATIONS


def _fake_get_cached_translations(hass_arg, language, category, integration=None):
    return _FAKE_TRANSLATIONS


@fixture
def translations() -> Generator[None]:
    """Inject translation slugs for entity_id generation."""
    with (
        patch(
            "homeassistant.helpers.entity_platform.translation.async_get_translations",
            side_effect=_fake_get_translations,
        ),
        patch(
            "homeassistant.helpers.translation.async_get_cached_translations",
            side_effect=_fake_get_cached_translations,
        ),
    ):
        yield


@fixture
def mock_single_broadcast_address() -> Generator[None]:
    """Mock network's async_async_get_ipv4_broadcast_addresses."""
    with patch(
        "homeassistant.components.network.async_get_ipv4_broadcast_addresses",
        return_value={"10.255.255.255"},
    ):
        yield


@fixture
def mock_multiple_broadcast_addresses() -> Generator[None]:
    """Mock network's async_async_get_ipv4_broadcast_addresses to return multiple addresses."""
    with patch(
        "homeassistant.components.network.async_get_ipv4_broadcast_addresses",
        return_value={"10.255.255.255", "192.168.0.255"},
    ):
        yield
