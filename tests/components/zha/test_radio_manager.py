"""Tryke skip-stubs for test_radio_manager.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zha: sibling test pending tryke port")
async def migrate_matching_port() -> None:
    """Stub for test_migrate_matching_port."""


@test.skip("zha: sibling test pending tryke port")
async def migrate_matching_port_usb() -> None:
    """Stub for test_migrate_matching_port_usb."""


@test.skip("zha: sibling test pending tryke port")
async def migrate_matching_port_config_entry_not_loaded() -> None:
    """Stub for test_migrate_matching_port_config_entry_not_loaded."""


@test.skip("zha: sibling test pending tryke port")
async def migrate_matching_port_retry() -> None:
    """Stub for test_migrate_matching_port_retry."""


@test.skip("zha: sibling test pending tryke port")
async def migrate_non_matching_port() -> None:
    """Stub for test_migrate_non_matching_port."""


@test.skip("zha: sibling test pending tryke port")
async def migrate_initiate_failure() -> None:
    """Stub for test_migrate_initiate_failure."""


@test.skip("zha: sibling test pending tryke port")
async def detect_radio_type_success() -> None:
    """Stub for test_detect_radio_type_success."""


@test.skip("zha: sibling test pending tryke port")
async def detect_radio_type_failure_wrong_firmware() -> None:
    """Stub for test_detect_radio_type_failure_wrong_firmware."""


@test.skip("zha: sibling test pending tryke port")
async def detect_radio_type_failure_no_detect() -> None:
    """Stub for test_detect_radio_type_failure_no_detect."""


@test.skip("zha: sibling test pending tryke port")
async def load_network_settings_oserror() -> None:
    """Stub for test_load_network_settings_oserror."""


@test.skip("zha: sibling test pending tryke port")
async def create_zigpy_app_connect_oserror() -> None:
    """Stub for test_create_zigpy_app_connect_oserror."""
