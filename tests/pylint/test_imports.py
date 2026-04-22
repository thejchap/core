"""Tests for pylint hass_imports plugin."""

from __future__ import annotations

import astroid
from pylint.checkers import BaseChecker
import pylint.testutils
from pylint.testutils.unittest_linter import UnittestLinter
from tryke import Depends, fixture, test

from . import assert_adds_messages, assert_no_messages
from .fixtures import imports_checker, linter


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test.cases(
    test.case(
        "absolute_const",
        module_name="homeassistant.components.pylint_test.sensor",
        import_from="homeassistant.const",
        import_what="CONSTANT",
    ),
    test.case(
        "sibling_component",
        module_name="homeassistant.components.pylint_test.sensor",
        import_from="homeassistant.components.pylint_testing",
        import_what="CONSTANT",
    ),
    test.case(
        "relative_dot_const",
        module_name="homeassistant.components.pylint_test.sensor",
        import_from=".const",
        import_what="CONSTANT",
    ),
    test.case(
        "relative_dot_constant",
        module_name="homeassistant.components.pylint_test.sensor",
        import_from=".",
        import_what="CONSTANT",
    ),
    test.case(
        "relative_dotdot_pylint_test",
        module_name="homeassistant.components.pylint_test.sensor",
        import_from="..",
        import_what="pylint_test",
    ),
    test.case(
        "api_hub_absolute_const",
        module_name="homeassistant.components.pylint_test.api.hub",
        import_from="homeassistant.const",
        import_what="CONSTANT",
    ),
    test.case(
        "api_hub_relative_dotdot_const",
        module_name="homeassistant.components.pylint_test.api.hub",
        import_from="..const",
        import_what="CONSTANT",
    ),
    test.case(
        "api_hub_relative_dotdot",
        module_name="homeassistant.components.pylint_test.api.hub",
        import_from="..",
        import_what="CONSTANT",
    ),
    test.case(
        "api_hub_relative_triple_dot",
        module_name="homeassistant.components.pylint_test.api.hub",
        import_from="...",
        import_what="pylint_test",
    ),
    test.case(
        "tests_api_hub_dotdot_const",
        module_name="tests.components.pylint_test.api.hub",
        import_from="..const",
        import_what="CONSTANT",
    ),
)
def good_import(
    module_name: str,
    import_from: str,
    import_what: str,
    linter: UnittestLinter = Depends(linter),
    imports_checker: BaseChecker = Depends(imports_checker),
) -> None:
    """Ensure good imports pass through ok."""
    import_node = astroid.extract_node(
        f"from {import_from} import {import_what} #@",
        module_name,
    )
    imports_checker.visit_module(import_node.parent)

    with assert_no_messages(linter):
        imports_checker.visit_importfrom(import_node)


@test.cases(
    test.case(
        "sensor_pylint_test_const_relative",
        module_name="homeassistant.components.pylint_test.sensor",
        import_from="homeassistant.components.pylint_test.const",
        import_what="CONSTANT",
        error_code="hass-relative-import",
    ),
    test.case(
        "sensor_dotdot_const",
        module_name="homeassistant.components.pylint_test.sensor",
        import_from="..const",
        import_what="CONSTANT",
        error_code="hass-absolute-import",
    ),
    test.case(
        "sensor_tripledot_const",
        module_name="homeassistant.components.pylint_test.sensor",
        import_from="...const",
        import_what="CONSTANT",
        error_code="hass-absolute-import",
    ),
    test.case(
        "api_hub_pylint_test_api_const_relative",
        module_name="homeassistant.components.pylint_test.api.hub",
        import_from="homeassistant.components.pylint_test.api.const",
        import_what="CONSTANT",
        error_code="hass-relative-import",
    ),
    test.case(
        "api_hub_tripledot_const",
        module_name="homeassistant.components.pylint_test.api.hub",
        import_from="...const",
        import_what="CONSTANT",
        error_code="hass-absolute-import",
    ),
    test.case(
        "api_hub_components_pylint_test",
        module_name="homeassistant.components.pylint_test.api.hub",
        import_from="homeassistant.components",
        import_what="pylint_test",
        error_code="hass-relative-import",
    ),
    test.case(
        "api_hub_pylint_test_const_relative",
        module_name="homeassistant.components.pylint_test.api.hub",
        import_from="homeassistant.components.pylint_test.const",
        import_what="CONSTANT",
        error_code="hass-relative-import",
    ),
    test.case(
        "tests_api_hub_pylint_test_const",
        module_name="tests.components.pylint_test.api.hub",
        import_from="tests.components.pylint_test.const",
        import_what="CONSTANT",
        error_code="hass-relative-import",
    ),
    test.case(
        "tests_api_hub_tripledot_const",
        module_name="tests.components.pylint_test.api.hub",
        import_from="...const",
        import_what="CONSTANT",
        error_code="hass-absolute-import",
    ),
)
def bad_import(
    module_name: str,
    import_from: str,
    import_what: str,
    error_code: str,
    linter: UnittestLinter = Depends(linter),
    imports_checker: BaseChecker = Depends(imports_checker),
) -> None:
    """Ensure bad imports are rejected."""
    import_node = astroid.extract_node(
        f"from {import_from} import {import_what} #@",
        module_name,
    )
    imports_checker.visit_module(import_node.parent)

    with assert_adds_messages(
        linter,
        pylint.testutils.MessageTest(
            msg_id=error_code,
            node=import_node,
            args=None,
            line=1,
            col_offset=0,
            end_line=1,
            end_col_offset=len(import_from) + len(import_what) + 13,
        ),
    ):
        imports_checker.visit_importfrom(import_node)


@test.cases(
    test.case(
        "from_components_climate",
        import_node="from homeassistant.components import climate",
        module_name="homeassistant.components.pylint_test.climate",
    ),
    test.case(
        "from_climate_entity_feature",
        import_node="from homeassistant.components.climate import ClimateEntityFeature",
        module_name="homeassistant.components.pylint_test.climate",
    ),
    test.case(
        "tests_from_pylint_test_const",
        import_node="from homeassistant.components.pylint_test import const",
        module_name="tests.components.pylint_test.climate",
    ),
    test.case(
        "tests_from_pylint_test_const_import_constant",
        import_node="from homeassistant.components.pylint_test.const import CONSTANT",
        module_name="tests.components.pylint_test.climate",
    ),
    test.case(
        "tests_import_pylint_test_const_as_climate",
        import_node="import homeassistant.components.pylint_test.const as climate",
        module_name="tests.components.pylint_test.climate",
    ),
)
def good_root_import(
    import_node: str,
    module_name: str,
    linter: UnittestLinter = Depends(linter),
    imports_checker: BaseChecker = Depends(imports_checker),
) -> None:
    """Ensure bad root imports are rejected."""
    node = astroid.extract_node(
        f"{import_node} #@",
        module_name,
    )
    imports_checker.visit_module(node.parent)

    with assert_no_messages(linter):
        if import_node.startswith("import"):
            imports_checker.visit_import(node)
        if import_node.startswith("from"):
            imports_checker.visit_importfrom(node)


@test.cases(
    test.case(
        "import_climate_const_as_climate",
        import_node="import homeassistant.components.climate.const as climate",
        module_name="homeassistant.components.pylint_test.climate",
    ),
    test.case(
        "from_climate_import_const",
        import_node="from homeassistant.components.climate import const",
        module_name="homeassistant.components.pylint_test.climate",
    ),
    test.case(
        "from_climate_const_import_feature",
        import_node="from homeassistant.components.climate.const import ClimateEntityFeature",
        module_name="homeassistant.components.pylint_test.climate",
    ),
    test.case(
        "from_climate_entity_import_feature",
        import_node="from homeassistant.components.climate.entity import ClimateEntityFeature",
        module_name="homeassistant.components.pylint_test.climate",
    ),
    test.case(
        "tests_from_climate_import_const",
        import_node="from homeassistant.components.climate import const",
        module_name="tests.components.pylint_test.climate",
    ),
    test.case(
        "tests_from_climate_const_import_constant",
        import_node="from homeassistant.components.climate.const import CONSTANT",
        module_name="tests.components.pylint_test.climate",
    ),
    test.case(
        "tests_import_climate_const_as_climate",
        import_node="import homeassistant.components.climate.const as climate",
        module_name="tests.components.pylint_test.climate",
    ),
    test.case(
        "tests_import_climate_entity_as_climate",
        import_node="import homeassistant.components.climate.entity as climate",
        module_name="tests.components.pylint_test.climate",
    ),
)
def bad_root_import(
    import_node: str,
    module_name: str,
    linter: UnittestLinter = Depends(linter),
    imports_checker: BaseChecker = Depends(imports_checker),
) -> None:
    """Ensure bad root imports are rejected."""
    node = astroid.extract_node(
        f"{import_node} #@",
        module_name,
    )
    imports_checker.visit_module(node.parent)

    with assert_adds_messages(
        linter,
        pylint.testutils.MessageTest(
            msg_id="hass-component-root-import",
            node=node,
            args=None,
            line=1,
            col_offset=0,
            end_line=1,
            end_col_offset=len(import_node),
        ),
    ):
        if import_node.startswith("import"):
            imports_checker.visit_import(node)
        if import_node.startswith("from"):
            imports_checker.visit_importfrom(node)


@test.cases(
    test.case(
        "issue_registry_async_get",
        import_node="from homeassistant.helpers.issue_registry import async_get",
        module_name="tests.components.pylint_test.climate",
        expected_args=(
            "async_get",
            "homeassistant.helpers.issue_registry",
            "ir",
            "ir",
            "async_get",
        ),
    ),
    test.case(
        "issue_registry_async_get_alias",
        import_node="from homeassistant.helpers.issue_registry import async_get as async_get_issue_registry",
        module_name="tests.components.pylint_test.climate",
        expected_args=(
            "async_get",
            "homeassistant.helpers.issue_registry",
            "ir",
            "ir",
            "async_get",
        ),
    ),
)
def bad_namespace_import(
    import_node: str,
    module_name: str,
    expected_args: tuple[str, ...],
    linter: UnittestLinter = Depends(linter),
    imports_checker: BaseChecker = Depends(imports_checker),
) -> None:
    """Ensure bad namespace imports are rejected."""
    node = astroid.extract_node(
        f"{import_node} #@",
        module_name,
    )
    imports_checker.visit_module(node.parent)

    with assert_adds_messages(
        linter,
        pylint.testutils.MessageTest(
            msg_id="hass-helper-namespace-import",
            node=node,
            args=expected_args,
            line=1,
            col_offset=0,
            end_line=1,
            end_col_offset=len(import_node),
        ),
    ):
        imports_checker.visit_importfrom(node)


@test.cases(
    test.case(
        "with_alias",
        module_name="homeassistant.components.pylint_test.sensor",
        import_string="from homeassistant.components.other import DOMAIN as OTHER_DOMAIN",
        end_col_offset=-1,
    ),
    test.case(
        "no_alias",
        module_name="homeassistant.components.pylint_test.sensor",
        import_string="from homeassistant.components.other import DOMAIN",
        end_col_offset=49,
    ),
)
def domain_alias(
    module_name: str,
    import_string: str,
    end_col_offset: int,
    linter: UnittestLinter = Depends(linter),
    imports_checker: BaseChecker = Depends(imports_checker),
) -> None:
    """Ensure good imports pass through ok."""
    import_node = astroid.extract_node(
        f"{import_string}  #@",
        module_name,
    )
    imports_checker.visit_module(import_node.parent)

    expected_messages = []
    if end_col_offset > 0:
        expected_messages.append(
            pylint.testutils.MessageTest(
                msg_id="hass-import-constant-alias",
                node=import_node,
                args=("DOMAIN", "DOMAIN", "OTHER_DOMAIN"),
                line=1,
                col_offset=0,
                end_line=1,
                end_col_offset=end_col_offset,
            )
        )

    with assert_adds_messages(linter, *expected_messages):
        if import_string.startswith("import"):
            imports_checker.visit_import(import_node)
        else:
            imports_checker.visit_importfrom(import_node)
