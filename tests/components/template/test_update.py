"""The tests for the Template update platform."""

from __future__ import annotations

from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components import template, update
from homeassistant.const import (
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.setup import async_setup_component

from ._fixtures import (
    ConfigurationStyle,
    TemplatePlatformSetup,
    make_test_action,
    make_test_trigger,
    setup_and_test_nested_unique_id,
    setup_and_test_unique_id,
    setup_entity,
)

from tests.common import MockConfigEntry, assert_setup_component
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)

TEST_INSTALLED_SENSOR = "sensor.installed_update"
TEST_LATEST_SENSOR = "sensor.latest_update"
TEST_SENSOR_ID = "sensor.test_update"
TEST_INSTALLED_TEMPLATE = "{{ '1.0' }}"
TEST_LATEST_TEMPLATE = "{{ '2.0' }}"

TEST_UPDATE = TemplatePlatformSetup(
    update.DOMAIN,
    None,
    "template_update",
    make_test_trigger(TEST_INSTALLED_SENSOR, TEST_LATEST_SENSOR, TEST_SENSOR_ID),
)

TEST_UPDATE_CONFIG = {
    "installed_version": TEST_INSTALLED_TEMPLATE,
    "latest_version": TEST_LATEST_TEMPLATE,
}

INSTALL_ACTION = make_test_action(
    "install",
    {
        "backup": "{{ backup }}",
        "specific_version": "{{ specific_version }}",
    },
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture (tryke 0.0.27 quirk)."""
    return hass


@test
async def legacy_platform_config(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test a legacy platform does not create update entities."""
    with assert_setup_component(1, update.DOMAIN):
        expect(
            await async_setup_component(
                hass,
                update.DOMAIN,
                {"update": {"platform": "template", "updates": {"anything": {}}}},
            )
        ).to_be(True)
    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()
    expect(hass.states.async_all("update")).to_equal([])


@test.skip("requires snapshot fixture (syrupy) — port deferred")
async def setup_config_entry() -> None:
    """Stub: requires syrupy snapshot."""


@test
async def device_id(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test for device for Template."""
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
        domain=template.DOMAIN,
        options={
            "name": TEST_UPDATE.object_id,
            "template_type": update.DOMAIN,
            **TEST_UPDATE_CONFIG,
            "device_id": device_entry.id,
        },
        title="My template",
    )
    template_config_entry.add_to_hass(hass)

    expect(
        await hass.config_entries.async_setup(template_config_entry.entry_id)
    ).to_be(True)
    await hass.async_block_till_done()

    template_entity = entity_registry.async_get(TEST_UPDATE.entity_id)
    expect(template_entity).not_.to_be(None)
    expect(template_entity.device_id).to_equal(device_entry.id)


@test.cases(
    test.case(
        "modern_install_syntax",
        style=ConfigurationStyle.MODERN,
        installed_template="{{states.test['big.fat...']}}",
        latest_template=TEST_LATEST_TEMPLATE,
    ),
    test.case(
        "modern_latest_syntax",
        style=ConfigurationStyle.MODERN,
        installed_template=TEST_INSTALLED_TEMPLATE,
        latest_template="{{states.test['big.fat...']}}",
    ),
    test.case(
        "modern_both_syntax",
        style=ConfigurationStyle.MODERN,
        installed_template="{{states.test['big.fat...']}}",
        latest_template="{{states.test['big.fat...']}}",
    ),
    test.case(
        "trigger_install_syntax",
        style=ConfigurationStyle.TRIGGER,
        installed_template="{{states.test['big.fat...']}}",
        latest_template=TEST_LATEST_TEMPLATE,
    ),
    test.case(
        "trigger_latest_syntax",
        style=ConfigurationStyle.TRIGGER,
        installed_template=TEST_INSTALLED_TEMPLATE,
        latest_template="{{states.test['big.fat...']}}",
    ),
    test.case(
        "trigger_both_syntax",
        style=ConfigurationStyle.TRIGGER,
        installed_template="{{states.test['big.fat...']}}",
        latest_template="{{states.test['big.fat...']}}",
    ),
)
async def syntax_error(
    *,
    style: ConfigurationStyle,
    installed_template: str,
    latest_template: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test template update with render error."""
    await setup_entity(
        hass,
        TEST_UPDATE,
        style,
        1,
        {
            "installed_version": installed_template,
            "latest_version": latest_template,
        },
    )
    state = hass.states.get(TEST_UPDATE.entity_id)
    expect(state.state).to_be(STATE_UNKNOWN)


@test.cases(
    test.case(
        "modern_on", style=ConfigurationStyle.MODERN, installed="1.0", latest="2.0", expected=STATE_ON
    ),
    test.case(
        "modern_off", style=ConfigurationStyle.MODERN, installed="2.0", latest="2.0", expected=STATE_OFF
    ),
    test.case(
        "trigger_on", style=ConfigurationStyle.TRIGGER, installed="1.0", latest="2.0", expected=STATE_ON
    ),
    test.case(
        "trigger_off", style=ConfigurationStyle.TRIGGER, installed="2.0", latest="2.0", expected=STATE_OFF
    ),
)
async def update_templates(
    *,
    style: ConfigurationStyle,
    installed: str,
    latest: str,
    expected: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test update template."""
    await setup_entity(
        hass,
        TEST_UPDATE,
        style,
        1,
        {
            "installed_version": "{{ states('sensor.installed_update') }}",
            "latest_version": "{{ states('sensor.latest_update') }}",
        },
    )

    hass.states.async_set(TEST_INSTALLED_SENSOR, installed)
    hass.states.async_set(TEST_LATEST_SENSOR, latest)
    await hass.async_block_till_done()

    state = hass.states.get(TEST_UPDATE.entity_id)
    expect(state).not_.to_be(None)
    expect(state.state).to_be(expected)
    expect(state.attributes["installed_version"]).to_equal(installed)
    expect(state.attributes["latest_version"]).to_equal(latest)
    expect(state.attributes["entity_picture"]).to_equal(
        "/api/brands/integration/template/icon.png"
    )


@test.cases(
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def installed_and_latest_template_updates_from_entity(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test template installed and latest version templates updates from entities."""
    await setup_entity(
        hass,
        TEST_UPDATE,
        style,
        1,
        {
            "installed_version": "{{ states('sensor.installed_update') }}",
            "latest_version": "{{ states('sensor.latest_update') }}",
        },
    )

    hass.states.async_set(TEST_INSTALLED_SENSOR, "1.0")
    hass.states.async_set(TEST_LATEST_SENSOR, "2.0")
    await hass.async_block_till_done()

    state = hass.states.get(TEST_UPDATE.entity_id)
    expect(state).not_.to_be(None)
    expect(state.state).to_be(STATE_ON)
    expect(state.attributes["installed_version"]).to_equal("1.0")
    expect(state.attributes["latest_version"]).to_equal("2.0")

    hass.states.async_set(TEST_INSTALLED_SENSOR, "2.0")
    hass.states.async_set(TEST_LATEST_SENSOR, "2.0")
    await hass.async_block_till_done()

    state = hass.states.get(TEST_UPDATE.entity_id)
    expect(state.state).to_be(STATE_OFF)
    expect(state.attributes["installed_version"]).to_equal("2.0")
    expect(state.attributes["latest_version"]).to_equal("2.0")

    hass.states.async_set(TEST_INSTALLED_SENSOR, "2.0")
    hass.states.async_set(TEST_LATEST_SENSOR, "3.0")
    await hass.async_block_till_done()

    state = hass.states.get(TEST_UPDATE.entity_id)
    expect(state.state).to_be(STATE_ON)
    expect(state.attributes["installed_version"]).to_equal("2.0")
    expect(state.attributes["latest_version"]).to_equal("3.0")


@test.cases(
    test.case("modern_str_one", style=ConfigurationStyle.MODERN, installed_tpl="{{ '1.0' }}", expected=STATE_ON, expected_attr="1.0"),
    test.case("modern_int_one", style=ConfigurationStyle.MODERN, installed_tpl="{{ 1.0 }}", expected=STATE_ON, expected_attr="1.0"),
    test.case("modern_str_two", style=ConfigurationStyle.MODERN, installed_tpl="{{ '2.0' }}", expected=STATE_OFF, expected_attr="2.0"),
    test.case("modern_int_two", style=ConfigurationStyle.MODERN, installed_tpl="{{ 2.0 }}", expected=STATE_OFF, expected_attr="2.0"),
    test.case("modern_none", style=ConfigurationStyle.MODERN, installed_tpl="{{ None }}", expected=STATE_UNKNOWN, expected_attr=None),
    test.case("modern_foo", style=ConfigurationStyle.MODERN, installed_tpl="{{ 'foo' }}", expected=STATE_ON, expected_attr="foo"),
    test.case("modern_invalid", style=ConfigurationStyle.MODERN, installed_tpl="{{ x + 2 }}", expected=STATE_UNKNOWN, expected_attr=None),
    test.case("trigger_str_one", style=ConfigurationStyle.TRIGGER, installed_tpl="{{ '1.0' }}", expected=STATE_ON, expected_attr="1.0"),
    test.case("trigger_int_one", style=ConfigurationStyle.TRIGGER, installed_tpl="{{ 1.0 }}", expected=STATE_ON, expected_attr="1.0"),
    test.case("trigger_str_two", style=ConfigurationStyle.TRIGGER, installed_tpl="{{ '2.0' }}", expected=STATE_OFF, expected_attr="2.0"),
    test.case("trigger_int_two", style=ConfigurationStyle.TRIGGER, installed_tpl="{{ 2.0 }}", expected=STATE_OFF, expected_attr="2.0"),
    test.case("trigger_none", style=ConfigurationStyle.TRIGGER, installed_tpl="{{ None }}", expected=STATE_UNKNOWN, expected_attr=None),
    test.case("trigger_foo", style=ConfigurationStyle.TRIGGER, installed_tpl="{{ 'foo' }}", expected=STATE_ON, expected_attr="foo"),
    test.case("trigger_invalid", style=ConfigurationStyle.TRIGGER, installed_tpl="{{ x + 2 }}", expected=STATE_UNKNOWN, expected_attr=None),
)
async def installed_version_template(
    *,
    style: ConfigurationStyle,
    installed_tpl: str,
    expected: str,
    expected_attr: Any,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test installed_version template results."""
    await setup_entity(
        hass,
        TEST_UPDATE,
        style,
        1,
        {
            "installed_version": installed_tpl,
            "latest_version": TEST_LATEST_TEMPLATE,
        },
    )
    hass.states.async_set(TEST_INSTALLED_SENSOR, STATE_ON)
    await hass.async_block_till_done()

    state = hass.states.get(TEST_UPDATE.entity_id)
    expect(state).not_.to_be(None)
    expect(state.state).to_be(expected)
    expect(state.attributes["installed_version"]).to_equal(expected_attr)


@test.cases(
    test.case("modern_str_one", style=ConfigurationStyle.MODERN, latest_tpl="{{ '1.0' }}", expected=STATE_OFF, expected_attr="1.0"),
    test.case("modern_int_one", style=ConfigurationStyle.MODERN, latest_tpl="{{ 1.0 }}", expected=STATE_OFF, expected_attr="1.0"),
    test.case("modern_str_two", style=ConfigurationStyle.MODERN, latest_tpl="{{ '2.0' }}", expected=STATE_ON, expected_attr="2.0"),
    test.case("modern_int_two", style=ConfigurationStyle.MODERN, latest_tpl="{{ 2.0 }}", expected=STATE_ON, expected_attr="2.0"),
    test.case("modern_none", style=ConfigurationStyle.MODERN, latest_tpl="{{ None }}", expected=STATE_UNKNOWN, expected_attr=None),
    test.case("modern_foo", style=ConfigurationStyle.MODERN, latest_tpl="{{ 'foo' }}", expected=STATE_ON, expected_attr="foo"),
    test.case("modern_invalid", style=ConfigurationStyle.MODERN, latest_tpl="{{ x + 2 }}", expected=STATE_UNKNOWN, expected_attr=None),
    test.case("trigger_str_one", style=ConfigurationStyle.TRIGGER, latest_tpl="{{ '1.0' }}", expected=STATE_OFF, expected_attr="1.0"),
    test.case("trigger_int_one", style=ConfigurationStyle.TRIGGER, latest_tpl="{{ 1.0 }}", expected=STATE_OFF, expected_attr="1.0"),
    test.case("trigger_str_two", style=ConfigurationStyle.TRIGGER, latest_tpl="{{ '2.0' }}", expected=STATE_ON, expected_attr="2.0"),
    test.case("trigger_int_two", style=ConfigurationStyle.TRIGGER, latest_tpl="{{ 2.0 }}", expected=STATE_ON, expected_attr="2.0"),
    test.case("trigger_none", style=ConfigurationStyle.TRIGGER, latest_tpl="{{ None }}", expected=STATE_UNKNOWN, expected_attr=None),
    test.case("trigger_foo", style=ConfigurationStyle.TRIGGER, latest_tpl="{{ 'foo' }}", expected=STATE_ON, expected_attr="foo"),
    test.case("trigger_invalid", style=ConfigurationStyle.TRIGGER, latest_tpl="{{ x + 2 }}", expected=STATE_UNKNOWN, expected_attr=None),
)
async def latest_version_template(
    *,
    style: ConfigurationStyle,
    latest_tpl: str,
    expected: str,
    expected_attr: Any,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test latest_version template results."""
    await setup_entity(
        hass,
        TEST_UPDATE,
        style,
        1,
        {
            "installed_version": TEST_INSTALLED_TEMPLATE,
            "latest_version": latest_tpl,
        },
    )
    hass.states.async_set(TEST_INSTALLED_SENSOR, STATE_ON)
    await hass.async_block_till_done()

    state = hass.states.get(TEST_UPDATE.entity_id)
    expect(state).not_.to_be(None)
    expect(state.state).to_be(expected)
    expect(state.attributes["latest_version"]).to_equal(expected_attr)


@test.cases(
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def available_template_with_entities(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test availability templates with values from other entities."""
    await setup_entity(
        hass,
        TEST_UPDATE,
        style,
        1,
        {
            "installed_version": "{{ states('sensor.installed_update') }}",
            "latest_version": "{{ states('sensor.latest_update') }}",
        },
        extra_config={
            "availability": "{{ is_state('sensor.test_update', 'on') }}"
        },
    )

    hass.states.async_set(TEST_INSTALLED_SENSOR, "1.0")
    hass.states.async_set(TEST_LATEST_SENSOR, "2.0")
    hass.states.async_set(TEST_SENSOR_ID, STATE_ON)
    await hass.async_block_till_done()

    state = hass.states.get(TEST_UPDATE.entity_id)
    expect(state.state != STATE_UNAVAILABLE).to_be(True)

    hass.states.async_set(TEST_SENSOR_ID, STATE_OFF)
    await hass.async_block_till_done()
    expect(hass.states.get(TEST_UPDATE.entity_id).state).to_be(STATE_UNAVAILABLE)


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
        TEST_UPDATE,
        style,
        1,
        TEST_UPDATE_CONFIG,
        extra_config={"availability": "{{ x - 12 }}"},
    )

    hass.states.async_set(TEST_INSTALLED_SENSOR, "1.0")
    await hass.async_block_till_done()

    expect(
        hass.states.get(TEST_UPDATE.entity_id).state != STATE_UNAVAILABLE
    ).to_be(True)


@test.cases(
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def unique_id(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test unique_id option only creates one update per id."""
    await setup_and_test_unique_id(hass, TEST_UPDATE, style, TEST_UPDATE_CONFIG)


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
    """Test a template unique_id propagates to update unique_ids."""
    await setup_and_test_nested_unique_id(
        hass, TEST_UPDATE, style, entity_registry, TEST_UPDATE_CONFIG
    )


@test.skip("requires hass_ws_client (websocket flow preview) — port deferred")
async def flow_preview() -> None:
    """Stub: requires WebSocketGenerator flow preview."""


@test.skip("requires mock_restore_cache_with_extra_data — port deferred")
async def trigger_entity_restore_state() -> None:
    """Stub: requires restore-cache scaffolding."""


@test.skip("install_action requires service handler interplay — port deferred")
async def install_action() -> None:
    """Stub: install action timing test, port later."""


@test.skip("entity_picture/icon templates need extra fixtures — port deferred")
async def entity_picture_and_icon_templates() -> None:
    """Stub."""


@test.skip("entity_picture_uses_default uses internal expected URL — port deferred")
async def entity_picture_uses_default() -> None:
    """Stub."""


@test.skip("in_process template stub — port deferred")
async def in_process_template() -> None:
    """Stub."""


@test.skip("release templates have action interplay — port deferred")
async def release_summary_and_title_templates() -> None:
    """Stub."""


@test.skip("release_url_template stub — port deferred")
async def release_url_template() -> None:
    """Stub."""


@test.skip("update_percent template stub — port deferred")
async def update_percent_template() -> None:
    """Stub."""


@test.skip("optimistic_in_progress_with_update_percent_template stub — port deferred")
async def optimistic_in_progress_with_update_percent_template() -> None:
    """Stub."""


@test.skip("supported_features stub — port deferred")
async def supported_features() -> None:
    """Stub."""
