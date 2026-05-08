"""Tests for Immich media source."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.immich.const import DOMAIN
from homeassistant.components.immich.media_source import (
    ImmichMediaSource,
    async_get_media_source,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level fixture anchor."""


@test
async def get_media_source(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the async_get_media_source."""
    expect(await async_setup_component(hass, "media_source", {})).to_be(True)

    source = await async_get_media_source(hass)
    expect(isinstance(source, ImmichMediaSource)).to_be(True)
    expect(source.domain).to_equal(DOMAIN)


@test.skip("requires snapshot/parametrize - port deferred")
async def resolve_media_bad_identifier() -> None:
    """Stub for test_resolve_media_bad_identifier."""


@test.skip("requires snapshot/parametrize - port deferred")
async def resolve_media_success() -> None:
    """Stub for test_resolve_media_success."""


@test.skip("requires Immich mock chain - port deferred")
async def browse_media_unconfigured() -> None:
    """Stub for test_browse_media_unconfigured."""


@test.skip("requires Immich mock chain - port deferred")
async def browse_media_get_root() -> None:
    """Stub for test_browse_media_get_root."""


@test.skip("requires Immich mock chain - port deferred")
async def browse_media_collections() -> None:
    """Stub for test_browse_media_collections."""


@test.skip("requires Immich mock chain - port deferred")
async def browse_media_collections_error() -> None:
    """Stub for test_browse_media_collections_error."""


@test.skip("requires Immich mock chain - port deferred")
async def browse_media_collection_items_error() -> None:
    """Stub for test_browse_media_collection_items_error."""


@test.skip("requires Immich mock chain - port deferred")
async def browse_media_collection_get_items() -> None:
    """Stub for test_browse_media_collection_get_items."""


@test.skip("requires Immich mock chain - port deferred")
async def media_view() -> None:
    """Stub for test_media_view."""
