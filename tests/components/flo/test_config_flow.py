"""Test the flo config flow."""

from http import HTTPStatus
import json
import time
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.flo.const import DOMAIN
from homeassistant.const import CONTENT_TYPE_JSON
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import aioclient_mock_setup
from .common import TEST_EMAIL_ADDRESS, TEST_PASSWORD, TEST_TOKEN, TEST_USER_ID

from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_setup),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.flo.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"username": TEST_USER_ID, "password": TEST_PASSWORD}
        )

        expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result2["title"]).to_equal(TEST_USER_ID)
        expect(result2["data"]).to_equal(
            {"username": TEST_USER_ID, "password": TEST_PASSWORD}
        )
        await hass.async_block_till_done()
        expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test we handle cannot connect error."""
    now = round(time.time())
    # Mocks a failed login response for flo.
    aioclient_mock.post(
        "https://api.meetflo.com/api/v1/users/auth",
        json=json.dumps(
            {
                "token": TEST_TOKEN,
                "tokenPayload": {
                    "user": {"user_id": TEST_USER_ID, "email": TEST_EMAIL_ADDRESS},
                    "timestamp": now,
                },
                "tokenExpiration": 86400,
                "timeNow": now,
            }
        ),
        headers={"Content-Type": CONTENT_TYPE_JSON},
        status=HTTPStatus.BAD_REQUEST,
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"username": "test-username", "password": "test-password"}
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})
