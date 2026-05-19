"""Tryke fixtures for vacuum platform tests."""

from __future__ import annotations

from collections.abc import Generator

from tryke import Depends, fixture

from homeassistant.config_entries import ConfigFlow
from homeassistant.core import HomeAssistant

from tests.common import mock_config_flow, mock_platform
from tests.hass_fixtures import hass as hass_fixture
from tests.hass_tryke_helpers import setup_recorder_mock

TEST_DOMAIN = "test"


class MockFlow(ConfigFlow):
    """Test flow."""


@fixture
def config_flow_fixture(
    hass: HomeAssistant = Depends(hass_fixture),
) -> Generator[None]:
    """Mock config flow."""
    mock_platform(hass, f"{TEST_DOMAIN}.config_flow")

    with mock_config_flow(TEST_DOMAIN, MockFlow):
        yield


@fixture
async def recorder_mock(
    hass: HomeAssistant = Depends(hass_fixture),
):
    """Set up the recorder for tests that need it."""
    return await setup_recorder_mock(hass)
