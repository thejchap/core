"""Tests for the storage helper with minimal mocking."""

from datetime import timedelta
import os
from pathlib import Path
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.helpers import storage
from homeassistant.util import dt as dt_util

from tests.common import async_fire_time_changed, async_test_home_assistant
from tests.hass_fixtures import tmp_path


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def removing_while_delay_in_progress(tmp_path: Path = Depends(tmp_path)) -> None:
    """Test removing while delay in progress."""

    async with async_test_home_assistant() as hass:
        test_dir = await hass.async_add_executor_job(
            lambda: tmp_path / "storage"
        )
        await hass.async_add_executor_job(test_dir.mkdir)

        with patch.object(storage, "STORAGE_DIR", str(test_dir)):
            real_store = storage.Store(hass, 1, "remove_me")

            await real_store.async_save({"delay": "no"})

            expect(
                await hass.async_add_executor_job(os.path.exists, real_store.path)
            ).to_be(True)

            real_store.async_delay_save(lambda: {"delay": "yes"}, 1)

            await real_store.async_remove()
            expect(
                await hass.async_add_executor_job(os.path.exists, real_store.path)
            ).to_be(False)

            async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=1))
            await hass.async_block_till_done()
            expect(
                await hass.async_add_executor_job(os.path.exists, real_store.path)
            ).to_be(False)
            await hass.async_stop()
