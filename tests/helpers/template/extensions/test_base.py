"""Test base template extension."""

from __future__ import annotations

from tryke import expect, test

from homeassistant.exceptions import TemplateError
from homeassistant.helpers.template import TemplateEnvironment
from homeassistant.helpers.template.extensions.base import (
    BaseTemplateExtension,
    TemplateFunction,
)


@test
def hass_property_raises_when_hass_is_none() -> None:
    """Test that accessing hass property raises RuntimeError when hass is None."""
    # Create an environment without hass
    env = TemplateEnvironment(None)

    # Create a simple extension
    extension = BaseTemplateExtension(env)

    # Accessing hass property should raise RuntimeError
    expect(lambda: extension.hass).to_raise(
        RuntimeError,
        match=(
            "Home Assistant instance is not available. "
            "This property should only be used in extensions with "
            "functions marked requires_hass=True."
        ),
    )


@test
def requires_hass_functions_not_registered_without_hass() -> None:
    """Test that functions requiring hass are not registered when hass is None."""
    # Create an environment without hass
    env = TemplateEnvironment(None)

    def test_func() -> str:
        return "test"

    # Create extension with a function that requires hass
    extension = BaseTemplateExtension(
        env,
        functions=[
            TemplateFunction(
                "test_func",
                test_func,
                as_global=True,
                requires_hass=True,
            ),
        ],
    )

    # Function should not be registered
    expect("test_func" in env.globals).to_be(False)
    expect(extension is not None).to_be(True)


@test
def requires_hass_false_functions_registered_without_hass() -> None:
    """Test that functions not requiring hass are registered even when hass is None."""
    # Create an environment without hass
    env = TemplateEnvironment(None)

    def test_func() -> str:
        return "test"

    # Create extension with a function that does not require hass
    extension = BaseTemplateExtension(
        env,
        functions=[
            TemplateFunction(
                "test_func",
                test_func,
                as_global=True,
                requires_hass=False,
            ),
        ],
    )

    # Function should be registered
    expect("test_func" in env.globals).to_be(True)
    expect(extension is not None).to_be(True)


@test
def limited_ok_functions_not_registered_in_limited_env() -> None:
    """Test that functions with limited_ok=False raise error in limited env."""
    env = TemplateEnvironment(None, limited=True)

    def allowed_func() -> str:
        return "allowed"

    def restricted_func() -> str:
        return "restricted"

    extension = BaseTemplateExtension(
        env,
        functions=[
            TemplateFunction(
                "allowed_func",
                allowed_func,
                as_global=True,
                limited_ok=True,
            ),
            TemplateFunction(
                "restricted_func",
                restricted_func,
                as_global=True,
                limited_ok=False,
            ),
        ],
    )

    # The allowed function should be registered and work
    expect("allowed_func" in env.globals).to_be(True)
    expect(env.globals["allowed_func"]()).to_equal("allowed")

    # The restricted function should be registered but raise TemplateError
    expect("restricted_func" in env.globals).to_be(True)
    expect(lambda: env.globals["restricted_func"]()).to_raise(
        TemplateError,
        match="Use of 'restricted_func' is not supported in limited templates",
    )

    expect(extension is not None).to_be(True)


@test
def limited_ok_true_functions_registered_in_limited_env() -> None:
    """Test that functions with limited_ok=True are registered in limited env."""
    env = TemplateEnvironment(None, limited=True)

    def test_func() -> str:
        return "test"

    extension = BaseTemplateExtension(
        env,
        functions=[
            TemplateFunction(
                "test_func",
                test_func,
                as_global=True,
                limited_ok=True,
            ),
        ],
    )

    expect("test_func" in env.globals).to_be(True)
    expect(extension is not None).to_be(True)


@test
def function_registered_as_global() -> None:
    """Test that functions can be registered as globals."""
    env = TemplateEnvironment(None)

    def test_func() -> str:
        return "global"

    extension = BaseTemplateExtension(
        env,
        functions=[
            TemplateFunction(
                "test_func",
                test_func,
                as_global=True,
            ),
        ],
    )

    expect("test_func" in env.globals).to_be(True)
    expect(env.globals["test_func"] is test_func).to_be(True)
    expect(extension is not None).to_be(True)


@test
def function_registered_as_filter() -> None:
    """Test that functions can be registered as filters."""
    env = TemplateEnvironment(None)

    def test_filter(value: str) -> str:
        return f"filtered_{value}"

    extension = BaseTemplateExtension(
        env,
        functions=[
            TemplateFunction(
                "test_filter",
                test_filter,
                as_filter=True,
            ),
        ],
    )

    expect("test_filter" in env.filters).to_be(True)
    expect(env.filters["test_filter"] is test_filter).to_be(True)
    expect("test_filter" not in env.globals).to_be(True)
    expect(extension is not None).to_be(True)


@test
def function_registered_as_test() -> None:
    """Test that functions can be registered as tests."""
    env = TemplateEnvironment(None)

    def test_check(value: str) -> bool:
        return value == "test"

    extension = BaseTemplateExtension(
        env,
        functions=[
            TemplateFunction(
                "test_check",
                test_check,
                as_test=True,
            ),
        ],
    )

    expect("test_check" in env.tests).to_be(True)
    expect(env.tests["test_check"] is test_check).to_be(True)
    expect("test_check" not in env.globals).to_be(True)
    expect("test_check" not in env.filters).to_be(True)
    expect(extension is not None).to_be(True)


@test
def function_registered_as_multiple_types() -> None:
    """Test that functions can be registered as multiple types simultaneously."""
    env = TemplateEnvironment(None)

    def multi_func(value: str = "default") -> str:
        return f"multi_{value}"

    extension = BaseTemplateExtension(
        env,
        functions=[
            TemplateFunction(
                "multi_func",
                multi_func,
                as_global=True,
                as_filter=True,
                as_test=True,
            ),
        ],
    )

    expect("multi_func" in env.globals).to_be(True)
    expect(env.globals["multi_func"] is multi_func).to_be(True)
    expect("multi_func" in env.filters).to_be(True)
    expect(env.filters["multi_func"] is multi_func).to_be(True)
    expect("multi_func" in env.tests).to_be(True)
    expect(env.tests["multi_func"] is multi_func).to_be(True)
    expect(extension is not None).to_be(True)


@test
def multiple_functions_registered() -> None:
    """Test that multiple functions can be registered at once."""
    env = TemplateEnvironment(None)

    def func1() -> str:
        return "one"

    def func2() -> str:
        return "two"

    def func3() -> str:
        return "three"

    extension = BaseTemplateExtension(
        env,
        functions=[
            TemplateFunction("func1", func1, as_global=True),
            TemplateFunction("func2", func2, as_filter=True),
            TemplateFunction("func3", func3, as_test=True),
        ],
    )

    expect("func1" in env.globals).to_be(True)
    expect("func2" in env.filters).to_be(True)
    expect("func3" in env.tests).to_be(True)
    expect(extension is not None).to_be(True)
