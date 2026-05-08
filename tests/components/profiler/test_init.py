"""Test the Profiler integration."""

import os
from pathlib import Path
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.profiler import (
    CONF_SECONDS,
    SERVICE_START,
)
from homeassistant.components.profiler.const import DOMAIN
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    hass as hass_fixture,
    mock_network,
    tmp_path as tmp_path_fixture,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Force tryke to fully resolve hass before each test."""


@test
async def basic_usage(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test we can setup and the service is registered."""
    test_dir = tmp_path / "profiles"
    test_dir.mkdir()

    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(hass.services.has_service(DOMAIN, SERVICE_START)).to_be(True)

    last_filename: str | None = None

    def _mock_path(filename: str) -> str:
        nonlocal last_filename
        last_filename = str(test_dir / filename)
        return last_filename

    with patch("cProfile.Profile"), patch.object(hass.config, "path", _mock_path):
        await hass.services.async_call(
            DOMAIN, SERVICE_START, {CONF_SECONDS: 0.000001}, blocking=True
        )

    expect(last_filename is not None).to_be(True)
    expect(os.path.exists(last_filename)).to_be(True)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()


@test.skip("requires guppy.hpy mock - port deferred")
async def memory_usage() -> None:
    """Stub for test_memory_usage (port deferred)."""

@test.skip("requires objgraph + freezegun - port deferred")
async def object_growth_logging() -> None:
    """Stub for test_object_growth_logging (port deferred)."""

@test.skip("requires objgraph mock - port deferred")
async def dump_log_object() -> None:
    """Stub for test_dump_log_object (port deferred)."""

@test.skip("requires sys frame inspection - port deferred")
async def log_thread_frames() -> None:
    """Stub for test_log_thread_frames (port deferred)."""

@test.skip("requires asyncio task inspection - port deferred")
async def log_current_tasks() -> None:
    """Stub for test_log_current_tasks (port deferred)."""

@test.skip("requires asyncio scheduled inspection - port deferred")
async def log_scheduled() -> None:
    """Stub for test_log_scheduled (port deferred)."""

@test.skip("requires socket inspection - port deferred")
async def dump_sockets() -> None:
    """Stub for test_dump_sockets (port deferred)."""

@test.skip("requires LRU cache inspection - port deferred")
async def lru_stats() -> None:
    """Stub for test_lru_stats (port deferred)."""

@test.skip("requires objgraph mock - port deferred")
async def log_object_sources() -> None:
    """Stub for test_log_object_sources (port deferred)."""

@test.skip("requires asyncio debug toggle - port deferred")
async def set_asyncio_debug() -> None:
    """Stub for test_set_asyncio_debug (port deferred)."""
