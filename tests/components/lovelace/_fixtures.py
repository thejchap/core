"""Tryke fixtures for lovelace tests."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

from tryke import fixture


@fixture
def mock_onboarding_not_done() -> Generator[MagicMock]:
    """Mock that Home Assistant is currently onboarding."""
    with patch(
        "homeassistant.components.onboarding.async_is_onboarded",
        return_value=False,
    ) as mock_onboarding:
        yield mock_onboarding


@fixture
def mock_onboarding_done() -> Generator[MagicMock]:
    """Mock that Home Assistant is finished onboarding."""
    with patch(
        "homeassistant.components.onboarding.async_is_onboarded",
        return_value=True,
    ) as mock_onboarding:
        yield mock_onboarding


@fixture
def mock_add_onboarding_listener() -> Generator[MagicMock]:
    """Mock add onboarding listener."""
    with patch(
        "homeassistant.components.onboarding.async_add_listener",
    ) as mock_add_onboarding_listener:
        yield mock_add_onboarding_listener
