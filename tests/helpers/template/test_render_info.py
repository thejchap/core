"""Test template render information tracking for Home Assistant."""

from __future__ import annotations

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import TemplateError
from homeassistant.helpers import template
from homeassistant.helpers.template.render_info import (
    ALL_STATES_RATE_LIMIT,
    DOMAIN_STATES_RATE_LIMIT,
    RenderInfo,
    _false,
    _true,
    render_info_cv,
)

from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@fixture
async def template_obj(hass: HomeAssistant = Depends(hass)) -> template.Template:
    """Template object for render_info tests."""
    return template.Template("{{ 1 + 1 }}", hass)


@test
async def render_info_initialization(
    template_obj: template.Template = Depends(template_obj),
) -> None:
    """Test RenderInfo initialization."""
    info = RenderInfo(template_obj)

    expect(info.template is template_obj).to_be(True)
    expect(info._result).to_be(None)
    expect(info.is_static).to_be(False)
    expect(info.exception).to_be(None)
    expect(info.all_states).to_be(False)
    expect(info.all_states_lifecycle).to_be(False)
    expect(info.domains).to_equal(set())
    expect(info.domains_lifecycle).to_equal(set())
    expect(info.entities).to_equal(set())
    expect(info.rate_limit).to_be(None)
    expect(info.has_time).to_be(False)
    expect(info.filter_lifecycle is _true).to_be(True)
    expect(info.filter is _true).to_be(True)


@test
async def render_info_repr(
    template_obj: template.Template = Depends(template_obj),
) -> None:
    """Test RenderInfo representation."""
    info = RenderInfo(template_obj)
    info.domains.add("sensor")
    info.entities.add("sensor.test")

    repr_str = repr(info)
    expect(repr_str).to_contain("RenderInfo")
    expect(repr_str).to_contain("domains={'sensor'}")
    expect(repr_str).to_contain("entities={'sensor.test'}")


@test
async def render_info_result(
    template_obj: template.Template = Depends(template_obj),
) -> None:
    """Test RenderInfo result property."""
    info = RenderInfo(template_obj)

    # Test with no result set - should return None cast as str
    expect(info.result()).to_be(None)

    # Test with result set
    info._result = "test_result"
    expect(info.result()).to_equal("test_result")

    # Test with exception
    info.exception = TemplateError("Test error")
    expect(lambda: info.result()).to_raise(TemplateError, match="Test error")


@test
async def render_info_filter_domains_and_entities(
    template_obj: template.Template = Depends(template_obj),
) -> None:
    """Test RenderInfo entity and domain filtering."""
    info = RenderInfo(template_obj)

    # Add domain and entity
    info.domains.add("sensor")
    info.entities.add("light.test")

    # Should match domain
    expect(info._filter_domains_and_entities("sensor.temperature")).to_be(True)
    # Should match entity
    expect(info._filter_domains_and_entities("light.test")).to_be(True)
    # Should not match
    expect(info._filter_domains_and_entities("switch.kitchen")).to_be(False)


@test
async def render_info_filter_entities(
    template_obj: template.Template = Depends(template_obj),
) -> None:
    """Test RenderInfo entity-only filtering."""
    info = RenderInfo(template_obj)

    info.entities.add("sensor.test")

    expect(info._filter_entities("sensor.test")).to_be(True)
    expect(info._filter_entities("sensor.other")).to_be(False)


@test
async def render_info_filter_lifecycle_domains(
    template_obj: template.Template = Depends(template_obj),
) -> None:
    """Test RenderInfo domain lifecycle filtering."""
    info = RenderInfo(template_obj)

    info.domains_lifecycle.add("sensor")

    expect(info._filter_lifecycle_domains("sensor.test")).to_be(True)
    expect(info._filter_lifecycle_domains("light.test")).to_be(False)


@test
async def render_info_freeze_static(
    template_obj: template.Template = Depends(template_obj),
) -> None:
    """Test RenderInfo static freezing."""
    info = RenderInfo(template_obj)

    info.domains.add("sensor")
    info.entities.add("sensor.test")
    info.all_states = True

    info._freeze_static()

    expect(info.is_static).to_be(True)
    expect(info.all_states).to_be(False)
    expect(isinstance(info.domains, frozenset)).to_be(True)
    expect(isinstance(info.entities, frozenset)).to_be(True)


@test
async def render_info_freeze(
    template_obj: template.Template = Depends(template_obj),
) -> None:
    """Test RenderInfo freezing with rate limits."""
    info = RenderInfo(template_obj)

    # Test all_states rate limit
    info.all_states = True
    info._freeze()
    expect(info.rate_limit).to_equal(ALL_STATES_RATE_LIMIT)

    # Test domain rate limit
    info = RenderInfo(template_obj)
    info.domains.add("sensor")
    info._freeze()
    expect(info.rate_limit).to_equal(DOMAIN_STATES_RATE_LIMIT)

    # Test exception rate limit
    info = RenderInfo(template_obj)
    info.exception = TemplateError("Test")
    info._freeze()
    expect(info.rate_limit).to_equal(ALL_STATES_RATE_LIMIT)


@test
async def render_info_freeze_filters(
    template_obj: template.Template = Depends(template_obj),
) -> None:
    """Test RenderInfo filter assignment during freeze."""

    # Test lifecycle filter assignment
    info = RenderInfo(template_obj)
    info.domains_lifecycle.add("sensor")
    info._freeze()
    expect(info.filter_lifecycle == info._filter_lifecycle_domains).to_be(True)

    # Test no lifecycle domains
    info = RenderInfo(template_obj)
    info._freeze()
    expect(info.filter_lifecycle is _false).to_be(True)

    # Test domain and entity filter
    info = RenderInfo(template_obj)
    info.domains.add("sensor")
    info._freeze()
    expect(info.filter == info._filter_domains_and_entities).to_be(True)

    # Test entity-only filter
    info = RenderInfo(template_obj)
    info.entities.add("sensor.test")
    info._freeze()
    expect(info.filter == info._filter_entities).to_be(True)

    # Test no domains or entities
    info = RenderInfo(template_obj)
    info._freeze()
    expect(info.filter is _false).to_be(True)


@test
async def render_info_context_var(
    template_obj: template.Template = Depends(template_obj),
) -> None:
    """Test render_info_cv context variable."""
    # Should start as None
    expect(render_info_cv.get()).to_be(None)

    # Test setting and getting
    info = RenderInfo(template_obj)
    render_info_cv.set(info)
    expect(render_info_cv.get() is info).to_be(True)

    # Reset for other tests
    render_info_cv.set(None)
    expect(render_info_cv.get()).to_be(None)
