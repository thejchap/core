"""Tests for iAquaLink integration utility functions."""

from iaqualink.exception import AqualinkServiceException
from tryke import Depends, fixture, test

from homeassistant.components.iaqualink.utils import await_or_reraise
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from ._fixtures import async_raises, async_returns

from tests.hass_fixtures import hass as hass_fixture
from tests.hass_tryke_helpers import expect_raises_async


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture."""
    return hass


@test
async def await_or_reraise_test(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test await_or_reraise for all values of awaitable."""
    async_noop = async_returns(None)
    await await_or_reraise(async_noop())

    async with expect_raises_async(Exception, match="Test exception"):
        await await_or_reraise(async_raises(Exception("Test exception"))())

    async_ex = async_raises(AqualinkServiceException)
    async with expect_raises_async(HomeAssistantError):
        await await_or_reraise(async_ex())
