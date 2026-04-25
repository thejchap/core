"""Tryke fixtures for the Daikin integration."""

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

from tryke import fixture


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.daikin.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


@fixture
def mock_daikin() -> Generator[MagicMock]:
    """Mock pydaikin."""

    async def mock_daikin_factory(*args: Any, **kwargs: Any) -> MagicMock:
        return Appliance

    with patch(
        "homeassistant.components.daikin.config_flow.DaikinFactory"
    ) as Appliance:
        type(Appliance).mac = PropertyMock(return_value="AABBCCDDEEFF")
        Appliance.side_effect = mock_daikin_factory
        yield Appliance


@fixture
def mock_daikin_discovery() -> Generator[MagicMock]:
    """Mock pydaikin Discovery."""
    with patch("homeassistant.components.daikin.config_flow.Discovery") as Discovery:
        Discovery().poll.return_value = {
            "127.0.01": {"mac": "AABBCCDDEEFF", "id": "test"}
        }.values()
        yield Discovery
