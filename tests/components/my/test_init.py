"""Test the my init."""

from unittest import mock

from tryke import Depends, expect, fixture, test

from homeassistant.components.my import URL_PATH
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def setup(hass: HomeAssistant = Depends(_trigger_executor)) -> None:
    """Test setup."""
    with mock.patch(
        "homeassistant.components.frontend.async_register_built_in_panel"
    ) as mock_register_panel:
        expect(await async_setup_component(hass, "my", {"foo": "bar"})).to_be_truthy()
        expect(mock_register_panel.call_args).to_equal(
            mock.call(hass, "my", frontend_url_path=URL_PATH)
        )
