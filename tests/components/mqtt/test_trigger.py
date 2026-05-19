"""The tests for the MQTT automation."""

from typing import Any
from unittest.mock import ANY

from tryke import Depends, expect, fixture, test

from homeassistant.components import automation
from homeassistant.const import ATTR_ENTITY_ID, ENTITY_MATCH_ALL, SERVICE_TURN_OFF
from homeassistant.core import HassJobType, HomeAssistant, ServiceCall
from homeassistant.setup import async_setup_component

from ._fixtures import mqtt_mock as mqtt_mock_fixture, service_calls
from tests.common import async_fire_mqtt_message, mock_component
from tests.hass_fixtures import LogCapture, caplog, hass as hass_fixture, mock_network


@fixture
async def setup_comp(
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> Any:
    """Initialize components."""
    mock_component(hass, "group")
    return mqtt_mock


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: Any = Depends(setup_comp),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def if_fires_on_topic_match(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test if message is fired on topic match."""
    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {"platform": "mqtt", "topic": "test-topic"},
                "action": {
                    "service": "test.automation",
                    "data_template": {
                        "some": "{{ trigger.platform }} - {{ trigger.topic }} - "
                        "{{ trigger.payload }} - {{ trigger.payload_json.hello }} - "
                        "{{ trigger.id }}"
                    },
                },
            }
        },
    )

    async_fire_mqtt_message(hass, "test-topic", '{ "hello": "world" }')
    await hass.async_block_till_done()
    expect(len(calls)).to_be(1)
    expect(calls[0].data["some"]).to_equal(
        'mqtt - test-topic - { "hello": "world" } - world - 0'
    )

    await hass.services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_MATCH_ALL},
        blocking=True,
    )
    expect(len(calls)).to_be(2)

    async_fire_mqtt_message(hass, "test-topic", "test_payload")
    await hass.async_block_till_done()
    expect(len(calls)).to_be(2)


@test
async def if_fires_on_topic_and_payload_match(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test if message is fired on topic and payload match."""
    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "mqtt",
                    "topic": "test-topic",
                    "payload": "hello",
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    async_fire_mqtt_message(hass, "test-topic", "hello")
    await hass.async_block_till_done()
    expect(len(calls)).to_be(1)


@test
async def if_fires_on_topic_and_payload_match2(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test if message is fired on topic and payload match.

    Make sure a payload which would render as a non string can still be matched.
    """
    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "mqtt",
                    "topic": "test-topic",
                    "payload": "0",
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    async_fire_mqtt_message(hass, "test-topic", "0")
    await hass.async_block_till_done()
    expect(len(calls)).to_be(1)


@test
async def if_fires_on_templated_topic_and_payload_match(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test if message is fired on templated topic and payload match."""
    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "mqtt",
                    "topic": "test-topic-{{ sqrt(16)|round }}",
                    "payload": '{{ "foo"|regex_replace("foo", "bar") }}',
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    async_fire_mqtt_message(hass, "test-topic-", "foo")
    await hass.async_block_till_done()
    expect(len(calls)).to_be(0)

    async_fire_mqtt_message(hass, "test-topic-4", "foo")
    await hass.async_block_till_done()
    expect(len(calls)).to_be(0)

    async_fire_mqtt_message(hass, "test-topic-4", "bar")
    await hass.async_block_till_done()
    expect(len(calls)).to_be(1)


@test
async def if_fires_on_payload_template(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test if message is fired on templated topic and payload match."""
    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "mqtt",
                    "topic": "test-topic",
                    "payload": "hello",
                    "value_template": "{{ value_json.wanted_key }}",
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    async_fire_mqtt_message(hass, "test-topic", "hello")
    await hass.async_block_till_done()
    expect(len(calls)).to_be(0)

    async_fire_mqtt_message(hass, "test-topic", '{"unwanted_key":"hello"}')
    await hass.async_block_till_done()
    expect(len(calls)).to_be(0)

    async_fire_mqtt_message(hass, "test-topic", '{"wanted_key":"hello"}')
    await hass.async_block_till_done()
    expect(len(calls)).to_be(1)


@test
async def non_allowed_templates(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog_fixture: LogCapture = Depends(caplog),
) -> None:
    """Test non allowed function in template."""
    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "mqtt",
                    "topic": "test-topic-{{ states() }}",
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    assert (
        "Got error 'TemplateError: Use of 'states' is not supported in limited templates' when setting up triggers"
        in caplog_fixture.text
    )


@test
async def if_not_fires_on_topic_but_no_payload_match(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test if message is not fired on topic but no payload."""
    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "mqtt",
                    "topic": "test-topic",
                    "payload": "hello",
                },
                "action": {"service": "test.automation"},
            }
        },
    )

    async_fire_mqtt_message(hass, "test-topic", "no-hello")
    await hass.async_block_till_done()
    expect(len(calls)).to_be(0)


@test
async def encoding_default(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_comp_value: Any = Depends(setup_comp),
) -> None:
    """Test default encoding."""
    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {"platform": "mqtt", "topic": "test-topic"},
                "action": {"service": "test.automation"},
            }
        },
    )

    setup_comp_value.async_subscribe.assert_called_with(
        "test-topic", ANY, 0, "utf-8", HassJobType.Callback
    )


@test
async def encoding_custom(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_comp_value: Any = Depends(setup_comp),
) -> None:
    """Test default encoding."""
    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {"platform": "mqtt", "topic": "test-topic", "encoding": ""},
                "action": {"service": "test.automation"},
            }
        },
    )

    setup_comp_value.async_subscribe.assert_called_with(
        "test-topic", ANY, 0, None, HassJobType.Callback
    )
