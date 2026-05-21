"""Test automation logbook."""

from tryke import Depends, expect, fixture, test

from homeassistant.components import automation
from homeassistant.core import Context, HomeAssistant
from homeassistant.setup import async_setup_component

from tests.components.automation._fixtures import recorder_mock as recorder_mock_fixture
from tests.components.logbook.common import MockRow, mock_humanify
from tests.hass_fixtures import hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def humanify_automation_trigger_event(
    hass: HomeAssistant = Depends(_trigger_executor),
    recorder_mock: object = Depends(recorder_mock_fixture),
) -> None:
    """Test humanifying Shelly click event."""
    expect(await async_setup_component(hass, "automation", {})).to_be_truthy()
    expect(await async_setup_component(hass, "logbook", {})).to_be_truthy()
    await hass.async_block_till_done()
    context = Context()

    event1, event2 = mock_humanify(
        hass,
        [
            MockRow(
                automation.EVENT_AUTOMATION_TRIGGERED,
                {
                    "name": "Bla",
                    "entity_id": "automation.bla",
                    "source": "state change of input_boolean.yo",
                },
                context=context,
            ),
            MockRow(
                automation.EVENT_AUTOMATION_TRIGGERED,
                {
                    "name": "Bla",
                    "entity_id": "automation.bla",
                },
                context=context,
            ),
        ],
    )

    expect(event1["name"]).to_equal("Bla")
    expect(event1["message"]).to_equal("triggered by state change of input_boolean.yo")
    expect(event1["source"]).to_equal("state change of input_boolean.yo")
    expect(event1["context_id"]).to_equal(context.id)
    expect(event1["entity_id"]).to_equal("automation.bla")

    expect(event2["name"]).to_equal("Bla")
    expect(event2["message"]).to_equal("triggered")
    expect(event2["source"]).to_be(None)
    expect(event2["context_id"]).to_equal(context.id)
    expect(event2["entity_id"]).to_equal("automation.bla")
