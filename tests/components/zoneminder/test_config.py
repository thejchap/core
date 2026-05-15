"""Tests for ZoneMinder YAML configuration validation."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.zoneminder.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_SSL
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from .conftest import MOCK_HOST

from tests.hass_fixtures import hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def invalid_config_missing_host(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that config without host is rejected."""
    config: dict = {DOMAIN: [{}]}

    result = await async_setup_component(hass, DOMAIN, config)
    expect(result).to_be_falsy()


@test
async def invalid_config_bad_ssl_type(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that non-boolean ssl value is rejected."""
    config = {DOMAIN: [{CONF_HOST: MOCK_HOST, CONF_SSL: "not_bool"}]}

    result = await async_setup_component(hass, DOMAIN, config)
    expect(result).to_be_falsy()
