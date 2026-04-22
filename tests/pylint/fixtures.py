"""Shared Tryke fixtures for pylint plugin tests.

Mirrors the legacy pytest ``conftest.py`` fixture tree for pylint
tests. Tests that need the checker fixtures import them from here
and wire with ``Depends()``.
"""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from types import ModuleType

from pylint.checkers import BaseChecker
from pylint.testutils.unittest_linter import UnittestLinter
from tryke import Depends, fixture

BASE_PATH = Path(__file__).parents[2]


def _load_plugin_from_file(module_name: str, file: str) -> ModuleType:
    """Load plugin from file path."""
    spec = spec_from_file_location(
        module_name,
        str(BASE_PATH.joinpath(file)),
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load plugin {module_name} from {file}")

    module = module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@fixture
def linter() -> UnittestLinter:
    """Fresh UnittestLinter per test."""
    return UnittestLinter()


@fixture
def hass_enforce_type_hints() -> ModuleType:
    """Load the hass_enforce_type_hints pylint plugin."""
    return _load_plugin_from_file(
        "hass_enforce_type_hints",
        "pylint/plugins/hass_enforce_type_hints.py",
    )


@fixture
def type_hint_checker(
    hass_enforce_type_hints: ModuleType = Depends(hass_enforce_type_hints),
    linter: UnittestLinter = Depends(linter),
) -> BaseChecker:
    """HassTypeHintChecker instance."""
    checker = hass_enforce_type_hints.HassTypeHintChecker(linter)
    checker.module = "homeassistant.components.pylint_test"
    return checker


@fixture
def hass_imports() -> ModuleType:
    """Load the hass_imports pylint plugin."""
    return _load_plugin_from_file(
        "hass_imports",
        "pylint/plugins/hass_imports.py",
    )


@fixture
def imports_checker(
    hass_imports: ModuleType = Depends(hass_imports),
    linter: UnittestLinter = Depends(linter),
) -> BaseChecker:
    """HassImportsFormatChecker instance."""
    checker = hass_imports.HassImportsFormatChecker(linter)
    checker.module = "homeassistant.components.pylint_test"
    return checker


@fixture
def hass_enforce_super_call() -> ModuleType:
    """Load the hass_enforce_super_call pylint plugin."""
    return _load_plugin_from_file(
        "hass_enforce_super_call",
        "pylint/plugins/hass_enforce_super_call.py",
    )


@fixture
def super_call_checker(
    hass_enforce_super_call: ModuleType = Depends(hass_enforce_super_call),
    linter: UnittestLinter = Depends(linter),
) -> BaseChecker:
    """HassEnforceSuperCallChecker instance."""
    checker = hass_enforce_super_call.HassEnforceSuperCallChecker(linter)
    checker.module = "homeassistant.components.pylint_test"
    return checker


@fixture
def hass_enforce_sorted_platforms() -> ModuleType:
    """Load the hass_enforce_sorted_platforms pylint plugin."""
    return _load_plugin_from_file(
        "hass_enforce_sorted_platforms",
        "pylint/plugins/hass_enforce_sorted_platforms.py",
    )


@fixture
def enforce_sorted_platforms_checker(
    hass_enforce_sorted_platforms: ModuleType = Depends(hass_enforce_sorted_platforms),
    linter: UnittestLinter = Depends(linter),
) -> BaseChecker:
    """HassEnforceSortedPlatformsChecker instance."""
    checker = hass_enforce_sorted_platforms.HassEnforceSortedPlatformsChecker(linter)
    checker.module = "homeassistant.components.pylint_test"
    return checker


@fixture
def hass_enforce_class_module() -> ModuleType:
    """Load the hass_enforce_class_module pylint plugin."""
    return _load_plugin_from_file(
        "hass_enforce_class_module",
        "pylint/plugins/hass_enforce_class_module.py",
    )


@fixture
def enforce_class_module_checker(
    hass_enforce_class_module: ModuleType = Depends(hass_enforce_class_module),
    linter: UnittestLinter = Depends(linter),
) -> BaseChecker:
    """HassEnforceClassModule instance."""
    checker = hass_enforce_class_module.HassEnforceClassModule(linter)
    checker.module = "homeassistant.components.pylint_test"
    return checker


@fixture
def hass_decorator() -> ModuleType:
    """Load the hass_decorator pylint plugin."""
    return _load_plugin_from_file(
        "hass_imports",
        "pylint/plugins/hass_decorator.py",
    )


@fixture
def decorator_checker(
    hass_decorator: ModuleType = Depends(hass_decorator),
    linter: UnittestLinter = Depends(linter),
) -> BaseChecker:
    """HassDecoratorChecker instance."""
    checker = hass_decorator.HassDecoratorChecker(linter)
    checker.module = "homeassistant.components.pylint_test"
    return checker


@fixture
def hass_enforce_greek_micro_char() -> ModuleType:
    """Load the hass_enforce_greek_micro_char pylint plugin."""
    return _load_plugin_from_file(
        "hass_enforce_greek_micro_char",
        "pylint/plugins/hass_enforce_greek_micro_char.py",
    )


@fixture
def enforce_greek_micro_char_checker(
    hass_enforce_greek_micro_char: ModuleType = Depends(hass_enforce_greek_micro_char),
    linter: UnittestLinter = Depends(linter),
) -> BaseChecker:
    """HassEnforceGreekMicroCharChecker instance."""
    checker = hass_enforce_greek_micro_char.HassEnforceGreekMicroCharChecker(linter)
    checker.module = "homeassistant.components.pylint_test"
    return checker
