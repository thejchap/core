"""Tryke skip-stubs for template/test_helpers.py."""

from tryke import test


@test.skip("requires template integration setup — port deferred")
async def yaml_device_actions() -> None:
    """Stub for test_yaml_device_actions."""

@test.skip("requires template integration setup — port deferred")
async def yaml_device_actions_modern_config() -> None:
    """Stub for test_yaml_device_actions_modern_config."""

@test.skip("requires template integration setup — port deferred")
async def config_entry_device_actions() -> None:
    """Stub for test_config_entry_device_actions."""

@test.skip("requires template integration setup — port deferred")
async def platform_not_ready() -> None:
    """Stub for test_platform_not_ready."""

