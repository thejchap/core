"""Tests for the STIEBEL ELTRON integration."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.stiebel_eltron.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import (
    hass as hass_fixture,
    issue_registry as issue_registry_fixture,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level anchor fixture."""


@test
async def async_setup_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test successful async_setup."""
    config = {}

    expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)
    await hass.async_block_till_done()

    issue = issue_registry.async_get_issue(DOMAIN, "deprecated_yaml")
    expect(issue).to_be(None)
