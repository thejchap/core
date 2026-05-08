"""Tryke skip stub for test_device_tracker.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def all_entities() -> None:
    """Stub for test_all_entities."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def vehicle_icons() -> None:
    """Stub for test_vehicle_icons."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def entity_unavailable_on_coordinator_error() -> None:
    """Stub for test_entity_unavailable_on_coordinator_error."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def entity_recovers_after_error() -> None:
    """Stub for test_entity_recovers_after_error."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def reauth_success() -> None:
    """Stub for test_reauth_success."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def reauth_failure() -> None:
    """Stub for test_reauth_failure."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def vehicle_name_update() -> None:
    """Stub for test_vehicle_name_update."""


