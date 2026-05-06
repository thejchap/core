"""Test script variables."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import TemplateError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.script_variables import ScriptRunVariables, ScriptVariables

from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def static_vars() -> None:
    """Test static vars."""
    orig = {"hello": "world"}
    var = ScriptVariables(orig)
    rendered = var.async_render(None, None)
    expect(rendered is not orig).to_be(True)
    expect(rendered).to_equal(orig)


@test
async def static_vars_run_args() -> None:
    """Test static vars."""
    orig = {"hello": "world"}
    orig_copy = dict(orig)
    var = ScriptVariables(orig)
    rendered = var.async_render(None, {"hello": "override", "run": "var"})
    expect(rendered).to_equal({"hello": "override", "run": "var"})
    # Make sure we don't change original vars
    expect(orig).to_equal(orig_copy)


@test
async def static_vars_simple() -> None:
    """Test static vars."""
    orig = {"hello": "world"}
    var = ScriptVariables(orig)
    rendered = var.async_simple_render({})
    expect(rendered is orig).to_be(True)


@test
async def static_vars_run_args_simple() -> None:
    """Test static vars."""
    orig = {"hello": "world"}
    orig_copy = dict(orig)
    var = ScriptVariables(orig)
    rendered = var.async_simple_render({"hello": "override", "run": "var"})
    expect(rendered is orig).to_be(True)
    # Make sure we don't change original vars
    expect(orig).to_equal(orig_copy)


@test
async def template_vars(hass: HomeAssistant = Depends(hass)) -> None:
    """Test template vars."""
    var = cv.SCRIPT_VARIABLES_SCHEMA({"hello": "{{ 1 + 1 }}"})
    rendered = var.async_render(hass, None)
    expect(rendered).to_equal({"hello": 2})


@test
async def template_vars_run_args(hass: HomeAssistant = Depends(hass)) -> None:
    """Test template vars."""
    var = cv.SCRIPT_VARIABLES_SCHEMA(
        {
            "something": "{{ run_var_ex + 1 }}",
            "something_2": "{{ run_var_ex + 1 }}",
        }
    )
    rendered = var.async_render(
        hass,
        {
            "run_var_ex": 5,
            "something_2": 1,
        },
    )
    expect(rendered).to_equal(
        {
            "run_var_ex": 5,
            "something": 6,
            "something_2": 1,
        }
    )


@test
async def template_vars_simple(hass: HomeAssistant = Depends(hass)) -> None:
    """Test template vars."""
    var = cv.SCRIPT_VARIABLES_SCHEMA({"hello": "{{ 1 + 1 }}"})
    rendered = var.async_simple_render({})
    expect(rendered).to_equal({"hello": 2})


@test
async def template_vars_run_args_simple(hass: HomeAssistant = Depends(hass)) -> None:
    """Test template vars."""
    var = cv.SCRIPT_VARIABLES_SCHEMA(
        {
            "something": "{{ run_var_ex + 1 }}",
            "something_2": "{{ run_var_ex + 1 }}",
        }
    )
    rendered = var.async_simple_render(
        {
            "run_var_ex": 5,
            "something_2": 1,
        }
    )
    expect(rendered).to_equal(
        {
            "something": 6,
            "something_2": 6,
        }
    )


@test
async def template_vars_error(hass: HomeAssistant = Depends(hass)) -> None:
    """Test template vars."""
    var = cv.SCRIPT_VARIABLES_SCHEMA({"hello": "{{ canont.work }}"})
    expect(lambda: var.async_render(hass, None)).to_raise(TemplateError)


@test
async def script_vars_exit_top_level() -> None:
    """Test exiting top level script run variables."""
    script_vars = ScriptRunVariables.create_top_level()
    expect(lambda: script_vars.exit_scope()).to_raise(ValueError)


@test
async def script_vars_delete_var() -> None:
    """Test deleting from script run variables."""
    script_vars = ScriptRunVariables.create_top_level({"x": 1, "y": 2})

    def _del() -> None:
        del script_vars["x"]

    expect(_del).to_raise(TypeError)
    expect(lambda: script_vars.pop("y")).to_raise(TypeError)
    expect(script_vars._full_scope).to_equal({"x": 1, "y": 2})


@test
async def script_vars_scopes() -> None:
    """Test script run variables scopes."""
    script_vars = ScriptRunVariables.create_top_level()
    script_vars["x"] = 1
    script_vars["y"] = 1
    expect(script_vars["x"]).to_equal(1)
    expect(script_vars["y"]).to_equal(1)

    script_vars_2 = script_vars.enter_scope()
    script_vars_2.define_local("x", 2)
    expect(script_vars_2["x"]).to_equal(2)
    expect(script_vars_2["y"]).to_equal(1)

    script_vars_3 = script_vars_2.enter_scope()
    script_vars_3["x"] = 3
    script_vars_3["y"] = 3
    expect(script_vars_3["x"]).to_equal(3)
    expect(script_vars_3["y"]).to_equal(3)

    script_vars_4 = script_vars_3.enter_scope()
    expect(script_vars_4["x"]).to_equal(3)
    expect(script_vars_4["y"]).to_equal(3)

    expect(script_vars_4.exit_scope() is script_vars_3).to_be(True)

    expect(script_vars_3._full_scope).to_equal({"x": 3, "y": 3})
    expect(script_vars_3.local_scope).to_equal({})

    expect(script_vars_3.exit_scope() is script_vars_2).to_be(True)

    expect(script_vars_2._full_scope).to_equal({"x": 3, "y": 3})
    expect(script_vars_2.local_scope).to_equal({"x": 3})

    expect(script_vars_2.exit_scope() is script_vars).to_be(True)

    expect(script_vars._full_scope).to_equal({"x": 1, "y": 3})
    expect(script_vars.local_scope).to_equal({"x": 1, "y": 3})


@test
async def script_vars_parallel() -> None:
    """Test script run variables parallel support."""
    script_vars = ScriptRunVariables.create_top_level({"x": 1, "y": 1, "z": 1})

    script_vars_2a = script_vars.enter_scope(parallel=True)
    script_vars_3a = script_vars_2a.enter_scope()

    script_vars_2b = script_vars.enter_scope(parallel=True)
    script_vars_3b = script_vars_2b.enter_scope()

    script_vars_3a["x"] = "a"
    script_vars_3a.assign_parallel_protected("y", "a")

    script_vars_3b["x"] = "b"
    script_vars_3b.assign_parallel_protected("y", "b")

    expect(script_vars_3a._full_scope).to_equal({"x": "b", "y": "a", "z": 1})
    expect(script_vars_3a.non_parallel_scope).to_equal({"x": "a", "y": "a"})

    expect(script_vars_3b._full_scope).to_equal({"x": "b", "y": "b", "z": 1})
    expect(script_vars_3b.non_parallel_scope).to_equal({"x": "b", "y": "b"})

    expect(script_vars_3a.exit_scope() is script_vars_2a).to_be(True)
    expect(script_vars_2a.exit_scope() is script_vars).to_be(True)
    expect(script_vars_3b.exit_scope() is script_vars_2b).to_be(True)
    expect(script_vars_2b.exit_scope() is script_vars).to_be(True)

    expect(script_vars._full_scope).to_equal({"x": "b", "y": 1, "z": 1})
    expect(script_vars.local_scope).to_equal({"x": "b", "y": 1, "z": 1})
