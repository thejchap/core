"""Test the IDrive e2 storage integration."""

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


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def async_setup_entry_does_not_mask_when_close_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    client: AsyncMock = Depends(mock_client),
) -> None:
    """Test close failures do not mask the original setup exception."""
    config_entry.add_to_hass(hass)

    # Force setup to fail after the client has been created
    client.head_bucket.side_effect = ClientError(
        {"Error": {"Code": "403", "Message": "Forbidden"}}, "HeadBucket"
    )

    # Also force close() to fail
    client.close.side_effect = RuntimeError("boom")

    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(False)
    expect(config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)

    client.close.assert_awaited_once()


@test
async def load_unload_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _client: AsyncMock = Depends(mock_client),
) -> None:
    """Test loading and unloading the integration."""
    await setup_integration(hass, config_entry)

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.cases(
    test.case(
        "param_validation",
        exception=ParamValidationError(report="Invalid bucket name"),
        state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "value_error",
        exception=ValueError(),
        state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "endpoint_connection",
        exception=EndpointConnectionError(endpoint_url="https://example.com"),
        state=ConfigEntryState.SETUP_RETRY,
    ),
)
async def setup_entry_create_client_errors(
    *,
    exception: Exception,
    state: ConfigEntryState,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test various setup errors."""
    with patch(
        "homeassistant.components.idrive_e2.AioSession.create_client",
        side_effect=exception,
    ):
        await setup_integration(hass, config_entry)
        expect(config_entry.state).to_be(state)


@test.cases(
    test.case(
        "invalid_access_key",
        error_response={"Error": {"Code": "InvalidAccessKeyId"}},
    ),
    test.case(
        "bucket_not_found",
        error_response={"Error": {"Code": "404", "Message": "Not Found"}},
    ),
)
async def setup_entry_head_bucket_errors(
    *,
    error_response: dict,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    client: AsyncMock = Depends(mock_client),
) -> None:
    """Test setup_entry errors when calling head_bucket."""
    client.head_bucket.side_effect = ClientError(
        error_response=error_response,
        operation_name="head_bucket",
    )

    await setup_integration(hass, config_entry)

    expect(config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)
