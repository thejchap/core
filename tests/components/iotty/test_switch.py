"""Tryke skip-stubs for test_switch.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def turn_on_light_ok() -> None:
    """Stub for test_turn_on_light_ok."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def turn_on_outlet_ok() -> None:
    """Stub for test_turn_on_outlet_ok."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def turn_off_light_ok() -> None:
    """Stub for test_turn_off_light_ok."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def turn_off_outlet_ok() -> None:
    """Stub for test_turn_off_outlet_ok."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def setup_entry_ok_nodevices() -> None:
    """Stub for test_setup_entry_ok_nodevices."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def devices_creaction_ok() -> None:
    """Stub for test_devices_creaction_ok."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def devices_deletion_ok() -> None:
    """Stub for test_devices_deletion_ok."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def devices_insertion_ok() -> None:
    """Stub for test_devices_insertion_ok."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def outlet_insertion_ok() -> None:
    """Stub for test_outlet_insertion_ok."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def api_not_ok_entities_stay_the_same_as_before() -> None:
    """Stub for test_api_not_ok_entities_stay_the_same_as_before."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def api_throws_response_entities_stay_the_same_as_before() -> None:
    """Stub for test_api_throws_response_entities_stay_the_same_as_before."""
