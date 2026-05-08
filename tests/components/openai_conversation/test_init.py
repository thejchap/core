"""Tryke skip-stubs for openai_conversation init tests.

Original tests use OpenAI API mocks + conversation pipeline; full port deferred.
"""

from tryke import test

@test.skip("OpenAI API mocks + conversation pipeline")
async def generate_image_service() -> None:
    """Test generate image service."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def generate_image_service_error() -> None:
    """Test generate image service handles errors."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def generate_content_service_with_image_not_allowed_path() -> None:
    """Test generate content service with an image in a not allowed path."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def invalid_config_entry() -> None:
    """Assert exception when invalid config entry is provided."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def init_error() -> None:
    """Test initialization errors."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def init_auth_error() -> None:
    """Test auth error during init errors."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def generate_content_service() -> None:
    """Test generate content service."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def generate_content_service_invalid() -> None:
    """Test generate content service."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def generate_content_service_error() -> None:
    """Test generate content service handles errors."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def service_auth_error() -> None:
    """Test generate content service handles errors."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def migration_from_v1() -> None:
    """Test migration from version 1 to version 2."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def migration_from_v1_with_multiple_keys() -> None:
    """Test migration from version 1 with different API keys."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def migration_from_v1_with_same_keys() -> None:
    """Test migration from version 1 with same API keys consolidates entries."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def migration_from_v1_disabled() -> None:
    """Test migration where the config entries are disabled."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def migration_from_v2_1() -> None:
    """Test migration from version 2.1."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def devices() -> None:
    """Test devices are correctly created for subentries."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def migration_from_v2_2() -> None:
    """Test migration from version 2.2."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def migrate_entry_from_v2_3() -> None:
    """Test migration from version 2.3."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def migration_from_v2_4() -> None:
    """Test migration from version 2.4."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def migration_from_v2_5() -> None:
    """Test migration from version 2.5."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def migration_from_v2_6() -> None:
    """Test migration from version 2.6."""
