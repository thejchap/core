"""Tryke skip stub for test_sensor.py - sibling test pending fixture port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("amberelectric conftest fixtures (mock_amber_client, general_channel_config_entry, general_channel_and_controlled_load_config_entry, etc.) need _fixtures.py port")
async def placeholder() -> None:
    """Placeholder skipped sibling tests."""
