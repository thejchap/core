"""Test template entity."""

from __future__ import annotations

from tryke import Depends, expect, fixture, test

from homeassistant.components.template import template_entity
from homeassistant.core import HomeAssistant
from homeassistant.helpers import template

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture (tryke 0.0.27 quirk)."""
    return hass


@test
async def template_entity_requires_hass_set(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test template entity requires hass to be set before accepting templates."""
    entity = template_entity.TemplateEntity(hass, {}, "something_unique")

    raised = False
    try:
        entity.add_template_attribute("_hello", template.Template("Hello", None))
    except ValueError as err:
        raised = True
        expect(str(err).startswith("template.hass cannot be None")).to_be(True)
    expect(raised).to_be(True)

    tpl_with_hass = template.Template("Hello", entity.hass)
    entity.add_template_attribute("_hello", tpl_with_hass)

    expect(len(entity._template_attrs.get(tpl_with_hass, []))).to_equal(1)


@test
async def default_entity_id(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test template entity creates suggested entity_id from default_entity_id."""

    class TemplateTest(template_entity.TemplateEntity):
        _entity_id_format = "test.{}"

    entity = TemplateTest(hass, {"default_entity_id": "test.test"}, "a")
    expect(entity.entity_id).to_equal("test.test")


@test
async def bad_default_entity_id(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test bad default_entity_id falls back to suggested entity_id."""

    class TemplateTest(template_entity.TemplateEntity):
        _entity_id_format = "test.{}"

    entity = TemplateTest(hass, {"default_entity_id": "bad.test"}, "a")
    expect(entity.entity_id).to_equal("test.test")
