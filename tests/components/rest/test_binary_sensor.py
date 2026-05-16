"""The tests for the REST binary sensor platform."""

from http import HTTPStatus
import ssl
from unittest.mock import patch

import aiohttp
from tryke import Depends, expect, fixture, test

from homeassistant import config as hass_config
from homeassistant.components.binary_sensor import (
    DOMAIN as BINARY_SENSOR_DOMAIN,
    BinarySensorDeviceClass,
)
from homeassistant.components.rest import DOMAIN
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_ENTITY_ID,
    CONTENT_TYPE_JSON,
    SERVICE_RELOAD,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component

from tests.common import get_fixture_path
from tests.hass_fixtures import (
    LogCapture,
    aioclient_mock as aioclient_mock_fixture,
    caplog as caplog_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _aiomock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> int:
    """Ensure mock_network and aioclient_mock patches are active before hass."""
    return 0


@test
async def setup_missing_basic_config(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup with configuration missing required entries."""
    expect(
        await async_setup_component(
            hass, BINARY_SENSOR_DOMAIN, {BINARY_SENSOR_DOMAIN: {"platform": DOMAIN}}
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    expect(len(hass.states.async_all(BINARY_SENSOR_DOMAIN))).to_equal(0)


@test
async def setup_missing_config(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup with configuration missing required entries."""
    expect(
        await async_setup_component(
            hass,
            BINARY_SENSOR_DOMAIN,
            {
                BINARY_SENSOR_DOMAIN: {
                    "platform": DOMAIN,
                    "resource": "localhost",
                    "method": "GET",
                }
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    expect(len(hass.states.async_all(BINARY_SENSOR_DOMAIN))).to_equal(0)


@test
async def setup_failed_connect(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test setup when connection error occurs."""
    aioclient_mock.get("http://localhost", exc=Exception("server offline"))
    expect(
        await async_setup_component(
            hass,
            BINARY_SENSOR_DOMAIN,
            {
                BINARY_SENSOR_DOMAIN: {
                    "platform": DOMAIN,
                    "resource": "http://localhost",
                    "method": "GET",
                }
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    expect(len(hass.states.async_all(BINARY_SENSOR_DOMAIN))).to_equal(0)
    expect("server offline" in caplog.text).to_be_truthy()


@test
async def setup_fail_on_ssl_erros(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test setup when connection error occurs."""
    aioclient_mock.get("https://localhost", exc=ssl.SSLError("ssl error"))
    expect(
        await async_setup_component(
            hass,
            BINARY_SENSOR_DOMAIN,
            {
                BINARY_SENSOR_DOMAIN: {
                    "platform": DOMAIN,
                    "resource": "https://localhost",
                    "method": "GET",
                }
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    expect(len(hass.states.async_all(BINARY_SENSOR_DOMAIN))).to_equal(0)
    expect("ssl error" in caplog.text).to_be_truthy()


@test
async def setup_timeout(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test setup when connection timeout occurs."""
    aioclient_mock.get("http://localhost", exc=TimeoutError())
    expect(
        await async_setup_component(
            hass,
            BINARY_SENSOR_DOMAIN,
            {
                BINARY_SENSOR_DOMAIN: {
                    "platform": DOMAIN,
                    "resource": "localhost",
                    "method": "GET",
                }
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    expect(len(hass.states.async_all(BINARY_SENSOR_DOMAIN))).to_equal(0)


@test
async def setup_minimum(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test setup with minimum configuration."""
    aioclient_mock.get("http://localhost", status=HTTPStatus.OK)
    expect(
        await async_setup_component(
            hass,
            BINARY_SENSOR_DOMAIN,
            {
                BINARY_SENSOR_DOMAIN: {
                    "platform": DOMAIN,
                    "resource": "http://localhost",
                    "method": "GET",
                }
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    expect(len(hass.states.async_all(BINARY_SENSOR_DOMAIN))).to_equal(1)


@test
async def setup_minimum_resource_template(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test setup with minimum configuration (resource_template)."""
    aioclient_mock.get("http://localhost", status=HTTPStatus.OK)
    expect(
        await async_setup_component(
            hass,
            BINARY_SENSOR_DOMAIN,
            {
                BINARY_SENSOR_DOMAIN: {
                    "platform": DOMAIN,
                    "resource_template": "{% set url = 'http://localhost' %}{{ url }}",
                }
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    expect(len(hass.states.async_all(BINARY_SENSOR_DOMAIN))).to_equal(1)


@test
async def setup_duplicate_resource_template(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test setup with duplicate resources."""
    aioclient_mock.get("http://localhost", status=HTTPStatus.OK)
    expect(
        await async_setup_component(
            hass,
            BINARY_SENSOR_DOMAIN,
            {
                BINARY_SENSOR_DOMAIN: {
                    "platform": DOMAIN,
                    "resource": "http://localhost",
                    "resource_template": "http://localhost",
                }
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    expect(len(hass.states.async_all(BINARY_SENSOR_DOMAIN))).to_equal(0)


@test
async def setup_get(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test setup with valid configuration."""
    aioclient_mock.get("http://localhost", status=HTTPStatus.OK, json={})
    expect(
        await async_setup_component(
            hass,
            BINARY_SENSOR_DOMAIN,
            {
                BINARY_SENSOR_DOMAIN: {
                    "platform": DOMAIN,
                    "resource": "http://localhost",
                    "method": "GET",
                    "value_template": "{{ value_json.key }}",
                    "name": "foo",
                    "verify_ssl": "true",
                    "timeout": 30,
                    "authentication": "basic",
                    "username": "my username",
                    "password": "my password",
                    "headers": {"Accept": CONTENT_TYPE_JSON},
                    "device_class": BinarySensorDeviceClass.PLUG,
                }
            },
        )
    ).to_be_truthy()

    await hass.async_block_till_done()
    expect(len(hass.states.async_all(BINARY_SENSOR_DOMAIN))).to_equal(1)

    state = hass.states.get("binary_sensor.foo")
    expect(state.state).to_equal(STATE_OFF)
    expect(state.attributes[ATTR_DEVICE_CLASS]).to_equal(BinarySensorDeviceClass.PLUG)


@test
async def setup_get_template_headers_params(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test setup with valid configuration."""
    aioclient_mock.get("http://localhost", status=200, json={})
    expect(
        await async_setup_component(
            hass,
            "sensor",
            {
                "sensor": {
                    "platform": DOMAIN,
                    "resource": "http://localhost",
                    "method": "GET",
                    "value_template": "{{ value_json.key }}",
                    "name": "foo",
                    "verify_ssl": "true",
                    "timeout": 30,
                    "headers": {
                        "Accept": CONTENT_TYPE_JSON,
                        "User-Agent": "Mozilla/{{ 3 + 2 }}.0",
                    },
                    "params": {
                        "start": 0,
                        "end": "{{ 3 + 2 }}",
                    },
                }
            },
        )
    ).to_be_truthy()
    await async_setup_component(hass, "homeassistant", {})
    await hass.async_block_till_done()

    expect(aioclient_mock.call_count).to_equal(1)
    last_request_headers = aioclient_mock.mock_calls[0][3]
    expect(last_request_headers["Accept"]).to_equal(CONTENT_TYPE_JSON)
    expect(last_request_headers["User-Agent"]).to_equal("Mozilla/5.0")


@test
async def setup_get_digest_auth(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test setup with valid configuration."""
    aioclient_mock.get("http://localhost", status=HTTPStatus.OK, json={})
    expect(
        await async_setup_component(
            hass,
            BINARY_SENSOR_DOMAIN,
            {
                BINARY_SENSOR_DOMAIN: {
                    "platform": DOMAIN,
                    "resource": "http://localhost",
                    "method": "GET",
                    "value_template": "{{ value_json.key }}",
                    "name": "foo",
                    "verify_ssl": "true",
                    "timeout": 30,
                    "authentication": "digest",
                    "username": "my username",
                    "password": "my password",
                    "headers": {"Accept": CONTENT_TYPE_JSON},
                }
            },
        )
    ).to_be_truthy()

    await hass.async_block_till_done()
    expect(len(hass.states.async_all(BINARY_SENSOR_DOMAIN))).to_equal(1)


@test
async def setup_post(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test setup with valid configuration."""
    aioclient_mock.post("http://localhost", status=HTTPStatus.OK, json={})
    expect(
        await async_setup_component(
            hass,
            BINARY_SENSOR_DOMAIN,
            {
                BINARY_SENSOR_DOMAIN: {
                    "platform": DOMAIN,
                    "resource": "http://localhost",
                    "method": "POST",
                    "value_template": "{{ value_json.key }}",
                    "payload": '{ "device": "toaster"}',
                    "name": "foo",
                    "verify_ssl": "true",
                    "timeout": 30,
                    "authentication": "basic",
                    "username": "my username",
                    "password": "my password",
                    "headers": {"Accept": CONTENT_TYPE_JSON},
                }
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    expect(len(hass.states.async_all(BINARY_SENSOR_DOMAIN))).to_equal(1)


@test
async def setup_get_off(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test setup with valid off configuration."""
    aioclient_mock.get(
        "http://localhost",
        status=HTTPStatus.OK,
        headers={"content-type": "text/json"},
        json={"dog": False},
    )
    expect(
        await async_setup_component(
            hass,
            BINARY_SENSOR_DOMAIN,
            {
                BINARY_SENSOR_DOMAIN: {
                    "platform": DOMAIN,
                    "resource": "http://localhost",
                    "method": "GET",
                    "value_template": "{{ value_json.dog }}",
                    "name": "foo",
                    "verify_ssl": "true",
                    "timeout": 30,
                }
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    expect(len(hass.states.async_all(BINARY_SENSOR_DOMAIN))).to_equal(1)

    state = hass.states.get("binary_sensor.foo")
    expect(state.state).to_equal(STATE_OFF)


@test
async def setup_get_on(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test setup with valid on configuration."""
    aioclient_mock.get(
        "http://localhost",
        status=HTTPStatus.OK,
        headers={"content-type": "text/json"},
        json={"dog": True},
    )
    expect(
        await async_setup_component(
            hass,
            BINARY_SENSOR_DOMAIN,
            {
                BINARY_SENSOR_DOMAIN: {
                    "platform": DOMAIN,
                    "resource": "http://localhost",
                    "method": "GET",
                    "value_template": "{{ value_json.dog }}",
                    "name": "foo",
                    "verify_ssl": "true",
                    "timeout": 30,
                }
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    expect(len(hass.states.async_all(BINARY_SENSOR_DOMAIN))).to_equal(1)

    state = hass.states.get("binary_sensor.foo")
    expect(state.state).to_equal(STATE_ON)


@test
async def setup_get_xml(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test setup with valid xml configuration."""
    aioclient_mock.get(
        "http://localhost",
        status=HTTPStatus.OK,
        headers={"content-type": "text/xml"},
        text="<dog>1</dog>",
    )
    expect(
        await async_setup_component(
            hass,
            BINARY_SENSOR_DOMAIN,
            {
                BINARY_SENSOR_DOMAIN: {
                    "platform": DOMAIN,
                    "resource": "http://localhost",
                    "method": "GET",
                    "value_template": "{{ value_json.dog }}",
                    "name": "foo",
                    "verify_ssl": "true",
                    "timeout": 30,
                }
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    expect(len(hass.states.async_all(BINARY_SENSOR_DOMAIN))).to_equal(1)

    state = hass.states.get("binary_sensor.foo")
    expect(state.state).to_equal(STATE_ON)


@test.cases(
    test.case("empty", content=""),
    test.case("malformed", content="<open></close>"),
)
async def setup_get_bad_xml(
    content: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test attributes get extracted from a XML result with bad xml."""
    aioclient_mock.get(
        "http://localhost",
        status=HTTPStatus.OK,
        headers={"content-type": "text/xml"},
        text=content,
    )
    expect(
        await async_setup_component(
            hass,
            BINARY_SENSOR_DOMAIN,
            {
                BINARY_SENSOR_DOMAIN: {
                    "platform": DOMAIN,
                    "resource": "http://localhost",
                    "method": "GET",
                    "value_template": "{{ value_json.toplevel.master_value }}",
                    "name": "foo",
                    "verify_ssl": "true",
                    "timeout": 30,
                }
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    expect(len(hass.states.async_all(BINARY_SENSOR_DOMAIN))).to_equal(1)
    state = hass.states.get("binary_sensor.foo")

    expect(state.state).to_equal(STATE_OFF)
    expect("REST xml result could not be parsed" in caplog.text).to_be_truthy()


@test
async def setup_with_exception(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test setup with exception."""
    aioclient_mock.get("http://localhost", status=HTTPStatus.OK, json={})
    expect(
        await async_setup_component(
            hass,
            BINARY_SENSOR_DOMAIN,
            {
                BINARY_SENSOR_DOMAIN: {
                    "platform": DOMAIN,
                    "resource": "http://localhost",
                    "method": "GET",
                    "value_template": "{{ value_json.dog }}",
                    "name": "foo",
                    "verify_ssl": "true",
                    "timeout": 30,
                }
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    expect(len(hass.states.async_all(BINARY_SENSOR_DOMAIN))).to_equal(1)

    state = hass.states.get("binary_sensor.foo")
    expect(state.state).to_equal(STATE_OFF)

    await async_setup_component(hass, "homeassistant", {})
    await hass.async_block_till_done()

    aioclient_mock.clear_requests()
    aioclient_mock.get("http://localhost", exc=aiohttp.ClientError("Request failed"))
    await hass.services.async_call(
        "homeassistant",
        "update_entity",
        {ATTR_ENTITY_ID: ["binary_sensor.foo"]},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.foo")
    expect(state.state).to_equal(STATE_UNAVAILABLE)


@test
async def reload(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Verify we can reload reset sensors."""
    aioclient_mock.get("http://localhost", status=HTTPStatus.OK)

    await async_setup_component(
        hass,
        BINARY_SENSOR_DOMAIN,
        {
            BINARY_SENSOR_DOMAIN: {
                "platform": DOMAIN,
                "method": "GET",
                "name": "mockrest",
                "resource": "http://localhost",
            }
        },
    )
    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    expect(len(hass.states.async_all(BINARY_SENSOR_DOMAIN))).to_equal(1)

    expect(hass.states.get("binary_sensor.mockrest")).not_.to_be_none()

    yaml_path = get_fixture_path("configuration.yaml", DOMAIN)
    with patch.object(hass_config, "YAML_CONFIG_FILE", yaml_path):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await hass.async_block_till_done()

    expect(hass.states.get("binary_sensor.mockreset")).to_be_none()
    expect(hass.states.get("binary_sensor.rollout")).not_.to_be_none()


@test
async def setup_query_params(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test setup with query params."""
    aioclient_mock.get("http://localhost?search=something", status=HTTPStatus.OK)
    expect(
        await async_setup_component(
            hass,
            BINARY_SENSOR_DOMAIN,
            {
                BINARY_SENSOR_DOMAIN: {
                    "platform": DOMAIN,
                    "resource": "http://localhost",
                    "method": "GET",
                    "params": {"search": "something"},
                }
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    expect(len(hass.states.async_all(BINARY_SENSOR_DOMAIN))).to_equal(1)


@test
async def entity_config(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test entity configuration."""
    config = {
        BINARY_SENSOR_DOMAIN: {
            # REST configuration
            "platform": DOMAIN,
            "method": "GET",
            "resource": "http://localhost",
            # Entity configuration
            "icon": "{{'mdi:one_two_three'}}",
            "picture": "{{'blabla.png'}}",
            "name": "{{'REST' + ' ' + 'Binary Sensor'}}",
            "unique_id": "very_unique",
        },
    }

    aioclient_mock.get("http://localhost", status=HTTPStatus.OK)
    expect(
        await async_setup_component(hass, BINARY_SENSOR_DOMAIN, config)
    ).to_be_truthy()
    await hass.async_block_till_done()

    expect(
        entity_registry.async_get("binary_sensor.rest_binary_sensor").unique_id
    ).to_equal("very_unique")

    state = hass.states.get("binary_sensor.rest_binary_sensor")
    expect(state.state).to_equal("off")
    expect(state.attributes).to_equal(
        {
            "entity_picture": "blabla.png",
            "friendly_name": "REST Binary Sensor",
            "icon": "mdi:one_two_three",
        }
    )


@test
async def availability_in_config(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test entity configuration."""
    config = {
        BINARY_SENSOR_DOMAIN: {
            # REST configuration
            "platform": DOMAIN,
            "method": "GET",
            "resource": "http://localhost",
            # Entity configuration
            "availability": "{{value==1}}",
            "name": "{{'REST' + ' ' + 'Binary Sensor'}}",
        },
    }

    aioclient_mock.get("http://localhost", status=HTTPStatus.OK)
    expect(
        await async_setup_component(hass, BINARY_SENSOR_DOMAIN, config)
    ).to_be_truthy()
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.rest_binary_sensor")
    expect(state.state).to_equal(STATE_UNAVAILABLE)


@test
async def availability_blocks_value_template(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test availability blocks value_template from rendering."""
    error = "Error parsing value for binary_sensor.block_template: 'x' is undefined"
    aioclient_mock.get("http://localhost", status=HTTPStatus.OK, text="51")
    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: [
                    {
                        "resource": "http://localhost",
                        "binary_sensor": [
                            {
                                "unique_id": "block_template",
                                "name": "block_template",
                                "value_template": "{{ x - 1 }}",
                                "availability": "{{ value == '50' }}",
                            }
                        ],
                    }
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    await async_setup_component(hass, "homeassistant", {})
    await hass.async_block_till_done()

    expect(error not in caplog.text).to_be_truthy()

    state = hass.states.get("binary_sensor.block_template")
    expect(state).not_.to_be_none()
    expect(state.state).to_equal(STATE_UNAVAILABLE)

    aioclient_mock.clear_requests()
    aioclient_mock.get("http://localhost", status=HTTPStatus.OK, text="50")
    await hass.services.async_call(
        "homeassistant",
        "update_entity",
        {ATTR_ENTITY_ID: ["binary_sensor.block_template"]},
        blocking=True,
    )
    await hass.async_block_till_done()

    expect(error in caplog.text).to_be_truthy()


@test
async def setup_get_basic_auth_utf8(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test setup with basic auth using UTF-8 characters including Unicode char ‘."""
    # Use a password with the Unicode character ‘ (left single quotation mark)
    aioclient_mock.get("http://localhost", status=HTTPStatus.OK, json={"key": "on"})
    expect(
        await async_setup_component(
            hass,
            BINARY_SENSOR_DOMAIN,
            {
                BINARY_SENSOR_DOMAIN: {
                    "platform": DOMAIN,
                    "resource": "http://localhost",
                    "method": "GET",
                    "value_template": "{{ value_json.key }}",
                    "name": "foo",
                    "verify_ssl": "true",
                    "timeout": 30,
                    "authentication": "basic",
                    "username": "test_user",
                    "password": "test‘password",  # Password with Unicode char
                    "headers": {"Accept": CONTENT_TYPE_JSON},
                }
            },
        )
    ).to_be_truthy()

    await hass.async_block_till_done()
    expect(len(hass.states.async_all(BINARY_SENSOR_DOMAIN))).to_equal(1)

    state = hass.states.get("binary_sensor.foo")
    expect(state.state).to_equal(STATE_ON)
