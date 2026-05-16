"""The tests for the Alert component."""

from copy import deepcopy

from tryke import Depends, expect, fixture, test

from homeassistant.components import alert, notify
from homeassistant.components.alert.const import (
    CONF_ALERT_MESSAGE,
    CONF_DATA,
    CONF_DONE_MESSAGE,
    CONF_NOTIFIERS,
    CONF_SKIP_FIRST,
    CONF_TITLE,
    DOMAIN,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_ENTITY_ID,
    CONF_NAME,
    CONF_REPEAT,
    CONF_STATE,
    SERVICE_TOGGLE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_IDLE,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.setup import async_setup_component

from tests.common import MockEntityPlatform, async_mock_service
from tests.hass_fixtures import hass
from tests.hass_tryke_helpers import expect_raises_async

NAME = "alert_test"
DONE_MESSAGE = "alert_gone"
NOTIFIER = "test"
BAD_NOTIFIER = "bad_notifier"
TEMPLATE = "{{ states.sensor.test.entity_id }}"
TEST_ENTITY = "sensor.test"
TITLE = "{{ states.sensor.test.entity_id }}"
TEST_TITLE = "sensor.test"
TEST_DATA = {"data": {"inline_keyboard": ["Close garage:/close_garage"]}}
TEST_CONFIG = {
    DOMAIN: {
        NAME: {
            CONF_NAME: NAME,
            CONF_DONE_MESSAGE: DONE_MESSAGE,
            CONF_ENTITY_ID: TEST_ENTITY,
            CONF_STATE: STATE_ON,
            CONF_REPEAT: 30,
            CONF_SKIP_FIRST: False,
            CONF_NOTIFIERS: [NOTIFIER],
            CONF_TITLE: TITLE,
            CONF_DATA: {},
        }
    }
}
TEST_NOACK = [
    NAME,
    NAME,
    "sensor.test",
    STATE_ON,
    [30],
    False,
    None,
    None,
    NOTIFIER,
    False,
    None,
    None,
]
ENTITY_ID = f"{DOMAIN}.{NAME}"


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@fixture
def mock_notifier(hass: HomeAssistant = Depends(hass)) -> list[ServiceCall]:
    """Mock for notifier."""
    return async_mock_service(hass, notify.DOMAIN, NOTIFIER)


@test
async def setup(hass: HomeAssistant = Depends(hass)) -> None:
    """Test setup method."""
    expect(await async_setup_component(hass, DOMAIN, TEST_CONFIG)).to_be(True)
    expect(hass.states.get(ENTITY_ID).state).to_equal(STATE_IDLE)


@test
async def fire(
    hass: HomeAssistant = Depends(hass),
    mock_notifier: list[ServiceCall] = Depends(mock_notifier),
) -> None:
    """Test the alert firing."""
    expect(await async_setup_component(hass, DOMAIN, TEST_CONFIG)).to_be(True)
    hass.states.async_set("sensor.test", STATE_ON)
    await hass.async_block_till_done()
    expect(hass.states.get(ENTITY_ID).state).to_equal(STATE_ON)


@test
async def silence(
    hass: HomeAssistant = Depends(hass),
    mock_notifier: list[ServiceCall] = Depends(mock_notifier),
) -> None:
    """Test silencing the alert."""
    expect(await async_setup_component(hass, DOMAIN, TEST_CONFIG)).to_be(True)
    hass.states.async_set("sensor.test", STATE_ON)
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )
    expect(hass.states.get(ENTITY_ID).state).to_equal(STATE_OFF)

    # alert should not be silenced on next fire
    hass.states.async_set("sensor.test", STATE_OFF)
    await hass.async_block_till_done()
    expect(hass.states.get(ENTITY_ID).state).to_equal(STATE_IDLE)
    hass.states.async_set("sensor.test", STATE_ON)
    await hass.async_block_till_done()
    expect(hass.states.get(ENTITY_ID).state).to_equal(STATE_ON)


@test
async def silence_can_acknowledge_false(hass: HomeAssistant = Depends(hass)) -> None:
    """Test that attempting to silence an alert with can_acknowledge=False will not silence."""
    config = deepcopy(TEST_CONFIG)
    config[DOMAIN][NAME]["can_acknowledge"] = False

    expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set(ENTITY_ID, STATE_ON)
    await hass.async_block_till_done()
    expect(hass.states.get(ENTITY_ID).state).to_equal(STATE_ON)

    async with expect_raises_async(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: ENTITY_ID},
            blocking=True,
        )
    await hass.async_block_till_done()

    # The state should still be ON because can_acknowledge=False
    expect(hass.states.get(ENTITY_ID).state).to_equal(STATE_ON)


@test
async def reset_test(
    hass: HomeAssistant = Depends(hass),
    mock_notifier: list[ServiceCall] = Depends(mock_notifier),
) -> None:
    """Test resetting the alert."""
    expect(await async_setup_component(hass, DOMAIN, TEST_CONFIG)).to_be(True)
    hass.states.async_set("sensor.test", STATE_ON)
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )

    expect(hass.states.get(ENTITY_ID).state).to_equal(STATE_OFF)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )
    expect(hass.states.get(ENTITY_ID).state).to_equal(STATE_ON)


@test
async def toggle(
    hass: HomeAssistant = Depends(hass),
    mock_notifier: list[ServiceCall] = Depends(mock_notifier),
) -> None:
    """Test toggling alert."""
    expect(await async_setup_component(hass, DOMAIN, TEST_CONFIG)).to_be(True)
    hass.states.async_set("sensor.test", STATE_ON)
    await hass.async_block_till_done()
    expect(hass.states.get(ENTITY_ID).state).to_equal(STATE_ON)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_TOGGLE,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )
    expect(hass.states.get(ENTITY_ID).state).to_equal(STATE_OFF)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_TOGGLE,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )
    expect(hass.states.get(ENTITY_ID).state).to_equal(STATE_ON)


@test
async def notification_no_done_message(
    hass: HomeAssistant = Depends(hass),
    mock_notifier: list[ServiceCall] = Depends(mock_notifier),
) -> None:
    """Test notifications."""
    config = deepcopy(TEST_CONFIG)
    del config[DOMAIN][NAME][CONF_DONE_MESSAGE]

    expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)
    expect(len(mock_notifier)).to_equal(0)

    hass.states.async_set("sensor.test", STATE_ON)
    await hass.async_block_till_done()
    expect(len(mock_notifier)).to_equal(1)

    hass.states.async_set("sensor.test", STATE_OFF)
    await hass.async_block_till_done()
    expect(len(mock_notifier)).to_equal(1)


@test
async def notification(
    hass: HomeAssistant = Depends(hass),
    mock_notifier: list[ServiceCall] = Depends(mock_notifier),
) -> None:
    """Test notifications."""
    expect(await async_setup_component(hass, DOMAIN, TEST_CONFIG)).to_be(True)
    expect(len(mock_notifier)).to_equal(0)

    hass.states.async_set("sensor.test", STATE_ON)
    await hass.async_block_till_done()
    expect(len(mock_notifier)).to_equal(1)

    hass.states.async_set("sensor.test", STATE_OFF)
    await hass.async_block_till_done()
    expect(len(mock_notifier)).to_equal(2)


@test
async def bad_notifier(
    hass: HomeAssistant = Depends(hass),
    mock_notifier: list[ServiceCall] = Depends(mock_notifier),
) -> None:
    """Test a broken notifier does not break the alert."""
    config = deepcopy(TEST_CONFIG)
    config[DOMAIN][NAME][CONF_NOTIFIERS] = [BAD_NOTIFIER, NOTIFIER]
    expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)
    expect(len(mock_notifier)).to_equal(0)

    hass.states.async_set("sensor.test", STATE_ON)
    await hass.async_block_till_done()
    expect(len(mock_notifier)).to_equal(1)
    expect(hass.states.get(ENTITY_ID).state).to_equal(STATE_ON)

    hass.states.async_set("sensor.test", STATE_OFF)
    await hass.async_block_till_done()
    expect(len(mock_notifier)).to_equal(2)
    expect(hass.states.get(ENTITY_ID).state).to_equal(STATE_IDLE)


@test
async def no_notifiers(
    hass: HomeAssistant = Depends(hass),
    mock_notifier: list[ServiceCall] = Depends(mock_notifier),
) -> None:
    """Test we send no notifications when there are not no."""
    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    NAME: {
                        CONF_NAME: NAME,
                        CONF_ENTITY_ID: TEST_ENTITY,
                        CONF_STATE: STATE_ON,
                        CONF_REPEAT: 30,
                    }
                }
            },
        )
    ).to_be(True)
    expect(len(mock_notifier)).to_equal(0)

    hass.states.async_set("sensor.test", STATE_ON)
    await hass.async_block_till_done()
    expect(len(mock_notifier)).to_equal(0)

    hass.states.async_set("sensor.test", STATE_OFF)
    await hass.async_block_till_done()
    expect(len(mock_notifier)).to_equal(0)


@test
async def sending_non_templated_notification(
    hass: HomeAssistant = Depends(hass),
    mock_notifier: list[ServiceCall] = Depends(mock_notifier),
) -> None:
    """Test notifications."""
    expect(await async_setup_component(hass, DOMAIN, TEST_CONFIG)).to_be(True)

    hass.states.async_set(TEST_ENTITY, STATE_ON)
    await hass.async_block_till_done()
    expect(len(mock_notifier)).to_equal(1)
    last_event = mock_notifier[-1]
    expect(last_event.data[notify.ATTR_MESSAGE]).to_equal(NAME)


@test
async def sending_templated_notification(
    hass: HomeAssistant = Depends(hass),
    mock_notifier: list[ServiceCall] = Depends(mock_notifier),
) -> None:
    """Test templated notification."""
    config = deepcopy(TEST_CONFIG)
    config[DOMAIN][NAME][CONF_ALERT_MESSAGE] = TEMPLATE
    expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)

    hass.states.async_set(TEST_ENTITY, STATE_ON)
    await hass.async_block_till_done()
    expect(len(mock_notifier)).to_equal(1)
    last_event = mock_notifier[-1]
    expect(last_event.data[notify.ATTR_MESSAGE]).to_equal(TEST_ENTITY)


@test
async def sending_templated_done_notification(
    hass: HomeAssistant = Depends(hass),
    mock_notifier: list[ServiceCall] = Depends(mock_notifier),
) -> None:
    """Test templated notification."""
    config = deepcopy(TEST_CONFIG)
    config[DOMAIN][NAME][CONF_DONE_MESSAGE] = TEMPLATE
    expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)

    hass.states.async_set(TEST_ENTITY, STATE_ON)
    await hass.async_block_till_done()
    hass.states.async_set(TEST_ENTITY, STATE_OFF)
    await hass.async_block_till_done()
    expect(len(mock_notifier)).to_equal(2)
    last_event = mock_notifier[-1]
    expect(last_event.data[notify.ATTR_MESSAGE]).to_equal(TEST_ENTITY)


@test
async def sending_titled_notification(
    hass: HomeAssistant = Depends(hass),
    mock_notifier: list[ServiceCall] = Depends(mock_notifier),
) -> None:
    """Test notifications."""
    config = deepcopy(TEST_CONFIG)
    config[DOMAIN][NAME][CONF_TITLE] = TITLE
    expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)

    hass.states.async_set(TEST_ENTITY, STATE_ON)
    await hass.async_block_till_done()
    expect(len(mock_notifier)).to_equal(1)
    last_event = mock_notifier[-1]
    expect(last_event.data[notify.ATTR_TITLE]).to_equal(TEST_TITLE)


@test
async def sending_data_notification(
    hass: HomeAssistant = Depends(hass),
    mock_notifier: list[ServiceCall] = Depends(mock_notifier),
) -> None:
    """Test notifications."""
    config = deepcopy(TEST_CONFIG)
    config[DOMAIN][NAME][CONF_DATA] = TEST_DATA
    expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)

    hass.states.async_set(TEST_ENTITY, STATE_ON)
    await hass.async_block_till_done()
    expect(len(mock_notifier)).to_equal(1)
    last_event = mock_notifier[-1]
    expect(last_event.data[notify.ATTR_DATA]).to_equal(TEST_DATA)


@test
async def skipfirst(
    hass: HomeAssistant = Depends(hass),
    mock_notifier: list[ServiceCall] = Depends(mock_notifier),
) -> None:
    """Test skipping first notification."""
    config = deepcopy(TEST_CONFIG)
    config[DOMAIN][NAME][CONF_SKIP_FIRST] = True
    expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)
    expect(len(mock_notifier)).to_equal(0)

    hass.states.async_set("sensor.test", STATE_ON)
    await hass.async_block_till_done()
    expect(len(mock_notifier)).to_equal(0)


@test
async def done_message_state_tracker_reset_on_cancel(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test that the done message is reset when canceled."""
    entity = alert.AlertEntity(hass, *TEST_NOACK)
    entity.platform = MockEntityPlatform(hass)
    entity._cancel = lambda *args: None
    expect(entity._send_done_message).to_be(False)
    entity._send_done_message = True
    await entity.end_alerting()
    await hass.async_block_till_done()
    expect(entity._send_done_message).to_be(False)
