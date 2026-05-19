"""The tests for the MQTT subscription component."""

from typing import Any
from unittest.mock import ANY

from tryke import Depends, expect, fixture, test

from homeassistant.components.mqtt.subscription import (
    async_prepare_subscribe_topics,
    async_subscribe_topics,
    async_unsubscribe_topics,
)
from homeassistant.core import HomeAssistant, callback

from ._fixtures import mqtt_mock as mqtt_mock_fixture
from tests.common import async_fire_mqtt_message
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _mqtt: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def subscribe_topics(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test subscription to topics."""
    calls1: list[Any] = []

    @callback
    def record_calls1(*args: Any) -> None:
        """Record calls."""
        calls1.append(args)

    calls2: list[Any] = []

    @callback
    def record_calls2(*args: Any) -> None:
        """Record calls."""
        calls2.append(args)

    sub_state = None
    sub_state = async_prepare_subscribe_topics(
        hass,
        sub_state,
        {
            "test_topic1": {"topic": "test-topic1", "msg_callback": record_calls1},
            "test_topic2": {"topic": "test-topic2", "msg_callback": record_calls2},
        },
    )
    await async_subscribe_topics(hass, sub_state)

    async_fire_mqtt_message(hass, "test-topic1", "test-payload1")
    expect(len(calls1)).to_be(1)
    expect(calls1[0][0].topic).to_equal("test-topic1")
    expect(calls1[0][0].payload).to_equal("test-payload1")
    expect(len(calls2)).to_be(0)

    async_fire_mqtt_message(hass, "test-topic2", "test-payload2")
    expect(len(calls1)).to_be(1)
    expect(len(calls2)).to_be(1)
    expect(calls2[0][0].topic).to_equal("test-topic2")
    expect(calls2[0][0].payload).to_equal("test-payload2")

    async_unsubscribe_topics(hass, sub_state)

    async_fire_mqtt_message(hass, "test-topic1", "test-payload")
    async_fire_mqtt_message(hass, "test-topic2", "test-payload")

    expect(len(calls1)).to_be(1)
    expect(len(calls2)).to_be(1)


@test
async def modify_topics(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test modification of topics."""
    calls1: list[Any] = []

    @callback
    def record_calls1(*args: Any) -> None:
        """Record calls."""
        calls1.append(args)

    calls2: list[Any] = []

    @callback
    def record_calls2(*args: Any) -> None:
        """Record calls."""
        calls2.append(args)

    sub_state = None
    sub_state = async_prepare_subscribe_topics(
        hass,
        sub_state,
        {
            "test_topic1": {"topic": "test-topic1", "msg_callback": record_calls1},
            "test_topic2": {"topic": "test-topic2", "msg_callback": record_calls2},
        },
    )
    await async_subscribe_topics(hass, sub_state)

    async_fire_mqtt_message(hass, "test-topic1", "test-payload")
    expect(len(calls1)).to_be(1)
    expect(len(calls2)).to_be(0)

    async_fire_mqtt_message(hass, "test-topic2", "test-payload")
    expect(len(calls1)).to_be(1)
    expect(len(calls2)).to_be(1)

    sub_state = async_prepare_subscribe_topics(
        hass,
        sub_state,
        {"test_topic1": {"topic": "test-topic1_1", "msg_callback": record_calls1}},
    )
    await async_subscribe_topics(hass, sub_state)

    async_fire_mqtt_message(hass, "test-topic1", "test-payload")
    async_fire_mqtt_message(hass, "test-topic2", "test-payload")
    expect(len(calls1)).to_be(1)
    expect(len(calls2)).to_be(1)

    async_fire_mqtt_message(hass, "test-topic1_1", "test-payload")
    expect(len(calls1)).to_be(2)
    expect(calls1[1][0].topic).to_equal("test-topic1_1")
    expect(calls1[1][0].payload).to_equal("test-payload")
    expect(len(calls2)).to_be(1)

    async_unsubscribe_topics(hass, sub_state)

    async_fire_mqtt_message(hass, "test-topic1_1", "test-payload")
    async_fire_mqtt_message(hass, "test-topic2", "test-payload")

    expect(len(calls1)).to_be(2)
    expect(len(calls2)).to_be(1)


@test
async def qos_encoding_default(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test default qos and encoding."""

    @callback
    def msg_callback(*args: Any) -> None:
        """Do nothing."""

    sub_state = None
    sub_state = async_prepare_subscribe_topics(
        hass,
        sub_state,
        {"test_topic1": {"topic": "test-topic1", "msg_callback": msg_callback}},
    )
    await async_subscribe_topics(hass, sub_state)
    mqtt_mock.async_subscribe.assert_called_with("test-topic1", ANY, 0, "utf-8", None)


@test
async def qos_encoding_custom(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test custom qos and encoding."""

    @callback
    def msg_callback(*args: Any) -> None:
        """Do nothing."""

    sub_state = None
    sub_state = async_prepare_subscribe_topics(
        hass,
        sub_state,
        {
            "test_topic1": {
                "topic": "test-topic1",
                "msg_callback": msg_callback,
                "qos": 1,
                "encoding": "utf-16",
            }
        },
    )
    await async_subscribe_topics(hass, sub_state)
    mqtt_mock.async_subscribe.assert_called_with("test-topic1", ANY, 1, "utf-16", None)


@test
async def no_change(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test subscription to topics without change."""
    calls: list[Any] = []

    @callback
    def record_calls(*args: Any) -> None:
        """Record calls."""
        calls.append(args)

    sub_state = None
    sub_state = async_prepare_subscribe_topics(
        hass,
        sub_state,
        {"test_topic1": {"topic": "test-topic1", "msg_callback": record_calls}},
    )
    await async_subscribe_topics(hass, sub_state)
    subscribe_call_count = mqtt_mock.async_subscribe.call_count

    async_fire_mqtt_message(hass, "test-topic1", "test-payload")
    expect(len(calls)).to_be(1)

    sub_state = async_prepare_subscribe_topics(
        hass,
        sub_state,
        {"test_topic1": {"topic": "test-topic1", "msg_callback": record_calls}},
    )
    await async_subscribe_topics(hass, sub_state)
    expect(subscribe_call_count).to_equal(mqtt_mock.async_subscribe.call_count)

    async_fire_mqtt_message(hass, "test-topic1", "test-payload")
    expect(len(calls)).to_be(2)

    async_unsubscribe_topics(hass, sub_state)

    async_fire_mqtt_message(hass, "test-topic1", "test-payload")
    expect(len(calls)).to_be(2)
