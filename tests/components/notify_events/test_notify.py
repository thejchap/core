"""The tests for notify_events."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.notify import (
    ATTR_DATA,
    ATTR_MESSAGE,
    DOMAIN as NOTIFY_DOMAIN,
)
from homeassistant.components.notify_events.notify import (
    ATTR_LEVEL,
    ATTR_PRIORITY,
    ATTR_TOKEN,
)
from homeassistant.core import HomeAssistant

from tests.common import async_mock_service
from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def send_msg(hass: HomeAssistant = Depends(hass)) -> None:
    """Test notify.events service."""
    notify_calls = async_mock_service(hass, NOTIFY_DOMAIN, "events")

    await hass.services.async_call(
        NOTIFY_DOMAIN,
        "events",
        {
            ATTR_MESSAGE: "message content",
            ATTR_DATA: {
                ATTR_TOKEN: "XYZ",
                ATTR_LEVEL: "warning",
                ATTR_PRIORITY: "high",
            },
        },
        blocking=True,
    )

    expect(len(notify_calls)).to_equal(1)
    call = notify_calls[-1]

    expect(call.domain).to_equal(NOTIFY_DOMAIN)
    expect(call.service).to_equal("events")
    expect(call.data.get(ATTR_MESSAGE)).to_equal("message content")
    expect(call.data.get(ATTR_DATA).get(ATTR_TOKEN)).to_equal("XYZ")
    expect(call.data.get(ATTR_DATA).get(ATTR_LEVEL)).to_equal("warning")
    expect(call.data.get(ATTR_DATA).get(ATTR_PRIORITY)).to_equal("high")
