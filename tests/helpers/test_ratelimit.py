"""Tests for ratelimit."""

import asyncio
import time

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import ratelimit

from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path.

    Required so imported fixtures resolved via ``Depends(...)`` actually
    execute (Tryke only wires Depends resolution for modules that
    statically declare at least one ``@fixture``).
    """
    return 0


@test
async def hit(hass: HomeAssistant = Depends(hass)) -> None:
    """Test hitting the rate limit."""
    refresh_called = False

    @callback
    def _refresh() -> None:
        nonlocal refresh_called
        refresh_called = True

    rate_limiter = ratelimit.KeyedRateLimit(hass)
    rate_limiter.async_triggered("key1", time.time())

    expect(
        rate_limiter.async_schedule_action("key1", 0.001, time.time(), _refresh)
        is not None
    ).to_be(True)

    expect(refresh_called).to_be(False)

    expect(rate_limiter.async_has_timer("key1")).to_be(True)

    await asyncio.sleep(0.002)
    expect(refresh_called).to_be(True)

    expect(
        rate_limiter.async_schedule_action("key2", 0.001, time.time(), _refresh) is None
    ).to_be(True)
    rate_limiter.async_remove()


@test
async def miss(hass: HomeAssistant = Depends(hass)) -> None:
    """Test missing the rate limit."""
    refresh_called = False

    @callback
    def _refresh() -> None:
        nonlocal refresh_called
        refresh_called = True

    rate_limiter = ratelimit.KeyedRateLimit(hass)
    expect(
        rate_limiter.async_schedule_action("key1", 0.1, time.time(), _refresh) is None
    ).to_be(True)
    expect(refresh_called).to_be(False)
    expect(rate_limiter.async_has_timer("key1")).to_be(False)

    expect(
        rate_limiter.async_schedule_action("key1", 0.1, time.time(), _refresh) is None
    ).to_be(True)
    expect(refresh_called).to_be(False)
    expect(rate_limiter.async_has_timer("key1")).to_be(False)
    rate_limiter.async_remove()


@test
async def no_limit(hass: HomeAssistant = Depends(hass)) -> None:
    """Test async_schedule_action always return None when there is no rate limit."""
    refresh_called = False

    @callback
    def _refresh() -> None:
        nonlocal refresh_called
        refresh_called = True

    rate_limiter = ratelimit.KeyedRateLimit(hass)
    rate_limiter.async_triggered("key1", time.time())

    expect(
        rate_limiter.async_schedule_action("key1", None, time.time(), _refresh) is None
    ).to_be(True)
    expect(refresh_called).to_be(False)
    expect(rate_limiter.async_has_timer("key1")).to_be(False)

    rate_limiter.async_triggered("key1", time.time())

    expect(
        rate_limiter.async_schedule_action("key1", None, time.time(), _refresh) is None
    ).to_be(True)
    expect(refresh_called).to_be(False)
    expect(rate_limiter.async_has_timer("key1")).to_be(False)
    rate_limiter.async_remove()
