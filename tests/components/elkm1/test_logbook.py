"""The tests for elkm1 logbook."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.elkm1.const import (
    ATTR_KEY,
    ATTR_KEY_NAME,
    ATTR_KEYPAD_ID,
    ATTR_KEYPAD_NAME,
    DOMAIN,
    EVENT_ELKM1_KEYPAD_KEY_PRESSED,
)
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from . import _patch_discovery, _patch_elk

from tests.common import MockConfigEntry
from tests.components.logbook.common import MockRow, mock_humanify
from tests.hass_fixtures import hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def humanify_elkm1_keypad_event(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test humanifying elkm1 keypad presses."""
    hass.config.components.add("recorder")
    expect(await async_setup_component(hass, "logbook", {})).to_be(True)
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "elks://1.2.3.4"},
        unique_id="aa:bb:cc:dd:ee:ff",
    )
    config_entry.add_to_hass(hass)

    with _patch_discovery(), _patch_elk():
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    (event1, event2) = mock_humanify(
        hass,
        [
            MockRow(
                EVENT_ELKM1_KEYPAD_KEY_PRESSED,
                {
                    ATTR_KEYPAD_ID: 1,
                    ATTR_KEY_NAME: "four",
                    ATTR_KEY: "4",
                    ATTR_KEYPAD_NAME: "Main Bedroom",
                },
            ),
            MockRow(
                EVENT_ELKM1_KEYPAD_KEY_PRESSED,
                {
                    ATTR_KEYPAD_ID: 1,
                    ATTR_KEY_NAME: "five",
                    ATTR_KEY: "5",
                },
            ),
        ],
    )

    expect(event1["name"]).to_equal("Elk Keypad Main Bedroom")
    expect(event1["domain"]).to_equal(DOMAIN)
    expect(event1["message"]).to_equal("pressed four (4)")

    expect(event2["name"]).to_equal("Elk Keypad 1")
    expect(event2["domain"]).to_equal(DOMAIN)
    expect(event2["message"]).to_equal("pressed five (5)")
