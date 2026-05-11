"""Tryke skip stub for test_humidifier.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("snapshot test — out of scope")
async def all_entities() -> None:
    """Stub for test_all_entities."""


@test.skip("snapshot test — out of scope")
async def humidifier_data_update() -> None:
    """Stub for test_humidifier_data_update."""


@test.skip("snapshot test — out of scope")
async def humidifier_set_humidity() -> None:
    """Stub for test_humidifier_set_humidity."""


@test.skip("snapshot test — out of scope")
async def humidifier_set_humidity_while_off() -> None:
    """Stub for test_humidifier_set_humidity_while_off."""


@test.skip("snapshot test — out of scope")
async def humidifier_set_mode() -> None:
    """Stub for test_humidifier_set_mode."""


@test.skip("snapshot test — out of scope")
async def humidifier_set_status() -> None:
    """Stub for test_humidifier_set_status."""


@test.skip("snapshot test — out of scope")
async def humidifier_dehumidifier_remove_stale() -> None:
    """Stub for test_humidifier_dehumidifier_remove_stale."""


