"""Test Backblaze B2 diagnostics."""

from unittest.mock import Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.backblaze_b2.diagnostics import (
    async_get_config_entry_diagnostics,
)
from homeassistant.core import HomeAssistant

from . import setup_integration
from ._fixtures import b2_fixture, mock_config_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def diagnostics_basic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test basic diagnostics data collection."""
    await setup_integration(hass, entry)

    result = await async_get_config_entry_diagnostics(hass, entry)

    expect("entry_data" in result).to_be(True)
    expect("entry_options" in result).to_be(True)
    expect("bucket_info" in result).to_be(True)
    expect("account_info" in result).to_be(True)

    expect(entry.data["key_id"] not in str(result["entry_data"])).to_be(True)
    expect(entry.data["application_key"] not in str(result["entry_data"])).to_be(True)


@test
async def diagnostics_error_handling(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test diagnostics handles errors gracefully."""
    entry.runtime_data = None
    entry.add_to_hass(hass)

    result = await async_get_config_entry_diagnostics(hass, entry)

    expect("bucket_info" in result).to_be(True)
    expect("account_info" in result).to_be(True)


@test
async def diagnostics_bucket_data_redaction(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test diagnostics redacts bucket-specific sensitive data."""
    await setup_integration(hass, entry)

    mock_bucket = Mock()
    mock_bucket.name = "test-bucket"
    mock_bucket.id_ = "bucket_id_123"
    mock_bucket.type_ = "allPrivate"
    mock_bucket.cors_rules = []
    mock_bucket.lifecycle_rules = []
    mock_bucket.revision = 1

    mock_api = Mock()
    mock_account_info = Mock()
    mock_account_info.get_account_id.return_value = "account123"
    mock_account_info.get_api_url.return_value = "https://api.backblazeb2.com"
    mock_account_info.get_download_url.return_value = "https://f001.backblazeb2.com"
    mock_account_info.get_minimum_part_size.return_value = 5000000
    mock_account_info.get_allowed.return_value = {
        "capabilities": ["writeFiles", "listFiles", "readFiles"],
        "bucketId": "test_bucket_id_123",
        "bucketName": "restricted_bucket",
        "namePrefix": "restricted/path/",
    }

    mock_bucket.api = mock_api
    mock_api.account_info = mock_account_info

    with patch.object(entry, "runtime_data", mock_bucket):
        result = await async_get_config_entry_diagnostics(hass, entry)

    account_data = result["account_info"]

    expect(account_data["allowed"]["capabilities"]).to_equal(
        ["writeFiles", "listFiles", "readFiles"]
    )
    expect(account_data["allowed"]["bucketId"]).to_equal("**REDACTED**")
    expect(account_data["allowed"]["bucketName"]).to_equal("**REDACTED**")
    expect(account_data["allowed"]["namePrefix"]).to_equal("**REDACTED**")
