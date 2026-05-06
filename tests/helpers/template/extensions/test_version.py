"""Test version functions for Home Assistant templates."""

from __future__ import annotations

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import TemplateError

from tests.hass_fixtures import hass
from tests.helpers.template.helpers import render


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def version(hass: HomeAssistant = Depends(hass)) -> None:
    """Test version filter and function."""
    filter_result = render(hass, "{{ '2099.9.9' | version}}")
    function_result = render(hass, "{{ version('2099.9.9')}}")
    expect(filter_result).to_equal("2099.9.9")
    expect(function_result).to_equal("2099.9.9")

    filter_result = render(hass, "{{ '2099.9.9' | version < '2099.9.10' }}")
    function_result = render(hass, "{{ version('2099.9.9') < '2099.9.10' }}")
    expect(filter_result).to_be(True)
    expect(function_result).to_be(True)

    filter_result = render(hass, "{{ '2099.9.9' | version == '2099.9.9' }}")
    function_result = render(hass, "{{ version('2099.9.9') == '2099.9.9' }}")
    expect(filter_result).to_be(True)
    expect(function_result).to_be(True)

    expect(lambda: render(hass, "{{ version(None) < '2099.9.10' }}")).to_raise(
        TemplateError
    )
