"""Tryke fixtures for the Plaato integration."""

from collections.abc import Generator
from unittest.mock import patch

from tryke import fixture


@fixture
def webhook_id() -> Generator[None]:
    """Mock webhook_id (matches the pytest ``webhook_id`` fixture)."""
    with (
        patch(
            "homeassistant.components.webhook.async_generate_id",
            return_value="webhook_id",
        ),
        patch(
            "homeassistant.components.webhook.async_generate_url",
            return_value="hook_id",
        ),
    ):
        yield
