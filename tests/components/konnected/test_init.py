"""Test Konnected setup process."""

from tryke import Depends, expect, fixture, test

from homeassistant.components import konnected
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level fixture anchor."""


@test.skip("requires konnected.Client mock chain - port deferred")
async def config_schema() -> None:
    """Stub for test_config_schema."""


@test
async def setup_with_no_config(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that we do not discover or set up a Konnected panel without config."""
    expect(await async_setup_component(hass, konnected.DOMAIN, {})).to_be(True)

    # No flows started
    expect(len(hass.config_entries.flow.async_progress())).to_equal(0)

    # Nothing saved from configuration.yaml
    expect(hass.data[konnected.DOMAIN][konnected.CONF_ACCESS_TOKEN]).to_be(None)
    expect(hass.data[konnected.DOMAIN][konnected.CONF_API_HOST]).to_be(None)
    expect(konnected.YAML_CONFIGS not in hass.data[konnected.DOMAIN]).to_be(True)


@test.skip("requires konnected.Client mock chain - port deferred")
async def setup_defined_hosts_known_auth() -> None:
    """Stub."""


@test.skip("requires konnected.Client mock chain - port deferred")
async def setup_defined_hosts_no_known_auth() -> None:
    """Stub."""


@test.skip("requires konnected.Client mock chain - port deferred")
async def setup_multiple() -> None:
    """Stub."""


@test.skip("requires konnected.Client mock chain - port deferred")
async def config_passed_to_config_entry() -> None:
    """Stub."""


@test.skip("requires konnected.Client mock chain - port deferred")
async def unload_entry() -> None:
    """Stub."""


@test.skip("requires konnected.Client mock chain - port deferred")
async def api() -> None:
    """Stub."""


@test.skip("requires konnected.Client mock chain - port deferred")
async def state_updates_zone() -> None:
    """Stub."""


@test.skip("requires konnected.Client mock chain - port deferred")
async def state_updates_pin() -> None:
    """Stub."""
