"""Test config."""

import asyncio
from unittest.mock import patch

from tryke import Depends, fixture, test

from homeassistant.core import HomeAssistant

from .test_common import get_default_config

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def enable_proactive_mode_in_parallel(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test enabling proactive mode does not happen in parallel."""
    config = get_default_config(hass)

    with patch(
        "homeassistant.components.alexa.config.async_enable_proactive_mode"
    ) as mock_enable_proactive_mode:
        await asyncio.gather(
            config.async_enable_proactive_mode(), config.async_enable_proactive_mode()
        )

    mock_enable_proactive_mode.assert_awaited_once()
