"""Tests for async util methods from Python source."""

from __future__ import annotations

import contextlib
import glob
import importlib
import os
from pathlib import Path, PurePosixPath
import ssl
import time
from typing import Any
from unittest.mock import Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import block_async_io
from homeassistant.core import HomeAssistant

from .common import extract_stack_to_frame
from .hass_fixtures import LogCapture, caplog, disable_block_async_io, hass


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


def _expect_raises(exc_type: type[BaseException], fn: Any) -> None:
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(f"Expected {exc_type.__name__}")


@test
async def protect_loop_debugger_sleep(
    caplog: LogCapture = Depends(caplog),
    _: None = Depends(disable_block_async_io),
) -> None:
    """Test time.sleep injected by the debugger is not reported."""
    block_async_io.enable()
    frames = extract_stack_to_frame(
        [
            Mock(
                filename="/home/paulus/homeassistant/.venv/blah/pydevd.py",
                lineno="23",
                line="do_something()",
            ),
        ]
    )
    with (
        patch(
            "homeassistant.block_async_io.get_current_frame",
            return_value=frames,
        ),
        patch(
            "homeassistant.helpers.frame.get_current_frame",
            return_value=frames,
        ),
    ):
        time.sleep(0)  # noqa: ASYNC251
    expect(caplog.text).not_.to_contain("Detected blocking call inside the event loop")


@test
async def protect_loop_sleep(
    _: None = Depends(disable_block_async_io),
) -> None:
    """Test time.sleep not injected by the debugger raises."""
    block_async_io.enable()
    frames = extract_stack_to_frame(
        [
            Mock(
                filename="/home/paulus/homeassistant/no_dev.py",
                lineno="23",
                line="do_something()",
            ),
        ]
    )
    with (
        patch(
            "homeassistant.block_async_io.get_current_frame",
            return_value=frames,
        ),
        patch(
            "homeassistant.helpers.frame.get_current_frame",
            return_value=frames,
        ),
    ):
        _expect_raises(RuntimeError, lambda: time.sleep(0))


@test
async def protect_loop_sleep_get_current_frame_raises(
    _: None = Depends(disable_block_async_io),
) -> None:
    """Test time.sleep when get_current_frame raises ValueError."""
    block_async_io.enable()
    frames = extract_stack_to_frame(
        [
            Mock(
                filename="/home/paulus/homeassistant/no_dev.py",
                lineno="23",
                line="do_something()",
            ),
        ]
    )
    with (
        patch(
            "homeassistant.block_async_io.get_current_frame",
            side_effect=ValueError,
        ),
        patch(
            "homeassistant.helpers.frame.get_current_frame",
            return_value=frames,
        ),
    ):
        _expect_raises(RuntimeError, lambda: time.sleep(0))


@test
async def protect_loop_importlib_import_module_non_integration(
    caplog: LogCapture = Depends(caplog),
    _: None = Depends(disable_block_async_io),
) -> None:
    """Test import_module in the loop for non-loaded module."""
    frames = extract_stack_to_frame(
        [
            Mock(
                filename="/home/paulus/homeassistant/no_dev.py",
                lineno="23",
                line="do_something()",
            ),
        ]
    )
    with (
        patch.object(block_async_io, "_IN_TESTS", False),
        patch(
            "homeassistant.block_async_io.get_current_frame",
            return_value=frames,
        ),
        patch(
            "homeassistant.helpers.frame.get_current_frame",
            return_value=frames,
        ),
    ):
        block_async_io.enable()
        _expect_raises(
            ImportError, lambda: importlib.import_module("not_loaded_module")
        )

    expect(caplog.text).to_contain("Detected blocking call to import_module")


@test
async def protect_loop_importlib_import_loaded_module_non_integration(
    caplog: LogCapture = Depends(caplog),
    _: None = Depends(disable_block_async_io),
) -> None:
    """Test import_module in the loop for a loaded module."""
    frames = extract_stack_to_frame(
        [
            Mock(
                filename="/home/paulus/homeassistant/no_dev.py",
                lineno="23",
                line="do_something()",
            ),
        ]
    )
    with (
        patch.object(block_async_io, "_IN_TESTS", False),
        patch(
            "homeassistant.block_async_io.get_current_frame",
            return_value=frames,
        ),
        patch(
            "homeassistant.helpers.frame.get_current_frame",
            return_value=frames,
        ),
    ):
        block_async_io.enable()
        importlib.import_module("sys")

    expect(caplog.text).not_.to_contain("Detected blocking call to import_module")


@test
async def protect_loop_importlib_import_module_in_integration(
    caplog: LogCapture = Depends(caplog),
    _: None = Depends(disable_block_async_io),
) -> None:
    """Test import_module in the loop for non-loaded module in an integration."""
    frames = extract_stack_to_frame(
        [
            Mock(
                filename="/home/paulus/homeassistant/core.py",
                lineno="23",
                line="do_something()",
            ),
            Mock(
                filename="/home/paulus/homeassistant/components/hue/light.py",
                lineno="23",
                line="self.light.is_on",
            ),
            Mock(
                filename="/home/paulus/aiohue/lights.py",
                lineno="2",
                line="something()",
            ),
        ]
    )
    with (
        patch.object(block_async_io, "_IN_TESTS", False),
        patch(
            "homeassistant.block_async_io.get_current_frame",
            return_value=frames,
        ),
        patch(
            "homeassistant.helpers.frame.get_current_frame",
            return_value=frames,
        ),
    ):
        block_async_io.enable()
        _expect_raises(
            ImportError, lambda: importlib.import_module("not_loaded_module")
        )

    expect(caplog.text).to_contain(
        "Detected blocking call to import_module with args ('not_loaded_module',) "
        "inside the event loop by "
        "integration 'hue' at homeassistant/components/hue/light.py, line 23"
    )


@test
async def protect_loop_open(
    caplog: LogCapture = Depends(caplog),
    _: None = Depends(disable_block_async_io),
) -> None:
    """Test open of a file in /proc is not reported."""
    block_async_io.enable()
    with (
        contextlib.suppress(FileNotFoundError),
        open("/proc/does_not_exist", encoding="utf8"),  # noqa: ASYNC230
    ):
        pass
    expect(caplog.text).not_.to_contain("Detected blocking call to open with args")


@test
async def protect_loop_path_open(
    caplog: LogCapture = Depends(caplog),
    _: None = Depends(disable_block_async_io),
) -> None:
    """Test opening a file in /proc is not reported."""
    block_async_io.enable()
    with (
        contextlib.suppress(FileNotFoundError),
        Path("/proc/does_not_exist").open(encoding="utf8"),  # noqa: ASYNC230
    ):
        pass
    expect(caplog.text).not_.to_contain("Detected blocking call to open with args")


@test
async def protect_open(
    caplog: LogCapture = Depends(caplog),
    _: None = Depends(disable_block_async_io),
) -> None:
    """Test opening a file in the event loop logs."""
    with patch.object(block_async_io, "_IN_TESTS", False):
        block_async_io.enable()
    with (
        contextlib.suppress(FileNotFoundError),
        open("/config/data_not_exist", encoding="utf8"),  # noqa: ASYNC230
    ):
        pass

    expect(caplog.text).to_contain("Detected blocking call to open with args")


@test
async def protect_path_open(
    caplog: LogCapture = Depends(caplog),
    _: None = Depends(disable_block_async_io),
) -> None:
    """Test opening a file in the event loop logs."""
    with patch.object(block_async_io, "_IN_TESTS", False):
        block_async_io.enable()
    with (
        contextlib.suppress(FileNotFoundError),
        Path("/config/data_not_exist").open(encoding="utf8"),  # noqa: ASYNC230
    ):
        pass

    expect(caplog.text).to_contain("Detected blocking call to open with args")


@test
async def protect_path_read_bytes(
    caplog: LogCapture = Depends(caplog),
    _: None = Depends(disable_block_async_io),
) -> None:
    """Test reading file bytes in the event loop logs."""
    with patch.object(block_async_io, "_IN_TESTS", False):
        block_async_io.enable()
    with (
        contextlib.suppress(FileNotFoundError),
        Path("/config/data_not_exist").read_bytes(),
    ):
        pass

    expect(caplog.text).to_contain("Detected blocking call to read_bytes with args")


@test
async def protect_path_read_text(
    caplog: LogCapture = Depends(caplog),
    _: None = Depends(disable_block_async_io),
) -> None:
    """Test reading a file text in the event loop logs."""
    with patch.object(block_async_io, "_IN_TESTS", False):
        block_async_io.enable()
    with (
        contextlib.suppress(FileNotFoundError),
        Path("/config/data_not_exist").read_text(encoding="utf8"),
    ):
        pass

    expect(caplog.text).to_contain("Detected blocking call to read_text with args")


@test
async def protect_path_write_bytes(
    caplog: LogCapture = Depends(caplog),
    _: None = Depends(disable_block_async_io),
) -> None:
    """Test writing file bytes in the event loop logs."""
    with patch.object(block_async_io, "_IN_TESTS", False):
        block_async_io.enable()
    with (
        contextlib.suppress(FileNotFoundError),
        Path("/config/data/not/exist").write_bytes(b"xxx"),
    ):
        pass

    expect(caplog.text).to_contain("Detected blocking call to write_bytes with args")


@test
async def protect_path_write_text(
    caplog: LogCapture = Depends(caplog),
    _: None = Depends(disable_block_async_io),
) -> None:
    """Test writing file text in the event loop logs."""
    with patch.object(block_async_io, "_IN_TESTS", False):
        block_async_io.enable()
    with (
        contextlib.suppress(FileNotFoundError),
        Path("/config/data/not/exist").write_text("xxx", encoding="utf8"),
    ):
        pass

    expect(caplog.text).to_contain("Detected blocking call to write_text with args")


@test
async def enable_multiple_times(
    _: None = Depends(disable_block_async_io),
) -> None:
    """Test trying to enable multiple times."""
    with patch.object(block_async_io, "_IN_TESTS", False):
        block_async_io.enable()

    _expect_raises(RuntimeError, block_async_io.enable)


@test.cases(
    test.case("str", path="/config/data_not_exist"),
    test.case("path", path=Path("/config/data_not_exist")),
    test.case("pureposixpath", path=PurePosixPath("/config/data_not_exist")),
)
async def protect_open_path(
    path: Any,
    caplog: LogCapture = Depends(caplog),
    _: None = Depends(disable_block_async_io),
) -> None:
    """Test opening a file by path in the event loop logs."""
    with patch.object(block_async_io, "_IN_TESTS", False):
        block_async_io.enable()
    with contextlib.suppress(FileNotFoundError), open(path, encoding="utf8"):  # noqa: ASYNC230
        pass

    expect(caplog.text).to_contain("Detected blocking call to open with args")


@test
async def protect_loop_glob(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
    _: None = Depends(disable_block_async_io),
) -> None:
    """Test glob calls in the loop are logged."""
    with patch.object(block_async_io, "_IN_TESTS", False):
        block_async_io.enable()
    glob.glob("/dev/null")
    expect(caplog.text).to_contain("Detected blocking call to glob with args")
    caplog.clear()
    await hass.async_add_executor_job(glob.glob, "/dev/null")
    expect(caplog.text).not_.to_contain("Detected blocking call to glob with args")


@test
async def protect_loop_iglob(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
    _: None = Depends(disable_block_async_io),
) -> None:
    """Test iglob calls in the loop are logged."""
    with patch.object(block_async_io, "_IN_TESTS", False):
        block_async_io.enable()
    glob.iglob("/dev/null")
    expect(caplog.text).to_contain("Detected blocking call to iglob with args")
    caplog.clear()
    await hass.async_add_executor_job(glob.iglob, "/dev/null")
    expect(caplog.text).not_.to_contain("Detected blocking call to iglob with args")


@test
async def protect_loop_scandir(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
    _: None = Depends(disable_block_async_io),
) -> None:
    """Test glob calls in the loop are logged."""
    with patch.object(block_async_io, "_IN_TESTS", False):
        block_async_io.enable()
    with contextlib.suppress(FileNotFoundError):
        os.scandir("/path/that/does/not/exists")
    expect(caplog.text).to_contain("Detected blocking call to scandir with args")
    caplog.clear()
    with contextlib.suppress(FileNotFoundError):
        await hass.async_add_executor_job(os.scandir, "/path/that/does/not/exists")
    expect(caplog.text).not_.to_contain("Detected blocking call to scandir with args")


@test
async def protect_loop_listdir(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
    _: None = Depends(disable_block_async_io),
) -> None:
    """Test listdir calls in the loop are logged."""
    with patch.object(block_async_io, "_IN_TESTS", False):
        block_async_io.enable()
    with contextlib.suppress(FileNotFoundError):
        os.listdir("/path/that/does/not/exists")
    expect(caplog.text).to_contain("Detected blocking call to listdir with args")
    caplog.clear()
    with contextlib.suppress(FileNotFoundError):
        await hass.async_add_executor_job(os.listdir, "/path/that/does/not/exists")
    expect(caplog.text).not_.to_contain("Detected blocking call to listdir with args")


@test
async def protect_loop_walk(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
    _: None = Depends(disable_block_async_io),
) -> None:
    """Test os.walk calls in the loop are logged."""
    with patch.object(block_async_io, "_IN_TESTS", False):
        block_async_io.enable()
    with contextlib.suppress(FileNotFoundError):
        os.walk("/path/that/does/not/exists")
    expect(caplog.text).to_contain("Detected blocking call to walk with args")
    caplog.clear()
    with contextlib.suppress(FileNotFoundError):
        await hass.async_add_executor_job(os.walk, "/path/that/does/not/exists")
    expect(caplog.text).not_.to_contain("Detected blocking call to walk with args")


@test
async def protect_loop_load_default_certs(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
    _: None = Depends(disable_block_async_io),
) -> None:
    """Test SSLContext.load_default_certs calls in the loop are logged."""
    with patch.object(block_async_io, "_IN_TESTS", False):
        block_async_io.enable()
    context = ssl.create_default_context()
    expect(caplog.text).to_contain("Detected blocking call to load_default_certs")
    expect(context).to_be_truthy()


@test
async def protect_loop_load_verify_locations(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
    _: None = Depends(disable_block_async_io),
) -> None:
    """Test SSLContext.load_verify_locations calls in the loop are logged."""
    with patch.object(block_async_io, "_IN_TESTS", False):
        block_async_io.enable()
    context = ssl.create_default_context()
    _expect_raises(OSError, lambda: context.load_verify_locations("/dev/null"))
    expect(caplog.text).to_contain("Detected blocking call to load_verify_locations")

    # ignore with only cadata
    caplog.clear()
    _expect_raises(ssl.SSLError, lambda: context.load_verify_locations(cadata="xxx"))
    expect(caplog.text).not_.to_contain(
        "Detected blocking call to load_verify_locations"
    )


@test
async def protect_loop_load_cert_chain(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
    _: None = Depends(disable_block_async_io),
) -> None:
    """Test SSLContext.load_cert_chain calls in the loop are logged."""
    with patch.object(block_async_io, "_IN_TESTS", False):
        block_async_io.enable()
    context = ssl.create_default_context()
    _expect_raises(OSError, lambda: context.load_cert_chain("/dev/null"))
    expect(caplog.text).to_contain("Detected blocking call to load_cert_chain")


@test
async def open_calls_ignored_in_tests(
    caplog: LogCapture = Depends(caplog),
    _: None = Depends(disable_block_async_io),
) -> None:
    """Test opening a file in tests is ignored."""
    expect(block_async_io._IN_TESTS).to_be_truthy()
    block_async_io.enable()
    with (
        contextlib.suppress(FileNotFoundError),
        open("/config/data_not_exist", encoding="utf8"),  # noqa: ASYNC230
    ):
        pass

    expect(caplog.text).not_.to_contain("Detected blocking call to open with args")


@test
async def protect_loop_set_default_verify_paths(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
    _: None = Depends(disable_block_async_io),
) -> None:
    """Test SSLContext.set_default_verify_paths calls in the loop are logged."""
    with patch.object(block_async_io, "_IN_TESTS", False):
        block_async_io.enable()
    context = ssl.create_default_context()
    context.set_default_verify_paths()
    expect(caplog.text).to_contain("Detected blocking call to set_default_verify_paths")
