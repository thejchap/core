"""Tests for pylint hass_enforce_sorted_platforms plugin."""

from __future__ import annotations

import astroid
from pylint.checkers import BaseChecker
from pylint.interfaces import UNDEFINED
from pylint.testutils import MessageTest
from pylint.testutils.unittest_linter import UnittestLinter
from pylint.utils.ast_walker import ASTWalker
from tryke import Depends, fixture, test

from . import assert_adds_messages, assert_no_messages
from .fixtures import enforce_sorted_platforms_checker, linter


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test.cases(
    test.case(
        "one_platform",
        code="""
        PLATFORMS = [Platform.SENSOR]
        """,
    ),
    test.case(
        "multiple_platforms",
        code="""
        PLATFORMS = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.SENSOR]
        """,
    ),
    test.case(
        "typed_on_platform",
        code="""
        PLATFORMS: list[str] = [Platform.SENSOR]
        """,
    ),
    test.case(
        "typed_multiple_platform",
        code="""
        PLATFORMS: list[str] = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.SENSOR]
        """,
    ),
    test.case(
        "private_one_platform",
        code="""
        _PLATFORMS = [Platform.SENSOR]
        """,
    ),
    test.case(
        "private_multiple_platforms",
        code="""
        _PLATFORMS = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.SENSOR]
        """,
    ),
    test.case(
        "private_typed_one_platform",
        code="""
        _PLATFORMS: list[str] = [Platform.SENSOR]
        """,
    ),
    test.case(
        "private_typed_multiple_platforms",
        code="""
        _PLATFORMS: list[str] = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.SENSOR]
        """,
    ),
)
def enforce_sorted_platforms(
    code: str,
    linter: UnittestLinter = Depends(linter),
    enforce_sorted_platforms_checker: BaseChecker = Depends(
        enforce_sorted_platforms_checker
    ),
) -> None:
    """Good test cases."""
    root_node = astroid.parse(code, "homeassistant.components.pylint_test")
    walker = ASTWalker(linter)
    walker.add_checker(enforce_sorted_platforms_checker)

    with assert_no_messages(linter):
        walker.walk(root_node)


@test
def enforce_sorted_platforms_bad(
    linter: UnittestLinter = Depends(linter),
    enforce_sorted_platforms_checker: BaseChecker = Depends(
        enforce_sorted_platforms_checker
    ),
) -> None:
    """Bad test case."""
    assign_node = astroid.extract_node(
        """
    PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON]
    """,
        "homeassistant.components.pylint_test",
    )

    with assert_adds_messages(
        linter,
        MessageTest(
            msg_id="hass-enforce-sorted-platforms",
            line=2,
            node=assign_node,
            args=None,
            confidence=UNDEFINED,
            col_offset=0,
            end_line=2,
            end_col_offset=70,
        ),
    ):
        enforce_sorted_platforms_checker.visit_assign(assign_node)


@test
def enforce_sorted_platforms_bad_typed(
    linter: UnittestLinter = Depends(linter),
    enforce_sorted_platforms_checker: BaseChecker = Depends(
        enforce_sorted_platforms_checker
    ),
) -> None:
    """Bad typed test case."""
    assign_node = astroid.extract_node(
        """
    PLATFORMS: list[str] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON]
    """,
        "homeassistant.components.pylint_test",
    )

    with assert_adds_messages(
        linter,
        MessageTest(
            msg_id="hass-enforce-sorted-platforms",
            line=2,
            node=assign_node,
            args=None,
            confidence=UNDEFINED,
            col_offset=0,
            end_line=2,
            end_col_offset=81,
        ),
    ):
        enforce_sorted_platforms_checker.visit_annassign(assign_node)


@test
def enforce_sorted_private_platforms_bad(
    linter: UnittestLinter = Depends(linter),
    enforce_sorted_platforms_checker: BaseChecker = Depends(
        enforce_sorted_platforms_checker
    ),
) -> None:
    """Bad test case for private _PLATFORMS."""
    assign_node = astroid.extract_node(
        """
    _PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON]
    """,
        "homeassistant.components.pylint_test",
    )

    with assert_adds_messages(
        linter,
        MessageTest(
            msg_id="hass-enforce-sorted-platforms",
            line=2,
            node=assign_node,
            args=None,
            confidence=UNDEFINED,
            col_offset=0,
            end_line=2,
            end_col_offset=71,
        ),
    ):
        enforce_sorted_platforms_checker.visit_assign(assign_node)


@test
def enforce_sorted_private_platforms_bad_typed(
    linter: UnittestLinter = Depends(linter),
    enforce_sorted_platforms_checker: BaseChecker = Depends(
        enforce_sorted_platforms_checker
    ),
) -> None:
    """Bad typed test case for private _PLATFORMS."""
    assign_node = astroid.extract_node(
        """
    _PLATFORMS: list[str] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON]
    """,
        "homeassistant.components.pylint_test",
    )

    with assert_adds_messages(
        linter,
        MessageTest(
            msg_id="hass-enforce-sorted-platforms",
            line=2,
            node=assign_node,
            args=None,
            confidence=UNDEFINED,
            col_offset=0,
            end_line=2,
            end_col_offset=82,
        ),
    ):
        enforce_sorted_platforms_checker.visit_annassign(assign_node)
