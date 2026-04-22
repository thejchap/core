"""Test config entry functions for Home Assistant templates."""

from __future__ import annotations

from datetime import timedelta
import json
import logging

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import TemplateError
from homeassistant.helpers import entity, entity_registry as er
from homeassistant.helpers.entity_platform import EntityPlatform

from tests.common import MockConfigEntry
from tests.hass_fixtures import entity_registry, hass
from tests.helpers.template.helpers import assert_result_info, render, render_to_info


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def integration_entities(
    hass: HomeAssistant = Depends(hass),
    entity_registry: er.EntityRegistry = Depends(entity_registry),
) -> None:
    """Test integration_entities function."""
    # test entities for untitled config entry
    config_entry = MockConfigEntry(domain="mock", title="")
    config_entry.add_to_hass(hass)
    entity_registry.async_get_or_create(
        "sensor", "mock", "untitled", config_entry=config_entry
    )
    info = render_to_info(hass, "{{ integration_entities('') }}")
    assert_result_info(info, [])
    expect(info.rate_limit).to_be(None)

    # test entities for given config entry title
    config_entry = MockConfigEntry(domain="mock", title="Mock bridge 2")
    config_entry.add_to_hass(hass)
    entity_entry = entity_registry.async_get_or_create(
        "sensor", "mock", "test", config_entry=config_entry
    )
    info = render_to_info(hass, "{{ integration_entities('Mock bridge 2') }}")
    assert_result_info(info, [entity_entry.entity_id])
    expect(info.rate_limit).to_be(None)

    # test entities for given non unique config entry title
    config_entry = MockConfigEntry(domain="mock", title="Not unique")
    config_entry.add_to_hass(hass)
    entity_entry_not_unique_1 = entity_registry.async_get_or_create(
        "sensor", "mock", "not_unique_1", config_entry=config_entry
    )
    config_entry = MockConfigEntry(domain="mock", title="Not unique")
    config_entry.add_to_hass(hass)
    entity_entry_not_unique_2 = entity_registry.async_get_or_create(
        "sensor", "mock", "not_unique_2", config_entry=config_entry
    )
    info = render_to_info(hass, "{{ integration_entities('Not unique') }}")
    assert_result_info(
        info, [entity_entry_not_unique_1.entity_id, entity_entry_not_unique_2.entity_id]
    )
    expect(info.rate_limit).to_be(None)

    # test integration entities not in entity registry
    mock_entity = entity.Entity()
    mock_entity.hass = hass
    mock_entity.entity_id = "light.test_entity"
    mock_entity.platform = EntityPlatform(
        hass=hass,
        logger=logging.getLogger(__name__),
        domain="light",
        platform_name="entryless_integration",
        platform=None,
        scan_interval=timedelta(seconds=30),
        entity_namespace=None,
    )
    await mock_entity.async_internal_added_to_hass()
    info = render_to_info(hass, "{{ integration_entities('entryless_integration') }}")
    assert_result_info(info, ["light.test_entity"])
    expect(info.rate_limit).to_be(None)

    # Test non existing integration/entry title
    info = render_to_info(hass, "{{ integration_entities('abc123') }}")
    assert_result_info(info, [])
    expect(info.rate_limit).to_be(None)


@test
async def config_entry_id(
    hass: HomeAssistant = Depends(hass),
    entity_registry: er.EntityRegistry = Depends(entity_registry),
) -> None:
    """Test config_entry_id function."""
    config_entry = MockConfigEntry(domain="light", title="Some integration")
    config_entry.add_to_hass(hass)
    entity_entry = entity_registry.async_get_or_create(
        "sensor", "test", "test", suggested_object_id="test", config_entry=config_entry
    )

    info = render_to_info(hass, "{{ 'sensor.fail' | config_entry_id }}")
    assert_result_info(info, None)
    expect(info.rate_limit).to_be(None)

    info = render_to_info(hass, "{{ 56 | config_entry_id }}")
    assert_result_info(info, None)

    info = render_to_info(hass, "{{ 'not_a_real_entity_id' | config_entry_id }}")
    assert_result_info(info, None)

    info = render_to_info(
        hass, f"{{{{ config_entry_id('{entity_entry.entity_id}') }}}}"
    )
    assert_result_info(info, config_entry.entry_id)
    expect(info.rate_limit).to_be(None)


@test
async def config_entry_attr(hass: HomeAssistant = Depends(hass)) -> None:
    """Test config entry attr."""
    info: dict[str, object] = {
        "domain": "mock_light",
        "title": "mock title",
        "source": config_entries.SOURCE_BLUETOOTH,
        "disabled_by": config_entries.ConfigEntryDisabler.USER,
        "pref_disable_polling": True,
    }
    config_entry = MockConfigEntry(**info)
    config_entry.add_to_hass(hass)

    info["state"] = config_entries.ConfigEntryState.NOT_LOADED

    for key, value in info.items():
        expect(
            render(
                hass,
                "{{ config_entry_attr('"
                + config_entry.entry_id
                + "', '"
                + key
                + "') }}",
                parse_result=False,
            )
        ).to_equal(str(value))

    for config_entry_id_val, key in (
        (config_entry.entry_id, "invalid_key"),
        (56, "domain"),
    ):
        expect(
            lambda cid=config_entry_id_val, k=key: render(
                hass,
                "{{ config_entry_attr("
                + json.dumps(cid)
                + ", '"
                + k
                + "') }}",
            )
        ).to_raise(TemplateError)

    expect(
        render(
            hass, "{{ config_entry_attr('invalid_id', 'domain') }}", parse_result=False
        )
    ).to_equal("None")
