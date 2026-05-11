"""Tryke skip-stubs for test_diagnostics.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot test — out of scope")
async def bulb_diagnostics() -> None:
    """Stub for test_bulb_diagnostics."""

@test.skip("snapshot test — out of scope")
async def clean_bulb_diagnostics() -> None:
    """Stub for test_clean_bulb_diagnostics."""

@test.skip("snapshot test — out of scope")
async def infrared_bulb_diagnostics() -> None:
    """Stub for test_infrared_bulb_diagnostics."""

@test.skip("snapshot test — out of scope")
async def legacy_multizone_bulb_diagnostics() -> None:
    """Stub for test_legacy_multizone_bulb_diagnostics."""

@test.skip("snapshot test — out of scope")
async def multizone_bulb_diagnostics() -> None:
    """Stub for test_multizone_bulb_diagnostics."""

@test.skip("snapshot test — out of scope")
async def matrix_diagnostics() -> None:
    """Stub for test_matrix_diagnostics."""

@test.skip("snapshot test — out of scope")
async def 128zone_matrix_diagnostics() -> None:
    """Stub for test_128zone_matrix_diagnostics."""
