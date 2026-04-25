"""Tryke fixtures for html5 integration."""

from tryke import fixture

from homeassistant.components.html5.const import (
    ATTR_VAPID_EMAIL,
    ATTR_VAPID_PRV_KEY,
    ATTR_VAPID_PUB_KEY,
    DOMAIN,
)
from homeassistant.const import CONF_NAME

from tests.common import MockConfigEntry

MOCK_CONF = {
    ATTR_VAPID_EMAIL: "test@example.com",
    ATTR_VAPID_PRV_KEY: "h6acSRds8_KR8hT9djD8WucTL06Gfe29XXyZ1KcUjN8",
}
MOCK_CONF_PUB_KEY = "BIUtPN7Rq_8U7RBEqClZrfZ5dR9zPCfvxYPtLpWtRVZTJEc7lzv2dhzDU6Aw1m29Ao0-UA1Uq6XO9Df8KALBKqA"


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Mock html5 configuration entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="HTML5",
        data={
            ATTR_VAPID_PRV_KEY: MOCK_CONF[ATTR_VAPID_PRV_KEY],
            ATTR_VAPID_PUB_KEY: MOCK_CONF_PUB_KEY,
            ATTR_VAPID_EMAIL: MOCK_CONF[ATTR_VAPID_EMAIL],
            CONF_NAME: DOMAIN,
        },
        entry_id="ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    )
