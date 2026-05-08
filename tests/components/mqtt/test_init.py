"""The tests for the MQTT component setup and helpers."""

from unittest.mock import MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import mqtt
from homeassistant.components.mqtt.models import (
    MqttCommandTemplateException,
    MqttValueTemplateException,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import template
from homeassistant.helpers.entity import Entity

from tests.common import MockEntity, MockEntityPlatform
from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


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


@test.skip("requires mqtt_mock_entry fixture (full mqtt setup)")
async def init_placeholder() -> None:
    """Placeholder skipped sibling tests for test_init.py."""
