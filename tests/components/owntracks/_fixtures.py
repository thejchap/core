"""Tryke fixtures for OwnTracks tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

from tryke import fixture

WEBHOOK_ID = "webhook_id"
SECRET = "test-secret"


@fixture
def webhook_id() -> Generator[None]:
    """Mock webhook_id."""
    with patch(
        "homeassistant.components.webhook.async_generate_id", return_value=WEBHOOK_ID
    ):
        yield


@fixture
def secret() -> Generator[None]:
    """Mock secret."""
    with patch("secrets.token_hex", return_value=SECRET):
        yield


@fixture
def not_supports_encryption() -> Generator[None]:
    """Mock non successful nacl import."""
    with patch(
        "homeassistant.components.owntracks.config_flow.supports_encryption",
        return_value=False,
    ):
        yield
