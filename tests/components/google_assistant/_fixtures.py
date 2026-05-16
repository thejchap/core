"""Tryke fixtures for Google Assistant tests."""

from tryke import Depends, fixture

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import (
    ClientSessionGenerator,
    LogCapture,
    caplog as caplog_fx,
    device_registry as device_registry_fx,
    entity_registry as entity_registry_fx,
    hass as hass_fixture,
    hass_client as hass_client_fx,
)


@fixture
def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force a HookExecutor for this module."""
    return hass
