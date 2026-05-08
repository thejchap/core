"""Test cloud subscription functions."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

from hass_nabucasa import Cloud, payments_api
from tryke import Depends, expect, fixture, test

from homeassistant.components.cloud.subscription import (
    async_migrate_paypal_agreement,
    async_subscription_info,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from ._fixtures import load_homeassistant

from tests.hass_fixtures import LogCapture, caplog, hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _load_homeassistant: None = Depends(load_homeassistant),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@fixture
async def mocked_cloud(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> Cloud:
    """Mock cloud object."""
    return Mock(
        auth=Mock(async_check_token=AsyncMock()),
        websession=async_get_clientsession(hass),
        payments=Mock(
            spec=payments_api.PaymentsApi,
            subscription_info=AsyncMock(),
            migrate_paypal_agreement=AsyncMock(),
        ),
    )


@test
async def fetching_subscription_with_api_error(
    cap: LogCapture = Depends(caplog),
    cloud: Cloud = Depends(mocked_cloud),
) -> None:
    """Test that we handle API errors."""
    cloud.payments.subscription_info.side_effect = payments_api.PaymentsApiError(
        "There was an error with the API"
    )

    expect(await async_subscription_info(cloud)).to_be(None)
    expect(
        "Failed to fetch subscription information - There was an error with the API"
        in cap.text
    ).to_be(True)


@test
async def fetching_subscription_with_timeout_error(
    cap: LogCapture = Depends(caplog),
    cloud: Cloud = Depends(mocked_cloud),
) -> None:
    """Test that we handle timeout error."""
    cloud.payments.subscription_info = lambda: asyncio.sleep(1)
    with patch("homeassistant.components.cloud.subscription.REQUEST_TIMEOUT", 0):
        expect(await async_subscription_info(cloud)).to_be(None)

    expect(
        "A timeout of 0 was reached while trying to fetch subscription information"
        in cap.text
    ).to_be(True)


@test
async def migrate_paypal_agreement_with_timeout_error(
    cap: LogCapture = Depends(caplog),
    cloud: Cloud = Depends(mocked_cloud),
) -> None:
    """Test that we handle timeout error."""
    cloud.payments.migrate_paypal_agreement.side_effect = TimeoutError()

    expect(await async_migrate_paypal_agreement(cloud)).to_be(None)
    expect(
        "A timeout of 10 was reached while trying to start agreement migration"
        in cap.text
    ).to_be(True)
