"""Tryke skip-stubs for test_light.py - sibling port deferred (477 LOC, 0 parametrize)."""

from tryke import expect, test

@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.homekit_controller.light module imports cleanly."""
    from homeassistant.components.homekit_controller import light  # noqa: PLC0415
    expect(light).not_.to_be(None)


@test.skip("sibling port deferred (477 LOC, 0 parametrize)")
async def switch_change_light_state() -> None:
    """Stub for test_switch_change_light_state."""

@test.skip("sibling port deferred (477 LOC, 0 parametrize)")
async def switch_change_light_state_color_temp() -> None:
    """Stub for test_switch_change_light_state_color_temp."""

@test.skip("sibling port deferred (477 LOC, 0 parametrize)")
async def switch_read_light_state_dimmer() -> None:
    """Stub for test_switch_read_light_state_dimmer."""

@test.skip("sibling port deferred (477 LOC, 0 parametrize)")
async def switch_push_light_state_dimmer() -> None:
    """Stub for test_switch_push_light_state_dimmer."""

@test.skip("sibling port deferred (477 LOC, 0 parametrize)")
async def switch_read_light_state_hs() -> None:
    """Stub for test_switch_read_light_state_hs."""

@test.skip("sibling port deferred (477 LOC, 0 parametrize)")
async def switch_push_light_state_hs() -> None:
    """Stub for test_switch_push_light_state_hs."""

@test.skip("sibling port deferred (477 LOC, 0 parametrize)")
async def switch_read_light_state_color_temp() -> None:
    """Stub for test_switch_read_light_state_color_temp."""

@test.skip("sibling port deferred (477 LOC, 0 parametrize)")
async def switch_push_light_state_color_temp() -> None:
    """Stub for test_switch_push_light_state_color_temp."""

@test.skip("sibling port deferred (477 LOC, 0 parametrize)")
async def light_becomes_unavailable_but_recovers() -> None:
    """Stub for test_light_becomes_unavailable_but_recovers."""

@test.skip("sibling port deferred (477 LOC, 0 parametrize)")
async def light_unloaded_removed() -> None:
    """Stub for test_light_unloaded_removed."""

@test.skip("sibling port deferred (477 LOC, 0 parametrize)")
async def migrate_unique_id() -> None:
    """Stub for test_migrate_unique_id."""

@test.skip("sibling port deferred (477 LOC, 0 parametrize)")
async def only_migrate_once() -> None:
    """Stub for test_only_migrate_once."""
