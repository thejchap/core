"""Tryke skip stub for test_sensor.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def setup() -> None:
    """Stub for test_setup."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def sensor_video_parameters() -> None:
    """Stub for test_sensor_video_parameters."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def sensor_audio_parameters() -> None:
    """Stub for test_sensor_audio_parameters."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def sensor_enum_unknown() -> None:
    """Stub for test_sensor_enum_unknown."""


