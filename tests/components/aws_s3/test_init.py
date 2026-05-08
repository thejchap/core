"""Test the AWS S3 storage integration."""

from unittest.mock import AsyncMock, patch

from botocore.exceptions import (
    ClientError,
    EndpointConnectionError,
    ParamValidationError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import setup_integration
from ._fixtures import mock_client, mock_config_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import mock_async_zeroconf


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _zc: None = Depends(mock_async_zeroconf),
) -> None:
    """Per-module trigger to anchor fixture resolution."""


@test
async def load_unload_config_entry(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test loading and unloading the integration."""
    await setup_integration(hass, mock_config_entry)

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.cases(
    test.case(
        "param_validation_error",
        exception=ParamValidationError(report="Invalid bucket name"),
        state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "value_error",
        exception=ValueError(),
        state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "endpoint_connection_error",
        exception=EndpointConnectionError(endpoint_url="https://example.com"),
        state=ConfigEntryState.SETUP_RETRY,
    ),
)
async def setup_entry_create_client_errors(
    exception: Exception,
    state: ConfigEntryState,
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test various setup errors."""
    with patch(
        "aiobotocore.session.AioSession.create_client",
        side_effect=exception,
    ):
        await setup_integration(hass, mock_config_entry)
        expect(mock_config_entry.state).to_be(state)


@test
async def setup_entry_head_bucket_error(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_client: AsyncMock = Depends(mock_client),
) -> None:
    """Test setup_entry error when calling head_bucket."""
    mock_client.head_bucket.side_effect = ClientError(
        error_response={"Error": {"Code": "InvalidAccessKeyId"}},
        operation_name="head_bucket",
    )
    await setup_integration(hass, mock_config_entry)
    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)
