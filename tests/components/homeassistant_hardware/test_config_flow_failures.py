"""Tryke skip-stubs for test_config_flow_failures.py - addon manager fixtures not in shim."""

from tryke import expect, test


@test
def domain_module_importable() -> None:
    """Smoke test: the homeassistant_hardware integration imports cleanly."""
    from homeassistant.components.homeassistant_hardware import DOMAIN  # noqa: PLC0415
    expect(DOMAIN).to_equal("homeassistant_hardware")


@test.skip("addon manager fixtures not in shim")
async def config_flow_thread_not_hassio() -> None:
    """Stub for test_config_flow_thread_not_hassio."""

@test.skip("addon manager fixtures not in shim")
async def config_flow_thread_addon_info_fails() -> None:
    """Stub for test_config_flow_thread_addon_info_fails."""

@test.skip("addon manager fixtures not in shim")
async def config_flow_thread_addon_install_fails() -> None:
    """Stub for test_config_flow_thread_addon_install_fails."""

@test.skip("addon manager fixtures not in shim")
async def config_flow_thread_addon_set_config_fails() -> None:
    """Stub for test_config_flow_thread_addon_set_config_fails."""

@test.skip("addon manager fixtures not in shim")
async def config_flow_thread_flasher_run_fails() -> None:
    """Stub for test_config_flow_thread_flasher_run_fails."""

@test.skip("addon manager fixtures not in shim")
async def config_flow_thread_confirmation_fails() -> None:
    """Stub for test_config_flow_thread_confirmation_fails."""

@test.skip("addon manager fixtures not in shim")
async def config_flow_firmware_index_download_fails_and_required() -> None:
    """Stub for test_config_flow_firmware_index_download_fails_and_required."""

@test.skip("addon manager fixtures not in shim")
async def config_flow_firmware_download_fails_and_required() -> None:
    """Stub for test_config_flow_firmware_download_fails_and_required."""

@test.skip("addon manager fixtures not in shim")
async def options_flow_zigbee_to_thread_zha_configured() -> None:
    """Stub for test_options_flow_zigbee_to_thread_zha_configured."""

@test.skip("addon manager fixtures not in shim")
async def options_flow_thread_to_zigbee_otbr_configured() -> None:
    """Stub for test_options_flow_thread_to_zigbee_otbr_configured."""
