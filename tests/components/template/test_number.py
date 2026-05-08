"""The tests for the Template number platform."""

from __future__ import annotations

from tryke import Depends, expect, fixture, test

from homeassistant.components import number
from homeassistant.components.number import (
    ATTR_MAX,
    ATTR_MIN,
    ATTR_STEP,
    ATTR_VALUE as NUMBER_ATTR_VALUE,
    DOMAIN as NUMBER_DOMAIN,
    SERVICE_SET_VALUE as NUMBER_SERVICE_SET_VALUE,
)
from homeassistant.components.template import DOMAIN
from homeassistant.components.template.const import CONF_PICTURE
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_ENTITY_PICTURE,
    ATTR_ICON,
    CONF_ENTITY_ID,
    CONF_ICON,
    CONF_UNIT_OF_MEASUREMENT,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from ._fixtures import (
    ConfigurationStyle,
    TemplatePlatformSetup,
    assert_action,
    async_trigger,
    make_test_action,
    make_test_trigger,
    mock_calls,
    setup_and_test_nested_unique_id,
    setup_and_test_unique_id,
    setup_entity,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)

TEST_AVAILABILITY_ENTITY_ID = "binary_sensor.test_availability"
TEST_MAXIMUM_ENTITY_ID = "sensor.maximum"
TEST_MINIMUM_ENTITY_ID = "sensor.minimum"
TEST_STATE_ENTITY_ID = "number.test_state"
TEST_STEP_ENTITY_ID = "sensor.step"
TEST_NUMBER = TemplatePlatformSetup(
    number.DOMAIN,
    None,
    "template_number",
    make_test_trigger(
        TEST_AVAILABILITY_ENTITY_ID,
        TEST_MAXIMUM_ENTITY_ID,
        TEST_MINIMUM_ENTITY_ID,
        TEST_STATE_ENTITY_ID,
        TEST_STEP_ENTITY_ID,
    ),
)
TEST_SET_VALUE_ACTION = make_test_action("set_value", {"value": "{{ value }}"})
TEST_REQUIRED = {"state": "0", "step": "1", "set_value": []}


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture (tryke 0.0.27 quirk)."""
    return hass


def _verify(
    hass: HomeAssistant,
    expected_value: int,
    expected_step: int,
    expected_minimum: int,
    expected_maximum: int,
    expected_unit_of_measurement: str | None,
) -> None:
    """Verify number's state."""
    state = hass.states.get(TEST_NUMBER.entity_id)
    attributes = state.attributes
    assert state.state == str(float(expected_value))
    assert attributes.get(ATTR_STEP) == float(expected_step)
    assert attributes.get(ATTR_MAX) == float(expected_maximum)
    assert attributes.get(ATTR_MIN) == float(expected_minimum)
    assert attributes.get(CONF_UNIT_OF_MEASUREMENT) == expected_unit_of_measurement


@test.skip("requires snapshot fixture (syrupy) — port deferred")
async def setup_config_entry() -> None:
    """Stub: requires syrupy snapshot."""


@test.cases(
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def missing_optional_config(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test: missing optional template is ok."""
    await setup_entity(
        hass,
        TEST_NUMBER,
        style,
        1,
        {
            "state": "{{ 4 }}",
            "set_value": {"service": "script.set_value"},
            "step": "{{ 1 }}",
        },
    )
    await async_trigger(hass, TEST_STATE_ENTITY_ID, "anything")
    _verify(hass, 4, 1, 0.0, 100.0, None)


@test.cases(
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def missing_required_keys(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test: missing required fields will fail."""
    await setup_entity(
        hass, TEST_NUMBER, style, 0, {"state": "{{ 4 }}"}
    )
    expect(hass.states.async_all("number")).to_equal([])


@test.cases(
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def all_optional_config(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test: including all optional templates is ok."""
    await setup_entity(
        hass,
        TEST_NUMBER,
        style,
        1,
        {
            "state": "{{ 4 }}",
            "set_value": {"service": "script.set_value"},
            "min": "{{ 3 }}",
            "max": "{{ 5 }}",
            "step": "{{ 1 }}",
            "unit_of_measurement": "beer",
        },
    )
    await async_trigger(hass, TEST_STATE_ENTITY_ID, "anything")
    _verify(hass, 4, 1, 3, 5, "beer")


@test.cases(
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def template_number(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test templates with values from other entities."""
    calls = mock_calls(hass)
    await setup_entity(
        hass,
        TEST_NUMBER,
        style,
        1,
        {
            "state": f"{{{{ states('{TEST_STATE_ENTITY_ID}') | float(1.0) }}}}",
            "step": f"{{{{ states('{TEST_STEP_ENTITY_ID}') | float(5.0) }}}}",
            "min": f"{{{{ states('{TEST_MINIMUM_ENTITY_ID}') | float(0.0) }}}}",
            "max": f"{{{{ states('{TEST_MAXIMUM_ENTITY_ID}') | float(100.0) }}}}",
            **TEST_SET_VALUE_ACTION,
        },
    )
    await async_trigger(hass, TEST_STATE_ENTITY_ID, 4)
    await async_trigger(hass, TEST_STEP_ENTITY_ID, 1)
    await async_trigger(hass, TEST_MINIMUM_ENTITY_ID, 3)
    await async_trigger(hass, TEST_MAXIMUM_ENTITY_ID, 5)
    _verify(hass, 4, 1, 3, 5, None)

    await async_trigger(hass, TEST_STATE_ENTITY_ID, 5)
    _verify(hass, 5, 1, 3, 5, None)

    await async_trigger(hass, TEST_STEP_ENTITY_ID, 2)
    _verify(hass, 5, 2, 3, 5, None)

    await async_trigger(hass, TEST_MINIMUM_ENTITY_ID, 2)
    _verify(hass, 5, 2, 2, 5, None)

    await async_trigger(hass, TEST_MAXIMUM_ENTITY_ID, 6)
    _verify(hass, 5, 2, 2, 6, None)

    await hass.services.async_call(
        NUMBER_DOMAIN,
        NUMBER_SERVICE_SET_VALUE,
        {CONF_ENTITY_ID: TEST_NUMBER.entity_id, NUMBER_ATTR_VALUE: 2},
        blocking=True,
    )

    assert_action(TEST_NUMBER, calls, 1, "set_value", value=2)

    await async_trigger(hass, TEST_STATE_ENTITY_ID, 2)
    _verify(hass, 2, 2, 2, 6, None)


@test.cases(
    test.case(
        "modern_icon",
        style=ConfigurationStyle.MODERN,
        initial_expected_state="",
        attribute=ATTR_ICON,
        attribute_key=CONF_ICON,
        attribute_template=(
            "{% if states.number.test_state.state == '1' %}mdi:check{% endif %}"
        ),
        expected="mdi:check",
    ),
    test.case(
        "modern_picture",
        style=ConfigurationStyle.MODERN,
        initial_expected_state="",
        attribute=ATTR_ENTITY_PICTURE,
        attribute_key=CONF_PICTURE,
        attribute_template=(
            "{% if states.number.test_state.state == '1' %}check.jpg{% endif %}"
        ),
        expected="check.jpg",
    ),
    test.case(
        "trigger_icon",
        style=ConfigurationStyle.TRIGGER,
        initial_expected_state=None,
        attribute=ATTR_ICON,
        attribute_key=CONF_ICON,
        attribute_template=(
            "{% if states.number.test_state.state == '1' %}mdi:check{% endif %}"
        ),
        expected="mdi:check",
    ),
    test.case(
        "trigger_picture",
        style=ConfigurationStyle.TRIGGER,
        initial_expected_state=None,
        attribute=ATTR_ENTITY_PICTURE,
        attribute_key=CONF_PICTURE,
        attribute_template=(
            "{% if states.number.test_state.state == '1' %}check.jpg{% endif %}"
        ),
        expected="check.jpg",
    ),
)
async def templated_optional_config(
    *,
    style: ConfigurationStyle,
    initial_expected_state: str | None,
    attribute: str,
    attribute_key: str,
    attribute_template: str,
    expected: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test optional config templates."""
    await setup_entity(
        hass,
        TEST_NUMBER,
        style,
        1,
        {attribute_key: attribute_template, **TEST_REQUIRED},
    )

    state = hass.states.get(TEST_NUMBER.entity_id)
    expect(state.attributes.get(attribute)).to_equal(initial_expected_state)

    await async_trigger(hass, TEST_STATE_ENTITY_ID, "1")

    state = hass.states.get(TEST_NUMBER.entity_id)
    expect(state.attributes[attribute]).to_equal(expected)


@test
async def device_id(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test for device for number template."""
    device_config_entry = MockConfigEntry()
    device_config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=device_config_entry.entry_id,
        identifiers={("test", "identifier_test")},
        connections={("mac", "30:31:32:33:34:35")},
    )
    await hass.async_block_till_done()
    expect(device_entry).not_.to_be(None)

    template_config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "name": "My template",
            "template_type": "number",
            "state": "{{ 10 }}",
            "min": 0,
            "max": 100,
            "step": 0.1,
            "set_value": {
                "action": "input_number.set_value",
                "target": {"entity_id": "input_number.test"},
                "data": {"value": "{{ value }}"},
            },
            "device_id": device_entry.id,
        },
        title="My template",
    )
    template_config_entry.add_to_hass(hass)

    expect(
        await hass.config_entries.async_setup(template_config_entry.entry_id)
    ).to_be(True)
    await hass.async_block_till_done()

    template_entity = entity_registry.async_get("number.my_template")
    expect(template_entity).not_.to_be(None)
    expect(template_entity.device_id).to_equal(device_entry.id)


@test.cases(
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def optimistic(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test configuration with optimistic state."""
    await setup_entity(hass, TEST_NUMBER, style, 1, {"set_value": []})

    await hass.services.async_call(
        number.DOMAIN,
        number.SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: TEST_NUMBER.entity_id, "value": 4},
        blocking=True,
    )

    state = hass.states.get(TEST_NUMBER.entity_id)
    expect(float(state.state)).to_equal(4)

    await hass.services.async_call(
        number.DOMAIN,
        number.SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: TEST_NUMBER.entity_id, "value": 2},
        blocking=True,
    )

    state = hass.states.get(TEST_NUMBER.entity_id)
    expect(float(state.state)).to_equal(2)


@test.cases(
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def not_optimistic(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test optimistic yaml option set to false."""
    await setup_entity(
        hass,
        TEST_NUMBER,
        style,
        1,
        {
            "state": "{{ states('sensor.test_state') }}",
            "optimistic": False,
            "set_value": [],
        },
    )

    await hass.services.async_call(
        number.DOMAIN,
        number.SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: TEST_NUMBER.entity_id, "value": 4},
        blocking=True,
    )

    state = hass.states.get(TEST_NUMBER.entity_id)
    expect(state.state).to_be(STATE_UNKNOWN)


@test.cases(
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def availability(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test availability template."""
    await setup_entity(
        hass,
        TEST_NUMBER,
        style,
        1,
        {
            "set_value": [],
            "state": "{{ states('number.test_state') }}",
            "availability": (
                "{{ is_state('binary_sensor.test_availability', 'on') }}"
            ),
        },
    )
    await async_trigger(hass, TEST_STATE_ENTITY_ID, "4.0")
    await async_trigger(hass, TEST_AVAILABILITY_ENTITY_ID, "on")
    state = hass.states.get(TEST_NUMBER.entity_id)
    expect(float(state.state)).to_equal(4)

    await async_trigger(hass, TEST_AVAILABILITY_ENTITY_ID, "off")
    expect(hass.states.get(TEST_NUMBER.entity_id).state).to_be(STATE_UNAVAILABLE)

    await async_trigger(hass, TEST_STATE_ENTITY_ID, "2.0")
    expect(hass.states.get(TEST_NUMBER.entity_id).state).to_be(STATE_UNAVAILABLE)

    await async_trigger(hass, TEST_AVAILABILITY_ENTITY_ID, "on")
    expect(float(hass.states.get(TEST_NUMBER.entity_id).state)).to_equal(2)


@test.cases(
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def invalid_availability_template_keeps_component_available(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that an invalid availability keeps the device available."""
    await setup_entity(
        hass,
        TEST_NUMBER,
        style,
        1,
        {
            "set_value": [],
            "state": "{{ states('number.test_state') }}",
            "availability": "{{ x - 12 }}",
        },
    )
    await async_trigger(hass, TEST_AVAILABILITY_ENTITY_ID, "anything")
    expect(
        hass.states.get(TEST_NUMBER.entity_id).state != STATE_UNAVAILABLE
    ).to_be(True)


@test
async def empty_action_config(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test configuration with empty script."""
    await setup_entity(
        hass,
        TEST_NUMBER,
        ConfigurationStyle.MODERN,
        1,
        {
            "state": "{{ 1 }}",
            "set_value": [],
            "step": "{{ 1 }}",
            "optimistic": True,
        },
    )

    await hass.services.async_call(
        number.DOMAIN,
        number.SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: TEST_NUMBER.entity_id, "value": 4},
        blocking=True,
    )

    state = hass.states.get(TEST_NUMBER.entity_id)
    expect(float(state.state)).to_equal(4)


@test.skip("requires hass_ws_client (websocket flow preview) — port deferred")
async def flow_preview() -> None:
    """Stub: requires WebSocketGenerator flow preview."""


@test.cases(
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def unique_id(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test unique_id option only creates one number per id."""
    await setup_and_test_unique_id(hass, TEST_NUMBER, style, TEST_REQUIRED, "{{ 0 }}")


@test.cases(
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def nested_unique_id(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test a template unique_id propagates to number unique_ids."""
    await setup_and_test_nested_unique_id(
        hass, TEST_NUMBER, style, entity_registry, TEST_REQUIRED, "{{ 0 }}"
    )


@test.cases(
    test.case(
        "modern_temperature",
        style=ConfigurationStyle.MODERN,
        config={
            **TEST_REQUIRED,
            "unit_of_measurement": "°C",
            "device_class": "temperature",
        },
        expected_device_class="temperature",
    ),
    test.case(
        "modern_none",
        style=ConfigurationStyle.MODERN,
        config=TEST_REQUIRED,
        expected_device_class=None,
    ),
    test.case(
        "trigger_temperature",
        style=ConfigurationStyle.TRIGGER,
        config={
            **TEST_REQUIRED,
            "unit_of_measurement": "°C",
            "device_class": "temperature",
        },
        expected_device_class="temperature",
    ),
    test.case(
        "trigger_none",
        style=ConfigurationStyle.TRIGGER,
        config=TEST_REQUIRED,
        expected_device_class=None,
    ),
)
async def setup_valid_device_class(
    *,
    style: ConfigurationStyle,
    config: dict,
    expected_device_class: str | None,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setup with valid device_class."""
    await setup_entity(hass, TEST_NUMBER, style, 1, config)
    await async_trigger(hass, TEST_STATE_ENTITY_ID, "75")
    expect(
        hass.states.get(TEST_NUMBER.entity_id).attributes.get("device_class")
    ).to_equal(expected_device_class)
