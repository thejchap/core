"""Tests for the TP-Link LTE integration."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.tplink_lte import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import (
    hass as hass_fixture,
    issue_registry as issue_registry_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def tplink_lte_repair_issue(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test the TP-Link LTE repair issue is created on setup."""
    expect(
        bool(
            await async_setup_component(
                hass,
                DOMAIN,
                {DOMAIN: [{"host": "192.168.0.1", "password": "secret"}]},
            )
        )
    ).to_be(True)
    await hass.async_block_till_done()

    expect(issue_registry.async_get_issue(DOMAIN, DOMAIN) is not None).to_be(True)
    issue = issue_registry.async_get_issue(DOMAIN, DOMAIN)
    expect(issue.severity).to_be(ir.IssueSeverity.ERROR)
    expect(issue.translation_key).to_equal("integration_removed")
