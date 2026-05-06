"""Tryke fixtures for the Android TV integration."""

from collections.abc import Generator
from unittest.mock import Mock, patch

from tryke import fixture

from . import patchers


@fixture
def adb_device_tcp_fixture() -> Generator[None]:
    """Patch ADB Device TCP."""
    with patch(
        "androidtv.adb_manager.adb_manager_async.AdbDeviceTcpAsync",
        patchers.AdbDeviceTcpAsyncFake,
    ):
        yield


@fixture
def load_adbkey_fixture() -> Generator[None]:
    """Patch load_adbkey."""
    with patch(
        "homeassistant.components.androidtv.ADBPythonSync.load_adbkey",
        return_value="signer for testing",
    ):
        yield


@fixture
def keygen_fixture() -> Generator[None]:
    """Patch keygen."""
    with patch(
        "homeassistant.components.androidtv.keygen",
        return_value=Mock(),
    ):
        yield
