"""Tests for the storage helper."""

import asyncio
from datetime import timedelta
import json
import os
from pathlib import Path
import re
import tempfile
import threading
from typing import Any, NamedTuple
from unittest.mock import Mock, patch

from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test

from homeassistant.const import (
    EVENT_HOMEASSISTANT_FINAL_WRITE,
    EVENT_HOMEASSISTANT_START,
    EVENT_HOMEASSISTANT_STARTED,
    EVENT_HOMEASSISTANT_STOP,
)
from homeassistant.core import (
    DOMAIN as HOMEASSISTANT_DOMAIN,
    CoreState,
    HomeAssistant,
    callback,
)
from homeassistant.exceptions import HomeAssistantError, UnsupportedStorageVersionError
from homeassistant.helpers import issue_registry as ir, storage
from homeassistant.helpers.json import json_bytes, prepare_save_json
from homeassistant.util import dt as dt_util
from homeassistant.util.color import RGBColor

from tests.common import (
    async_fire_time_changed,
    async_fire_time_changed_exact,
    async_test_home_assistant,
)
from tests.hass_fixtures import (
    LogCapture,
    caplog,
    freezer,
    hass,
    hass_storage,
    tmp_path,
)

MOCK_VERSION = 1
MOCK_VERSION_2 = 2
MOCK_MINOR_VERSION_1 = 1
MOCK_MINOR_VERSION_2 = 2
MOCK_KEY = "storage-test"
MOCK_KEY2 = "storage-test-2"
MOCK_DATA = {"hello": "world"}
MOCK_DATA2 = {"goodbye": "cruel world"}


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@fixture
def store(hass: HomeAssistant = Depends(hass)) -> storage.Store:
    """Fixture of a store that prevents writing on Home Assistant stop."""
    return storage.Store(hass, MOCK_VERSION, MOCK_KEY)


@fixture
def store_v_1_1(hass: HomeAssistant = Depends(hass)) -> storage.Store:
    """Fixture of a store that prevents writing on Home Assistant stop."""
    return storage.Store(
        hass, MOCK_VERSION, MOCK_KEY, minor_version=MOCK_MINOR_VERSION_1
    )


@fixture
def store_v_1_2(hass: HomeAssistant = Depends(hass)) -> storage.Store:
    """Fixture of a store that prevents writing on Home Assistant stop."""
    return storage.Store(
        hass, MOCK_VERSION, MOCK_KEY, minor_version=MOCK_MINOR_VERSION_2
    )


@fixture
def store_v_2_1(hass: HomeAssistant = Depends(hass)) -> storage.Store:
    """Fixture of a store that prevents writing on Home Assistant stop."""
    return storage.Store(
        hass, MOCK_VERSION_2, MOCK_KEY, minor_version=MOCK_MINOR_VERSION_1
    )


@fixture
def read_only_store(hass: HomeAssistant = Depends(hass)) -> storage.Store:
    """Fixture of a read only store."""
    return storage.Store(hass, MOCK_VERSION, MOCK_KEY, read_only=True)


async def _expect_raises_async(
    exc_type: type[BaseException], coro: Any, match: str | None = None
) -> None:
    """Assert awaiting ``coro`` raises ``exc_type``."""
    try:
        await coro
    except exc_type as err:
        if match is not None:
            expect(bool(re.search(match, str(err)))).to_be(True)
    else:
        raise AssertionError(f"Expected {exc_type.__name__} to be raised")


@test
async def loading(
    hass: HomeAssistant = Depends(hass),
    store: storage.Store = Depends(store),
) -> None:
    """Test we can save and load data."""
    await store.async_save(MOCK_DATA)
    data = await store.async_load()
    expect(data).to_equal(MOCK_DATA)


@test
async def custom_encoder(hass: HomeAssistant = Depends(hass)) -> None:
    """Test we can save and load data."""

    class JSONEncoder(json.JSONEncoder):
        """Mock JSON encoder."""

        def default(self, o):
            """Mock JSON encode method."""
            return "9"

    store = storage.Store(hass, MOCK_VERSION, MOCK_KEY, encoder=JSONEncoder)
    await _expect_raises_async(TypeError, store.async_save(Mock()))
    await store.async_save(object())
    data = await store.async_load()
    expect(data).to_equal("9")


@test
async def loading_non_existing(
    hass: HomeAssistant = Depends(hass),
    store: storage.Store = Depends(store),
) -> None:
    """Test we can save and load data."""
    with patch("homeassistant.util.json.open", side_effect=FileNotFoundError):
        data = await store.async_load()
    expect(data).to_be(None)


@test
async def loading_parallel(
    hass: HomeAssistant = Depends(hass),
    store: storage.Store = Depends(store),
    hass_storage: dict[str, Any] = Depends(hass_storage),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test we can save and load data."""
    hass_storage[store.key] = {"version": MOCK_VERSION, "data": MOCK_DATA}

    results = await asyncio.gather(store.async_load(), store.async_load())

    expect(results[0]).to_equal(MOCK_DATA)
    expect(results[1]).to_equal(MOCK_DATA)
    # Assert log was emitted at least once (truthy count).
    expect(caplog.text.count(f"Loading data for {store.key}") > 0).to_be(True)


@test
async def saving_with_delay(
    hass: HomeAssistant = Depends(hass),
    store: storage.Store = Depends(store),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test saving data after a delay."""
    store.async_delay_save(lambda: MOCK_DATA, 1)
    expect(store.key in hass_storage).to_be(False)

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=1))
    await hass.async_block_till_done()
    expect(hass_storage[store.key]).to_equal(
        {
            "version": MOCK_VERSION,
            "minor_version": 1,
            "key": MOCK_KEY,
            "data": MOCK_DATA,
        }
    )


@test.skip("async_test_home_assistant + delayed thread-executor scheduling — mock_prepare not called under Tryke event loop")
async def saving_with_delay_threading(tmp_path: Path = Depends(tmp_path)) -> None:
    """Test thread handling when saving with a delay."""
    calls = []

    async def assert_storage_data(store_key: str, expected_data: str) -> None:
        """Assert storage data."""

        def read_storage_data(store_key: str) -> str:
            """Read storage data."""
            return Path(tmp_path / f".storage/{store_key}").read_text(encoding="utf-8")

        store_data = await asyncio.to_thread(read_storage_data, store_key)
        expect(store_data).to_equal(expected_data)

    async with async_test_home_assistant(config_dir=tmp_path) as hass:

        def data_producer_thread_safe() -> Any:
            """Produce data to store."""
            expect(threading.get_ident() != hass.loop_thread_id).to_be(True)
            calls.append("thread_safe")
            return MOCK_DATA

        @callback
        def data_producer_callback() -> Any:
            """Produce data to store."""
            expect(threading.get_ident() == hass.loop_thread_id).to_be(True)
            calls.append("callback")
            return MOCK_DATA2

        def mock_prepare_thread_safe(*args, **kwargs):
            """Mock prepare thread safe."""
            expect(threading.get_ident() != hass.loop_thread_id).to_be(True)
            return prepare_save_json(*args, **kwargs)

        def mock_prepare_not_thread_safe(*args, **kwargs):
            """Mock prepare not thread safe."""
            expect(threading.get_ident() == hass.loop_thread_id).to_be(True)
            return prepare_save_json(*args, **kwargs)

        with patch(
            "homeassistant.helpers.storage.json_helper.prepare_save_json",
            wraps=mock_prepare_thread_safe,
        ) as mock_prepare:
            store = storage.Store(
                hass, MOCK_VERSION, MOCK_KEY, serialize_in_event_loop=False
            )
            store.async_delay_save(data_producer_thread_safe, 1)

            async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=1))
            await hass.async_block_till_done()

            mock_prepare.assert_called_once()

        with patch(
            "homeassistant.helpers.storage.json_helper.prepare_save_json",
            wraps=mock_prepare_not_thread_safe,
        ) as mock_prepare:
            store = storage.Store(hass, MOCK_VERSION, MOCK_KEY2)
            store.async_delay_save(data_producer_callback, 1)

            async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=1))
            await hass.async_block_till_done()

            mock_prepare.assert_called_once()

        expect(calls).to_equal(["thread_safe", "callback"])
        expected_data = (
            "{\n"
            '  "version": 1,\n'
            '  "minor_version": 1,\n'
            '  "key": "storage-test",\n'
            '  "data": {\n'
            '    "hello": "world"\n'
            "  }\n"
            "}"
        )
        await assert_storage_data(MOCK_KEY, expected_data)
        expected_data = (
            "{\n"
            '  "version": 1,\n'
            '  "minor_version": 1,\n'
            '  "key": "storage-test-2",\n'
            '  "data": {\n'
            '    "goodbye": "cruel world"\n'
            "  }\n"
            "}"
        )
        await assert_storage_data(MOCK_KEY2, expected_data)

        await hass.async_stop(force=True)


@test.skip("async_test_home_assistant + thread-executor scheduling — mock_prepare not called under Tryke event loop")
async def saving_with_threading(tmp_path: Path = Depends(tmp_path)) -> None:
    """Test thread handling when saving."""

    async def assert_storage_data(store_key: str, expected_data: str) -> None:
        """Assert storage data."""

        def read_storage_data(store_key: str) -> str:
            """Read storage data."""
            return Path(tmp_path / f".storage/{store_key}").read_text(encoding="utf-8")

        store_data = await asyncio.to_thread(read_storage_data, store_key)
        expect(store_data).to_equal(expected_data)

    async with async_test_home_assistant(config_dir=tmp_path) as hass:

        def mock_prepare_thread_safe(*args, **kwargs):
            """Mock prepare thread safe."""
            expect(threading.get_ident() != hass.loop_thread_id).to_be(True)
            return prepare_save_json(*args, **kwargs)

        def mock_prepare_not_thread_safe(*args, **kwargs):
            """Mock prepare not thread safe."""
            expect(threading.get_ident() == hass.loop_thread_id).to_be(True)
            return prepare_save_json(*args, **kwargs)

        with patch(
            "homeassistant.helpers.storage.json_helper.prepare_save_json",
            wraps=mock_prepare_thread_safe,
        ) as mock_prepare:
            store = storage.Store(
                hass, MOCK_VERSION, MOCK_KEY, serialize_in_event_loop=False
            )
            await store.async_save(MOCK_DATA)
            mock_prepare.assert_called_once()

        with patch(
            "homeassistant.helpers.storage.json_helper.prepare_save_json",
            wraps=mock_prepare_not_thread_safe,
        ) as mock_prepare:
            store = storage.Store(hass, MOCK_VERSION, MOCK_KEY2)
            await store.async_save(MOCK_DATA2)
            mock_prepare.assert_called_once()

        expected_data = (
            "{\n"
            '  "version": 1,\n'
            '  "minor_version": 1,\n'
            '  "key": "storage-test",\n'
            '  "data": {\n'
            '    "hello": "world"\n'
            "  }\n"
            "}"
        )
        await assert_storage_data(MOCK_KEY, expected_data)
        expected_data = (
            "{\n"
            '  "version": 1,\n'
            '  "minor_version": 1,\n'
            '  "key": "storage-test-2",\n'
            '  "data": {\n'
            '    "goodbye": "cruel world"\n'
            "  }\n"
            "}"
        )
        await assert_storage_data(MOCK_KEY2, expected_data)

        await hass.async_stop(force=True)


@test
async def saving_with_delay_churn_reduction(
    hass: HomeAssistant = Depends(hass),
    store: storage.Store = Depends(store),
    hass_storage: dict[str, Any] = Depends(hass_storage),
    freezer: FrozenDateTimeFactory = Depends(freezer),
) -> None:
    """Test saving data after a delay with timer churn reduction."""
    store.async_delay_save(lambda: MOCK_DATA, 1)
    expect(store.key in hass_storage).to_be(False)

    freezer.tick(0.2)
    async_fire_time_changed_exact(hass)
    await hass.async_block_till_done()
    expect(store.key in hass_storage).to_be(False)

    freezer.tick(1)
    async_fire_time_changed_exact(hass)
    await hass.async_block_till_done()
    expect(hass_storage[store.key]).to_equal(
        {
            "version": MOCK_VERSION,
            "minor_version": 1,
            "key": MOCK_KEY,
            "data": MOCK_DATA,
        }
    )

    del hass_storage[store.key]
    # Simulate what some of the registries do when they add 100 entities
    for _ in range(100):
        store.async_delay_save(lambda: MOCK_DATA, 1)

    freezer.tick(0.2)
    async_fire_time_changed_exact(hass)
    await hass.async_block_till_done()
    expect(store.key in hass_storage).to_be(False)
    store.async_delay_save(lambda: MOCK_DATA, 1)

    freezer.tick(1)
    async_fire_time_changed_exact(hass)
    await hass.async_block_till_done()
    expect(store.key in hass_storage).to_be(True)

    del hass_storage[store.key]

    store.async_delay_save(lambda: MOCK_DATA, 1)
    freezer.tick(0.5)
    async_fire_time_changed_exact(hass)
    await hass.async_block_till_done()
    expect(store.key in hass_storage).to_be(False)

    store.async_delay_save(lambda: MOCK_DATA, 1)
    freezer.tick(0.8)
    async_fire_time_changed_exact(hass)
    await hass.async_block_till_done()
    expect(store.key in hass_storage).to_be(False)

    store.async_delay_save(lambda: MOCK_DATA, 1)
    freezer.tick(0.8)
    async_fire_time_changed_exact(hass)
    await hass.async_block_till_done()
    expect(store.key in hass_storage).to_be(False)

    freezer.tick(0.2)
    async_fire_time_changed_exact(hass)
    await hass.async_block_till_done()
    expect(store.key in hass_storage).to_be(True)

    # Make sure if we do another delayed save
    # and one with a shorter delay, the shorter delay wins
    del hass_storage[store.key]
    store.async_delay_save(lambda: MOCK_DATA, 2)
    freezer.tick(0.2)
    async_fire_time_changed_exact(hass)
    await hass.async_block_till_done()
    expect(store.key in hass_storage).to_be(False)

    store.async_delay_save(lambda: MOCK_DATA, 1)
    freezer.tick(1.0)
    async_fire_time_changed_exact(hass)
    await hass.async_block_till_done()
    expect(store.key in hass_storage).to_be(True)


@test
async def saving_on_final_write(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test delayed saves trigger when we quit Home Assistant."""
    store = storage.Store(hass, MOCK_VERSION, MOCK_KEY)
    store.async_delay_save(lambda: MOCK_DATA, 5)
    expect(store.key in hass_storage).to_be(False)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    hass.set_state(CoreState.stopping)
    await hass.async_block_till_done()

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=10))
    await hass.async_block_till_done()
    expect(store.key in hass_storage).to_be(False)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_FINAL_WRITE)
    await hass.async_block_till_done()
    expect(hass_storage[store.key]).to_equal(
        {
            "version": MOCK_VERSION,
            "minor_version": 1,
            "key": MOCK_KEY,
            "data": MOCK_DATA,
        }
    )


@test
async def not_delayed_saving_while_stopping(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test delayed saves don't write after the stop event has fired."""
    store = storage.Store(hass, MOCK_VERSION, MOCK_KEY)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()
    hass.set_state(CoreState.stopping)

    store.async_delay_save(lambda: MOCK_DATA, 1)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=2))
    await hass.async_block_till_done()
    expect(store.key in hass_storage).to_be(False)


@test
async def not_delayed_saving_after_stopping(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test delayed saves don't write after stop if issued before stopping Home Assistant."""
    store = storage.Store(hass, MOCK_VERSION, MOCK_KEY)
    store.async_delay_save(lambda: MOCK_DATA, 10)
    expect(store.key in hass_storage).to_be(False)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    hass.set_state(CoreState.stopping)
    await hass.async_block_till_done()
    expect(store.key in hass_storage).to_be(False)

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=15))
    await hass.async_block_till_done()
    expect(store.key in hass_storage).to_be(False)


@test
async def not_saving_while_stopping(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test saves don't write when stopping Home Assistant."""
    store = storage.Store(hass, MOCK_VERSION, MOCK_KEY)
    hass.set_state(CoreState.stopping)
    await store.async_save(MOCK_DATA)
    expect(store.key in hass_storage).to_be(False)


@test
async def loading_while_delay(
    hass: HomeAssistant = Depends(hass),
    store: storage.Store = Depends(store),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test we load new data even if not written yet."""
    await store.async_save({"delay": "no"})
    expect(hass_storage[store.key]).to_equal(
        {
            "version": MOCK_VERSION,
            "minor_version": 1,
            "key": MOCK_KEY,
            "data": {"delay": "no"},
        }
    )

    store.async_delay_save(lambda: {"delay": "yes"}, 1)
    expect(hass_storage[store.key]).to_equal(
        {
            "version": MOCK_VERSION,
            "minor_version": 1,
            "key": MOCK_KEY,
            "data": {"delay": "no"},
        }
    )

    data = await store.async_load()
    expect(data).to_equal({"delay": "yes"})


@test
async def writing_while_writing_delay(
    hass: HomeAssistant = Depends(hass),
    store: storage.Store = Depends(store),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test a write while a write with delay is active."""
    store.async_delay_save(lambda: {"delay": "yes"}, 1)
    expect(store.key in hass_storage).to_be(False)
    await store.async_save({"delay": "no"})
    expect(hass_storage[store.key]).to_equal(
        {
            "version": MOCK_VERSION,
            "minor_version": 1,
            "key": MOCK_KEY,
            "data": {"delay": "no"},
        }
    )

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=1))
    await hass.async_block_till_done()
    expect(hass_storage[store.key]).to_equal(
        {
            "version": MOCK_VERSION,
            "minor_version": 1,
            "key": MOCK_KEY,
            "data": {"delay": "no"},
        }
    )

    data = await store.async_load()
    expect(data).to_equal({"delay": "no"})


@test
async def multiple_delay_save_calls(
    hass: HomeAssistant = Depends(hass),
    store: storage.Store = Depends(store),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test a write while a write with changing delays."""
    store.async_delay_save(lambda: {"delay": "yes"}, 1)
    store.async_delay_save(lambda: {"delay": "yes"}, 2)
    store.async_delay_save(lambda: {"delay": "yes"}, 3)

    expect(store.key in hass_storage).to_be(False)
    await store.async_save({"delay": "no"})
    expect(hass_storage[store.key]).to_equal(
        {
            "version": MOCK_VERSION,
            "minor_version": 1,
            "key": MOCK_KEY,
            "data": {"delay": "no"},
        }
    )

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=1))
    await hass.async_block_till_done()
    expect(hass_storage[store.key]).to_equal(
        {
            "version": MOCK_VERSION,
            "minor_version": 1,
            "key": MOCK_KEY,
            "data": {"delay": "no"},
        }
    )

    data = await store.async_load()
    expect(data).to_equal({"delay": "no"})


@test
async def delay_save_zero(
    hass: HomeAssistant = Depends(hass),
    store: storage.Store = Depends(store),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test async_delay_save accepts 0."""
    store.async_delay_save(lambda: {"delay": "0"}, 0)
    # sleep is to run one event loop to get the task scheduled
    await asyncio.sleep(0)
    await hass.async_block_till_done()
    expect(store.key in hass_storage).to_be(True)
    expect(hass_storage[store.key]).to_equal(
        {
            "version": MOCK_VERSION,
            "minor_version": 1,
            "key": MOCK_KEY,
            "data": {"delay": "0"},
        }
    )


@test
async def multiple_save_calls(
    hass: HomeAssistant = Depends(hass),
    store: storage.Store = Depends(store),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test multiple write tasks."""

    expect(store.key in hass_storage).to_be(False)

    tasks = [store.async_save({"savecount": savecount}) for savecount in range(6)]
    await asyncio.gather(*tasks)
    expect(hass_storage[store.key]).to_equal(
        {
            "version": MOCK_VERSION,
            "minor_version": 1,
            "key": MOCK_KEY,
            "data": {"savecount": 5},
        }
    )

    data = await store.async_load()
    expect(data).to_equal({"savecount": 5})


@test
async def migrator_no_existing_config(
    hass: HomeAssistant = Depends(hass),
    store: storage.Store = Depends(store),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test migrator with no existing config."""
    with (
        patch("os.path.isfile", return_value=False),
        patch.object(store, "async_load", return_value={"cur": "config"}),
    ):
        data = await storage.async_migrator(hass, "old-path", store)

    expect(data).to_equal({"cur": "config"})
    expect(store.key in hass_storage).to_be(False)


@test
async def migrator_existing_config(
    hass: HomeAssistant = Depends(hass),
    store: storage.Store = Depends(store),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test migrating existing config."""
    with patch("os.path.isfile", return_value=True), patch("os.remove") as mock_remove:
        data = await storage.async_migrator(
            hass, "old-path", store, old_conf_load_func=lambda _: {"old": "config"}
        )

    expect(len(mock_remove.mock_calls)).to_equal(1)
    expect(data).to_equal({"old": "config"})
    expect(hass_storage[store.key]).to_equal(
        {
            "key": MOCK_KEY,
            "version": MOCK_VERSION,
            "minor_version": 1,
            "data": data,
        }
    )


@test
async def migrator_transforming_config(
    hass: HomeAssistant = Depends(hass),
    store: storage.Store = Depends(store),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test migrating config to new format."""

    async def old_conf_migrate_func(old_config):
        """Migrate old config to new format."""
        return {"new": old_config["old"]}

    with patch("os.path.isfile", return_value=True), patch("os.remove") as mock_remove:
        data = await storage.async_migrator(
            hass,
            "old-path",
            store,
            old_conf_migrate_func=old_conf_migrate_func,
            old_conf_load_func=lambda _: {"old": "config"},
        )

    expect(len(mock_remove.mock_calls)).to_equal(1)
    expect(data).to_equal({"new": "config"})
    expect(hass_storage[store.key]).to_equal(
        {
            "key": MOCK_KEY,
            "version": MOCK_VERSION,
            "minor_version": 1,
            "data": data,
        }
    )


@test
async def minor_version_default(
    hass: HomeAssistant = Depends(hass),
    store: storage.Store = Depends(store),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test minor version default."""

    await store.async_save(MOCK_DATA)
    expect(hass_storage[store.key]["minor_version"]).to_equal(1)


@test
async def minor_version(
    hass: HomeAssistant = Depends(hass),
    store_v_1_2: storage.Store = Depends(store_v_1_2),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test minor version."""

    await store_v_1_2.async_save(MOCK_DATA)
    expect(hass_storage[store_v_1_2.key]["minor_version"]).to_equal(MOCK_MINOR_VERSION_2)


@test
async def loading_newer_major_version_raises(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
    store: storage.Store = Depends(store),
    store_v_2_1: storage.Store = Depends(store_v_2_1),
) -> None:
    """Test loading storage with a newer major version raises and preserves data."""
    await store_v_2_1.async_save(MOCK_DATA)
    exc: UnsupportedStorageVersionError | None = None
    try:
        await store.async_load()
    except UnsupportedStorageVersionError as err:
        exc = err
    expect(exc is None).to_be(False)
    assert exc is not None
    expect(exc.storage_key).to_equal(MOCK_KEY)
    expect(exc.found_version).to_equal(MOCK_VERSION_2)
    expect(exc.max_supported_version).to_equal(MOCK_VERSION)
    # Verify on-disk data is not modified
    expect(hass_storage[MOCK_KEY]["version"]).to_equal(MOCK_VERSION_2)
    expect(hass_storage[MOCK_KEY]["minor_version"]).to_equal(MOCK_MINOR_VERSION_1)
    expect(hass_storage[MOCK_KEY]["data"]).to_equal(MOCK_DATA)


@test
async def migrate_minor_not_implemented(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
    store_v_1_1: storage.Store = Depends(store_v_1_1),
    store_v_1_2: storage.Store = Depends(store_v_1_2),
) -> None:
    """Test migrating between minor versions does not fail if not implemented."""

    expect(store_v_1_1.key).to_equal(store_v_1_2.key)

    await store_v_1_1.async_save(MOCK_DATA)
    expect(hass_storage[store_v_1_1.key]).to_equal(
        {
            "key": MOCK_KEY,
            "version": MOCK_VERSION,
            "minor_version": MOCK_MINOR_VERSION_1,
            "data": MOCK_DATA,
        }
    )
    data = await store_v_1_2.async_load()
    expect(hass_storage[store_v_1_1.key]["data"]).to_equal(data)

    await store_v_1_2.async_save(MOCK_DATA)
    expect(hass_storage[store_v_1_2.key]).to_equal(
        {
            "key": MOCK_KEY,
            "version": MOCK_VERSION,
            "minor_version": MOCK_MINOR_VERSION_2,
            "data": MOCK_DATA,
        }
    )


@test
async def migration(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
    store_v_1_2: storage.Store = Depends(store_v_1_2),
) -> None:
    """Test migration."""
    calls = 0

    class CustomStore(storage.Store):
        async def _async_migrate_func(
            self, old_major_version, old_minor_version, old_data: dict
        ):
            nonlocal calls
            calls += 1
            expect(old_major_version).to_equal(store_v_1_2.version)
            expect(old_minor_version).to_equal(store_v_1_2.minor_version)
            return old_data

    await store_v_1_2.async_save(MOCK_DATA)
    expect(hass_storage[store_v_1_2.key]).to_equal(
        {
            "key": MOCK_KEY,
            "version": MOCK_VERSION,
            "minor_version": MOCK_MINOR_VERSION_2,
            "data": MOCK_DATA,
        }
    )
    expect(calls).to_equal(0)

    custom_store = CustomStore(hass, 2, store_v_1_2.key, minor_version=1)
    data = await custom_store.async_load()
    expect(calls).to_equal(1)
    expect(hass_storage[store_v_1_2.key]["data"]).to_equal(data)

    # Assert the migrated data has been saved
    expect(hass_storage[custom_store.key]).to_equal(
        {
            "key": MOCK_KEY,
            "version": 2,
            "minor_version": 1,
            "data": MOCK_DATA,
        }
    )


@test
async def legacy_migration(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
    store_v_1_2: storage.Store = Depends(store_v_1_2),
) -> None:
    """Test legacy migration method signature."""
    calls = 0

    class LegacyStore(storage.Store):
        async def _async_migrate_func(self, old_version, old_data: dict):
            nonlocal calls
            calls += 1
            expect(old_version).to_equal(store_v_1_2.version)
            return old_data

    await store_v_1_2.async_save(MOCK_DATA)
    expect(hass_storage[store_v_1_2.key]).to_equal(
        {
            "key": MOCK_KEY,
            "version": MOCK_VERSION,
            "minor_version": MOCK_MINOR_VERSION_2,
            "data": MOCK_DATA,
        }
    )
    expect(calls).to_equal(0)

    legacy_store = LegacyStore(hass, 2, store_v_1_2.key, minor_version=1)
    data = await legacy_store.async_load()
    expect(calls).to_equal(1)
    expect(hass_storage[store_v_1_2.key]["data"]).to_equal(data)

    # Assert the migrated data has been saved
    expect(hass_storage[legacy_store.key]).to_equal(
        {
            "key": MOCK_KEY,
            "version": 2,
            "minor_version": 1,
            "data": MOCK_DATA,
        }
    )


@test
async def changing_delayed_written_data(
    hass: HomeAssistant = Depends(hass),
    store: storage.Store = Depends(store),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test changing data that is written with delay."""
    data_to_store = {"hello": "world"}
    store.async_delay_save(lambda: data_to_store, 1)
    expect(store.key in hass_storage).to_be(False)

    loaded_data = await store.async_load()
    expect(loaded_data).to_equal(data_to_store)
    expect(loaded_data is not data_to_store).to_be(True)

    loaded_data["hello"] = "earth"

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=1))
    await hass.async_block_till_done()
    expect(hass_storage[store.key]).to_equal(
        {
            "version": MOCK_VERSION,
            "minor_version": 1,
            "key": MOCK_KEY,
            "data": {"hello": "world"},
        }
    )


@test
async def saving_load_round_trip() -> None:
    """Test saving and loading round trip."""

    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / "temp_storage"
        config_dir.mkdir()
        async with async_test_home_assistant(config_dir=str(config_dir)) as hass:

            class NamedTupleSubclass(NamedTuple):
                """A NamedTuple subclass."""

                name: str

            nts = NamedTupleSubclass("a")

            data = {
                "named_tuple_subclass": nts,
                "rgb_color": RGBColor(255, 255, 0),
                "set": {1, 2, 3},
                "list": [1, 2, 3],
                "tuple": (1, 2, 3),
                "dict_with_int": {1: 1, 2: 2},
                "dict_with_named_tuple": {1: nts, 2: nts},
            }

            store = storage.Store(
                hass, MOCK_VERSION_2, MOCK_KEY, minor_version=MOCK_MINOR_VERSION_1
            )
            await store.async_save(data)
            load = await store.async_load()
            expect(load).to_equal(
                {
                    "dict_with_int": {"1": 1, "2": 2},
                    "dict_with_named_tuple": {"1": ["a"], "2": ["a"]},
                    "list": [1, 2, 3],
                    "named_tuple_subclass": ["a"],
                    "rgb_color": [255, 255, 0],
                    "set": [1, 2, 3],
                    "tuple": [1, 2, 3],
                }
            )

            await hass.async_stop(force=True)


@test.skip("async_test_home_assistant with custom config_dir + file corruption — file-not-found under Tryke event loop")
async def loading_corrupt_core_file(caplog: LogCapture = Depends(caplog)) -> None:
    """Test we handle unrecoverable corruption in a core file."""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_storage = Path(tmpdir) / "temp_storage"
        tmp_storage.mkdir()
        async with async_test_home_assistant(config_dir=str(tmp_storage)) as hass:
            storage_key = "core.anything"
            store = storage.Store(
                hass, MOCK_VERSION_2, storage_key, minor_version=MOCK_MINOR_VERSION_1
            )
            await store.async_save({"hello": "world"})
            storage_path = os.path.join(tmp_storage, ".storage")
            store_file = os.path.join(storage_path, store.key)

            data = await store.async_load()
            expect(data).to_equal({"hello": "world"})

            def _corrupt_store():
                with open(store_file, "w", encoding="utf8") as f:
                    f.write("corrupt")

            await hass.async_add_executor_job(_corrupt_store)

            data = await store.async_load()
            expect(data).to_be(None)
            expect("Unrecoverable error decoding storage" in caplog.text).to_be(True)

            issue_registry = ir.async_get(hass)
            found_issue = None
            issue_entry = None
            for (domain, issue), entry in issue_registry.issues.items():
                if domain == HOMEASSISTANT_DOMAIN and issue.startswith(
                    f"storage_corruption_{storage_key}_"
                ):
                    found_issue = issue
                    issue_entry = entry
                    break

            expect(found_issue is not None).to_be(True)
            expect(issue_entry is not None).to_be(True)
            assert issue_entry is not None
            expect(issue_entry.is_fixable).to_be(True)
            expect(issue_entry.translation_placeholders["storage_key"]).to_equal(
                storage_key
            )
            expect(issue_entry.issue_domain).to_equal(HOMEASSISTANT_DOMAIN)
            expect(
                "unexpected character: line 1 column 1 (char 0)"
                in issue_entry.translation_placeholders["error"]
            ).to_be(True)

            files = await hass.async_add_executor_job(
                os.listdir, os.path.join(tmp_storage, ".storage")
            )
            expect(".corrupt" in files[0]).to_be(True)

            await hass.async_stop(force=True)


@test.skip("async_test_home_assistant with custom config_dir + file corruption — file-not-found under Tryke event loop")
async def loading_corrupt_file_known_domain(
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test we handle unrecoverable corruption for a known domain."""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_storage = Path(tmpdir) / "temp_storage"
        tmp_storage.mkdir()

        async with async_test_home_assistant(config_dir=str(tmp_storage)) as hass:
            hass.config.components.add("testdomain")
            storage_key = "testdomain.testkey"

            store = storage.Store(
                hass, MOCK_VERSION_2, storage_key, minor_version=MOCK_MINOR_VERSION_1
            )
            await store.async_save({"hello": "world"})
            storage_path = os.path.join(tmp_storage, ".storage")
            store_file = os.path.join(storage_path, store.key)

            data = await store.async_load()
            expect(data).to_equal({"hello": "world"})

            def _corrupt_store():
                with open(store_file, "w", encoding="utf8") as f:
                    f.write('{"valid":"json"}..with..corrupt')

            await hass.async_add_executor_job(_corrupt_store)

            data = await store.async_load()
            expect(data).to_be(None)
            expect("Unrecoverable error decoding storage" in caplog.text).to_be(True)

            issue_registry = ir.async_get(hass)
            found_issue = None
            issue_entry = None
            for (domain, issue), entry in issue_registry.issues.items():
                if domain == HOMEASSISTANT_DOMAIN and issue.startswith(
                    f"storage_corruption_{storage_key}_"
                ):
                    found_issue = issue
                    issue_entry = entry
                    break

            expect(found_issue is not None).to_be(True)
            expect(issue_entry is not None).to_be(True)
            assert issue_entry is not None
            expect(issue_entry.is_fixable).to_be(True)
            expect(issue_entry.translation_placeholders["storage_key"]).to_equal(
                storage_key
            )
            expect(issue_entry.issue_domain).to_equal("testdomain")
            expect(
                "unexpected content after document: line 1 column 17 (char 16)"
                in issue_entry.translation_placeholders["error"]
            ).to_be(True)

            files = await hass.async_add_executor_job(
                os.listdir, os.path.join(tmp_storage, ".storage")
            )
            expect(".corrupt" in files[0]).to_be(True)

            await hass.async_stop(force=True)


@test.skip("async_test_home_assistant with custom config_dir — Store cache returns saved data before patched load_json runs")
async def os_error_is_fatal() -> None:
    """Test OSError during load is fatal."""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_storage = Path(tmpdir) / "temp_storage"
        tmp_storage.mkdir()
        async with async_test_home_assistant(config_dir=str(tmp_storage)) as hass:
            store = storage.Store(
                hass, MOCK_VERSION_2, MOCK_KEY, minor_version=MOCK_MINOR_VERSION_1
            )
            await store.async_save({"hello": "world"})

            with patch(
                "homeassistant.helpers.storage.json_util.load_json",
                side_effect=OSError,
            ):
                await _expect_raises_async(OSError, store.async_load())

            # Verify second load is also failing
            with patch(
                "homeassistant.helpers.storage.json_util.load_json",
                side_effect=OSError,
            ):
                await _expect_raises_async(OSError, store.async_load())

            await hass.async_stop(force=True)


@test.skip("async_test_home_assistant with custom config_dir — Store cache returns saved data before patched load_json runs")
async def json_load_failure() -> None:
    """Test json load raising HomeAssistantError."""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_storage = Path(tmpdir) / "temp_storage"
        tmp_storage.mkdir()
        async with async_test_home_assistant(config_dir=str(tmp_storage)) as hass:
            store = storage.Store(
                hass, MOCK_VERSION_2, MOCK_KEY, minor_version=MOCK_MINOR_VERSION_1
            )
            await store.async_save({"hello": "world"})
            base_os_error = OSError()
            base_os_error.errno = 30
            home_assistant_error = HomeAssistantError()
            home_assistant_error.__cause__ = base_os_error

            with patch(
                "homeassistant.helpers.storage.json_util.load_json",
                side_effect=home_assistant_error,
            ):
                await _expect_raises_async(HomeAssistantError, store.async_load())

            await hass.async_stop(force=True)


@test
async def read_only_store(
    hass: HomeAssistant = Depends(hass),
    read_only_store: storage.Store = Depends(read_only_store),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test store opened in read only mode does not save."""
    read_only_store.async_delay_save(lambda: MOCK_DATA, 1)
    expect(read_only_store.key in hass_storage).to_be(False)

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=1))
    await hass.async_block_till_done()
    expect(read_only_store.key in hass_storage).to_be(False)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    hass.set_state(CoreState.stopping)
    await hass.async_block_till_done()

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=10))
    await hass.async_block_till_done()
    expect(read_only_store.key in hass_storage).to_be(False)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_FINAL_WRITE)
    await hass.async_block_till_done()
    expect(read_only_store.key in hass_storage).to_be(False)


@test.skip("Multi-hass-instance persistence across async_test_home_assistant contexts — data does not persist as expected under Tryke")
async def store_manager_caching(caplog: LogCapture = Depends(caplog)) -> None:
    """Test store manager caching."""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_base = Path(tmpdir)

        def _setup_mock_storage():
            config_dir = tmp_base / "temp_config"
            config_dir.mkdir()
            tmp_storage = config_dir / ".storage"
            tmp_storage.mkdir()
            (tmp_storage / "integration1").write_bytes(
                json_bytes({"data": {"integration1": "integration1"}, "version": 1})
            )
            (tmp_storage / "integration2").write_bytes(
                json_bytes({"data": {"integration2": "integration2"}, "version": 1})
            )
            (tmp_storage / "broken").write_bytes(b"invalid")
            return config_dir

        loop = asyncio.get_running_loop()
        config_dir = await loop.run_in_executor(None, _setup_mock_storage)

        async with async_test_home_assistant(config_dir=str(config_dir)) as hass:
            store_manager = storage.get_internal_store_manager(hass)
            expect(store_manager.async_fetch("integration1")).to_be(None)
            expect(store_manager.async_fetch("integration2")).to_be(None)
            expect(store_manager.async_fetch("integration3")).to_be(None)

            await store_manager.async_initialize()
            expect(store_manager.async_fetch("integration1")).to_be(None)
            expect(store_manager.async_fetch("integration2")).to_be(None)
            expect(
                store_manager.async_fetch("integration3") is not None
            ).to_be(True)

            result = store_manager.async_fetch("integration3")
            assert result is not None
            exists, data = result
            expect(exists).to_be(False)
            expect(data).to_be(None)

            await store_manager.async_preload(
                ["integration3", "integration2", "broken"]
            )
            expect("Error loading broken" in caplog.text).to_be(True)

            expect(store_manager.async_fetch("integration1")).to_be(None)
            result = store_manager.async_fetch("integration2")
            assert result is not None
            exists, data = result
            expect(exists).to_be(True)
            expect(data).to_equal(
                {"data": {"integration2": "integration2"}, "version": 1}
            )

            expect(
                store_manager.async_fetch("integration3") is not None
            ).to_be(True)
            result = store_manager.async_fetch("integration3")
            assert result is not None
            exists, data = result
            expect(exists).to_be(False)
            expect(data).to_be(None)

            integration1 = storage.Store(hass, 1, "integration1")
            await integration1.async_save({"integration1": "updated"})
            expect(store_manager.async_fetch("integration1")).to_be(None)

            integration2 = storage.Store(hass, 1, "integration2")
            integration2.async_delay_save(lambda: {"integration2": "updated"})
            expect("integration2" not in store_manager._invalidated).to_be(True)

            await hass.async_block_till_done()
            await hass.async_block_till_done()
            expect(store_manager.async_fetch("integration2")).to_be(None)

            store_manager.async_invalidate("integration3")
            expect(store_manager.async_fetch("integration1")).to_be(None)
            expect(store_manager.async_fetch("integration2")).to_be(None)
            expect(store_manager.async_fetch("integration3")).to_be(None)

            await hass.async_stop(force=True)

        async with async_test_home_assistant(config_dir=str(config_dir)) as hass:
            store_manager = storage.get_internal_store_manager(hass)
            expect(store_manager.async_fetch("integration1")).to_be(None)
            expect(store_manager.async_fetch("integration2")).to_be(None)
            expect(store_manager.async_fetch("integration3")).to_be(None)
            await store_manager.async_initialize()
            await store_manager.async_preload(["integration1", "integration2"])
            result = store_manager.async_fetch("integration1")
            assert result is not None
            exists, data = result
            expect(exists).to_be(True)
            assert data is not None
            expect(data["data"]).to_equal({"integration1": "updated"})

            integration1 = storage.Store(hass, 1, "integration1")
            expect(await integration1.async_load()).to_equal(
                {"integration1": "updated"}
            )

            expect(store_manager.async_fetch("integration1")).to_be(None)

            integration2 = storage.Store(hass, 1, "integration2")
            expect(await integration2.async_load()).to_equal(
                {"integration2": "updated"}
            )

            expect(store_manager.async_fetch("integration2")).to_be(None)

            integration3 = storage.Store(hass, 1, "integration3")
            expect(await integration3.async_load()).to_be(None)

            await integration3.async_save({"integration3": "updated"})
            expect(await integration3.async_load()).to_equal(
                {"integration3": "updated"}
            )

            await hass.async_stop(force=True)

        async with async_test_home_assistant(config_dir=str(config_dir)) as hass:
            integration1 = storage.Store(hass, 1, "integration1")
            expect(await integration1.async_load()).to_equal(
                {"integration1": "updated"}
            )
            await integration1.async_save({"integration1": "updated2"})
            expect(await integration1.async_load()).to_equal(
                {"integration1": "updated2"}
            )

            integration2 = storage.Store(hass, 1, "integration2")
            expect(await integration2.async_load()).to_equal(
                {"integration2": "updated"}
            )
            await integration2.async_save({"integration2": "updated2"})
            expect(await integration2.async_load()).to_equal(
                {"integration2": "updated2"}
            )

            await hass.async_stop(force=True)

        async with async_test_home_assistant(config_dir=str(config_dir)) as hass:
            store_manager = storage.get_internal_store_manager(hass)
            await store_manager.async_initialize()
            await store_manager.async_preload(["integration1", "integration2"])

            integration1 = storage.Store(hass, 1, "integration1")
            expect(integration1._manager is store_manager).to_be(True)
            expect(await integration1.async_load()).to_equal(
                {"integration1": "updated2"}
            )

            integration2 = storage.Store(hass, 1, "integration2")
            expect(integration2._manager is store_manager).to_be(True)
            expect(await integration2.async_load()).to_equal(
                {"integration2": "updated2"}
            )

            await integration1.async_remove()
            await integration2.async_remove()

            expect(store_manager.async_fetch("integration1")).to_be(None)
            expect(store_manager.async_fetch("integration2")).to_be(None)

            expect(await integration1.async_load()).to_be(None)
            expect(await integration2.async_load()).to_be(None)

            await hass.async_stop(force=True)

        async with async_test_home_assistant(config_dir=str(config_dir)) as hass:
            store_manager = storage.get_internal_store_manager(hass)
            await store_manager.async_initialize()
            await store_manager.async_preload(["integration1"])
            result = store_manager.async_fetch("integration1")
            assert result is not None
            exists, data = result
            expect(exists).to_be(False)
            expect(data).to_be(None)
            await hass.async_stop(force=True)


@test.skip("async_test_home_assistant with pre-populated subdir storage — integration1 not loaded under Tryke")
async def store_manager_sub_dirs() -> None:
    """Test store manager ignores subdirs."""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_base = Path(tmpdir)

        def _setup_mock_storage():
            config_dir = tmp_base / "temp_config"
            config_dir.mkdir()
            sub_dir_storage = config_dir / ".storage" / "subdir"
            sub_dir_storage.mkdir(parents=True)

            (sub_dir_storage / "integration1").write_bytes(
                json_bytes({"data": {"integration1": "integration1"}, "version": 1})
            )
            return config_dir

        loop = asyncio.get_running_loop()
        config_dir = await loop.run_in_executor(None, _setup_mock_storage)

        async with async_test_home_assistant(config_dir=str(config_dir)) as hass:
            store_manager = storage.get_internal_store_manager(hass)
            await store_manager.async_initialize()
            expect(store_manager.async_fetch("subdir/integration1")).to_be(None)
            expect(store_manager.async_fetch("subdir/integrationx")).to_be(None)
            integration1 = storage.Store(hass, 1, "subdir/integration1")
            expect(await integration1.async_load()).to_equal(
                {"integration1": "integration1"}
            )
            await hass.async_stop(force=True)


@test
async def store_manager_cleanup_after_started(
    freezer: FrozenDateTimeFactory = Depends(freezer),
) -> None:
    """Test that the cache is cleaned up after startup."""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_base = Path(tmpdir)

        def _setup_mock_storage():
            config_dir = tmp_base / "temp_config"
            config_dir.mkdir()
            tmp_storage = config_dir / ".storage"
            tmp_storage.mkdir()
            (tmp_storage / "integration1").write_bytes(
                json_bytes({"data": {"integration1": "integration1"}, "version": 1})
            )
            (tmp_storage / "integration2").write_bytes(
                json_bytes({"data": {"integration2": "integration2"}, "version": 1})
            )
            return config_dir

        loop = asyncio.get_running_loop()
        config_dir = await loop.run_in_executor(None, _setup_mock_storage)

        async with async_test_home_assistant(config_dir=str(config_dir)) as hass:
            hass.set_state(CoreState.not_running)
            store_manager = storage.get_internal_store_manager(hass)
            await store_manager.async_initialize()
            await store_manager.async_preload(["integration1", "integration2"])
            expect("integration1" in store_manager._data_preload).to_be(True)
            expect("integration2" in store_manager._data_preload).to_be(True)
            hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
            await hass.async_block_till_done()
            expect("integration1" in store_manager._data_preload).to_be(True)
            expect("integration2" in store_manager._data_preload).to_be(True)
            hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
            await hass.async_block_till_done()
            expect("integration1" in store_manager._data_preload).to_be(True)
            expect("integration2" in store_manager._data_preload).to_be(True)
            freezer.tick(storage.MANAGER_CLEANUP_DELAY)
            async_fire_time_changed(hass)
            await hass.async_block_till_done()
            expect("integration1" in store_manager._data_preload).to_be(False)
            expect("integration2" in store_manager._data_preload).to_be(False)
            expect(store_manager.async_fetch("integration1")).to_be(None)
            expect(store_manager.async_fetch("integration2")).to_be(None)
            await hass.async_stop(force=True)


@test
async def store_manager_cleanup_after_stop(
    freezer: FrozenDateTimeFactory = Depends(freezer),
) -> None:
    """Test that the cache is cleaned up after stop event.

    This should only happen if we stop within the cleanup delay.
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_base = Path(tmpdir)

        def _setup_mock_storage():
            config_dir = tmp_base / "temp_config"
            config_dir.mkdir()
            tmp_storage = config_dir / ".storage"
            tmp_storage.mkdir()
            (tmp_storage / "integration1").write_bytes(
                json_bytes({"data": {"integration1": "integration1"}, "version": 1})
            )
            (tmp_storage / "integration2").write_bytes(
                json_bytes({"data": {"integration2": "integration2"}, "version": 1})
            )
            return config_dir

        loop = asyncio.get_running_loop()
        config_dir = await loop.run_in_executor(None, _setup_mock_storage)

        async with async_test_home_assistant(config_dir=str(config_dir)) as hass:
            hass.set_state(CoreState.not_running)
            store_manager = storage.get_internal_store_manager(hass)
            await store_manager.async_initialize()
            await store_manager.async_preload(["integration1", "integration2"])
            expect("integration1" in store_manager._data_preload).to_be(True)
            expect("integration2" in store_manager._data_preload).to_be(True)
            hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
            await hass.async_block_till_done()
            expect("integration1" in store_manager._data_preload).to_be(True)
            expect("integration2" in store_manager._data_preload).to_be(True)
            hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
            await hass.async_block_till_done()
            expect("integration1" in store_manager._data_preload).to_be(True)
            expect("integration2" in store_manager._data_preload).to_be(True)
            hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
            await hass.async_block_till_done()
            expect("integration1" in store_manager._data_preload).to_be(False)
            expect("integration2" in store_manager._data_preload).to_be(False)
            expect(store_manager.async_fetch("integration1")).to_be(None)
            expect(store_manager.async_fetch("integration2")).to_be(None)
            await hass.async_stop(force=True)


@test
async def storage_concurrent_load(hass: HomeAssistant = Depends(hass)) -> None:
    """Test that we can load the store concurrently."""

    store = storage.Store(hass, MOCK_VERSION, MOCK_KEY)

    async def _load_store():
        await asyncio.sleep(0)
        return "data"

    with patch.object(store, "_async_load", side_effect=_load_store):
        # Test that we can load the store concurrently
        loads = await asyncio.gather(
            store.async_load(), store.async_load(), store.async_load()
        )
        for load in loads:
            expect(load).to_equal("data")


@test
async def load_empty_returns_none_and_read_only(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test store with load_empty returns None, becomes read-only, and skips version checks."""
    # Use a future version to also verify no version error is raised
    hass_storage[MOCK_KEY] = {
        "version": 99,
        "minor_version": 1,
        "key": MOCK_KEY,
        "data": MOCK_DATA,
    }

    store = storage.Store(hass, MOCK_VERSION, MOCK_KEY)
    store.set_load_empty()

    data = await store.async_load()
    expect(data).to_be(None)
    expect(store._read_only).to_be(True)

    await store.async_save({"new": "data"})
    expect(hass_storage[MOCK_KEY]["data"]).to_equal(MOCK_DATA)
    expect(hass_storage[MOCK_KEY]["version"]).to_equal(99)
