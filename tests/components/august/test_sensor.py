"""Tryke skip stub for test_sensor.py."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.august.sensor module imports cleanly."""
    from homeassistant.components.august import sensor  # noqa: PLC0415
    expect(sensor).not_.to_be(None)


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def create_doorbell() -> None:
    """Stub for test_create_doorbell."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def create_doorbell_offline() -> None:
    """Stub for test_create_doorbell_offline."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def create_doorbell_hardwired() -> None:
    """Stub for test_create_doorbell_hardwired."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def create_lock_with_linked_keypad() -> None:
    """Stub for test_create_lock_with_linked_keypad."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def create_lock_with_low_battery_linked_keypad() -> None:
    """Stub for test_create_lock_with_low_battery_linked_keypad."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def lock_operator_bluetooth() -> None:
    """Stub for test_lock_operator_bluetooth."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def lock_operator_keypad() -> None:
    """Stub for test_lock_operator_keypad."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def lock_operator_remote() -> None:
    """Stub for test_lock_operator_remote."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def lock_operator_manual() -> None:
    """Stub for test_lock_operator_manual."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def lock_operator_autorelock() -> None:
    """Stub for test_lock_operator_autorelock."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def unlock_operator_manual() -> None:
    """Stub for test_unlock_operator_manual."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def unlock_operator_tag() -> None:
    """Stub for test_unlock_operator_tag."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def restored_state() -> None:
    """Stub for test_restored_state."""

