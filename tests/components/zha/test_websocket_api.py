"""Tryke skip-stubs for test_websocket_api.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zha: sibling test pending tryke port")
async def device_clusters() -> None:
    """Stub for test_device_clusters."""


@test.skip("zha: sibling test pending tryke port")
async def device_cluster_attributes() -> None:
    """Stub for test_device_cluster_attributes."""


@test.skip("zha: sibling test pending tryke port")
async def device_cluster_commands() -> None:
    """Stub for test_device_cluster_commands."""


@test.skip("zha: sibling test pending tryke port")
async def list_devices() -> None:
    """Stub for test_list_devices."""


@test.skip("zha: sibling test pending tryke port")
async def get_zha_config() -> None:
    """Stub for test_get_zha_config."""


@test.skip("zha: sibling test pending tryke port")
async def get_zha_config_with_alarm() -> None:
    """Stub for test_get_zha_config_with_alarm."""


@test.skip("zha: sibling test pending tryke port")
async def update_zha_config() -> None:
    """Stub for test_update_zha_config."""


@test.skip("zha: sibling test pending tryke port")
async def device_not_found() -> None:
    """Stub for test_device_not_found."""


@test.skip("zha: sibling test pending tryke port")
async def list_groups() -> None:
    """Stub for test_list_groups."""


@test.skip("zha: sibling test pending tryke port")
async def get_group() -> None:
    """Stub for test_get_group."""


@test.skip("zha: sibling test pending tryke port")
async def get_group_not_found() -> None:
    """Stub for test_get_group_not_found."""


@test.skip("zha: sibling test pending tryke port")
async def list_groupable_devices() -> None:
    """Stub for test_list_groupable_devices."""


@test.skip("zha: sibling test pending tryke port")
async def add_group() -> None:
    """Stub for test_add_group."""


@test.skip("zha: sibling test pending tryke port")
async def remove_group() -> None:
    """Stub for test_remove_group."""


@test.skip("zha: sibling test pending tryke port")
async def add_group_member() -> None:
    """Stub for test_add_group_member."""


@test.skip("zha: sibling test pending tryke port")
async def remove_group_member() -> None:
    """Stub for test_remove_group_member."""


@test.skip("zha: sibling test pending tryke port")
async def permit_ha12() -> None:
    """Stub for test_permit_ha12."""


@test.skip("zha: sibling test pending tryke port")
async def permit_with_install_code() -> None:
    """Stub for test_permit_with_install_code."""


@test.skip("zha: sibling test pending tryke port")
async def permit_with_install_code_fail() -> None:
    """Stub for test_permit_with_install_code_fail."""


@test.skip("zha: sibling test pending tryke port")
async def permit_with_qr_code() -> None:
    """Stub for test_permit_with_qr_code."""


@test.skip("zha: sibling test pending tryke port")
async def ws_permit_with_qr_code() -> None:
    """Stub for test_ws_permit_with_qr_code."""


@test.skip("zha: sibling test pending tryke port")
async def ws_permit_with_install_code_fail() -> None:
    """Stub for test_ws_permit_with_install_code_fail."""


@test.skip("zha: sibling test pending tryke port")
async def ws_permit_ha12() -> None:
    """Stub for test_ws_permit_ha12."""


@test.skip("zha: sibling test pending tryke port")
async def get_network_settings() -> None:
    """Stub for test_get_network_settings."""


@test.skip("zha: sibling test pending tryke port")
async def list_network_backups() -> None:
    """Stub for test_list_network_backups."""


@test.skip("zha: sibling test pending tryke port")
async def create_network_backup() -> None:
    """Stub for test_create_network_backup."""


@test.skip("zha: sibling test pending tryke port")
async def restore_network_backup_success() -> None:
    """Stub for test_restore_network_backup_success."""


@test.skip("zha: sibling test pending tryke port")
async def restore_network_backup_force_write_eui64() -> None:
    """Stub for test_restore_network_backup_force_write_eui64."""


@test.skip("zha: sibling test pending tryke port")
async def restore_network_backup_failure() -> None:
    """Stub for test_restore_network_backup_failure."""


@test.skip("zha: sibling test pending tryke port")
async def websocket_change_channel() -> None:
    """Stub for test_websocket_change_channel."""


@test.skip("zha: sibling test pending tryke port")
async def websocket_bind_unbind_devices() -> None:
    """Stub for test_websocket_bind_unbind_devices."""


@test.skip("zha: sibling test pending tryke port")
async def websocket_bind_unbind_group() -> None:
    """Stub for test_websocket_bind_unbind_group."""


@test.skip("zha: sibling test pending tryke port")
async def websocket_reconfigure() -> None:
    """Stub for test_websocket_reconfigure."""


@test.skip("zha: sibling test pending tryke port")
async def websocket_reconfigure_device_not_found() -> None:
    """Stub for test_websocket_reconfigure_device_not_found."""
