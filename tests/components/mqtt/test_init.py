"""The tests for the MQTT component setup and helpers."""

from typing import Any
from unittest.mock import MagicMock, patch

from tryke import Depends, expect, fixture, test
import voluptuous as vol

from homeassistant.components import mqtt
from homeassistant.components.mqtt.models import (
    MqttCommandTemplateException,
    MqttValueTemplateException,
)
from homeassistant.components.mqtt.schemas import (
    MQTT_ENTITY_DEVICE_INFO_SCHEMA,
    MQTT_ORIGIN_INFO_SCHEMA,
)
from homeassistant.components.mqtt.util import (
    valid_birth_will,
    valid_subscribe_topic_template,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import device_registry as dr, template
from homeassistant.helpers.entity import Entity

from ._fixtures import mqtt_mock as mqtt_mock_fixture
from tests.common import MockEntity, MockEntityPlatform, async_fire_mqtt_message
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@fixture
def _mqtt_executor(
    _network: None = Depends(mock_network),
    _mqtt: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Executor that also sets up the MQTT integration with a mocked client."""


@test
async def command_template_value(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the rendering of MQTT command template."""

    variables = {"id": 1234, "some_var": "beer"}

    # test rendering value
    tpl = template.Template("{{ value + 1 }}", hass=hass)
    cmd_tpl = mqtt.MqttCommandTemplate(tpl)
    expect(cmd_tpl.async_render(4321)).to_equal("4322")

    # test variables at rendering
    tpl = template.Template("{{ some_var }}", hass=hass)
    cmd_tpl = mqtt.MqttCommandTemplate(tpl)
    expect(cmd_tpl.async_render(None, variables=variables)).to_equal("beer")


@test
async def command_template_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the exception handling of an MQTT command template."""
    tpl = template.Template("{{ value * 2 }}", hass=hass)
    cmd_tpl = mqtt.MqttCommandTemplate(tpl)
    async with expect_raises_async(
        MqttCommandTemplateException,
        match=r"unsupported operand type\(s\) for \*: 'NoneType' and 'int'",
    ):
        cmd_tpl.async_render(None)


@test
async def value_template_value(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the rendering of MQTT value template."""

    variables = {"id": 1234, "some_var": "beer"}

    # test rendering value
    tpl = template.Template("{{ value_json.id }}", hass=hass)
    val_tpl = mqtt.MqttValueTemplate(tpl)
    expect(val_tpl.async_render_with_possible_json_value('{"id": 4321}')).to_equal(
        "4321"
    )

    # test variables at rendering
    tpl = template.Template("{{ value_json.id }} {{ some_var }} {{ code }}", hass=hass)
    val_tpl = mqtt.MqttValueTemplate(tpl, config_attributes={"code": 1234})
    expect(
        val_tpl.async_render_with_possible_json_value(
            '{"id": 4321}', variables=variables
        )
    ).to_equal("4321 beer 1234")

    # test with default value if an error occurs due to an invalid template
    tpl = template.Template("{{ value_json.id | as_datetime }}", hass=hass)
    val_tpl = mqtt.MqttValueTemplate(tpl)
    expect(
        val_tpl.async_render_with_possible_json_value('{"otherid": 4321}', "my default")
    ).to_equal("my default")

    # test value template with entity
    entity = Entity()
    entity.hass = hass
    entity.platform = MockEntityPlatform(hass)
    entity.entity_id = "select.test"
    tpl = template.Template("{{ value_json.id }}", hass=hass)
    val_tpl = mqtt.MqttValueTemplate(tpl, entity=entity)
    expect(val_tpl.async_render_with_possible_json_value('{"id": 4321}')).to_equal(
        "4321"
    )

    # test this object in a template
    tpl2 = template.Template("{{ this.entity_id }}", hass=hass)
    val_tpl2 = mqtt.MqttValueTemplate(tpl2, entity=entity)
    expect(val_tpl2.async_render_with_possible_json_value("bla")).to_equal(
        "select.test"
    )

    with patch(
        "homeassistant.helpers.template.TemplateStateFromEntityId", MagicMock()
    ) as template_state_calls:
        tpl3 = template.Template("{{ this.entity_id }}", hass=hass)
        val_tpl3 = mqtt.MqttValueTemplate(tpl3, entity=entity)
        val_tpl3.async_render_with_possible_json_value("call1")
        val_tpl3.async_render_with_possible_json_value("call2")
        expect(template_state_calls.call_count).to_equal(1)


@test
async def value_template_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the rendering of MQTT value template fails."""
    entity = MockEntity(entity_id="sensor.test")
    entity.hass = hass
    entity.platform = MockEntityPlatform(hass)
    tpl = template.Template("{{ value_json.some_var * 2 }}", hass=hass)
    val_tpl = mqtt.MqttValueTemplate(tpl, entity=entity)
    raised: MqttValueTemplateException | None = None
    try:
        val_tpl.async_render_with_possible_json_value('{"some_var": null }')
    except MqttValueTemplateException as exc:
        raised = exc
    expect(raised is not None).to_be(True)
    expect(str(raised)).to_equal(
        "TypeError: unsupported operand type(s) for *: 'NoneType' and 'int' "
        "rendering template for entity 'sensor.test', "
        "template: '{{ value_json.some_var * 2 }}' "
        'and payload: {"some_var": null }'
    )

    raised2: MqttValueTemplateException | None = None
    try:
        val_tpl.async_render_with_possible_json_value(
            '{"some_var": null }', default="100"
        )
    except MqttValueTemplateException as exc:
        raised2 = exc
    expect(raised2 is not None).to_be(True)
    expect(str(raised2)).to_equal(
        "TypeError: unsupported operand type(s) for *: 'NoneType' and 'int' "
        "rendering template for entity 'sensor.test', "
        "template: '{{ value_json.some_var * 2 }}', default value: 100 and payload: "
        '{"some_var": null }'
    )


@test
def validate_topic_test() -> None:
    """Test topic name/filter validation."""
    # Invalid UTF-8, must not contain U+D800 to U+DFFF.
    expect(lambda: mqtt.util.valid_topic("\ud800")).to_raise(vol.Invalid)
    expect(lambda: mqtt.util.valid_topic("\udfff")).to_raise(vol.Invalid)
    # Topic MUST NOT be empty
    expect(lambda: mqtt.util.valid_topic("")).to_raise(vol.Invalid)
    # Topic MUST NOT be longer than 65535 encoded bytes.
    expect(lambda: mqtt.util.valid_topic("ü" * 32768)).to_raise(vol.Invalid)
    # UTF-8 MUST NOT include null character
    expect(lambda: mqtt.util.valid_topic("bad\0one")).to_raise(vol.Invalid)

    # Topics "SHOULD NOT" include these special characters
    # (not MUST NOT, RFC2119). The receiver MAY close the connection.
    # We enforce this because mosquitto does.
    expect(lambda: mqtt.util.valid_topic("")).to_raise(vol.Invalid)
    expect(lambda: mqtt.util.valid_topic("")).to_raise(vol.Invalid)
    expect(lambda: mqtt.util.valid_topic("")).to_raise(vol.Invalid)
    expect(lambda: mqtt.util.valid_topic("")).to_raise(vol.Invalid)
    expect(lambda: mqtt.util.valid_topic("﷐")).to_raise(vol.Invalid)
    expect(lambda: mqtt.util.valid_topic("﷯")).to_raise(vol.Invalid)
    expect(lambda: mqtt.util.valid_topic("￾")).to_raise(vol.Invalid)
    expect(lambda: mqtt.util.valid_topic("￿")).to_raise(vol.Invalid)
    expect(lambda: mqtt.util.valid_topic("\U0001fffe")).to_raise(vol.Invalid)
    expect(lambda: mqtt.util.valid_topic("\U0001ffff")).to_raise(vol.Invalid)


@test
def validate_subscribe_topic_test() -> None:
    """Test invalid subscribe topics."""
    mqtt.valid_subscribe_topic("#")
    mqtt.valid_subscribe_topic("sport/#")
    expect(lambda: mqtt.valid_subscribe_topic("sport/#/")).to_raise(vol.Invalid)
    expect(lambda: mqtt.valid_subscribe_topic("foo/bar#")).to_raise(vol.Invalid)
    expect(lambda: mqtt.valid_subscribe_topic("foo/#/bar")).to_raise(vol.Invalid)

    mqtt.valid_subscribe_topic("+")
    mqtt.valid_subscribe_topic("+/tennis/#")
    expect(lambda: mqtt.valid_subscribe_topic("sport+")).to_raise(vol.Invalid)
    expect(lambda: mqtt.valid_subscribe_topic("sport+/")).to_raise(vol.Invalid)
    expect(lambda: mqtt.valid_subscribe_topic("sport/+1")).to_raise(vol.Invalid)
    expect(lambda: mqtt.valid_subscribe_topic("sport/+#")).to_raise(vol.Invalid)
    expect(lambda: mqtt.valid_subscribe_topic("bad+topic")).to_raise(vol.Invalid)
    mqtt.valid_subscribe_topic("sport/+/player1")
    mqtt.valid_subscribe_topic("/finance")
    mqtt.valid_subscribe_topic("+/+")
    mqtt.valid_subscribe_topic("$SYS/#")


@test
def validate_publish_topic_test() -> None:
    """Test invalid publish topics."""
    expect(lambda: mqtt.valid_publish_topic("pub+")).to_raise(vol.Invalid)
    expect(lambda: mqtt.valid_publish_topic("pub/+")).to_raise(vol.Invalid)
    expect(lambda: mqtt.valid_publish_topic("1#")).to_raise(vol.Invalid)
    expect(lambda: mqtt.valid_publish_topic("bad+topic")).to_raise(vol.Invalid)
    mqtt.valid_publish_topic("//")

    # Topic names beginning with $ SHOULD NOT be used, but can
    mqtt.valid_publish_topic("$SYS/")


@test
def entity_device_info_schema_test() -> None:
    """Test MQTT entity device info validation."""
    # just identifier
    MQTT_ENTITY_DEVICE_INFO_SCHEMA({"identifiers": ["abcd"]})
    MQTT_ENTITY_DEVICE_INFO_SCHEMA({"identifiers": "abcd"})
    # just connection
    MQTT_ENTITY_DEVICE_INFO_SCHEMA(
        {"connections": [[dr.CONNECTION_NETWORK_MAC, "02:5b:26:a8:dc:12"]]}
    )
    # full device info
    MQTT_ENTITY_DEVICE_INFO_SCHEMA(
        {
            "identifiers": ["helloworld", "hello"],
            "connections": [
                [dr.CONNECTION_NETWORK_MAC, "02:5b:26:a8:dc:12"],
                [dr.CONNECTION_ZIGBEE, "zigbee_id"],
            ],
            "manufacturer": "Whatever",
            "name": "Beer",
            "model": "Glass",
            "serial_number": "1234deadbeef",
            "sw_version": "0.1-beta",
            "configuration_url": "http://example.com",
        }
    )
    # full device info with via_device
    MQTT_ENTITY_DEVICE_INFO_SCHEMA(
        {
            "identifiers": ["helloworld", "hello"],
            "connections": [
                [dr.CONNECTION_NETWORK_MAC, "02:5b:26:a8:dc:12"],
                [dr.CONNECTION_ZIGBEE, "zigbee_id"],
            ],
            "manufacturer": "Whatever",
            "name": "Beer",
            "model": "Glass",
            "serial_number": "1234deadbeef",
            "sw_version": "0.1-beta",
            "via_device": "test-hub",
            "configuration_url": "http://example.com",
        }
    )
    # no identifiers
    expect(
        lambda: MQTT_ENTITY_DEVICE_INFO_SCHEMA(
            {
                "manufacturer": "Whatever",
                "name": "Beer",
                "model": "Glass",
                "sw_version": "0.1-beta",
            }
        )
    ).to_raise(vol.Invalid)
    # empty identifiers
    expect(
        lambda: MQTT_ENTITY_DEVICE_INFO_SCHEMA(
            {"identifiers": [], "connections": [], "name": "Beer"}
        )
    ).to_raise(vol.Invalid)

    # not a valid URL
    expect(
        lambda: MQTT_ENTITY_DEVICE_INFO_SCHEMA(
            {
                "manufacturer": "Whatever",
                "name": "Beer",
                "model": "Glass",
                "sw_version": "0.1-beta",
                "configuration_url": "fake://link",
            }
        )
    ).to_raise(vol.Invalid)


@test.cases(
    test.case("EntitySubscription", attr="EntitySubscription"),
    test.case("MqttCommandTemplate", attr="MqttCommandTemplate"),
    test.case("MqttValueTemplate", attr="MqttValueTemplate"),
    test.case("PayloadSentinel", attr="PayloadSentinel"),
    test.case("PublishPayloadType", attr="PublishPayloadType"),
    test.case("ReceiveMessage", attr="ReceiveMessage"),
    test.case(
        "async_prepare_subscribe_topics", attr="async_prepare_subscribe_topics"
    ),
    test.case("async_publish", attr="async_publish"),
    test.case("async_subscribe", attr="async_subscribe"),
    test.case("async_subscribe_topics", attr="async_subscribe_topics"),
    test.case("async_unsubscribe_topics", attr="async_unsubscribe_topics"),
    test.case("async_wait_for_mqtt_client", attr="async_wait_for_mqtt_client"),
    test.case("publish", attr="publish"),
    test.case("subscribe", attr="subscribe"),
    test.case("valid_publish_topic", attr="valid_publish_topic"),
    test.case("valid_qos_schema", attr="valid_qos_schema"),
    test.case("valid_subscribe_topic", attr="valid_subscribe_topic"),
)
async def mqtt_integration_level_imports(attr: str) -> None:
    """Test mqtt integration level public published imports are available."""
    expect(hasattr(mqtt, attr)).to_be(True)


@test
def valid_qos_schema_test() -> None:
    """Test the QoS validation schema accepts/rejects values correctly."""
    # Valid QoS values
    expect(mqtt.valid_qos_schema(0)).to_equal(0)
    expect(mqtt.valid_qos_schema(1)).to_equal(1)
    expect(mqtt.valid_qos_schema(2)).to_equal(2)
    # String coerce
    expect(mqtt.valid_qos_schema("0")).to_equal(0)
    expect(mqtt.valid_qos_schema("2")).to_equal(2)
    # Invalid QoS values
    expect(lambda: mqtt.valid_qos_schema(3)).to_raise(vol.Invalid)
    expect(lambda: mqtt.valid_qos_schema(-1)).to_raise(vol.Invalid)
    expect(lambda: mqtt.valid_qos_schema("bad")).to_raise(vol.Invalid)


@test
def valid_birth_will_test() -> None:
    """Test birth/will configuration validation."""
    # Empty config is allowed (returned as-is).
    expect(valid_birth_will({})).to_equal({})

    # Minimal valid config gets QoS/retain defaults filled in.
    validated = valid_birth_will({"topic": "test/topic", "payload": "online"})
    expect(validated["topic"]).to_equal("test/topic")
    expect(validated["payload"]).to_equal("online")
    expect(validated["qos"]).to_equal(0)
    expect(validated["retain"]).to_be(False)

    # Full config with explicit QoS/retain is preserved.
    validated_full = valid_birth_will(
        {"topic": "test/topic", "payload": "bye", "qos": 2, "retain": True}
    )
    expect(validated_full["qos"]).to_equal(2)
    expect(validated_full["retain"]).to_be(True)

    # Invalid topic (wildcard) raises
    expect(
        lambda: valid_birth_will({"topic": "test/+", "payload": "x"})
    ).to_raise(vol.Invalid)
    # Missing required payload raises
    expect(lambda: valid_birth_will({"topic": "test/topic"})).to_raise(vol.Invalid)
    # Invalid QoS raises
    expect(
        lambda: valid_birth_will(
            {"topic": "test/topic", "payload": "x", "qos": 5}
        )
    ).to_raise(vol.Invalid)


@test
def mqtt_origin_info_schema_test() -> None:
    """Test MQTT origin info validation."""
    # Minimal valid (only name required)
    MQTT_ORIGIN_INFO_SCHEMA({"name": "MyApp"})
    # Full valid
    MQTT_ORIGIN_INFO_SCHEMA(
        {
            "name": "MyApp",
            "sw_version": "1.0",
            "support_url": "https://example.com/support",
        }
    )
    # Missing name fails
    expect(lambda: MQTT_ORIGIN_INFO_SCHEMA({"sw_version": "1.0"})).to_raise(vol.Invalid)
    # Invalid support_url fails
    expect(
        lambda: MQTT_ORIGIN_INFO_SCHEMA(
            {"name": "MyApp", "support_url": "fake://broken"}
        )
    ).to_raise(vol.Invalid)


@test
def valid_subscribe_topic_template_test(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that valid_subscribe_topic_template accepts templates and static topics."""
    _ = hass  # Template parsing does not require the hass instance.
    # A non-template static string must still be a valid subscribe topic.
    tpl = valid_subscribe_topic_template("sport/+/player1")
    expect(tpl.is_static).to_be(True)
    # A template returns a template that is not static.
    tpl2 = valid_subscribe_topic_template("{{ 'sport/+/player1' }}")
    expect(tpl2.is_static).to_be(False)
    # An invalid static topic still raises.
    expect(lambda: valid_subscribe_topic_template("sport/#/")).to_raise(vol.Invalid)


@test
def mqtt_module_public_constants_test() -> None:
    """Test that key MQTT constants are exposed at the integration level."""
    expect(mqtt.DOMAIN).to_equal("mqtt")
    expect(hasattr(mqtt, "ATTR_TOPIC")).to_be(True)
    expect(hasattr(mqtt, "ATTR_PAYLOAD")).to_be(True)
    expect(hasattr(mqtt, "ATTR_QOS")).to_be(True)
    expect(hasattr(mqtt, "ATTR_RETAIN")).to_be(True)
    expect(hasattr(mqtt, "CONF_BROKER")).to_be(True)
    expect(hasattr(mqtt, "SERVICE_PUBLISH")).to_be(True)


@test
async def command_template_with_default_value(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test command template renders integers and dict values."""
    tpl = template.Template("{{ value | int + 1 }}", hass=hass)
    cmd_tpl = mqtt.MqttCommandTemplate(tpl)
    expect(cmd_tpl.async_render("41")).to_equal("42")

    # Variables-only template (no value passed)
    tpl2 = template.Template(
        "{{ var1 }}-{{ var2 }}",
        hass=hass,
    )
    cmd_tpl2 = mqtt.MqttCommandTemplate(tpl2)
    expect(
        cmd_tpl2.async_render(None, variables={"var1": "a", "var2": "b"})
    ).to_equal("a-b")


@test
async def value_template_default_when_no_template(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test MqttValueTemplate without a template returns the raw payload."""
    _ = hass
    val_tpl = mqtt.MqttValueTemplate(None)
    expect(val_tpl.async_render_with_possible_json_value("raw-value")).to_equal(
        "raw-value"
    )
    # JSON payload also passes through unchanged when no template is supplied.
    expect(
        val_tpl.async_render_with_possible_json_value('{"id": 1}')
    ).to_equal('{"id": 1}')


@test
async def value_template_with_config_attributes(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config_attributes are exposed to the value template."""
    tpl = template.Template(
        "{{ value }}-{{ extra }}",
        hass=hass,
    )
    val_tpl = mqtt.MqttValueTemplate(tpl, config_attributes={"extra": "hello"})
    expect(val_tpl.async_render_with_possible_json_value("ok")).to_equal("ok-hello")


@test
async def value_template_caches_entity_template_state(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test repeated value template renders only construct TemplateStateFromEntityId once."""
    entity = Entity()
    entity.hass = hass
    entity.platform = MockEntityPlatform(hass)
    entity.entity_id = "sensor.cached"
    tpl = template.Template("{{ this.entity_id }}", hass=hass)
    val_tpl = mqtt.MqttValueTemplate(tpl, entity=entity)
    with patch(
        "homeassistant.helpers.template.TemplateStateFromEntityId", MagicMock()
    ) as state_calls:
        val_tpl.async_render_with_possible_json_value("first")
        val_tpl.async_render_with_possible_json_value("second")
        val_tpl.async_render_with_possible_json_value("third")
        expect(state_calls.call_count).to_equal(1)


@test
def device_info_schema_via_device_test() -> None:
    """Test device info schema accepts via_device alone with identifiers."""
    MQTT_ENTITY_DEVICE_INFO_SCHEMA(
        {"identifiers": ["abc"], "via_device": "parent_hub"}
    )
    # Connection list with invalid value fails
    expect(
        lambda: MQTT_ENTITY_DEVICE_INFO_SCHEMA(
            {"connections": [["not-a-real-type"]]}
        )
    ).to_raise(vol.Invalid)


@test
def device_info_schema_serial_number_only_test() -> None:
    """Test device info requires at least one identifier."""
    # serial_number alone is not sufficient
    expect(
        lambda: MQTT_ENTITY_DEVICE_INFO_SCHEMA(
            {"serial_number": "deadbeef", "name": "Sensor"}
        )
    ).to_raise(vol.Invalid)
    # serial_number + identifier is OK
    MQTT_ENTITY_DEVICE_INFO_SCHEMA(
        {"identifiers": ["abcd"], "serial_number": "deadbeef"}
    )


@test
def validate_topic_max_length_boundary_test() -> None:
    """Test that the largest valid topic is accepted, and one byte more is rejected."""
    # 65535 ASCII bytes is the upper bound and must be allowed.
    mqtt.util.valid_topic("a" * 65535)
    # One byte over the limit must raise.
    expect(lambda: mqtt.util.valid_topic("a" * 65536)).to_raise(vol.Invalid)


@test
def validate_subscribe_topic_accepts_root_test() -> None:
    """Test some additional subscribe-topic edge cases."""
    mqtt.valid_subscribe_topic("a")
    mqtt.valid_subscribe_topic("a/b/c")
    mqtt.valid_subscribe_topic("a/+/b/+/c")
    # Multi-level wildcard not at end is rejected.
    expect(lambda: mqtt.valid_subscribe_topic("a/#/b")).to_raise(vol.Invalid)


@test.cases(
    test.case("ATTR_TOPIC", name="ATTR_TOPIC"),
    test.case("ATTR_PAYLOAD", name="ATTR_PAYLOAD"),
    test.case("ATTR_QOS", name="ATTR_QOS"),
    test.case("ATTR_RETAIN", name="ATTR_RETAIN"),
    test.case("CONF_BROKER", name="CONF_BROKER"),
    test.case("DOMAIN", name="DOMAIN"),
    test.case("SERVICE_PUBLISH", name="SERVICE_PUBLISH"),
    test.case("CONFIG_ENTRY_VERSION", name="CONFIG_ENTRY_VERSION"),
)
def mqtt_module_constant_exports(name: str) -> None:
    """Test the public constants exported by the mqtt module."""
    expect(hasattr(mqtt, name)).to_be(True)


@test
async def service_call_without_topic_does_not_publish(
    _mqtt: None = Depends(_mqtt_executor),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the publish service call if topic is missing."""
    mqtt_mock.async_publish.reset_mock()
    async with expect_raises_async(vol.Invalid):
        await hass.services.async_call(
            mqtt.DOMAIN,
            mqtt.SERVICE_PUBLISH,
            {},
            blocking=True,
        )
    expect(mqtt_mock.async_publish.called).to_be(False)


@test
async def service_call_with_template_topic_renders_invalid_topic(
    _mqtt: None = Depends(_mqtt_executor),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the publish action call with a rendered, invalid topic template."""
    mqtt_mock.async_publish.reset_mock()
    async with expect_raises_async(vol.Invalid):
        await hass.services.async_call(
            mqtt.DOMAIN,
            mqtt.SERVICE_PUBLISH,
            {
                mqtt.ATTR_TOPIC: "test/{{ '+' if True else 'topic' }}/topic",
                mqtt.ATTR_PAYLOAD: "payload",
            },
            blocking=True,
        )
    expect(mqtt_mock.async_publish.called).to_be(False)


@test.cases(
    test.case(
        "raw-bytes",
        attr_payload="b'\\xde\\xad\\xbe\\xef'",
        payload=b"\xde\xad\xbe\xef",
        evaluate_payload=True,
        literal_eval_calls=1,
    ),
    test.case(
        "string-bytes-literal",
        attr_payload="b'\\xde\\xad\\xbe\\xef'",
        payload="b'\\xde\\xad\\xbe\\xef'",
        evaluate_payload=False,
        literal_eval_calls=0,
    ),
    test.case(
        "plain-string",
        attr_payload="DEADBEEF",
        payload="DEADBEEF",
        evaluate_payload=False,
        literal_eval_calls=0,
    ),
    test.case(
        "invalid-bytes-literal",
        attr_payload="b'\\xde",
        payload="b'\\xde",
        evaluate_payload=True,
        literal_eval_calls=1,
    ),
)
async def mqtt_publish_action_call_with_raw_data(
    attr_payload: str,
    payload: str | bytes,
    evaluate_payload: bool,
    literal_eval_calls: int,
    _mqtt: None = Depends(_mqtt_executor),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the mqtt publish action call with raw data.

    When ``payload`` represents a ``bytes`` object, it should be published
    as raw data if ``evaluate_payload`` is set.
    """
    mqtt_mock.async_publish.reset_mock()
    await hass.services.async_call(
        mqtt.DOMAIN,
        mqtt.SERVICE_PUBLISH,
        {
            mqtt.ATTR_TOPIC: "test/topic",
            mqtt.ATTR_PAYLOAD: attr_payload,
            "evaluate_payload": evaluate_payload,
        },
        blocking=True,
    )
    expect(mqtt_mock.async_publish.called).to_be(True)
    expect(mqtt_mock.async_publish.call_args[0][1]).to_equal(payload)

    with patch(
        "homeassistant.components.mqtt.models.literal_eval"
    ) as literal_eval_mock:
        await hass.services.async_call(
            mqtt.DOMAIN,
            mqtt.SERVICE_PUBLISH,
            {
                mqtt.ATTR_TOPIC: "test/topic",
                mqtt.ATTR_PAYLOAD: attr_payload,
            },
            blocking=True,
        )
        literal_eval_mock.assert_not_called()

        await hass.services.async_call(
            mqtt.DOMAIN,
            mqtt.SERVICE_PUBLISH,
            {
                mqtt.ATTR_TOPIC: "test/topic",
                mqtt.ATTR_PAYLOAD: attr_payload,
                "evaluate_payload": evaluate_payload,
            },
            blocking=True,
        )
        expect(len(literal_eval_mock.mock_calls)).to_equal(literal_eval_calls)


@test
async def service_call_with_ascii_qos_retain_flags(
    _mqtt: None = Depends(_mqtt_executor),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the publish service call with ascii formatted qos and retain flags."""
    mqtt_mock.async_publish.reset_mock()
    await hass.services.async_call(
        mqtt.DOMAIN,
        mqtt.SERVICE_PUBLISH,
        {
            mqtt.ATTR_TOPIC: "test/topic",
            mqtt.ATTR_PAYLOAD: "",
            mqtt.ATTR_QOS: "2",
            mqtt.ATTR_RETAIN: "no",
        },
        blocking=True,
    )
    expect(mqtt_mock.async_publish.called).to_be(True)
    expect(mqtt_mock.async_publish.call_args[0][1]).to_equal("")
    expect(mqtt_mock.async_publish.call_args[0][2]).to_equal(2)
    expect(bool(mqtt_mock.async_publish.call_args[0][3])).to_be(False)

    mqtt_mock.async_publish.reset_mock()

    # Test service call without payload
    await hass.services.async_call(
        mqtt.DOMAIN,
        mqtt.SERVICE_PUBLISH,
        {
            mqtt.ATTR_TOPIC: "test/topic",
            mqtt.ATTR_QOS: "2",
            mqtt.ATTR_RETAIN: "no",
        },
        blocking=True,
    )
    expect(mqtt_mock.async_publish.called).to_be(True)
    expect(mqtt_mock.async_publish.call_args[0][1]).to_be_none()
    expect(mqtt_mock.async_publish.call_args[0][2]).to_equal(2)
    expect(bool(mqtt_mock.async_publish.call_args[0][3])).to_be(False)


@test
async def publish_function_with_bad_encoding_conditions(
    _mqtt: None = Depends(_mqtt_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test the internal publish function with bad encoding conditions."""
    await mqtt.async_publish(
        hass, "some-topic", "test-payload", qos=0, retain=False, encoding=None
    )
    expect(
        "Can't pass-through payload for publishing test-payload"
        " on some-topic with no encoding set, need 'bytes'"
        " got <class 'str'>" in caplog.text
    ).to_be(True)
    caplog.clear()
    await mqtt.async_publish(
        hass,
        "some-topic",
        "test-payload",
        qos=0,
        retain=False,
        encoding="invalid_encoding",
    )
    expect(
        "Can't encode payload for publishing test-payload on"
        " some-topic with encoding invalid_encoding" in caplog.text
    ).to_be(True)


@test.cases(
    test.case("both-none", qos=None, retain=None),
    test.case("qos-zero", qos=0, retain=None),
    test.case("retain-false", qos=None, retain=False),
)
async def publish_api_with_fallback_to_none(
    qos: int | None,
    retain: bool | None,
    _mqtt: None = Depends(_mqtt_executor),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test the MQTT publish API with None as fallback for QoS or Retain."""
    mqtt_mock.async_publish.reset_mock()
    await mqtt.async_publish(
        hass, "some-topic", "test-payload", qos=qos, retain=retain
    )
    expect(
        "Detected code that that calls the MQTT publish API with `None` for "
        "qos or retain. The `qos` argument must be an `int`, and the `retain` "
        "argument must be a `bool`." in caplog.text
    ).to_be(True)
    async_publish_mock: MagicMock = mqtt_mock.async_publish
    expect(len(async_publish_mock.mock_calls)).to_equal(1)
    expect(async_publish_mock.mock_calls[0][1][0]).to_equal("some-topic")
    expect(async_publish_mock.mock_calls[0][1][1]).to_equal("test-payload")
    expect(async_publish_mock.mock_calls[0][1][2]).to_equal(0)
    expect(async_publish_mock.mock_calls[0][1][3]).to_be(False)


@test
async def receiving_non_utf8_message_gets_logged(
    _mqtt: None = Depends(_mqtt_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test receiving a non utf8 encoded message gets logged."""
    recorded_calls: list[Any] = []

    @callback
    def record_calls(msg: Any) -> None:
        recorded_calls.append(msg)

    await mqtt.async_subscribe(hass, "test-topic", record_calls)

    async_fire_mqtt_message(hass, "test-topic", b"\x9a")

    await hass.async_block_till_done()
    expect(
        "Can't decode payload b'\\x9a' on test-topic with encoding utf-8"
        in caplog.text
    ).to_be(True)


@test
async def message_callback_exception_gets_logged(
    _mqtt: None = Depends(_mqtt_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test an exception raised by a message handler gets logged."""

    @callback
    def bad_handler(msg: Any) -> None:
        """Handle callback."""
        raise ValueError("This is a bad message callback")

    await mqtt.async_subscribe(hass, "test-topic", bad_handler)
    async_fire_mqtt_message(hass, "test-topic", "test")
    await hass.async_block_till_done()

    expect(
        "Exception in bad_handler when handling msg on 'test-topic':"
        " 'test'" in caplog.text
    ).to_be(True)
