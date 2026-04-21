"""Test template trigger entity."""

from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.sensor.helpers import (  # pylint: disable=hass-component-root-import
    async_parse_date_datetime,
)
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_ICON,
    CONF_NAME,
    CONF_STATE,
    CONF_UNIQUE_ID,
    STATE_OFF,
    STATE_ON,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import template
from homeassistant.helpers.trigger_template_entity import (
    CONF_ATTRIBUTES,
    CONF_AVAILABILITY,
    CONF_PICTURE,
    ManualTriggerEntity,
    ManualTriggerSensorEntity,
    ValueTemplate,
)

from tests.hass_fixtures import LogCapture, caplog, hass

_ICON_TEMPLATE = 'mdi:o{{ "n" if value=="on" else "ff" }}'
_PICTURE_TEMPLATE = '/local/picture_o{{ "n" if value=="on" else "ff" }}'


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test.cases(
    test.case(
        "1-{{ value == 1 }}-None-True-None",
        value=1,
        test_template="{{ value == 1 }}",
        error_value=None,
        expected="True",
        error=None,
    ),
    test.case(
        "1-1-None-1-None",
        value=1,
        test_template="1",
        error_value=None,
        expected="1",
        error=None,
    ),
    test.case(
        "1-{{ x - 4 }}-None-None-",
        value=1,
        test_template="{{ x - 4 }}",
        error_value=None,
        expected=None,
        error="",
    ),
    test.case(
        "1-{{ x - 4 }}-error_value3-expected3-Error parsing value for test.entity: 'x' is undefined (value: 1, template: {{ x - 4 }})",
        value=1,
        test_template="{{ x - 4 }}",
        error_value=template._SENTINEL,
        expected=template._SENTINEL,
        error="Error parsing value for test.entity: 'x' is undefined (value: 1, template: {{ x - 4 }})",
    ),
)
async def value_template_object(
    value: Any,
    test_template: str,
    error_value: Any,
    expected: Any,
    error: str | None,
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test ValueTemplate object."""
    entity = ManualTriggerEntity(
        hass,
        {
            CONF_NAME: template.Template("test_entity", hass),
        },
    )
    entity.entity_id = "test.entity"

    value_template = ValueTemplate.from_template(template.Template(test_template, hass))

    variables = entity._template_variables_with_value(value)
    result = value_template.async_render_as_value_template(
        entity.entity_id, variables, error_value
    )

    expect(result).to_equal(expected)

    if error is not None:
        expect(error in caplog.text).to_be(True)


@test
async def template_entity_requires_hass_set(hass: HomeAssistant = Depends(hass)) -> None:
    """Test manual trigger template entity."""
    config = {
        "name": template.Template("test_entity", hass),
        "icon": template.Template(
            '{% if value=="on" %} mdi:on {% else %} mdi:off {% endif %}', hass
        ),
        "picture": template.Template(
            '{% if value=="on" %} /local/picture_on {% else %} /local/picture_off {% endif %}',
            hass,
        ),
    }

    entity = ManualTriggerEntity(hass, config)
    entity.entity_id = "test.entity"
    hass.states.async_set("test.entity", STATE_ON)
    await entity.async_added_to_hass()

    variables = entity._template_variables_with_value(STATE_ON)
    entity._process_manual_data(variables)
    await hass.async_block_till_done()

    expect(entity.name).to_equal("test_entity")
    expect(entity.icon).to_equal("mdi:on")
    expect(entity.entity_picture).to_equal("/local/picture_on")

    hass.states.async_set("test.entity", STATE_OFF)
    await entity.async_added_to_hass()

    variables = entity._template_variables_with_value(STATE_OFF)
    entity._process_manual_data(variables)
    await hass.async_block_till_done()

    expect(entity.name).to_equal("test_entity")
    expect(entity.icon).to_equal("mdi:off")
    expect(entity.entity_picture).to_equal("/local/picture_off")


@test.cases(
    test.case(
        '{{ has_value("test.entity") }}-on-True',
        test_template='{{ has_value("test.entity") }}',
        test_entity_state=STATE_ON,
        expected=True,
    ),
    test.case(
        '{{ has_value("test.entity") }}-off-True',
        test_template='{{ has_value("test.entity") }}',
        test_entity_state=STATE_OFF,
        expected=True,
    ),
    test.case(
        '{{ has_value("test.entity") }}-unknown-False',
        test_template='{{ has_value("test.entity") }}',
        test_entity_state=STATE_UNKNOWN,
        expected=False,
    ),
    test.case(
        '{{ "a" if has_value("test.entity") else "b" }}-on-False',
        test_template='{{ "a" if has_value("test.entity") else "b" }}',
        test_entity_state=STATE_ON,
        expected=False,
    ),
    test.case(
        '{{ "something_not_boolean" }}-off-False',
        test_template='{{ "something_not_boolean" }}',
        test_entity_state=STATE_OFF,
        expected=False,
    ),
    test.case(
        "{{ 1 }}-off-True",
        test_template="{{ 1 }}",
        test_entity_state=STATE_OFF,
        expected=True,
    ),
    test.case(
        "{{ 0 }}-off-False",
        test_template="{{ 0 }}",
        test_entity_state=STATE_OFF,
        expected=False,
    ),
)
async def trigger_template_availability(
    test_template: str,
    test_entity_state: str,
    expected: bool,
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test manual trigger template entity availability template."""
    config = {
        CONF_NAME: template.Template("test_entity", hass),
        CONF_AVAILABILITY: template.Template(test_template, hass),
        CONF_UNIQUE_ID: "9961786c-f8c8-4ea0-ab1d-b9e922c39088",
    }

    entity = ManualTriggerEntity(hass, config)
    entity.entity_id = "test.entity"
    hass.states.async_set("test.entity", test_entity_state)
    await entity.async_added_to_hass()

    variables = entity._template_variables()
    expect(entity._render_availability_template(variables) is expected).to_be(True)
    await hass.async_block_till_done()

    expect(entity.unique_id).to_equal("9961786c-f8c8-4ea0-ab1d-b9e922c39088")
    expect(entity.available is expected).to_be(True)


@test
async def trigger_no_availability_template(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test manual trigger template entity when availability template isn't used."""
    config = {
        CONF_NAME: template.Template("test_entity", hass),
        CONF_ICON: template.Template(_ICON_TEMPLATE, hass),
        CONF_PICTURE: template.Template(_PICTURE_TEMPLATE, hass),
        CONF_STATE: template.Template("{{ value == 'on' }}", hass),
    }

    class TestEntity(ManualTriggerEntity):
        """Test entity class."""

        extra_template_keys = (CONF_STATE,)

        @property
        def state(self) -> bool | None:
            """Return extra attributes."""
            return self._rendered.get(CONF_STATE)

    entity = TestEntity(hass, config)
    entity.entity_id = "test.entity"
    variables = entity._template_variables_with_value(STATE_ON)
    expect(entity._render_availability_template(variables)).to_be(True)
    expect(entity.available).to_be(True)
    entity._process_manual_data(variables)
    await hass.async_block_till_done()

    expect(entity.state).to_equal("True")
    expect(entity.icon).to_equal("mdi:on")
    expect(entity.entity_picture).to_equal("/local/picture_on")

    variables = entity._template_variables_with_value(STATE_OFF)
    expect(entity._render_availability_template(variables)).to_be(True)
    expect(entity.available).to_be(True)
    entity._process_manual_data(variables)
    await hass.async_block_till_done()

    expect(entity.state).to_equal("False")
    expect(entity.icon).to_equal("mdi:off")
    expect(entity.entity_picture).to_equal("/local/picture_off")


@test
async def trigger_template_availability_with_syntax_error(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test manual trigger template entity when availability render fails."""
    config = {
        CONF_NAME: template.Template("test_entity", hass),
        CONF_AVAILABILITY: template.Template("{{ incorrect ", hass),
    }

    entity = ManualTriggerEntity(hass, config)
    entity.entity_id = "test.entity"

    variables = entity._template_variables()
    entity._render_availability_template(variables)
    expect(entity.available).to_be(True)

    expect(
        "Error rendering availability template for test.entity" in caplog.text
    ).to_be(True)


@test
async def attribute_order(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test manual trigger template entity when availability render fails."""
    config = {
        CONF_NAME: template.Template("test_entity", hass),
        CONF_ATTRIBUTES: {
            "beer": template.Template("{{ value }}", hass),
            "no_beer": template.Template("{{ sad - 1 }}", hass),
            "more_beer": template.Template("{{ beer + 1 }}", hass),
        },
    }

    entity = ManualTriggerEntity(hass, config)
    entity.entity_id = "test.entity"
    hass.states.async_set("test.entity", STATE_ON)
    await entity.async_added_to_hass()

    variables = entity._template_variables_with_value(1)
    entity._process_manual_data(variables)
    await hass.async_block_till_done()

    expect(entity.extra_state_attributes).to_equal({"beer": 1, "more_beer": 2})

    expect(
        "Error rendering attributes.no_beer template for test.entity: UndefinedError: 'sad' is undefined"
        in caplog.text
    ).to_be(True)


@test
async def trigger_template_complex(hass: HomeAssistant = Depends(hass)) -> None:
    """Test manual trigger template entity complex template."""
    complex_template = """
    {% set d = {'test_key':'test_data'} %}
    {{ dict(d) }}

"""
    config = {
        CONF_NAME: template.Template("test_entity", hass),
        CONF_ICON: template.Template(
            '{% if value=="on" %} mdi:on {% else %} mdi:off {% endif %}', hass
        ),
        CONF_PICTURE: template.Template(
            '{% if value=="on" %} /local/picture_on {% else %} /local/picture_off {% endif %}',
            hass,
        ),
        CONF_AVAILABILITY: template.Template('{{ has_value("test.entity") }}', hass),
        "other_key": template.Template(complex_template, hass),
    }

    class TestEntity(ManualTriggerEntity):
        """Test entity class."""

        extra_template_keys_complex = ("other_key",)

        @property
        def some_other_key(self) -> dict[str, Any] | None:
            """Return extra attributes."""
            return self._rendered.get("other_key")

    entity = TestEntity(hass, config)
    entity.entity_id = "test.entity"
    hass.states.async_set("test.entity", STATE_ON)
    await entity.async_added_to_hass()

    variables = entity._template_variables_with_value(STATE_ON)
    entity._process_manual_data(variables)
    await hass.async_block_till_done()

    expect(entity.some_other_key).to_equal({"test_key": "test_data"})


@test
async def manual_trigger_sensor_entity_with_date(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test manual trigger template entity when availability template isn't used."""
    config = {
        CONF_NAME: template.Template("test_entity", hass),
        CONF_STATE: template.Template("{{ as_datetime(value) }}", hass),
        CONF_DEVICE_CLASS: SensorDeviceClass.TIMESTAMP,
    }

    class TestEntity(ManualTriggerSensorEntity):
        """Test entity class."""

        extra_template_keys = (CONF_STATE,)

        @property
        def state(self) -> bool | None:
            """Return extra attributes."""
            return "2025-01-01T00:00:00+00:00"

    entity = TestEntity(hass, config)
    entity.entity_id = "test.entity"
    variables = entity._template_variables_with_value("2025-01-01T00:00:00+00:00")
    expect(entity._render_availability_template(variables)).to_be(True)
    expect(entity.available).to_be(True)
    entity._set_native_value_with_possible_timestamp(entity.state)
    await hass.async_block_till_done()

    expect(entity.native_value).to_equal(
        async_parse_date_datetime(
            "2025-01-01T00:00:00+00:00", entity.entity_id, entity.device_class
        )
    )
    expect(entity.state).to_equal("2025-01-01T00:00:00+00:00")
    expect(entity.device_class).to_equal(SensorDeviceClass.TIMESTAMP)
