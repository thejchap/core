"""The tests for the datetime component."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from tryke import Depends, expect, fixture, test

from homeassistant.components.datetime import ATTR_DATETIME, DOMAIN, SERVICE_SET_VALUE
from homeassistant.const import ATTR_ENTITY_ID, ATTR_FRIENDLY_NAME, CONF_PLATFORM
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from .common import MockDateTimeEntity

from tests.common import setup_test_component_platform
from tests.hass_fixtures import hass

DEFAULT_VALUE = datetime(2020, 1, 1, 12, 0, 0, tzinfo=UTC)


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def datetime_entity(hass: HomeAssistant = Depends(hass)) -> None:
    """Test date/time entity."""
    await hass.config.async_set_time_zone("UTC")
    setup_test_component_platform(
        hass,
        DOMAIN,
        [
            MockDateTimeEntity(
                name="test",
                unique_id="unique_datetime",
                native_value=datetime(2020, 1, 1, 1, 2, 3, tzinfo=UTC),
            )
        ],
    )

    expect(
        await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    ).to_be(True)
    await hass.async_block_till_done()

    state = hass.states.get("datetime.test")
    expect(state.state).to_equal("2020-01-01T01:02:03+00:00")
    expect(state.attributes).to_equal({ATTR_FRIENDLY_NAME: "test"})

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_DATETIME: datetime(2022, 3, 3, 3, 4, 5), ATTR_ENTITY_ID: "datetime.test"},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("datetime.test")
    expect(state.state).to_equal("2022-03-03T03:04:05+00:00")

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_DATETIME: "2022-03-03T03:04:05+00:00", ATTR_ENTITY_ID: "datetime.test"},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("datetime.test")
    expect(state.state).to_equal("2022-03-03T03:04:05+00:00")

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_DATETIME: "2022-03-03T03:04:05-05:00", ATTR_ENTITY_ID: "datetime.test"},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("datetime.test")
    expect(state.state).to_equal("2022-03-03T08:04:05+00:00")

    expect(
        MockDateTimeEntity(
            native_value=datetime(2020, 1, 2, 3, 4, 5, tzinfo=ZoneInfo("US/Eastern"))
        ).state
    ).to_equal("2020-01-02T08:04:05+00:00")

    date_entity = MockDateTimeEntity(native_value=None)
    expect(date_entity.state is None).to_be(True)
    expect(date_entity.state_attributes is None).to_be(True)

    expect(
        lambda: MockDateTimeEntity(
            native_value=datetime(2020, 1, 2, 3, 4, 5, tzinfo=None)
        ).state
    ).to_raise(ValueError)
