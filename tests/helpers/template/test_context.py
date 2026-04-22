"""Test template context management for Home Assistant."""

from __future__ import annotations

import jinja2
from tryke import expect, test

from homeassistant.helpers.template.context import (
    TemplateContextManager,
    render_with_context,
    template_context_manager,
    template_cv,
)


@test
def template_context_manager_basic() -> None:
    """Test TemplateContextManager functionality."""
    cm = TemplateContextManager()

    # Test setting template
    cm.set_template("{{ test }}", "rendering")
    expect(template_cv.get()).to_equal(("{{ test }}", "rendering"))

    # Test context manager exit
    cm.__exit__(None, None, None)
    expect(template_cv.get()).to_be(None)


@test
def template_context_manager_context() -> None:
    """Test TemplateContextManager as context manager."""
    cm = TemplateContextManager()

    with cm:
        cm.set_template("{{ test }}", "parsing")
        expect(template_cv.get()).to_equal(("{{ test }}", "parsing"))

    # Should be cleared after exit
    expect(template_cv.get()).to_be(None)


@test
def global_template_context_manager() -> None:
    """Test global template context manager instance."""
    # Should be an instance of TemplateContextManager
    expect(isinstance(template_context_manager, TemplateContextManager)).to_be(True)

    # Test it works like any other context manager
    template_context_manager.set_template("{{ global_test }}", "testing")
    expect(template_cv.get()).to_equal(("{{ global_test }}", "testing"))

    template_context_manager.__exit__(None, None, None)
    expect(template_cv.get()).to_be(None)


@test
def render_with_context_basic() -> None:
    """Test render_with_context function."""
    # Create a simple template
    env = jinja2.Environment()
    template_obj = env.from_string("Hello {{ name }}!")

    # Test rendering with context tracking
    result = render_with_context("Hello {{ name }}!", template_obj, name="World")
    expect(result).to_equal("Hello World!")

    # Context should be cleared after rendering
    expect(template_cv.get()).to_be(None)


@test
def render_with_context_sets_context() -> None:
    """Test that render_with_context properly sets template context."""
    # Create a template that we can use to check context
    jinja2.Environment()

    # We'll use a custom template class to capture context during rendering
    context_during_render: list[tuple[str, str] | None] = []

    class MockTemplate:
        def render(self, **kwargs: object) -> str:
            # Capture the context during rendering
            context_during_render.append(template_cv.get())
            return "rendered"

    mock_template = MockTemplate()

    # Render with context
    result = render_with_context("{{ test_template }}", mock_template, test=True)

    expect(result).to_equal("rendered")
    # Should have captured the context during rendering
    expect(len(context_during_render)).to_equal(1)
    expect(context_during_render[0]).to_equal(("{{ test_template }}", "rendering"))
    # Context should be cleared after rendering
    expect(template_cv.get()).to_be(None)
