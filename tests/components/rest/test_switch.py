"""The tests for the REST switch platform."""

from http import HTTPStatus

import httpx
import respx
from tryke import Depends, expect, fixture, test

from homeassistant.components.rest import DOMAIN
from homeassistant.components.rest.switch import (
    CONF_BODY_OFF,
    CONF_BODY_ON,
    CONF_STATE_RESOURCE,
)
from homeassistant.components.switch import (
    DOMAIN as SWITCH_DOMAIN,
    SCAN_INTERVAL,
    SwitchDeviceClass,
)
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_ENTITY_ID,
    ATTR_ENTITY_PICTURE,
    ATTR_FRIENDLY_NAME,
    ATTR_ICON,
    CONF_DEVICE_CLASS,
    CONF_HEADERS,
    CONF_ICON,
    CONF_METHOD,
    CONF_NAME,
    CONF_PARAMS,
    CONF_PLATFORM,
    CONF_RESOURCE,
    CONF_UNIQUE_ID,
    CONTENT_TYPE_JSON,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.trigger_template_entity import CONF_PICTURE
from homeassistant.setup import async_setup_component
from homeassistant.util.dt import utcnow

from tests.common import assert_setup_component, async_fire_time_changed
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)

NAME = "foo"
DEVICE_CLASS = SwitchDeviceClass.SWITCH
RESOURCE = "http://localhost/"
STATE_RESOURCE = RESOURCE


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


async def _async_setup_test_switch(hass: HomeAssistant) -> None:
    respx.get(RESOURCE) % HTTPStatus.OK

    headers = {"Content-type": CONTENT_TYPE_JSON}
    config = {
        CONF_PLATFORM: DOMAIN,
        CONF_NAME: NAME,
        CONF_DEVICE_CLASS: DEVICE_CLASS,
        CONF_RESOURCE: RESOURCE,
        CONF_STATE_RESOURCE: STATE_RESOURCE,
        CONF_HEADERS: headers,
    }
    expect(
        await async_setup_component(hass, SWITCH_DOMAIN, {SWITCH_DOMAIN: config})
    ).to_be_truthy()
    await hass.async_block_till_done()
    assert_setup_component(1, SWITCH_DOMAIN)

    expect(hass.states.get("switch.foo").state).to_equal(STATE_UNKNOWN)
    respx.reset()


@test
async def setup_missing_config(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test setup with configuration missing required entries."""
    config = {SWITCH_DOMAIN: {CONF_PLATFORM: DOMAIN}}
    expect(await async_setup_component(hass, SWITCH_DOMAIN, config)).to_be_truthy()
    await hass.async_block_till_done()
    assert_setup_component(0, SWITCH_DOMAIN)
    expect(
        "Invalid config for 'switch' from integration 'rest': required key 'resource' "
        "not provided" in caplog.text
    ).to_be_truthy()


@test
async def setup_missing_schema(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test setup with resource missing schema."""
    config = {SWITCH_DOMAIN: {CONF_PLATFORM: DOMAIN, CONF_RESOURCE: "localhost"}}
    expect(await async_setup_component(hass, SWITCH_DOMAIN, config)).to_be_truthy()
    await hass.async_block_till_done()
    assert_setup_component(0, SWITCH_DOMAIN)
    expect(
        "Invalid config for 'switch' from integration 'rest': invalid url"
        in caplog.text
    ).to_be_truthy()


@test
async def setup_failed_connect(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test setup when connection error occurs."""
    with respx.mock:
        respx.get(RESOURCE).mock(side_effect=httpx.ConnectError(""))
        config = {SWITCH_DOMAIN: {CONF_PLATFORM: DOMAIN, CONF_RESOURCE: RESOURCE}}
        expect(
            await async_setup_component(hass, SWITCH_DOMAIN, config)
        ).to_be_truthy()
        await hass.async_block_till_done()
        assert_setup_component(0, SWITCH_DOMAIN)
        expect("No route to resource/endpoint" in caplog.text).to_be_truthy()


@test
async def setup_timeout(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test setup when connection timeout occurs."""
    with respx.mock:
        respx.get(RESOURCE).mock(side_effect=httpx.TimeoutException(""))
        config = {SWITCH_DOMAIN: {CONF_PLATFORM: DOMAIN, CONF_RESOURCE: RESOURCE}}
        expect(
            await async_setup_component(hass, SWITCH_DOMAIN, config)
        ).to_be_truthy()
        await hass.async_block_till_done()
        assert_setup_component(0, SWITCH_DOMAIN)
        expect("No route to resource/endpoint" in caplog.text).to_be_truthy()


@test
async def setup_minimum(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setup with minimum configuration."""
    with respx.mock:
        route = respx.get(RESOURCE) % HTTPStatus.OK
        config = {SWITCH_DOMAIN: {CONF_PLATFORM: DOMAIN, CONF_RESOURCE: RESOURCE}}
        with assert_setup_component(1, SWITCH_DOMAIN):
            expect(
                await async_setup_component(hass, SWITCH_DOMAIN, config)
            ).to_be_truthy()
            await hass.async_block_till_done()
        expect(route.call_count).to_equal(2)


@test
async def setup_query_params(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setup with query params."""
    with respx.mock:
        route = respx.get("http://localhost/?search=something") % HTTPStatus.OK
        config = {
            SWITCH_DOMAIN: {
                CONF_PLATFORM: DOMAIN,
                CONF_RESOURCE: RESOURCE,
                CONF_PARAMS: {"search": "something"},
            }
        }
        with assert_setup_component(1, SWITCH_DOMAIN):
            expect(
                await async_setup_component(hass, SWITCH_DOMAIN, config)
            ).to_be_truthy()
            await hass.async_block_till_done()

        expect(route.call_count).to_equal(2)


@test
async def setup(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setup with valid configuration."""
    with respx.mock:
        route = respx.get(RESOURCE) % HTTPStatus.OK
        config = {
            SWITCH_DOMAIN: {
                CONF_PLATFORM: DOMAIN,
                CONF_NAME: "foo",
                CONF_RESOURCE: RESOURCE,
                CONF_HEADERS: {"Content-type": CONTENT_TYPE_JSON},
                CONF_BODY_ON: "custom on text",
                CONF_BODY_OFF: "custom off text",
            }
        }
        expect(
            await async_setup_component(hass, SWITCH_DOMAIN, config)
        ).to_be_truthy()
        await hass.async_block_till_done()
        expect(route.call_count).to_equal(2)
        assert_setup_component(1, SWITCH_DOMAIN)


@test
async def setup_with_state_resource(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setup with valid configuration."""
    with respx.mock:
        respx.get(RESOURCE) % HTTPStatus.NOT_FOUND
        route = respx.get("http://localhost/state") % HTTPStatus.OK
        config = {
            SWITCH_DOMAIN: {
                CONF_PLATFORM: DOMAIN,
                CONF_NAME: "foo",
                CONF_RESOURCE: RESOURCE,
                CONF_STATE_RESOURCE: "http://localhost/state",
                CONF_HEADERS: {"Content-type": CONTENT_TYPE_JSON},
                CONF_BODY_ON: "custom on text",
                CONF_BODY_OFF: "custom off text",
            }
        }
        expect(
            await async_setup_component(hass, SWITCH_DOMAIN, config)
        ).to_be_truthy()
        await hass.async_block_till_done()
        expect(route.call_count).to_equal(2)
        assert_setup_component(1, SWITCH_DOMAIN)


@test
async def setup_with_templated_headers_params(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setup with valid configuration."""
    with respx.mock:
        route = respx.get(RESOURCE) % HTTPStatus.OK
        config = {
            SWITCH_DOMAIN: {
                CONF_PLATFORM: DOMAIN,
                CONF_NAME: "foo",
                CONF_RESOURCE: "http://localhost",
                CONF_HEADERS: {
                    "Accept": CONTENT_TYPE_JSON,
                    "User-Agent": "Mozilla/{{ 3 + 2 }}.0",
                },
                CONF_PARAMS: {
                    "start": 0,
                    "end": "{{ 3 + 2 }}",
                },
            }
        }
        expect(
            await async_setup_component(hass, SWITCH_DOMAIN, config)
        ).to_be_truthy()
        await hass.async_block_till_done()
        expect(route.call_count).to_equal(2)
        last_call = route.calls[-1]
        last_request: httpx.Request = last_call.request
        expect(last_request.headers.get("Accept")).to_equal(CONTENT_TYPE_JSON)
        expect(last_request.headers.get("User-Agent")).to_equal("Mozilla/5.0")
        expect(last_request.url.params["start"]).to_equal("0")
        expect(last_request.url.params["end"]).to_equal("5")
        assert_setup_component(1, SWITCH_DOMAIN)


# Tests for REST switch platform.


@test
async def name(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the name."""
    with respx.mock:
        await _async_setup_test_switch(hass)

        state = hass.states.get("switch.foo")
        expect(state.attributes[ATTR_FRIENDLY_NAME]).to_equal(NAME)


@test
async def device_class(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the device class."""
    with respx.mock:
        await _async_setup_test_switch(hass)

        state = hass.states.get("switch.foo")
        expect(state.attributes[ATTR_DEVICE_CLASS]).to_equal(DEVICE_CLASS)


@test
async def is_on_before_update(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test is_on in initial state."""
    with respx.mock:
        await _async_setup_test_switch(hass)

        state = hass.states.get("switch.foo")
        expect(state.state).to_equal(STATE_UNKNOWN)


@test.cases(
    test.case("ok", http_success_code=HTTPStatus.OK),
    test.case("created", http_success_code=HTTPStatus.CREATED),
    test.case("accepted", http_success_code=HTTPStatus.ACCEPTED),
    test.case(
        "non_authoritative_information",
        http_success_code=HTTPStatus.NON_AUTHORITATIVE_INFORMATION,
    ),
    test.case("no_content", http_success_code=HTTPStatus.NO_CONTENT),
    test.case("reset_content", http_success_code=HTTPStatus.RESET_CONTENT),
    test.case("partial_content", http_success_code=HTTPStatus.PARTIAL_CONTENT),
)
async def turn_on_success(
    http_success_code: HTTPStatus,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test turn_on."""
    with respx.mock:
        await _async_setup_test_switch(hass)

        route = respx.post(RESOURCE) % http_success_code
        respx.get(RESOURCE).mock(side_effect=httpx.RequestError)
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "switch.foo"},
            blocking=True,
        )
        await hass.async_block_till_done()

        last_call = route.calls[-1]
        last_request: httpx.Request = last_call.request
        expect(last_request.content.decode()).to_equal("ON")
        expect(hass.states.get("switch.foo").state).to_equal(STATE_ON)


@test
async def turn_on_status_not_ok(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test turn_on when error status returned."""
    with respx.mock:
        await _async_setup_test_switch(hass)

        route = respx.post(RESOURCE) % HTTPStatus.INTERNAL_SERVER_ERROR
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "switch.foo"},
            blocking=True,
        )
        await hass.async_block_till_done()

        last_call = route.calls[-1]
        last_request: httpx.Request = last_call.request
        expect(last_request.content.decode()).to_equal("ON")
        expect(hass.states.get("switch.foo").state).to_equal(STATE_UNKNOWN)


@test
async def turn_on_timeout(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test turn_on when timeout occurs."""
    with respx.mock:
        await _async_setup_test_switch(hass)

        respx.post(RESOURCE).mock(side_effect=httpx.TimeoutException(""))
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "switch.foo"},
            blocking=True,
        )
        await hass.async_block_till_done()

        expect(hass.states.get("switch.foo").state).to_equal(STATE_UNKNOWN)


@test.cases(
    test.case("ok", http_success_code=HTTPStatus.OK),
    test.case("created", http_success_code=HTTPStatus.CREATED),
    test.case("accepted", http_success_code=HTTPStatus.ACCEPTED),
    test.case(
        "non_authoritative_information",
        http_success_code=HTTPStatus.NON_AUTHORITATIVE_INFORMATION,
    ),
    test.case("no_content", http_success_code=HTTPStatus.NO_CONTENT),
    test.case("reset_content", http_success_code=HTTPStatus.RESET_CONTENT),
    test.case("partial_content", http_success_code=HTTPStatus.PARTIAL_CONTENT),
)
async def turn_off_success(
    http_success_code: HTTPStatus,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test turn_off."""
    with respx.mock:
        await _async_setup_test_switch(hass)

        route = respx.post(RESOURCE) % http_success_code
        respx.get(RESOURCE).mock(side_effect=httpx.RequestError)
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: "switch.foo"},
            blocking=True,
        )
        await hass.async_block_till_done()

        last_call = route.calls[-1]
        last_request: httpx.Request = last_call.request
        expect(last_request.content.decode()).to_equal("OFF")

        expect(hass.states.get("switch.foo").state).to_equal(STATE_OFF)


@test
async def turn_off_status_not_ok(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test turn_off when error status returned."""
    with respx.mock:
        await _async_setup_test_switch(hass)

        route = respx.post(RESOURCE) % HTTPStatus.INTERNAL_SERVER_ERROR
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: "switch.foo"},
            blocking=True,
        )
        await hass.async_block_till_done()

        last_call = route.calls[-1]
        last_request: httpx.Request = last_call.request
        expect(last_request.content.decode()).to_equal("OFF")

        expect(hass.states.get("switch.foo").state).to_equal(STATE_UNKNOWN)


@test
async def turn_off_timeout(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test turn_off when timeout occurs."""
    with respx.mock:
        await _async_setup_test_switch(hass)

        respx.post(RESOURCE).mock(side_effect=httpx.TimeoutException(""))
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: "switch.foo"},
            blocking=True,
        )
        await hass.async_block_till_done()

        expect(hass.states.get("switch.foo").state).to_equal(STATE_UNKNOWN)


@test
async def update_when_on(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test update when switch is on."""
    with respx.mock:
        await _async_setup_test_switch(hass)

        respx.get(RESOURCE).respond(text="ON")
        async_fire_time_changed(hass, utcnow() + SCAN_INTERVAL)
        await hass.async_block_till_done()

        expect(hass.states.get("switch.foo").state).to_equal(STATE_ON)


@test
async def update_when_off(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test update when switch is off."""
    with respx.mock:
        await _async_setup_test_switch(hass)

        respx.get(RESOURCE).respond(text="OFF")
        async_fire_time_changed(hass, utcnow() + SCAN_INTERVAL)
        await hass.async_block_till_done()

        expect(hass.states.get("switch.foo").state).to_equal(STATE_OFF)


@test
async def update_when_unknown(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test update when unknown status returned."""
    with respx.mock:
        await _async_setup_test_switch(hass)

        respx.get(RESOURCE).respond(text="unknown status")
        async_fire_time_changed(hass, utcnow() + SCAN_INTERVAL)
        await hass.async_block_till_done()

        expect(hass.states.get("switch.foo").state).to_equal(STATE_UNKNOWN)


@test
async def update_timeout(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test update when timeout occurs."""
    with respx.mock:
        await _async_setup_test_switch(hass)

        respx.get(RESOURCE).mock(side_effect=httpx.TimeoutException(""))
        async_fire_time_changed(hass, utcnow() + SCAN_INTERVAL)
        await hass.async_block_till_done()

        expect(hass.states.get("switch.foo").state).to_equal(STATE_UNKNOWN)


@test
async def entity_config(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test entity configuration."""
    with respx.mock:
        respx.get(RESOURCE) % HTTPStatus.OK
        config = {
            SWITCH_DOMAIN: {
                # REST configuration
                CONF_PLATFORM: DOMAIN,
                CONF_METHOD: "POST",
                CONF_RESOURCE: "http://localhost",
                # Entity configuration
                CONF_ICON: "{{'mdi:one_two_three'}}",
                CONF_PICTURE: "{{'blabla.png'}}",
                CONF_NAME: "{{'REST' + ' ' + 'Switch'}}",
                CONF_UNIQUE_ID: "very_unique",
            },
        }

        expect(
            await async_setup_component(hass, SWITCH_DOMAIN, config)
        ).to_be_truthy()
        await hass.async_block_till_done()

        expect(
            entity_registry.async_get("switch.rest_switch").unique_id
        ).to_equal("very_unique")

        state = hass.states.get("switch.rest_switch")
        expect(state.state).to_equal("unknown")
        expect(state.attributes).to_equal(
            {
                ATTR_ENTITY_PICTURE: "blabla.png",
                ATTR_FRIENDLY_NAME: "REST Switch",
                ATTR_ICON: "mdi:one_two_three",
            }
        )


@test
async def availability(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test entity configuration."""
    with respx.mock:
        respx.get("http://localhost").respond(
            status_code=HTTPStatus.OK,
            json={"beer": 1},
        )
        expect(
            await async_setup_component(
                hass,
                SWITCH_DOMAIN,
                {
                    SWITCH_DOMAIN: {
                        # REST configuration
                        CONF_PLATFORM: DOMAIN,
                        CONF_METHOD: "POST",
                        CONF_RESOURCE: "http://localhost",
                        # Entity configuration
                        CONF_NAME: "{{'REST' + ' ' + 'Switch'}}",
                        "is_on_template": "{{ value_json.beer == 1 }}",
                        "availability": "{{ value_json.beer is defined }}",
                        CONF_ICON: "mdi:{{ value_json.beer }}",
                        CONF_PICTURE: "{{ value_json.beer }}.png",
                    },
                },
            )
        ).to_be_truthy()
        await async_setup_component(hass, "homeassistant", {})
        await hass.async_block_till_done()

        state = hass.states.get("switch.rest_switch")
        expect(state).not_.to_be_none()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes["icon"]).to_equal("mdi:1")
        expect(state.attributes["entity_picture"]).to_equal("1.png")

        respx.get("http://localhost").respond(
            status_code=HTTPStatus.OK,
            json={"x": 1},
        )
        await hass.services.async_call(
            "homeassistant",
            "update_entity",
            {ATTR_ENTITY_ID: ["switch.rest_switch"]},
            blocking=True,
        )
        await hass.async_block_till_done()

        state = hass.states.get("switch.rest_switch")
        expect(state).not_.to_be_none()
        expect(state.state).to_equal(STATE_UNAVAILABLE)
        expect("icon" in state.attributes).to_be_falsy()
        expect("entity_picture" in state.attributes).to_be_falsy()

        respx.get("http://localhost").respond(
            status_code=HTTPStatus.OK,
            json={"beer": 0},
        )
        await hass.services.async_call(
            "homeassistant",
            "update_entity",
            {ATTR_ENTITY_ID: ["switch.rest_switch"]},
            blocking=True,
        )
        await hass.async_block_till_done()

        state = hass.states.get("switch.rest_switch")
        expect(state).not_.to_be_none()
        expect(state.state).to_equal(STATE_OFF)
        expect(state.attributes["icon"]).to_equal("mdi:0")
        expect(state.attributes["entity_picture"]).to_equal("0.png")


@test
async def availability_blocks_is_on_template(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test availability blocks is_on_template from rendering."""
    error = "Error parsing value for switch.block_template: 'x' is undefined"
    with respx.mock:
        respx.get(RESOURCE).respond(status_code=HTTPStatus.OK, content="51")
        config = {
            SWITCH_DOMAIN: {
                # REST configuration
                CONF_PLATFORM: DOMAIN,
                CONF_METHOD: "POST",
                CONF_RESOURCE: "http://localhost",
                # Entity configuration
                CONF_NAME: "block_template",
                "is_on_template": "{{ x - 1 }}",
                "availability": "{{ value == '50' }}",
            },
        }

        expect(
            await async_setup_component(hass, SWITCH_DOMAIN, config)
        ).to_be_truthy()
        await hass.async_block_till_done()
        await async_setup_component(hass, "homeassistant", {})
        await hass.async_block_till_done()

        expect(error not in caplog.text).to_be_truthy()

        state = hass.states.get("switch.block_template")
        expect(state).not_.to_be_none()
        expect(state.state).to_equal(STATE_UNAVAILABLE)

        respx.clear()
        respx.get("http://localhost").respond(status_code=HTTPStatus.OK, content="50")
        await hass.services.async_call(
            "homeassistant",
            "update_entity",
            {ATTR_ENTITY_ID: ["switch.block_template"]},
            blocking=True,
        )
        await hass.async_block_till_done()

        expect(error in caplog.text).to_be_truthy()
