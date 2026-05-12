"""Test Backblaze B2 repairs."""

from unittest.mock import Mock, patch

from b2sdk.v2.exception import (
    B2Error,
    NonExistentBucket,
    RestrictedBucket,
    Unauthorized,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.backblaze_b2.repairs import (
    async_check_for_repair_issues,
    async_create_fix_flow,
)
from homeassistant.components.repairs import ConfirmRepairFlow
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@fixture
def mock_entry() -> MockConfigEntry:
    """Create a mock config entry with runtime data."""
    entry = MockConfigEntry(domain="backblaze_b2", data={"bucket": "test"})
    entry.runtime_data = Mock()
    return entry


@test
async def unauthorized_triggers_reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_entry),
) -> None:
    """Test that Unauthorized exception triggers reauth flow."""
    entry.runtime_data.api.account_info.get_allowed.side_effect = Unauthorized(
        "test", "auth_failed"
    )
    with patch.object(entry, "async_start_reauth") as mock_reauth:
        await async_check_for_repair_issues(hass, entry)

    mock_reauth.assert_called_once_with(hass)
    expect(len(ir.async_get(hass).issues)).to_equal(0)


@test.cases(
    test.case(
        "restricted_bucket",
        exception=RestrictedBucket("test"),
        expected_issues=1,
    ),
    test.case(
        "non_existent_bucket",
        exception=NonExistentBucket("test"),
        expected_issues=1,
    ),
    test.case("b2_error", exception=B2Error("test"), expected_issues=0),
)
async def repair_issue_creation(
    exception: Exception,
    expected_issues: int,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_entry),
) -> None:
    """Test repair issue creation for different exception types."""
    entry.runtime_data.api.account_info.get_allowed.side_effect = exception
    with patch.object(entry, "async_start_reauth") as mock_reauth:
        await async_check_for_repair_issues(hass, entry)

    mock_reauth.assert_not_called()
    expect(len(ir.async_get(hass).issues)).to_equal(expected_issues)


@test
async def async_create_fix_flow_test(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test creating repair fix flow."""
    flow = await async_create_fix_flow(hass, "test_issue", None)
    expect(isinstance(flow, ConfirmRepairFlow)).to_be(True)
