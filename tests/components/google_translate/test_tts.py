"""Tryke skip stub for test_tts.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the google_translate.tts module imports cleanly."""
    from homeassistant.components.google_translate import tts  # noqa: PLC0415
    expect(tts).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def platform() -> None:
    """Stub for test_platform (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def tts_service() -> None:
    """Stub for test_tts_service (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service_say_german_config() -> None:
    """Stub for test_service_say_german_config (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service_say_german_service() -> None:
    """Stub for test_service_say_german_service (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service_say_en_uk_config() -> None:
    """Stub for test_service_say_en_uk_config (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service_say_en_uk_service() -> None:
    """Stub for test_service_say_en_uk_service (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service_say_en_couk() -> None:
    """Stub for test_service_say_en_couk (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service_say_error() -> None:
    """Stub for test_service_say_error (port deferred)."""


