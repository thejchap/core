"""Test cloud repairs."""

from datetime import timedelta
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.cloud.repairs import (
    async_manage_legacy_subscription_issue,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.util import dt as dt_util

from . import mock_cloud
from ._fixtures import load_homeassistant

from tests.common import async_fire_time_changed
from tests.hass_fixtures import (
    hass as hass_fixture,
    issue_registry as issue_registry_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _load_homeassistant: None = Depends(load_homeassistant),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def do_not_create_repair_issues_at_startup_if_not_logged_in(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test that we create repair issue at startup if we are logged in."""
    with patch("homeassistant.components.cloud.Cloud.is_logged_in", False):
        await mock_cloud(hass)

        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(hours=1))
        await hass.async_block_till_done()

    expect(
        bool(
            issue_registry.async_get_issue(
                domain="cloud", issue_id="legacy_subscription"
            )
        )
    ).to_be(False)


@test
async def legacy_subscription_delete_issue_if_no_longer_legacy(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test that we delete the legacy subscription issue if no longer legacy."""
    async_manage_legacy_subscription_issue(hass, {"provider": "legacy"})
    expect(
        bool(
            issue_registry.async_get_issue(
                domain="cloud", issue_id="legacy_subscription"
            )
        )
    ).to_be(True)

    async_manage_legacy_subscription_issue(hass, {})
    expect(
        bool(
            issue_registry.async_get_issue(
                domain="cloud", issue_id="legacy_subscription"
            )
        )
    ).to_be(False)


@test.skip("requires aioclient_mock + mock_auth + Cloud.is_logged_in patch chain")
async def create_repair_issues_at_startup_if_logged_in() -> None:
    """Stub for test_create_repair_issues_at_startup_if_logged_in."""


@test.skip("requires aioclient_mock + mock_auth + hass_client + repair flow")
async def legacy_subscription_repair_flow() -> None:
    """Stub for test_legacy_subscription_repair_flow."""


@test.skip("requires aioclient_mock + mock_auth + hass_client + repair flow")
async def legacy_subscription_repair_flow_timeout() -> None:
    """Stub for test_legacy_subscription_repair_flow_timeout."""
