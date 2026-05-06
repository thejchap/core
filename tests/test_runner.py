"""Test the runner."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Iterator
import fcntl
import json
import os
from pathlib import Path
import subprocess
import threading
import time
from typing import Any
from unittest.mock import MagicMock, patch

import packaging.tags
from tryke import Depends, expect, fixture, test

from homeassistant import core, runner
from homeassistant.const import __version__
from homeassistant.core import HomeAssistant
from homeassistant.util import executor, thread

from .hass_fixtures import CapFd, LogCapture, capfd, caplog, hass, tmp_path

# https://github.com/home-assistant/supervisor/blob/main/supervisor/docker/homeassistant.py
SUPERVISOR_HARD_TIMEOUT = 240

TIMEOUT_SAFETY_MARGIN = 10


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


def _run_catching(exc_type: type[BaseException], fn: Callable[..., Any]) -> None:
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(f"Expected {exc_type.__name__}")


@test
async def cumulative_shutdown_timeout_less_than_supervisor() -> None:
    """Verify the cumulative shutdown timeout is at least 10s less than the supervisor."""
    expect(
        core.STOPPING_STAGE_SHUTDOWN_TIMEOUT
        + core.STOP_STAGE_SHUTDOWN_TIMEOUT
        + core.FINAL_WRITE_STAGE_SHUTDOWN_TIMEOUT
        + core.CLOSE_STAGE_SHUTDOWN_TIMEOUT
        + executor.EXECUTOR_SHUTDOWN_TIMEOUT
        + thread.THREADING_SHUTDOWN_TIMEOUT
        + TIMEOUT_SAFETY_MARGIN
        <= SUPERVISOR_HARD_TIMEOUT
    ).to_be_truthy()


@test
async def setup_and_run_hass(
    hass: HomeAssistant = Depends(hass),
    tmp_path: Path = Depends(tmp_path),
) -> None:
    """Test we can setup and run."""
    test_dir = tmp_path / "config"
    test_dir.mkdir()
    default_config = runner.RuntimeConfig(str(test_dir))

    with (
        patch("homeassistant.bootstrap.async_setup_hass", return_value=hass),
        patch("threading._shutdown"),
        patch("homeassistant.core.HomeAssistant.async_run") as mock_run,
    ):
        await runner.setup_and_run_hass(default_config)
        expect(threading._shutdown is thread.deadlock_safe_shutdown).to_be_truthy()

    expect(mock_run.called).to_be_truthy()


@test
def run(
    hass: HomeAssistant = Depends(hass),
    tmp_path: Path = Depends(tmp_path),
) -> None:
    """Test we can run."""
    test_dir = tmp_path / "config"
    test_dir.mkdir()
    default_config = runner.RuntimeConfig(str(test_dir))

    with (
        patch.object(runner, "TASK_CANCELATION_TIMEOUT", 1),
        patch("homeassistant.bootstrap.async_setup_hass", return_value=hass),
        patch("threading._shutdown"),
        patch("homeassistant.core.HomeAssistant.async_run") as mock_run,
    ):
        runner.run(default_config)

    expect(mock_run.called).to_be_truthy()


@test
def run_executor_shutdown_throws(
    hass: HomeAssistant = Depends(hass),
    tmp_path: Path = Depends(tmp_path),
) -> None:
    """Test we can run and we still shutdown if the executor shutdown throws."""
    test_dir = tmp_path / "config"
    test_dir.mkdir()
    default_config = runner.RuntimeConfig(str(test_dir))

    with (
        patch.object(runner, "TASK_CANCELATION_TIMEOUT", 1),
        patch("homeassistant.bootstrap.async_setup_hass", return_value=hass),
        patch("threading._shutdown"),
        patch(
            "homeassistant.runner.InterruptibleThreadPoolExecutor.shutdown",
            side_effect=RuntimeError,
        ) as mock_shutdown,
        patch(
            "homeassistant.core.HomeAssistant.async_run",
        ) as mock_run,
    ):
        _run_catching(RuntimeError, lambda: runner.run(default_config))

    expect(mock_shutdown.called).to_be_truthy()
    expect(mock_run.called).to_be_truthy()


@test
def run_does_not_block_forever_with_shielded_task(
    hass: HomeAssistant = Depends(hass),
    tmp_path: Path = Depends(tmp_path),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test we can shutdown and not block forever."""
    test_dir = tmp_path / "config"
    test_dir.mkdir()
    default_config = runner.RuntimeConfig(str(test_dir))
    tasks: list[asyncio.Future[Any]] = []

    async def _async_create_tasks(*_: Any) -> int:
        async def async_raise(*_: Any) -> None:
            try:
                await asyncio.sleep(2)
            except asyncio.CancelledError:
                raise Exception  # noqa: TRY002

        async def async_shielded(*_: Any) -> None:
            try:
                await asyncio.sleep(2)
            except asyncio.CancelledError:
                await asyncio.sleep(2)

        tasks.append(asyncio.ensure_future(asyncio.shield(async_shielded())))
        tasks.append(asyncio.ensure_future(asyncio.sleep(2)))
        tasks.append(asyncio.ensure_future(async_raise()))
        await asyncio.sleep(0)
        return 0

    with (
        patch.object(runner, "TASK_CANCELATION_TIMEOUT", 0.1),
        patch("homeassistant.bootstrap.async_setup_hass", return_value=hass),
        patch("threading._shutdown"),
        patch("homeassistant.core.HomeAssistant.async_run", _async_create_tasks),
    ):
        runner.run(default_config)

    expect(len(tasks)).to_equal(3)
    expect(caplog.text).to_contain(
        "Task could not be canceled and was still running after shutdown"
    )


@test
async def unhandled_exception_traceback(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test an unhandled exception gets a traceback in debug mode."""

    raised = asyncio.Event()

    async def _unhandled_exception() -> None:
        raised.set()
        raise Exception("This is unhandled")  # noqa: TRY002

    try:
        hass.loop.set_debug(True)
        task = asyncio.create_task(_unhandled_exception(), name="name_of_task")
        await raised.wait()
        # Delete it without checking result to trigger unhandled exception
        del task
    finally:
        hass.loop.set_debug(False)

    expect(caplog.text).to_contain("Task exception was never retrieved")
    expect(caplog.text).to_contain("This is unhandled")
    expect(caplog.text).to_contain("_unhandled_exception")
    expect(caplog.text).to_contain("name_of_task")

    # The fixture re-raises captured loop exceptions on teardown; this
    # test deliberately generates one, so drop it before teardown.
    hass._captured_loop_exceptions.clear()


@test
def enable_posix_spawn() -> None:
    """Test that we can enable posix_spawn on musllinux."""

    def _mock_sys_tags_any() -> Iterator[packaging.tags.Tag]:
        yield from packaging.tags.parse_tag("py3-none-any")

    def _mock_sys_tags_musl() -> Iterator[packaging.tags.Tag]:
        yield from packaging.tags.parse_tag("cp311-cp311-musllinux_1_1_x86_64")

    with (
        patch.object(subprocess, "_USE_POSIX_SPAWN", False),
        patch(
            "homeassistant.runner.packaging.tags.sys_tags",
            side_effect=_mock_sys_tags_musl,
        ),
    ):
        runner._enable_posix_spawn()
        expect(subprocess._USE_POSIX_SPAWN).to_be_truthy()

    with (
        patch.object(subprocess, "_USE_POSIX_SPAWN", False),
        patch(
            "homeassistant.runner.packaging.tags.sys_tags",
            side_effect=_mock_sys_tags_any,
        ),
    ):
        runner._enable_posix_spawn()
        expect(subprocess._USE_POSIX_SPAWN).to_be_falsy()


@test
def ensure_single_execution_success(tmp_path: Path = Depends(tmp_path)) -> None:
    """Test successful single instance execution."""
    config_dir = str(tmp_path)
    lock_file_path = tmp_path / runner.LOCK_FILE_NAME

    with runner.ensure_single_execution(config_dir) as lock:
        expect(lock.exit_code).to_be_none()
        expect(lock_file_path.exists()).to_be_truthy()

        with open(lock_file_path, encoding="utf-8") as f:
            data = json.load(f)
            expect(data["pid"]).to_equal(os.getpid())
            expect(data["version"]).to_equal(runner.LOCK_FILE_VERSION)
            expect(data["ha_version"]).to_equal(__version__)
            expect("start_ts" in data).to_be_truthy()
            expect(isinstance(data["start_ts"], float)).to_be_truthy()

    # Lock file should still exist after context exit (we don't unlink to avoid races)
    expect(lock_file_path.exists()).to_be_truthy()


@test
def ensure_single_execution_blocked(
    tmp_path: Path = Depends(tmp_path),
    capfd: CapFd = Depends(capfd),
) -> None:
    """Test that second instance is blocked when lock exists."""
    config_dir = str(tmp_path)
    lock_file_path = tmp_path / runner.LOCK_FILE_NAME

    # Create and lock the file to simulate another instance
    with open(lock_file_path, "w+", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

        instance_info = {
            "pid": 12345,
            "version": 1,
            "ha_version": "2025.1.0",
            "start_ts": time.time() - 3600,  # Started 1 hour ago
        }
        json.dump(instance_info, lock_file)
        lock_file.flush()

        with runner.ensure_single_execution(config_dir) as lock:
            expect(lock.exit_code).to_equal(1)

        captured = capfd.readouterr()
        expect(captured.err).to_contain(
            "Another Home Assistant instance is already running!"
        )
        expect(captured.err).to_contain("PID: 12345")
        expect(captured.err).to_contain("Version: 2025.1.0")
        expect(captured.err).to_contain("Started: ")
        # Should show local time since naive datetime
        expect(captured.err).to_contain("(local time)")
        expect(captured.err).to_contain(f"Config directory: {config_dir}")


@test
def ensure_single_execution_corrupt_lock_file(
    tmp_path: Path = Depends(tmp_path),
    capfd: CapFd = Depends(capfd),
) -> None:
    """Test handling of corrupted lock file."""
    config_dir = str(tmp_path)
    lock_file_path = tmp_path / runner.LOCK_FILE_NAME

    with open(lock_file_path, "w+", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_file.write("not valid json{]")
        lock_file.flush()

        # Try to acquire lock (should set exit_code but handle corrupt file gracefully)
        with runner.ensure_single_execution(config_dir) as lock:
            expect(lock.exit_code).to_equal(1)

        # Check error output
        captured = capfd.readouterr()
        expect(captured.err).to_contain(
            "Another Home Assistant instance is already running!"
        )
        expect(captured.err).to_contain("Unable to read lock file details:")
        expect(captured.err).to_contain(f"Config directory: {config_dir}")


@test
def ensure_single_execution_empty_lock_file(
    tmp_path: Path = Depends(tmp_path),
    capfd: CapFd = Depends(capfd),
) -> None:
    """Test handling of empty lock file."""
    config_dir = str(tmp_path)
    lock_file_path = tmp_path / runner.LOCK_FILE_NAME

    with open(lock_file_path, "w+", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        # Don't write anything - leave it empty
        lock_file.flush()

        # Try to acquire lock (should set exit_code but handle empty file gracefully)
        with runner.ensure_single_execution(config_dir) as lock:
            expect(lock.exit_code).to_equal(1)

        # Check error output
        captured = capfd.readouterr()
        expect(captured.err).to_contain(
            "Another Home Assistant instance is already running!"
        )
        expect(captured.err).to_contain("Unable to read lock file details.")


@test
def ensure_single_execution_with_timezone(
    tmp_path: Path = Depends(tmp_path),
    capfd: CapFd = Depends(capfd),
) -> None:
    """Test handling of lock file with timezone info (edge case)."""
    config_dir = str(tmp_path)
    lock_file_path = tmp_path / runner.LOCK_FILE_NAME

    # Note: This tests an edge case - our code doesn't create timezone-aware timestamps,
    # but we handle them if they exist
    with open(lock_file_path, "w+", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

        # Started 2 hours ago
        instance_info = {
            "pid": 54321,
            "version": 1,
            "ha_version": "2025.2.0",
            "start_ts": time.time() - 7200,
        }
        json.dump(instance_info, lock_file)
        lock_file.flush()

        with runner.ensure_single_execution(config_dir) as lock:
            expect(lock.exit_code).to_equal(1)

        captured = capfd.readouterr()
        expect(captured.err).to_contain(
            "Another Home Assistant instance is already running!"
        )
        expect(captured.err).to_contain("PID: 54321")
        expect(captured.err).to_contain("Version: 2025.2.0")
        expect(captured.err).to_contain("Started: ")
        # Should show local time indicator since fromtimestamp creates naive datetime
        expect(captured.err).to_contain("(local time)")


@test
def ensure_single_execution_with_tz_abbreviation(
    tmp_path: Path = Depends(tmp_path),
    capfd: CapFd = Depends(capfd),
) -> None:
    """Test handling of lock file when timezone abbreviation is available."""
    config_dir = str(tmp_path)
    lock_file_path = tmp_path / runner.LOCK_FILE_NAME

    with open(lock_file_path, "w+", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

        instance_info = {
            "pid": 98765,
            "version": 1,
            "ha_version": "2025.3.0",
            "start_ts": time.time() - 1800,  # Started 30 minutes ago
        }
        json.dump(instance_info, lock_file)
        lock_file.flush()

        # Mock datetime to return a timezone abbreviation
        # We use mocking because strftime("%Z") behavior is OS-specific:
        # On some systems it returns empty string for naive datetimes
        mock_dt = MagicMock()

        def _mock_strftime(fmt: str) -> str:
            if fmt == "%Z":
                return "PST"
            if fmt == "%Y-%m-%d %H:%M:%S":
                return "2025-09-03 10:30:45"
            return "2025-09-03 10:30:45 PST"

        mock_dt.strftime.side_effect = _mock_strftime

        with patch("homeassistant.runner.datetime") as mock_datetime:
            mock_datetime.fromtimestamp.return_value = mock_dt
            with runner.ensure_single_execution(config_dir) as lock:
                expect(lock.exit_code).to_equal(1)

        captured = capfd.readouterr()
        expect(captured.err).to_contain(
            "Another Home Assistant instance is already running!"
        )
        expect(captured.err).to_contain("PID: 98765")
        expect(captured.err).to_contain("Version: 2025.3.0")
        expect(captured.err).to_contain("Started: 2025-09-03 10:30:45 PST")
        # Should NOT have "(local time)" when timezone abbreviation is present
        expect(captured.err).not_.to_contain("(local time)")


@test
def ensure_single_execution_file_not_unlinked(
    tmp_path: Path = Depends(tmp_path),
) -> None:
    """Test that lock file is never unlinked to avoid race conditions."""
    config_dir = str(tmp_path)
    lock_file_path = tmp_path / runner.LOCK_FILE_NAME

    # First run creates the lock file
    with runner.ensure_single_execution(config_dir) as lock:
        expect(lock.exit_code).to_be_none()
        expect(lock_file_path.exists()).to_be_truthy()
        # Get inode to verify it's the same file
        stat1 = lock_file_path.stat()

    # After context exit, file should still exist
    expect(lock_file_path.exists()).to_be_truthy()
    stat2 = lock_file_path.stat()
    # Verify it's the exact same file (same inode)
    expect(stat1.st_ino).to_equal(stat2.st_ino)

    # Second run should reuse the same file
    with runner.ensure_single_execution(config_dir) as lock:
        expect(lock.exit_code).to_be_none()
        expect(lock_file_path.exists()).to_be_truthy()
        stat3 = lock_file_path.stat()
        # Still the same file (not recreated)
        expect(stat1.st_ino).to_equal(stat3.st_ino)

    # After second run, still the same file
    expect(lock_file_path.exists()).to_be_truthy()
    stat4 = lock_file_path.stat()
    expect(stat1.st_ino).to_equal(stat4.st_ino)


@test
def ensure_single_execution_sequential_runs(
    tmp_path: Path = Depends(tmp_path),
) -> None:
    """Test that sequential runs work correctly after lock is released."""
    config_dir = str(tmp_path)
    lock_file_path = tmp_path / runner.LOCK_FILE_NAME

    with runner.ensure_single_execution(config_dir) as lock:
        expect(lock.exit_code).to_be_none()
        expect(lock_file_path.exists()).to_be_truthy()
        with open(lock_file_path, encoding="utf-8") as f:
            first_data = json.load(f)

    # Lock file should still exist after first run (not unlinked)
    expect(lock_file_path.exists()).to_be_truthy()

    # Small delay to ensure different timestamp
    time.sleep(0.00001)

    with runner.ensure_single_execution(config_dir) as lock:
        expect(lock.exit_code).to_be_none()
        expect(lock_file_path.exists()).to_be_truthy()
        with open(lock_file_path, encoding="utf-8") as f:
            second_data = json.load(f)
            expect(second_data["pid"]).to_equal(os.getpid())
            expect(second_data["start_ts"] > first_data["start_ts"]).to_be_truthy()

    # Lock file should still exist after second run (not unlinked)
    expect(lock_file_path.exists()).to_be_truthy()
