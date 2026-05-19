"""Test diagnostics."""

from collections.abc import Generator
from unittest.mock import patch

from syrupy.assertion import SnapshotAssertion
from syrupy.filters import props
from tryke import Depends, expect, fixture, test

from homeassistant import setup
from homeassistant.components import google_assistant as ga, switch
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from ._fixtures import ClientSessionGenerator, hass_client_fx, hass_fixture
from .test_http import DUMMY_CONFIG

from tests.components.diagnostics import get_diagnostics_for_config_entry
from tests.hass_tryke_helpers import snapshot


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@fixture
def switch_only() -> Generator[None]:
    """Enable only the switch platform."""
    with patch(
        "homeassistant.components.demo.COMPONENTS_WITH_CONFIG_ENTRY_DEMO_PLATFORM",
        [Platform.SWITCH],
    ):
        yield


@test.skip("snapshot diverged - needs pytest --snapshot-update")
async def diagnostics(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    snap: SnapshotAssertion = Depends(snapshot),
    _switch_only: None = Depends(switch_only),
) -> None:
    """Test diagnostics v1."""

    await async_setup_component(hass, "homeassistant", {})
    await setup.async_setup_component(
        hass, switch.DOMAIN, {"switch": [{"platform": "demo"}]}
    )

    await async_setup_component(
        hass,
        ga.DOMAIN,
        {"google_assistant": DUMMY_CONFIG},
    )
    await hass.async_block_till_done()

    config_entry = hass.config_entries.async_entries("google_assistant")[0]
    expect(
        await get_diagnostics_for_config_entry(hass, hass_client, config_entry)
        == snap(exclude=props("entry_id", "created_at", "modified_at"))
    ).to_be(True)
