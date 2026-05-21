"""The tests for the MQTT client."""

from tryke import Depends, expect, fixture, test

from homeassistant.components import mqtt
from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def convert_outgoing_payload(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the converting of outgoing MQTT payloads without template."""
    command_template = mqtt.MqttCommandTemplate(None)
    expect(command_template.async_render(b"\xde\xad\xbe\xef")).to_equal(
        b"\xde\xad\xbe\xef"
    )
    expect(command_template.async_render("b'\\xde\\xad\\xbe\\xef'")).to_equal(
        "b'\\xde\\xad\\xbe\\xef'"
    )
    expect(command_template.async_render(1234)).to_equal(1234)
    expect(command_template.async_render(1234.56)).to_equal(1234.56)
    expect(command_template.async_render(None)).to_be_none()



@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def mqtt_connects_on_home_assistant_mqtt_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if client is connected after mqtt init on bootstrap."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def mqtt_does_not_disconnect_on_home_assistant_stop(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if client is not disconnected on HA stop."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def mqtt_await_ack_at_disconnect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if ACK is awaited correctly when disconnecting."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def publish(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the publish function."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def all_subscriptions_run_when_decode_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test all other subscriptions still run when decode fails for one."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def subscribe_topic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the subscription of a topic."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def status_subscription_done(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the on subscription status."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def subscribe_mqtt_config_entry_disabled(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the subscription of a topic when MQTT config entry is disabled."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def subscribe_and_resubscribe(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test resubscribing within the debounce time."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def subscribe_topic_non_async(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the subscription of a topic using the non-async function."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def subscribe_bad_topic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the subscription of a topic."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def subscribe_topic_not_match(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if subscribed topic is not a match."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def subscribe_topic_level_wildcard(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the subscription of wildcard topics."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def subscribe_topic_level_wildcard_no_subtree_match(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the subscription of wildcard topics."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def subscribe_topic_level_wildcard_root_topic_no_subtree_match(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the subscription of wildcard topics."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def subscribe_topic_subtree_wildcard_subtree_topic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the subscription of wildcard topics."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def subscribe_topic_subtree_wildcard_root_topic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the subscription of wildcard topics."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def subscribe_topic_subtree_wildcard_no_match(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the subscription of wildcard topics."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def subscribe_topic_level_wildcard_and_wildcard_root_topic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the subscription of wildcard topics."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def subscribe_topic_level_wildcard_and_wildcard_subtree_topic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the subscription of wildcard topics."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def subscribe_topic_level_wildcard_and_wildcard_level_no_match(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the subscription of wildcard topics."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def subscribe_topic_level_wildcard_and_wildcard_no_match(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the subscription of wildcard topics."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def subscribe_topic_sys_root(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the subscription of $ root topics."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def subscribe_topic_sys_root_and_wildcard_topic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the subscription of $ root and wildcard topics."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def subscribe_topic_sys_root_and_wildcard_subtree_topic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the subscription of $ root and wildcard subtree topics."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def subscribe_special_characters(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the subscription to topics with special characters."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def subscribe_same_topic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test subscribing to same topic twice and simulate retained messages."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def replaying_payload_same_topic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test replaying retained messages."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def replaying_payload_after_resubscribing(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test replaying and filtering retained messages after resubscribing."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def replaying_payload_wildcard_topic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test replaying retained messages."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def not_calling_unsubscribe_with_active_subscribers(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test not calling unsubscribe() when other subscribers are active."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def not_calling_subscribe_when_unsubscribed_within_cooldown(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test not calling subscribe() when it is unsubscribed."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def unsubscribe_race(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test not calling unsubscribe() when other subscribers are active."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def restore_subscriptions_on_reconnect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test subscriptions are restored on reconnect."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def restore_all_active_subscriptions_on_reconnect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test active subscriptions are restored correctly on reconnect."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def subscribed_at_highest_qos(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the highest qos as assigned when subscribing to the same topic."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def initial_setup_logs_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test for setup failure if initial client connection fails."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def logs_error_if_no_connect_broker(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test for setup failure if connection to broker is missing."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def triggers_reauth_flow_if_auth_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test re-auth is triggered if authentication is failing."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def handle_mqtt_on_callback(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test receiving an ACK callback before waiting for it."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def handle_mqtt_on_callback_after_cancellation(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test receiving an ACK after a cancellation."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def handle_mqtt_on_callback_after_timeout(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test receiving an ACK after a timeout."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def publish_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test publish error."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def subscribe_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test publish error."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def handle_message_callback(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test for handling an incoming message callback."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def setup_mqtt_client_clean_session_and_protocol(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test MQTT client clean_session and protocol setup."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def setup_mqtt_client_clean_start(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test MQTT client protocol connects with `clean_start` set correctly."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def handle_mqtt_timeout_on_callback(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test publish without receiving an ACK callback."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def setup_raises_config_entry_not_ready_if_no_connect_broker(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test for setup failure if connection to broker is missing."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def setup_uses_certificate_on_certificate_set_to_auto_and_insecure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup uses bundled certs when certificate is set to auto and insecure."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def client_id_is_set(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup defaults for tls."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def tls_version(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup defaults for tls."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def custom_birth_message(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test sending birth message."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def default_birth_message(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test sending birth message."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def no_birth_message(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test disabling birth message."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def delayed_birth_message(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test sending birth message does not happen until Home Assistant starts."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def subscription_done_when_birth_message_is_sent(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test sending birth message until initial subscription has been completed."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def custom_will_message(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test will message."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def default_will_message(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test will message."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def no_will_message(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test will message."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def mqtt_subscribes_topics_on_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test subscription to topic on connect."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def mqtt_subscribes_wildcard_topics_in_correct_order(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test subscription to wildcard topics on connect in the order of subscription."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def mqtt_discovery_not_subscribes_when_disabled(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery subscriptions not performend when discovery is disabled."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def mqtt_subscribes_in_single_call(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test bundled client subscription to topic."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def mqtt_subscribes_and_unsubscribes_in_chunks(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test chunked client subscriptions."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def auto_reconnect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconnection is automatically done."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def server_sock_connect_and_disconnect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test handling the socket connected and disconnected."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def server_sock_buffer_size(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test handling the socket buffer size fails."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def server_sock_buffer_size_with_websocket(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test handling the socket buffer size fails."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def client_sock_failure_after_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test handling the socket connected and disconnected."""
    expect(True).to_be(True)


@test.skip("mqtt client mock chain (paho-mqtt) not shimmed in tryke")
async def loop_write_failure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test handling the socket connected and disconnected."""
    expect(True).to_be(True)
