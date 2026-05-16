"""Tests for pylint hass_enforce_super_call plugin."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from types import ModuleType
from unittest.mock import patch

import astroid
from pylint.checkers import BaseChecker
from pylint.interfaces import INFERENCE
from pylint.testutils import MessageTest
from pylint.testutils.unittest_linter import UnittestLinter
from pylint.utils.ast_walker import ASTWalker
from tryke import Depends, expect, fixture, test

from . import assert_adds_messages, assert_no_messages

BASE_PATH = Path(__file__).parents[2]


def _load_plugin_from_file(module_name: str, file: str) -> ModuleType:
    """Load plugin from file path."""
    spec = spec_from_file_location(
        module_name,
        str(BASE_PATH.joinpath(file)),
    )
    assert spec and spec.loader

    module = module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@fixture
def hass_enforce_super_call() -> ModuleType:
    """Fixture to provide the hass_enforce_super_call plugin module."""
    return _load_plugin_from_file(
        "hass_enforce_super_call",
        "pylint/plugins/hass_enforce_super_call.py",
    )


@fixture
def linter() -> UnittestLinter:
    """Fixture to provide a UnittestLinter."""
    return UnittestLinter()


@fixture
def super_call_checker(
    hass_enforce_super_call: ModuleType = Depends(hass_enforce_super_call),
    linter: UnittestLinter = Depends(linter),
) -> BaseChecker:
    """Fixture to provide a super_call_checker."""
    super_call_checker = hass_enforce_super_call.HassEnforceSuperCallChecker(linter)
    super_call_checker.module = "homeassistant.components.pylint_test"
    return super_call_checker


@test.cases(
    test.case(
        "no_parent",
        code="""
    class Entity:
        async def async_added_to_hass(self) -> None:
            pass
    """,
    ),
    test.case(
        "empty_parent_implementation",
        code="""
    class Entity:
        async def async_added_to_hass(self) -> None:
            \"\"\"Some docstring.\"\"\"

    class Child(Entity):
        async def async_added_to_hass(self) -> None:
            x = 2
        """,
    ),
    test.case(
        "empty_parent_implementation2",
        code="""
    class Entity:
        async def async_added_to_hass(self) -> None:
            \"\"\"Some docstring.\"\"\"
            pass

    class Child(Entity):
        async def async_added_to_hass(self) -> None:
            x = 2
        """,
    ),
    test.case(
        "correct_super_call",
        code="""
    class Entity:
        async def async_added_to_hass(self) -> None:
            x = 2

    class Child(Entity):
        async def async_added_to_hass(self) -> None:
            await super().async_added_to_hass()
        """,
    ),
    test.case(
        "super_call_in_return",
        code="""
    class Entity:
        async def async_added_to_hass(self) -> None:
            x = 2

    class Child(Entity):
        async def async_added_to_hass(self) -> None:
            return await super().async_added_to_hass()
        """,
    ),
    test.case(
        "super_call_not_async",
        code="""
    class Entity:
        def added_to_hass(self) -> None:
            x = 2

    class Child(Entity):
        def added_to_hass(self) -> None:
            super().added_to_hass()
        """,
    ),
    test.case(
        "multiple_inheritance",
        code="""
    class Entity:
        async def async_added_to_hass(self) -> None:
            \"\"\"\"\"\"

    class Coordinator:
        async def async_added_to_hass(self) -> None:
            x = 2

    class Child(Entity, Coordinator):
        async def async_added_to_hass(self) -> None:
            await super().async_added_to_hass()
        """,
    ),
    test.case(
        "not_a_method",
        code="""
        async def async_added_to_hass() -> None:
            x = 2
        """,
    ),
)
def enforce_super_call(
    code: str,
    linter: UnittestLinter = Depends(linter),
    hass_enforce_super_call: ModuleType = Depends(hass_enforce_super_call),
    super_call_checker: BaseChecker = Depends(super_call_checker),
) -> None:
    """Good test cases."""
    root_node = astroid.parse(code, "homeassistant.components.pylint_test")
    walker = ASTWalker(linter)
    walker.add_checker(super_call_checker)

    with (
        patch.object(
            hass_enforce_super_call,
            "METHODS",
            new={"added_to_hass", "async_added_to_hass"},
        ),
        assert_no_messages(linter),
    ):
        walker.walk(root_node)


@test.cases(
    test.case(
        "no_super_call",
        code="""
    class Entity:
        def added_to_hass(self) -> None:
            x = 2

    class Child(Entity):
        def added_to_hass(self) -> None:
            x = 3
    """,
        node_idx=1,
    ),
    test.case(
        "no_super_call_async",
        code="""
    class Entity:
        async def async_added_to_hass(self) -> None:
            x = 2

    class Child(Entity):
        async def async_added_to_hass(self) -> None:
            x = 3
    """,
        node_idx=1,
    ),
    test.case(
        "explicit_call_to_base_implementation",
        code="""
    class Entity:
        async def async_added_to_hass(self) -> None:
            x = 2

    class Child(Entity):
        async def async_added_to_hass(self) -> None:
            await Entity.async_added_to_hass()
    """,
        node_idx=1,
    ),
    test.case(
        "multiple_inheritance",
        code="""
    class Entity:
        async def async_added_to_hass(self) -> None:
            \"\"\"\"\"\"

    class Coordinator:
        async def async_added_to_hass(self) -> None:
            x = 2

    class Child(Entity, Coordinator):
        async def async_added_to_hass(self) -> None:
            x = 3
    """,
        node_idx=2,
    ),
)
def enforce_super_call_bad(
    code: str,
    node_idx: int,
    linter: UnittestLinter = Depends(linter),
    hass_enforce_super_call: ModuleType = Depends(hass_enforce_super_call),
    super_call_checker: BaseChecker = Depends(super_call_checker),
) -> None:
    """Bad test cases."""
    root_node = astroid.parse(code, "homeassistant.components.pylint_test")
    walker = ASTWalker(linter)
    walker.add_checker(super_call_checker)
    node = root_node.body[node_idx].body[0]

    with (
        patch.object(
            hass_enforce_super_call,
            "METHODS",
            new={"added_to_hass", "async_added_to_hass"},
        ),
        assert_adds_messages(
            linter,
            MessageTest(
                msg_id="hass-missing-super-call",
                node=node,
                line=node.lineno,
                args=(node.name,),
                col_offset=node.col_offset,
                end_line=node.position.end_lineno,
                end_col_offset=node.position.end_col_offset,
                confidence=INFERENCE,
            ),
        ),
    ):
        walker.walk(root_node)
