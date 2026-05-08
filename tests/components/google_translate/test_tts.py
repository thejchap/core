"""Tryke skip stubs for test_tts - sibling test pending port."""

from tryke import test


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


