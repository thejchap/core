"""Test the pushover notify platform."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.pushover import DOMAIN
from homeassistant.core import HomeAssistant

from ._fixtures import mock_pushover as mock_pushover_fx

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Module-level anchor fixture."""


@test
async def send_message(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_pushover: MagicMock = Depends(mock_pushover_fx),
) -> None:
    """Test sending a message."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "name": "pushover",
            "api_key": "API_KEY",
            "user_key": "USER_KEY",
        },
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    with patch(
        "homeassistant.components.pushover.notify.PushoverAPI.send_message"
    ) as mock_send_message:
        await hass.services.async_call(
            "notify",
            "pushover",
            {"message": "Hello TTL", "data": {"ttl": 900}},
            blocking=True,
        )

        mock_send_message.assert_called_once_with(
            user="USER_KEY",
            message="Hello TTL",
            device="",
            title="Home Assistant",
            url=None,
            url_title=None,
            image=None,
            priority=None,
            retry=None,
            expire=None,
            callback_url=None,
            timestamp=None,
            sound=None,
            html=0,
            ttl=900,
        )
        # Ensure fixture passes through
        expect(mock_send_message.called).to_be(True)
