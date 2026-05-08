"""Tests for the OpenAI integration init (tryke port)."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError

from ._fixtures import mock_config_entry, mock_init_component

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Force tryke fixture resolution before each test."""


@test.cases(
    test.case("generate_image", service_name="generate_image"),
    test.case("generate_content", service_name="generate_content"),
)
async def invalid_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    init: None = Depends(mock_init_component),
    *,
    service_name: str,
) -> None:
    """Assert exception when invalid config entry is provided.

    Translation lookup is unavailable in tryke shim, so just match against
    the raised ``translation_key`` (the bare ``__str__`` form).
    """
    service_data = {
        "prompt": "Picture of a dog",
        "config_entry": "invalid_entry",
    }
    async with expect_raises_async(
        ServiceValidationError, match="invalid_config_entry"
    ):
        await hass.services.async_call(
            "openai_conversation",
            service_name,
            service_data,
            blocking=True,
            return_response=True,
        )


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
