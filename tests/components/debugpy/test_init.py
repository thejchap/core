"""Tests for the Remote Python Debugger integration."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.debugpy import (
    CONF_HOST,
    CONF_PORT,
    CONF_START,
    CONF_WAIT,
    DOMAIN,
    SERVICE_START,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@fixture
def mock_debugpy() -> Generator[MagicMock]:
    """Mock debugpy lib."""
    with patch("homeassistant.components.debugpy.debugpy") as mocked_debugpy:
        yield mocked_debugpy


@test
async def default(
    hass: HomeAssistant = Depends(hass),
    mock_debugpy: MagicMock = Depends(mock_debugpy),
) -> None:
    """Test if the default settings work."""
    expect(await async_setup_component(hass, DOMAIN, {DOMAIN: {}})).to_be(True)

    mock_debugpy.listen.assert_called_once_with(("0.0.0.0", 5678))
    mock_debugpy.wait_for_client.assert_not_called()
    expect(len(mock_debugpy.method_calls)).to_equal(1)


@test
async def wait_on_startup(
    hass: HomeAssistant = Depends(hass),
    mock_debugpy: MagicMock = Depends(mock_debugpy),
) -> None:
    """Test if the waiting for client is called."""
    expect(
        await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_WAIT: True}})
    ).to_be(True)

    mock_debugpy.listen.assert_called_once_with(("0.0.0.0", 5678))
    mock_debugpy.wait_for_client.assert_called_once()
    expect(len(mock_debugpy.method_calls)).to_equal(2)


@test
async def on_demand(
    hass: HomeAssistant = Depends(hass),
    mock_debugpy: MagicMock = Depends(mock_debugpy),
) -> None:
    """Test on-demand debugging using a service call."""
    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {DOMAIN: {CONF_START: False, CONF_HOST: "127.0.0.1", CONF_PORT: 80}},
        )
    ).to_be(True)

    mock_debugpy.listen.assert_not_called()
    mock_debugpy.wait_for_client.assert_not_called()
    expect(len(mock_debugpy.method_calls)).to_equal(0)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_START,
        blocking=True,
    )

    mock_debugpy.listen.assert_called_once_with(("127.0.0.1", 80))
    mock_debugpy.wait_for_client.assert_not_called()
    expect(len(mock_debugpy.method_calls)).to_equal(1)
