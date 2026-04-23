"""The tests for the Configurator component."""

from datetime import timedelta

from tryke import Depends, expect, fixture, test

from homeassistant.components import configurator
from homeassistant.const import ATTR_FRIENDLY_NAME
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from tests.common import async_fire_time_changed
from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def request_least_info(hass: HomeAssistant = Depends(hass)) -> None:
    """Test request config with least amount of data."""
    request_id = configurator.async_request_config(hass, "Test Request", lambda _: None)

    expect(len(hass.services.async_services().get(configurator.DOMAIN, []))).to_equal(1)

    states = hass.states.async_all()

    expect(len(states)).to_equal(1)

    state = states[0]

    expect(state.state).to_equal(configurator.STATE_CONFIGURE)
    expect(state.attributes.get(configurator.ATTR_CONFIGURE_ID)).to_equal(request_id)


@test
async def request_all_info(hass: HomeAssistant = Depends(hass)) -> None:
    """Test request config with all possible info."""
    exp_attr = {
        ATTR_FRIENDLY_NAME: "Test Request",
        configurator.ATTR_DESCRIPTION: """config description

[link name](link url)

![Description image](config image url)""",
        configurator.ATTR_SUBMIT_CAPTION: "config submit caption",
        configurator.ATTR_FIELDS: [],
        configurator.ATTR_ENTITY_PICTURE: "config entity picture",
        configurator.ATTR_CONFIGURE_ID: configurator.async_request_config(
            hass,
            name="Test Request",
            callback=lambda _: None,
            description="config description",
            description_image="config image url",
            submit_caption="config submit caption",
            fields=None,
            link_name="link name",
            link_url="link url",
            entity_picture="config entity picture",
        ),
    }

    states = hass.states.async_all()
    expect(len(states)).to_equal(1)
    state = states[0]

    expect(state.state).to_equal(configurator.STATE_CONFIGURE)
    expect(state.attributes).to_equal(exp_attr)


@test
async def callback_called_on_configure(hass: HomeAssistant = Depends(hass)) -> None:
    """Test if our callback gets called when configure service called."""
    calls = []
    request_id = configurator.async_request_config(
        hass, "Test Request", lambda _: calls.append(1)
    )

    await hass.services.async_call(
        configurator.DOMAIN,
        configurator.SERVICE_CONFIGURE,
        {configurator.ATTR_CONFIGURE_ID: request_id},
    )

    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)


@test
async def state_change_on_notify_errors(hass: HomeAssistant = Depends(hass)) -> None:
    """Test state change on notify errors."""
    request_id = configurator.async_request_config(hass, "Test Request", lambda _: None)
    error = "Oh no bad bad bad"
    configurator.async_notify_errors(hass, request_id, error)

    states = hass.states.async_all()
    expect(len(states)).to_equal(1)
    state = states[0]
    expect(state.attributes.get(configurator.ATTR_ERRORS)).to_equal(error)


@test
async def notify_errors_fail_silently_on_bad_request_id(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test if notify errors fails silently with a bad request id."""
    configurator.async_notify_errors(hass, 2015, "Try this error")


@test
async def request_done_works(hass: HomeAssistant = Depends(hass)) -> None:
    """Test if calling request done works."""
    request_id = configurator.async_request_config(hass, "Test Request", lambda _: None)
    configurator.async_request_done(hass, request_id)
    expect(len(hass.states.async_all())).to_equal(1)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=1))
    await hass.async_block_till_done()
    expect(len(hass.states.async_all())).to_equal(0)


@test
async def request_done_fail_silently_on_bad_request_id(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test that request_done fails silently with a bad request id."""
    configurator.async_request_done(hass, 2016)
