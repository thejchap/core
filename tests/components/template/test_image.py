"""The tests for the Template image platform."""

from __future__ import annotations

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component

from tests.common import assert_setup_component
from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)


_TEST_IMAGE = "image.template_image"


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture (tryke 0.0.27 quirk)."""
    return hass


@test
async def missing_required_keys(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test: missing required fields will fail."""
    with assert_setup_component(0, "template"):
        expect(
            await async_setup_component(
                hass,
                "template",
                {
                    "template": {
                        "image": {
                            "name": "a name",
                        }
                    }
                },
            )
        ).to_be(True)

    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    expect(hass.states.async_all("image")).to_equal([])


@test
async def unique_id(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test unique_id configuration."""
    with assert_setup_component(1, "template"):
        expect(
            await async_setup_component(
                hass,
                "template",
                {
                    "template": {
                        "unique_id": "b",
                        "image": {
                            "url": "http://example.com",
                            "unique_id": "a",
                        },
                    }
                },
            )
        ).to_be(True)

    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    entry = entity_registry.async_get(_TEST_IMAGE)
    expect(entry).not_.to_be(None)
    expect(entry.unique_id).to_equal("b-a")


@test.skip("requires hass_client (image_proxy) — port deferred")
async def setup_config_entry() -> None:
    """Stub: requires hass_client + respx."""


@test.skip("requires hass_client (image_proxy) — port deferred")
async def platform_config() -> None:
    """Stub: requires hass_client + respx."""


@test.skip("requires hass_client (image_proxy) — port deferred")
async def missing_optional_config() -> None:
    """Stub: requires hass_client + respx."""


@test.skip("requires hass_client (image_proxy) — port deferred")
async def multiple_configs() -> None:
    """Stub: requires hass_client + respx."""


@test.skip("requires hass_client (image_proxy) — port deferred")
async def custom_entity_picture() -> None:
    """Stub: requires hass_client + respx."""


@test.skip("requires hass_client (image_proxy) — port deferred")
async def template_error() -> None:
    """Stub: requires hass_client + respx."""


@test.skip("requires hass_client (image_proxy) — port deferred")
async def templates_with_entities() -> None:
    """Stub: requires hass_client + respx."""


@test.skip("requires hass_client (image_proxy) — port deferred")
async def trigger_image() -> None:
    """Stub: requires hass_client + respx."""


@test.skip("requires hass_client (image_proxy) — port deferred")
async def trigger_image_custom_entity_picture() -> None:
    """Stub: requires hass_client + respx."""


@test.skip("device_id requires syrupy snapshot + config flow — port deferred")
async def device_id() -> None:
    """Stub."""
