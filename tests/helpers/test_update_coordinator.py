"""Tests for the update coordinator."""

from __future__ import annotations

import asyncio
from collections.abc import Generator
import contextlib
from datetime import datetime, timedelta
import logging
import re
import sys
from typing import Any
from unittest.mock import AsyncMock, Mock, patch
import urllib.error
import weakref

import aiohttp
from freezegun.api import FrozenDateTimeFactory
import requests

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import CALLBACK_TYPE, CoreState, HomeAssistant, callback
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryError,
    ConfigEntryNotReady,
    OAuth2TokenRequestError,
    OAuth2TokenRequestReauthError,
)
from homeassistant.helpers import frame, update_coordinator
from homeassistant.util.dt import utcnow

from tests.common import (
    MockConfigEntry,
    async_fire_time_changed,
    extract_stack_to_frame,
)
from tests.hass_fixtures import caplog, freezer, hass  # noqa: F401

_LOGGER = logging.getLogger(__name__)

KNOWN_ERRORS: list[tuple[Exception, type[Exception], str]] = [
    (TimeoutError(), TimeoutError, "Timeout fetching test data"),
    (
        requests.exceptions.Timeout(),
        requests.exceptions.Timeout,
        "Timeout fetching test data",
    ),
    (
        urllib.error.URLError("timed out"),
        urllib.error.URLError,
        "Timeout fetching test data",
    ),
    (aiohttp.ClientError(), aiohttp.ClientError, "Error requesting test data"),
    (
        requests.exceptions.RequestException(),
        requests.exceptions.RequestException,
        "Error requesting test data",
    ),
    (
        urllib.error.URLError("something"),
        urllib.error.URLError,
        "Error requesting test data",
    ),
    (
        update_coordinator.UpdateFailed(),
        update_coordinator.UpdateFailed,
        "Error fetching test data",
    ),
]

DEFAULT_UPDATE_INTERVAL = timedelta(seconds=10)


def get_crd(
    hass: HomeAssistant,
    update_interval: timedelta | None,
    config_entry: config_entries.ConfigEntry | None = None,
) -> update_coordinator.DataUpdateCoordinator[int]:
    """Make coordinator mocks."""
    calls = 0

    async def refresh() -> int:
        nonlocal calls
        calls += 1
        return calls

    return update_coordinator.DataUpdateCoordinator[int](
        hass,
        _LOGGER,
        config_entry=config_entry,
        name="test",
        update_method=refresh,
        update_interval=update_interval,
    )


async def _expect_raises_async(
    exc_type: type[BaseException],
    coro: Any,
    match: str | None = None,
) -> None:
    """Assert an awaitable raises exc_type, optionally matching a regex."""
    try:
        await coro
    except exc_type as exc:
        if match is not None and not re.search(match, str(exc)):
            raise AssertionError(
                f"Expected match {match!r} in {str(exc)!r}"
            ) from None
        return
    raise AssertionError(f"Expected {exc_type.__name__} to be raised")


def _make_integration_frame_patches(
    integration_frame_path: str,
) -> list[Any]:
    """Return the patch context managers used by mock_integration_frame."""
    correct_filename = f"/home/paulus/{integration_frame_path}/light.py"
    correct_module_name = f"{integration_frame_path.replace('/', '.')}.light"
    correct_frame = Mock(
        filename=correct_filename,
        lineno="23",
        line="self.light.is_on",
    )
    return [
        patch.dict(sys.modules, {correct_module_name: Mock(__file__=correct_filename)}),
        patch(
            "homeassistant.helpers.frame.linecache.getline",
            return_value=correct_frame.line,
        ),
        patch(
            "homeassistant.helpers.frame.get_current_frame",
            return_value=extract_stack_to_frame(
                [
                    Mock(
                        filename="/home/paulus/homeassistant/core.py",
                        lineno="23",
                        line="do_something()",
                    ),
                    correct_frame,
                    Mock(
                        filename="/home/paulus/aiohue/lights.py",
                        lineno="2",
                        line="something()",
                    ),
                ]
            ),
        ),
    ]


@fixture
def crd(
    hass: HomeAssistant = Depends(hass),
) -> update_coordinator.DataUpdateCoordinator[int]:
    """Coordinator mock with default update interval."""
    return get_crd(hass, DEFAULT_UPDATE_INTERVAL)


@fixture
def crd_without_update_interval(
    hass: HomeAssistant = Depends(hass),
) -> update_coordinator.DataUpdateCoordinator[int]:
    """Coordinator mock that never automatically updates."""
    return get_crd(hass, None)


@contextlib.contextmanager
def _mock_integration_frame(integration_frame_path: str) -> Generator[Mock]:
    """Context manager patching the frame helper for the given integration path.

    Cannot be a Tryke @fixture: module-level fixtures run for every test in
    the file, and having both core and custom variants would stomp each
    other. Call this inside a ``with`` block at the top of tests that need it.
    """
    patches = _make_integration_frame_patches(integration_frame_path)
    for p in patches:
        p.start()
    try:
        yield Mock()
    finally:
        for p in reversed(patches):
            p.stop()


@test
async def async_refresh(
    crd: update_coordinator.DataUpdateCoordinator[int] = Depends(crd),
) -> None:
    """Test async_refresh for update coordinator."""
    expect(crd.data).to_be_none()
    await crd.async_refresh()
    expect(crd.data).to_equal(1)
    expect(crd.last_update_success).to_be(True)
    expect(crd._unsub_refresh).to_be_none()

    updates: list[int] = []

    def update_callback() -> None:
        updates.append(crd.data)

    unsub = crd.async_add_listener(update_callback)
    await crd.async_refresh()
    expect(updates).to_equal([2])
    expect(crd._unsub_refresh is not None).to_be(True)

    unsub()
    await crd.async_refresh()
    expect(updates).to_equal([2])


@test
async def shutdown(
    hass: HomeAssistant = Depends(hass),
    crd: update_coordinator.DataUpdateCoordinator[int] = Depends(crd),
) -> None:
    """Test async_shutdown for update coordinator."""
    expect(crd.data).to_be_none()
    await crd.async_refresh()
    expect(crd.data).to_equal(1)
    expect(crd.last_update_success).to_be(True)
    expect(crd._unsub_refresh).to_be_none()

    updates: list[int] = []

    def update_callback() -> None:
        updates.append(crd.data)

    _ = crd.async_add_listener(update_callback)
    await crd.async_refresh()
    expect(updates).to_equal([2])
    expect(crd._unsub_refresh is not None).to_be(True)

    with patch.object(crd._debounced_refresh, "async_shutdown") as mock_shutdown:
        await crd.async_shutdown()

    async_fire_time_changed(hass, utcnow() + crd.update_interval)
    await hass.async_block_till_done()

    expect(len(mock_shutdown.mock_calls)).to_equal(1)
    expect(crd._unsub_refresh).to_be_none()

    await crd.async_refresh()
    expect(updates).to_equal([2])


@test
async def shutdown_on_entry_unload(
    hass: HomeAssistant = Depends(hass),
    crd: update_coordinator.DataUpdateCoordinator[int] = Depends(crd),
) -> None:
    """Test shutdown is requested on entry unload."""
    entry = MockConfigEntry()
    calls = 0

    async def _refresh() -> int:
        nonlocal calls
        calls += 1
        return calls

    crd = update_coordinator.DataUpdateCoordinator[int](
        hass,
        _LOGGER,
        config_entry=entry,
        name="test",
        update_method=_refresh,
        update_interval=DEFAULT_UPDATE_INTERVAL,
    )

    crd.async_add_listener(lambda: None)
    expect(crd._unsub_refresh is not None).to_be(True)
    expect(crd._shutdown_requested).to_be(False)

    await entry._async_process_on_unload(hass)

    expect(crd._shutdown_requested).to_be(True)
    expect(crd._unsub_refresh).to_be_none()


@test
async def shutdown_on_hass_stop(
    hass: HomeAssistant = Depends(hass),
    crd: update_coordinator.DataUpdateCoordinator[int] = Depends(crd),
) -> None:
    """Test shutdown can be shutdown on STOP event."""
    calls = 0

    async def _refresh() -> int:
        nonlocal calls
        calls += 1
        return calls

    crd = update_coordinator.DataUpdateCoordinator[int](
        hass,
        _LOGGER,
        config_entry=None,
        name="test",
        update_method=_refresh,
        update_interval=DEFAULT_UPDATE_INTERVAL,
    )
    await crd.async_register_shutdown()

    crd.async_add_listener(lambda: None)
    expect(crd._unsub_refresh is not None).to_be(True)
    expect(crd._shutdown_requested).to_be(False)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()

    expect(crd._shutdown_requested).to_be(True)
    expect(crd._unsub_refresh).to_be_none()


@test
async def update_context(
    crd: update_coordinator.DataUpdateCoordinator[int] = Depends(crd),
) -> None:
    """Test update contexts for the update coordinator."""
    await crd.async_refresh()
    expect(set(crd.async_contexts())).to_equal(set())

    def update_callback1() -> None:
        pass

    def update_callback2() -> None:
        pass

    unsub1 = crd.async_add_listener(update_callback1, 1)
    expect(set(crd.async_contexts())).to_equal({1})

    unsub2 = crd.async_add_listener(update_callback2, 2)
    expect(set(crd.async_contexts())).to_equal({1, 2})

    unsub1()
    expect(set(crd.async_contexts())).to_equal({2})

    unsub2()
    expect(set(crd.async_contexts())).to_equal(set())


@test
async def request_refresh(
    crd: update_coordinator.DataUpdateCoordinator[int] = Depends(crd),
) -> None:
    """Test request refresh for update coordinator."""
    expect(crd.data).to_be_none()
    await crd.async_request_refresh()
    expect(crd.data).to_equal(1)
    expect(crd.last_update_success).to_be(True)

    await crd.async_request_refresh()
    expect(crd.data).to_equal(1)
    expect(crd.last_update_success).to_be(True)

    crd._unschedule_refresh()


@test
async def request_refresh_no_auto_update(
    crd_without_update_interval: update_coordinator.DataUpdateCoordinator[int] = Depends(
        crd_without_update_interval
    ),
) -> None:
    """Test request refresh for update coordinator without automatic update."""
    crd = crd_without_update_interval
    expect(crd.data).to_be_none()
    await crd.async_request_refresh()
    expect(crd.data).to_equal(1)
    expect(crd.last_update_success).to_be(True)

    await crd.async_request_refresh()
    expect(crd.data).to_equal(1)
    expect(crd.last_update_success).to_be(True)

    crd._unschedule_refresh()


@test.cases(
    test.case("err_msg0", idx=0),
    test.case("err_msg1", idx=1),
    test.case("err_msg2", idx=2),
    test.case("err_msg3", idx=3),
    test.case("err_msg4", idx=4),
    test.case("err_msg5", idx=5),
    test.case("err_msg6", idx=6),
)
async def refresh_known_errors(
    idx: int,
    crd: update_coordinator.DataUpdateCoordinator[int] = Depends(crd),
    caplog: Any = Depends(caplog),
) -> None:
    """Test raising known errors."""
    err_msg = KNOWN_ERRORS[idx]
    crd.update_method = AsyncMock(side_effect=err_msg[0])

    await crd.async_refresh()

    expect(crd.data).to_be_none()
    expect(crd.last_update_success).to_be(False)
    expect(isinstance(crd.last_exception, err_msg[1])).to_be(True)
    expect(caplog.text).to_contain(err_msg[2])


@test
async def refresh_fail_unknown(
    crd: update_coordinator.DataUpdateCoordinator[int] = Depends(crd),
    caplog: Any = Depends(caplog),
) -> None:
    """Test raising unknown error."""
    await crd.async_refresh()

    crd.update_method = AsyncMock(side_effect=ValueError)

    await crd.async_refresh()

    expect(crd.data).to_equal(1)
    expect(crd.last_update_success).to_be(False)
    expect(caplog.text).to_contain("Unexpected error fetching test data")


@test.cases(
    test.case(
        "exception0-expected_exception0",
        exception=OAuth2TokenRequestReauthError,
        expected_exception=ConfigEntryAuthFailed,
    ),
)
async def oauth_token_request_refresh_errors(
    exception: type[OAuth2TokenRequestError],
    expected_exception: type[Exception],
    crd: update_coordinator.DataUpdateCoordinator[int] = Depends(crd),
) -> None:
    """Test OAuth2 token request errors are mapped during refresh."""
    request_info = Mock()
    request_info.real_url = "http://example.com/token"
    request_info.method = "POST"

    oauth_exception = exception(
        request_info=request_info,
        history=(),
        status=400,
        message="OAuth 2.0 token refresh failed",
        domain="domain",
    )

    crd.update_method = AsyncMock(side_effect=oauth_exception)

    err: Exception | None = None
    try:
        await crd._async_refresh(raise_on_auth_failed=True)
    except expected_exception as exc:
        err = exc

    expect(err is not None).to_be(True)
    expect(isinstance(err, expected_exception)).to_be(True)
    expect(isinstance(err.__cause__, exception)).to_be(True)
    expect(isinstance(err.__cause__, OAuth2TokenRequestError)).to_be(True)


@test.cases(
    test.case(
        "exception0-expected_exception0",
        exception=OAuth2TokenRequestReauthError,
        expected_exception=ConfigEntryAuthFailed,
    ),
    test.case(
        "exception1-expected_exception1",
        exception=OAuth2TokenRequestError,
        expected_exception=ConfigEntryNotReady,
    ),
)
async def token_request_setup_errors(
    exception: type[OAuth2TokenRequestError],
    expected_exception: type[Exception],
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test OAuth2 token request errors raised from setup."""
    entry = MockConfigEntry()
    entry._async_set_state(
        hass, config_entries.ConfigEntryState.SETUP_IN_PROGRESS, "For testing, duh"
    )
    crd = get_crd(hass, DEFAULT_UPDATE_INTERVAL, entry)

    request_info = Mock()
    request_info.real_url = "http://example.com/token"
    request_info.method = "POST"
    oauth_exception = exception(
        request_info=request_info,
        history=(),
        status=400,
        message="OAuth 2.0 token refresh failed",
        domain="domain",
    )

    crd.setup_method = AsyncMock(side_effect=oauth_exception)

    err: Exception | None = None
    try:
        await crd.async_config_entry_first_refresh()
    except expected_exception as exc:
        err = exc

    expect(err is not None).to_be(True)
    expect(crd.last_update_success).to_be(False)
    expect(isinstance(err, expected_exception)).to_be(True)
    expect(isinstance(err.__cause__, exception)).to_be(True)
    expect(isinstance(err.__cause__, OAuth2TokenRequestError)).to_be(True)


@test
async def refresh_no_update_method(
    crd: update_coordinator.DataUpdateCoordinator[int] = Depends(crd),
) -> None:
    """Test raising error is no update method is provided."""
    await crd.async_refresh()

    crd.update_method = None

    await _expect_raises_async(NotImplementedError, crd.async_refresh())


@test
async def refresh_cancelled(
    hass: HomeAssistant = Depends(hass),
    crd: update_coordinator.DataUpdateCoordinator[int] = Depends(crd),
) -> None:
    """Test that we don't swallow cancellation."""
    await crd.async_refresh()

    start = asyncio.Event()
    abort = asyncio.Event()

    async def _update() -> bool:
        start.set()
        await abort.wait()
        return True

    crd.update_method = _update
    crd.last_update_success = True

    task = hass.async_create_task(crd.async_refresh())
    await start.wait()
    task.cancel()

    await _expect_raises_async(asyncio.CancelledError, task)

    abort.set()
    expect(crd.last_update_success).to_be(False)


@test
async def update_interval(
    hass: HomeAssistant = Depends(hass),
    freezer: FrozenDateTimeFactory = Depends(freezer),
    crd: update_coordinator.DataUpdateCoordinator[int] = Depends(crd),
) -> None:
    """Test update interval works."""
    freezer.tick(crd.update_interval)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect(crd.data).to_be_none()

    update_callback = Mock()
    unsub = crd.async_add_listener(update_callback)

    freezer.tick(crd.update_interval)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect(crd.data).to_equal(1)

    freezer.tick(crd.update_interval)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect(crd.data).to_equal(2)

    unsub()

    freezer.tick(crd.update_interval)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(crd.data).to_equal(2)


@test
async def update_interval_not_present(
    hass: HomeAssistant = Depends(hass),
    crd_without_update_interval: update_coordinator.DataUpdateCoordinator[int] = Depends(
        crd_without_update_interval
    ),
) -> None:
    """Test update never happens with no update interval."""
    crd = crd_without_update_interval
    async_fire_time_changed(hass, utcnow() + DEFAULT_UPDATE_INTERVAL)
    await hass.async_block_till_done()
    expect(crd.data).to_be_none()

    update_callback = Mock()
    unsub = crd.async_add_listener(update_callback)

    async_fire_time_changed(hass, utcnow() + DEFAULT_UPDATE_INTERVAL)
    await hass.async_block_till_done()
    expect(crd.data).to_be_none()

    async_fire_time_changed(hass, utcnow() + DEFAULT_UPDATE_INTERVAL)
    await hass.async_block_till_done()
    expect(crd.data).to_be_none()

    unsub()

    async_fire_time_changed(hass, utcnow() + DEFAULT_UPDATE_INTERVAL)
    await hass.async_block_till_done()

    expect(crd.data).to_be_none()


@test
async def update_locks(
    hass: HomeAssistant = Depends(hass),
    freezer: FrozenDateTimeFactory = Depends(freezer),
    crd: update_coordinator.DataUpdateCoordinator[int] = Depends(crd),
) -> None:
    """Test update interval works."""
    start = asyncio.Event()
    block = asyncio.Event()

    async def _update_method() -> int:
        start.set()
        await block.wait()
        block.clear()
        return 0

    crd.update_method = _update_method

    update_callback = Mock()
    remove_callbacks = crd.async_add_listener(update_callback)

    expect(crd.update_interval is not None).to_be(True)

    freezer.tick(crd.update_interval)
    async_fire_time_changed(hass)
    await start.wait()
    start.clear()

    task = hass.async_create_background_task(crd.async_refresh(), "", eager_start=True)
    freezer.tick(timedelta(seconds=60))
    async_fire_time_changed(hass)

    expect(start.is_set()).to_be(False)

    block.set()

    await start.wait()
    start.clear()

    await crd.async_request_refresh()
    expect(start.is_set()).to_be(False)

    block.set()
    await task

    freezer.tick(timedelta(seconds=60))
    async_fire_time_changed(hass)
    await start.wait()
    start.clear()

    block.set()

    remove_callbacks()
    await crd.async_shutdown()


@test
async def refresh_recover(
    crd: update_coordinator.DataUpdateCoordinator[int] = Depends(crd),
    caplog: Any = Depends(caplog),
) -> None:
    """Test recovery of freshing data."""
    crd.last_update_success = False

    await crd.async_refresh()

    expect(crd.last_update_success).to_be(True)
    expect(caplog.text).to_contain("Fetching test data recovered")


@test
async def coordinator_entity(
    crd: update_coordinator.DataUpdateCoordinator[int] = Depends(crd),
) -> None:
    """Test the CoordinatorEntity class."""
    context = object()
    entity = update_coordinator.CoordinatorEntity(crd, context)

    expect(entity.should_poll).to_be(False)

    crd.last_update_success = False
    expect(entity.available).to_be(False)

    await entity.async_update()
    expect(entity.available).to_be(True)

    with patch(
        "homeassistant.helpers.entity.Entity.async_on_remove"
    ) as mock_async_on_remove:
        await entity.async_added_to_hass()

    mock_async_on_remove.assert_called_once()
    _on_remove_callback = mock_async_on_remove.call_args[0][0]

    crd.last_update_success = False
    with patch("homeassistant.helpers.entity.Entity.enabled", False):
        await entity.async_update()
    expect(entity.available).to_be(False)

    expect(list(crd.async_contexts())).to_equal([context])

    expect(len(crd._listeners)).to_equal(1)
    _on_remove_callback()
    expect(len(crd._listeners)).to_equal(0)


@test
async def async_set_updated_data(
    crd: update_coordinator.DataUpdateCoordinator[int] = Depends(crd),
) -> None:
    """Test async_set_updated_data for update coordinator."""
    expect(crd.data).to_be_none()

    with patch.object(crd._debounced_refresh, "async_cancel") as mock_cancel:
        crd.async_set_updated_data(100)
        expect(len(mock_cancel.mock_calls)).to_equal(1)

    expect(crd.data).to_equal(100)
    expect(crd.last_update_success).to_be(True)

    expect(crd._unsub_refresh).to_be_none()

    updates: list[int] = []

    def update_callback() -> None:
        updates.append(crd.data)

    remove_callbacks = crd.async_add_listener(update_callback)
    crd.async_set_updated_data(200)
    expect(updates).to_equal([200])
    expect(crd._unsub_refresh is not None).to_be(True)

    old_refresh = crd._unsub_refresh

    crd.async_set_updated_data(300)
    expect(crd._unsub_refresh is not old_refresh).to_be(True)

    remove_callbacks()


@test
async def stop_refresh_on_ha_stop(
    hass: HomeAssistant = Depends(hass),
    crd: update_coordinator.DataUpdateCoordinator[int] = Depends(crd),
) -> None:
    """Test no update interval refresh when Home Assistant is stopping."""
    update_callback = Mock()
    crd.async_add_listener(update_callback)

    update_interval = crd.update_interval

    async_fire_time_changed(hass, utcnow() + update_interval)
    await hass.async_block_till_done()
    expect(crd.data).to_equal(1)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    hass.set_state(CoreState.stopping)
    await hass.async_block_till_done()

    async_fire_time_changed(hass, utcnow() + update_interval)
    await hass.async_block_till_done()
    expect(crd.data).to_equal(1)

    await crd.async_refresh()
    expect(crd.data).to_equal(2)

    async_fire_time_changed(hass, utcnow() + update_interval)
    await hass.async_block_till_done()
    expect(crd.data).to_equal(2)


_FIRST_REFRESH_FAILURE_ERRORS: list[tuple[Exception, type[Exception], str]] = [
    *KNOWN_ERRORS,
    (Exception(), Exception, "Unknown exception"),
]


async def _first_refresh_failure_impl(
    hass: HomeAssistant,
    caplog: Any,
    method: str,
    idx: int,
) -> None:
    err_msg = _FIRST_REFRESH_FAILURE_ERRORS[idx]
    entry = MockConfigEntry()
    entry._async_set_state(
        hass, config_entries.ConfigEntryState.SETUP_IN_PROGRESS, None
    )
    crd = get_crd(hass, DEFAULT_UPDATE_INTERVAL, entry)
    setattr(crd, method, AsyncMock(side_effect=err_msg[0]))

    await _expect_raises_async(
        ConfigEntryNotReady, crd.async_config_entry_first_refresh()
    )

    expect(crd.last_update_success).to_be(False)
    expect(isinstance(crd.last_exception, err_msg[1])).to_be(True)
    expect(err_msg[2] not in caplog.text).to_be(True)


@test.cases(
    test.case("update_method-err_msg0", method="update_method", idx=0),
    test.case("update_method-err_msg1", method="update_method", idx=1),
    test.case("update_method-err_msg2", method="update_method", idx=2),
    test.case("update_method-err_msg3", method="update_method", idx=3),
    test.case("update_method-err_msg4", method="update_method", idx=4),
    test.case("update_method-err_msg5", method="update_method", idx=5),
    test.case("update_method-err_msg6", method="update_method", idx=6),
    test.case("update_method-err_msg7", method="update_method", idx=7),
    test.case("setup_method-err_msg0", method="setup_method", idx=0),
    test.case("setup_method-err_msg1", method="setup_method", idx=1),
    test.case("setup_method-err_msg2", method="setup_method", idx=2),
    test.case("setup_method-err_msg3", method="setup_method", idx=3),
    test.case("setup_method-err_msg4", method="setup_method", idx=4),
    test.case("setup_method-err_msg5", method="setup_method", idx=5),
    test.case("setup_method-err_msg6", method="setup_method", idx=6),
    test.case("setup_method-err_msg7", method="setup_method", idx=7),
)
async def async_config_entry_first_refresh_failure(
    method: str,
    idx: int,
    hass: HomeAssistant = Depends(hass),
    caplog: Any = Depends(caplog),
) -> None:
    """Test async_config_entry_first_refresh raises ConfigEntryNotReady on failure."""
    await _first_refresh_failure_impl(hass, caplog, method, idx)


_FIRST_REFRESH_PASSED_THROUGH_ERRORS: list[tuple[Exception, type[Exception], str]] = [
    (ConfigEntryError(), ConfigEntryError, "Config entry error"),
    (ConfigEntryAuthFailed(), ConfigEntryAuthFailed, "Config entry error"),
]


async def _first_refresh_passed_through_impl(
    hass: HomeAssistant,
    caplog: Any,
    method: str,
    idx: int,
) -> None:
    err_msg = _FIRST_REFRESH_PASSED_THROUGH_ERRORS[idx]
    entry = MockConfigEntry()
    entry._async_set_state(
        hass, config_entries.ConfigEntryState.SETUP_IN_PROGRESS, None
    )
    crd = get_crd(hass, DEFAULT_UPDATE_INTERVAL, entry)
    setattr(crd, method, AsyncMock(side_effect=err_msg[0]))

    await _expect_raises_async(err_msg[1], crd.async_config_entry_first_refresh())

    expect(crd.last_update_success).to_be(False)
    expect(isinstance(crd.last_exception, err_msg[1])).to_be(True)
    expect(err_msg[2] not in caplog.text).to_be(True)


@test.cases(
    test.case("update_method-err_msg0", method="update_method", idx=0),
    test.case("update_method-err_msg1", method="update_method", idx=1),
    test.case("setup_method-err_msg0", method="setup_method", idx=0),
    test.case("setup_method-err_msg1", method="setup_method", idx=1),
)
async def async_config_entry_first_refresh_failure_passed_through(
    method: str,
    idx: int,
    hass: HomeAssistant = Depends(hass),
    caplog: Any = Depends(caplog),
) -> None:
    """Test first_refresh passes ConfigEntryError / ConfigEntryAuthFailed through."""
    await _first_refresh_passed_through_impl(hass, caplog, method, idx)


@test
async def async_config_entry_first_refresh_success(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test first refresh successfully."""
    entry = MockConfigEntry()
    entry._async_set_state(
        hass, config_entries.ConfigEntryState.SETUP_IN_PROGRESS, None
    )
    crd = get_crd(hass, DEFAULT_UPDATE_INTERVAL, entry)
    crd.setup_method = AsyncMock()
    await crd.async_config_entry_first_refresh()

    expect(crd.last_update_success).to_be(True)
    crd.setup_method.assert_called_once()


@test
async def async_config_entry_first_refresh_invalid_state(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test first refresh fails due to invalid state."""
    entry = MockConfigEntry()
    crd = get_crd(hass, DEFAULT_UPDATE_INTERVAL, entry)
    crd.setup_method = AsyncMock()
    await _expect_raises_async(
        config_entries.ConfigEntryError,
        crd.async_config_entry_first_refresh(),
        match=(
            "`async_config_entry_first_refresh` called when config entry state is "
            "ConfigEntryState.NOT_LOADED, but should only be called in state "
            "ConfigEntryState.SETUP_IN_PROGRESS"
        ),
    )

    expect(entry.state is config_entries.ConfigEntryState.NOT_LOADED).to_be(True)

    expect(crd.last_update_success).to_be(True)
    crd.setup_method.assert_not_called()


@test
async def async_config_entry_first_refresh_invalid_state_in_integration(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test first refresh fails, because of wrong state."""
    with _mock_integration_frame("homeassistant/components/my_integration"):
        entry = MockConfigEntry()
        crd = get_crd(hass, DEFAULT_UPDATE_INTERVAL, entry)
        crd.setup_method = AsyncMock()

        await _expect_raises_async(
            config_entries.ConfigEntryError,
            crd.async_config_entry_first_refresh(),
            match=(
                "`async_config_entry_first_refresh` called when config entry state is "
                "ConfigEntryState.NOT_LOADED, but should only be called in state "
                "ConfigEntryState.SETUP_IN_PROGRESS"
            ),
        )

        expect(crd.last_update_success).to_be(True)
        crd.setup_method.assert_not_called()


@test
async def async_config_entry_first_refresh_no_entry(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test first refresh successfully."""
    crd = get_crd(hass, DEFAULT_UPDATE_INTERVAL, None)
    crd.setup_method = AsyncMock()
    await _expect_raises_async(
        ConfigEntryError,
        crd.async_config_entry_first_refresh(),
        match=(
            "Detected code that uses `async_config_entry_first_refresh`, "
            "which is only supported for coordinators with a config entry"
        ),
    )

    expect(crd.last_update_success).to_be(True)
    crd.setup_method.assert_not_called()


@test
async def not_schedule_refresh_if_system_option_disable_polling(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test we do not schedule a refresh if disable polling in config entry."""
    entry = MockConfigEntry(pref_disable_polling=True)
    crd = get_crd(hass, DEFAULT_UPDATE_INTERVAL, entry)
    crd.async_add_listener(lambda: None)
    expect(crd._unsub_refresh).to_be_none()


@test
async def async_set_update_error(
    crd: update_coordinator.DataUpdateCoordinator[int] = Depends(crd),
    caplog: Any = Depends(caplog),
) -> None:
    """Test manually setting an update failure."""
    update_callback = Mock()
    remove_callbacks = crd.async_add_listener(update_callback)

    crd.async_set_update_error(aiohttp.ClientError("Client Failure #1"))
    expect(crd.last_update_success).to_be(False)
    expect(caplog.text).to_contain("Client Failure #1")
    update_callback.assert_called_once()
    update_callback.reset_mock()

    crd.async_set_update_error(aiohttp.ClientError("Client Failure #2"))
    expect(crd.last_update_success).to_be(False)
    expect("Client Failure #2" not in caplog.text).to_be(True)
    update_callback.assert_not_called()
    update_callback.reset_mock()

    crd.async_set_updated_data(200)
    expect(crd.last_update_success).to_be(True)
    update_callback.assert_called_once()
    update_callback.reset_mock()

    crd.async_set_update_error(aiohttp.ClientError("Client Failure #3"))
    expect(crd.last_update_success).to_be(False)
    expect("Client Failure #2" not in caplog.text).to_be(True)
    update_callback.assert_called_once()

    remove_callbacks()


@test
async def only_callback_on_change_when_always_update_is_false(
    crd: update_coordinator.DataUpdateCoordinator[int] = Depends(crd),
) -> None:
    """Test we do not callback listeners unless something has actually changed."""
    update_callback = Mock()
    crd.always_update = False
    remove_callbacks = crd.async_add_listener(update_callback)
    mocked_data: dict[str, int] | None = None
    mocked_exception: Exception | None = None

    async def _update_method() -> Any:
        nonlocal mocked_data
        nonlocal mocked_exception
        if mocked_exception is not None:
            raise mocked_exception
        return mocked_data

    crd.update_method = _update_method

    mocked_data = {"a": 1}
    await crd.async_refresh()
    update_callback.assert_called_once()
    update_callback.reset_mock()

    mocked_data = {"a": 1}
    await crd.async_refresh()
    update_callback.assert_not_called()
    update_callback.reset_mock()

    mocked_data = None
    mocked_exception = aiohttp.ClientError("Client Failure #1")
    await crd.async_refresh()
    update_callback.assert_called_once()
    update_callback.reset_mock()

    mocked_data = None
    mocked_exception = aiohttp.ClientError("Client Failure #1")
    await crd.async_refresh()
    update_callback.assert_not_called()
    update_callback.reset_mock()

    mocked_exception = None
    mocked_data = {"a": 1}
    await crd.async_refresh()
    update_callback.assert_called_once()
    update_callback.reset_mock()

    mocked_data = {"a": 1}
    await crd.async_refresh()
    update_callback.assert_not_called()
    update_callback.reset_mock()

    mocked_data = {"a": 2}
    await crd.async_refresh()
    update_callback.assert_called_once()
    update_callback.reset_mock()

    mocked_data = {"a": 2}
    await crd.async_refresh()
    update_callback.assert_not_called()
    update_callback.reset_mock()

    mocked_data = {"a": 2, "b": 3}
    await crd.async_refresh()
    update_callback.assert_called_once()
    update_callback.reset_mock()

    remove_callbacks()


@test
async def always_callback_when_always_update_is_true(
    crd: update_coordinator.DataUpdateCoordinator[int] = Depends(crd),
) -> None:
    """Test we callback listeners even though the data is the same."""
    update_callback = Mock()
    remove_callbacks = crd.async_add_listener(update_callback)
    mocked_data: dict[str, int] | None = None
    mocked_exception: Exception | None = None

    async def _update_method() -> Any:
        nonlocal mocked_data
        nonlocal mocked_exception
        if mocked_exception is not None:
            raise mocked_exception
        return mocked_data

    crd.update_method = _update_method

    mocked_data = {"a": 1}
    await crd.async_refresh()
    update_callback.assert_called_once()
    update_callback.reset_mock()

    mocked_data = {"a": 1}
    await crd.async_refresh()
    update_callback.assert_called_once()
    update_callback.reset_mock()

    mocked_data = None
    mocked_exception = aiohttp.ClientError("Client Failure #1")
    await crd.async_refresh()
    update_callback.assert_called_once()
    update_callback.reset_mock()

    mocked_data = None
    mocked_exception = aiohttp.ClientError("Client Failure #1")
    await crd.async_refresh()
    update_callback.assert_not_called()
    update_callback.reset_mock()

    remove_callbacks()


@test
async def timestamp_date_update_coordinator(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test last_update_success_time is set before calling listeners."""
    last_update_success_times: list[datetime | None] = []

    async def refresh() -> int:
        return 1

    crd = update_coordinator.TimestampDataUpdateCoordinator[int](
        hass,
        _LOGGER,
        config_entry=None,
        name="test",
        update_method=refresh,
        update_interval=timedelta(seconds=10),
    )

    @callback
    def listener() -> None:
        last_update_success_times.append(crd.last_update_success_time)

    unsub = crd.async_add_listener(listener)

    await crd.async_refresh()

    expect(len(last_update_success_times)).to_equal(1)
    expect(last_update_success_times != [None]).to_be(True)

    unsub()
    await crd.async_refresh()
    expect(len(last_update_success_times)).to_equal(1)


@test.cases(
    test.case("homeassistant/components/my_integration"),
)
async def config_entry(
    hass: HomeAssistant = Depends(hass),
    caplog: Any = Depends(caplog),
) -> None:
    """Test behavior of coordinator.entry."""
    with _mock_integration_frame("homeassistant/components/my_integration"):
        # Pytest's autouse verify_cleanup clears this between tests; under
        # Tryke the set leaks, so reset it explicitly at test start.
        frame._REPORTED_INTEGRATIONS.clear()

        entry = MockConfigEntry()

        crd = update_coordinator.DataUpdateCoordinator[int](
            hass, _LOGGER, name="test", config_entry=None
        )
        expect(crd.config_entry).to_be_none()
        expect(
            "Detected that integration 'my_integration' relies on ContextVar"
            not in caplog.text
        ).to_be(True)

        caplog.clear()
        crd = update_coordinator.DataUpdateCoordinator[int](
            hass, _LOGGER, name="test", config_entry=entry
        )
        expect(crd.config_entry is entry).to_be(True)
        expect(
            "Detected that integration 'my_integration' relies on ContextVar"
            not in caplog.text
        ).to_be(True)

        another_entry = MockConfigEntry()
        caplog.clear()
        crd = update_coordinator.DataUpdateCoordinator[int](
            hass, _LOGGER, name="test", config_entry=another_entry
        )
        expect(crd.config_entry is another_entry).to_be(True)
        expect(
            "Detected that integration 'my_integration' relies on ContextVar"
            not in caplog.text
        ).to_be(True)

        caplog.clear()
        crd = update_coordinator.DataUpdateCoordinator[int](
            hass, _LOGGER, name="test"
        )
        expect(crd.config_entry).to_be_none()
        expect(caplog.text).to_contain(
            "Detected that integration 'my_integration' relies on ContextVar, "
            "but should pass the config entry explicitly."
        )

        caplog.clear()
        frame._REPORTED_INTEGRATIONS.clear()
        config_entries.current_entry.set(entry)
        crd = update_coordinator.DataUpdateCoordinator[int](
            hass, _LOGGER, name="test"
        )
        expect(caplog.text).to_contain(
            "Detected that integration 'my_integration' relies on ContextVar, "
            "but should pass the config entry explicitly."
        )
        expect(crd.config_entry is entry).to_be(True)


@test.cases(
    test.case("custom_components/my_integration"),
)
async def config_entry_custom_integration(
    hass: HomeAssistant = Depends(hass),
    caplog: Any = Depends(caplog),
) -> None:
    """Test behavior of coordinator.entry for custom integrations."""
    with _mock_integration_frame("custom_components/my_integration"):
        entry = MockConfigEntry(domain="custom_integration")

        crd = update_coordinator.DataUpdateCoordinator[int](
            hass, _LOGGER, name="test"
        )

        expect(crd.config_entry).to_be_none()
        frame_records = [
            record
            for record in caplog.records
            if record.name == "homeassistant.helpers.frame"
            and record.levelno >= logging.WARNING
        ]
        expect(len(frame_records)).to_equal(0)

        caplog.clear()

        crd = update_coordinator.DataUpdateCoordinator[int](
            hass, _LOGGER, name="test", config_entry=None
        )

        expect(crd.config_entry).to_be_none()
        expect(
            "Detected that integration 'my_integration' relies on ContextVar"
            not in caplog.text
        ).to_be(True)

        caplog.clear()

        crd = update_coordinator.DataUpdateCoordinator[int](
            hass, _LOGGER, name="test", config_entry=entry
        )

        expect(crd.config_entry is entry).to_be(True)
        frame_records = [
            record
            for record in caplog.records
            if record.name == "homeassistant.helpers.frame"
            and record.levelno >= logging.WARNING
        ]
        expect(len(frame_records)).to_equal(0)

        config_entries.current_entry.set(entry)

        caplog.clear()

        crd = update_coordinator.DataUpdateCoordinator[int](
            hass, _LOGGER, name="test"
        )

        expect(crd.config_entry is entry).to_be(True)
        frame_records = [
            record
            for record in caplog.records
            if record.name == "homeassistant.helpers.frame"
            and record.levelno >= logging.WARNING
        ]
        expect(len(frame_records)).to_equal(0)

        another_entry = MockConfigEntry()
        caplog.clear()

        crd = update_coordinator.DataUpdateCoordinator[int](
            hass, _LOGGER, name="test", config_entry=another_entry
        )

        expect(crd.config_entry is another_entry).to_be(True)
        frame_records = [
            record
            for record in caplog.records
            if record.name == "homeassistant.helpers.frame"
            and record.levelno >= logging.WARNING
        ]
        expect(len(frame_records)).to_equal(0)


@test
async def listener_unsubscribe_releases_coordinator(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test listener subscribe/unsubscribe releases parent class."""

    class Subscriber:
        _unsub: CALLBACK_TYPE | None = None

        def start_listen(
            self, coordinator: update_coordinator.DataUpdateCoordinator
        ) -> None:
            self._unsub = coordinator.async_add_listener(lambda: None)

        def stop_listen(self) -> None:
            self._unsub()
            self._unsub = None

    coordinator = update_coordinator.DataUpdateCoordinator[int](
        hass, _LOGGER, config_entry=None, name="test"
    )
    subscriber = Subscriber()
    subscriber.start_listen(coordinator)

    weak_ref = weakref.ref(coordinator)
    expect(weak_ref() is not None).to_be(True)

    subscriber.stop_listen()
    await coordinator.async_shutdown()
    del coordinator

    expect(weak_ref() is None).to_be(True)


_UPDATE_FAILED_RETRY_AFTER_ERRORS: list[tuple[Exception, type[Exception], str]] = [
    *KNOWN_ERRORS,
    (Exception(), Exception, "Unknown exception"),
    (
        update_coordinator.UpdateFailed(retry_after=60),
        update_coordinator.UpdateFailed,
        "Error fetching test data",
    ),
]


async def _update_failed_retry_after_impl(
    hass: HomeAssistant,
    caplog: Any,
    method: str,
    idx: int,
) -> None:
    exc, expected_exception, message = _UPDATE_FAILED_RETRY_AFTER_ERRORS[idx]
    entry = MockConfigEntry()
    entry.mock_state(
        hass,
        config_entries.ConfigEntryState.SETUP_IN_PROGRESS,
    )
    crd = get_crd(hass, DEFAULT_UPDATE_INTERVAL, entry)
    setattr(crd, method, AsyncMock(side_effect=exc))

    await _expect_raises_async(
        ConfigEntryNotReady, crd.async_config_entry_first_refresh()
    )

    expect(crd.last_update_success).to_be(False)
    expect(isinstance(crd.last_exception, expected_exception)).to_be(True)
    expect(message not in caplog.text).to_be(True)
    expect(crd._retry_after).to_be_none()


@test.cases(
    test.case(
        "update_method-exc0-TimeoutError-Timeout fetching test data",
        method="update_method",
        idx=0,
    ),
    test.case(
        "update_method-exc1-Timeout-Timeout fetching test data",
        method="update_method",
        idx=1,
    ),
    test.case(
        "update_method-exc2-URLError-Timeout fetching test data",
        method="update_method",
        idx=2,
    ),
    test.case(
        "update_method-exc3-ClientError-Error requesting test data",
        method="update_method",
        idx=3,
    ),
    test.case(
        "update_method-exc4-RequestException-Error requesting test data",
        method="update_method",
        idx=4,
    ),
    test.case(
        "update_method-exc5-URLError-Error requesting test data",
        method="update_method",
        idx=5,
    ),
    test.case(
        "update_method-exc6-UpdateFailed-Error fetching test data",
        method="update_method",
        idx=6,
    ),
    test.case(
        "update_method-exc7-Exception-Unknown exception",
        method="update_method",
        idx=7,
    ),
    test.case(
        "update_method-exc8-UpdateFailed-Error fetching test data",
        method="update_method",
        idx=8,
    ),
    test.case(
        "setup_method-exc0-TimeoutError-Timeout fetching test data",
        method="setup_method",
        idx=0,
    ),
    test.case(
        "setup_method-exc1-Timeout-Timeout fetching test data",
        method="setup_method",
        idx=1,
    ),
    test.case(
        "setup_method-exc2-URLError-Timeout fetching test data",
        method="setup_method",
        idx=2,
    ),
    test.case(
        "setup_method-exc3-ClientError-Error requesting test data",
        method="setup_method",
        idx=3,
    ),
    test.case(
        "setup_method-exc4-RequestException-Error requesting test data",
        method="setup_method",
        idx=4,
    ),
    test.case(
        "setup_method-exc5-URLError-Error requesting test data",
        method="setup_method",
        idx=5,
    ),
    test.case(
        "setup_method-exc6-UpdateFailed-Error fetching test data",
        method="setup_method",
        idx=6,
    ),
    test.case(
        "setup_method-exc7-Exception-Unknown exception",
        method="setup_method",
        idx=7,
    ),
    test.case(
        "setup_method-exc8-UpdateFailed-Error fetching test data",
        method="setup_method",
        idx=8,
    ),
)
async def update_failed_retry_after(
    method: str,
    idx: int,
    hass: HomeAssistant = Depends(hass),
    caplog: Any = Depends(caplog),
) -> None:
    """Test async_config_entry_first_refresh raises ConfigEntryNotReady on failure."""
    await _update_failed_retry_after_impl(hass, caplog, method, idx)


@test.cases(
    test.case(
        "exc0-UpdateFailed-Error fetching test data",
    ),
)
async def refresh_known_errors_retry_after(
    hass: HomeAssistant = Depends(hass),
    crd: update_coordinator.DataUpdateCoordinator[int] = Depends(crd),
    caplog: Any = Depends(caplog),
) -> None:
    """Test raising known errors, this time with retry_after."""
    exc = update_coordinator.UpdateFailed(retry_after=60)
    expected_exception = update_coordinator.UpdateFailed
    message = "Error fetching test data"

    unsub = crd.async_add_listener(lambda: None)

    crd.update_method = AsyncMock(side_effect=exc)

    with (
        patch.object(hass.loop, "time", return_value=1_000.0),
        patch.object(hass.loop, "call_at") as mock_call_at,
    ):
        await crd.async_refresh()

        expect(crd.data).to_be_none()
        expect(crd.last_update_success).to_be(False)
        expect(isinstance(crd.last_exception, expected_exception)).to_be(True)
        expect(caplog.text).to_contain(message)

        when = mock_call_at.call_args[0][0]

        expected = 1_000.0 + crd._microsecond + exc.retry_after
        expect(abs(when - expected) < 0.005).to_be(True)

        expect(crd._retry_after).to_be_none()

        mock_call_at.reset_mock()
        crd._schedule_refresh()
        when2 = mock_call_at.call_args[0][0]
        expected_cancelled = (
            1_000.0 + crd._microsecond + crd.update_interval.total_seconds()
        )
        expect(abs(when2 - expected_cancelled) < 0.005).to_be(True)

    unsub()
    crd._unschedule_refresh()
