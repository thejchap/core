"""Tests for pylint hass_enforce_class_module plugin."""

from __future__ import annotations

import astroid
from pylint.checkers import BaseChecker
from pylint.interfaces import UNDEFINED
from pylint.testutils import MessageTest
from pylint.testutils.unittest_linter import UnittestLinter
from pylint.utils.ast_walker import ASTWalker
from tryke import Depends, fixture, test

from . import assert_adds_messages, assert_no_messages
from .fixtures import enforce_class_module_checker, linter

_SIMPLE_CODE = """
    class DataUpdateCoordinator:
        pass

    class TestCoordinator(DataUpdateCoordinator):
        pass
    """

_NESTED_CODE = """
    class DataUpdateCoordinator:
        pass

    class TestCoordinator(DataUpdateCoordinator):
        pass

    class TestCoordinator2(TestCoordinator):
        pass
    """


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test.cases(
    test.case(
        "simple_coordinator_module",
        code=_SIMPLE_CODE,
        path="homeassistant.components.pylint_test.coordinator",
    ),
    test.case(
        "simple_my_coordinator_submodule",
        code=_SIMPLE_CODE,
        path="homeassistant.components.pylint_test.coordinator.my_coordinator",
    ),
    test.case(
        "nested_coordinator_module",
        code=_NESTED_CODE,
        path="homeassistant.components.pylint_test.coordinator",
    ),
    test.case(
        "nested_my_coordinator_submodule",
        code=_NESTED_CODE,
        path="homeassistant.components.pylint_test.coordinator.my_coordinator",
    ),
)
def enforce_class_module_good(
    code: str,
    path: str,
    linter: UnittestLinter = Depends(linter),
    enforce_class_module_checker: BaseChecker = Depends(enforce_class_module_checker),
) -> None:
    """Good test cases."""
    root_node = astroid.parse(code, path)
    walker = ASTWalker(linter)
    walker.add_checker(enforce_class_module_checker)

    with assert_no_messages(linter):
        walker.walk(root_node)


@test.cases(
    test.case("sensor", path="homeassistant.components.sensor"),
    test.case("sensor_entity", path="homeassistant.components.sensor.entity"),
    test.case("pylint_test_sensor", path="homeassistant.components.pylint_test.sensor"),
    test.case(
        "pylint_test_sensor_entity",
        path="homeassistant.components.pylint_test.sensor.entity",
    ),
)
def enforce_class_platform_good(
    path: str,
    linter: UnittestLinter = Depends(linter),
    enforce_class_module_checker: BaseChecker = Depends(enforce_class_module_checker),
) -> None:
    """Good test cases."""
    code = """
    class SensorEntity:
        pass

    class CustomSensorEntity(SensorEntity):
        pass

    class CoordinatorEntity:
        pass

    class CustomCoordinatorSensorEntity(CoordinatorEntity, SensorEntity):
        pass
    """
    root_node = astroid.parse(code, path)
    walker = ASTWalker(linter)
    walker.add_checker(enforce_class_module_checker)

    with assert_no_messages(linter):
        walker.walk(root_node)


@test.cases(
    test.case("pylint_test", path="homeassistant.components.pylint_test"),
    test.case(
        "pylint_test_my_coordinator",
        path="homeassistant.components.pylint_test.my_coordinator",
    ),
    test.case(
        "pylint_test_coordinator_other",
        path="homeassistant.components.pylint_test.coordinator_other",
    ),
    test.case(
        "pylint_test_sensor",
        path="homeassistant.components.pylint_test.sensor",
    ),
)
def enforce_class_module_bad_simple(
    path: str,
    linter: UnittestLinter = Depends(linter),
    enforce_class_module_checker: BaseChecker = Depends(enforce_class_module_checker),
) -> None:
    """Bad test case with coordinator extending directly."""
    root_node = astroid.parse(
        """
    class DataUpdateCoordinator:
        pass

    class TestCoordinator(DataUpdateCoordinator):
        pass

    class CoordinatorEntity:
        pass

    class CustomCoordinatorSensorEntity(CoordinatorEntity):
        pass
    """,
        path,
    )
    walker = ASTWalker(linter)
    walker.add_checker(enforce_class_module_checker)

    with assert_adds_messages(
        linter,
        MessageTest(
            msg_id="hass-enforce-class-module",
            line=5,
            node=root_node.body[1],
            args=("DataUpdateCoordinator", "coordinator"),
            confidence=UNDEFINED,
            col_offset=0,
            end_line=5,
            end_col_offset=21,
        ),
        MessageTest(
            msg_id="hass-enforce-class-module",
            line=11,
            node=root_node.body[3],
            args=("CoordinatorEntity", "entity"),
            confidence=UNDEFINED,
            col_offset=0,
            end_line=11,
            end_col_offset=35,
        ),
    ):
        walker.walk(root_node)


@test.cases(
    test.case("pylint_test", path="homeassistant.components.pylint_test"),
    test.case(
        "pylint_test_my_coordinator",
        path="homeassistant.components.pylint_test.my_coordinator",
    ),
    test.case(
        "pylint_test_coordinator_other",
        path="homeassistant.components.pylint_test.coordinator_other",
    ),
    test.case(
        "pylint_test_sensor",
        path="homeassistant.components.pylint_test.sensor",
    ),
)
def enforce_class_module_bad_nested(
    path: str,
    linter: UnittestLinter = Depends(linter),
    enforce_class_module_checker: BaseChecker = Depends(enforce_class_module_checker),
) -> None:
    """Bad test case with nested coordinators."""
    root_node = astroid.parse(
        """
    class DataUpdateCoordinator:
        pass

    class TestCoordinator(DataUpdateCoordinator):
        pass

    class NopeCoordinator(TestCoordinator):
        pass
    """,
        path,
    )
    walker = ASTWalker(linter)
    walker.add_checker(enforce_class_module_checker)

    with assert_adds_messages(
        linter,
        MessageTest(
            msg_id="hass-enforce-class-module",
            line=5,
            node=root_node.body[1],
            args=("DataUpdateCoordinator", "coordinator"),
            confidence=UNDEFINED,
            col_offset=0,
            end_line=5,
            end_col_offset=21,
        ),
        MessageTest(
            msg_id="hass-enforce-class-module",
            line=8,
            node=root_node.body[2],
            args=("DataUpdateCoordinator", "coordinator"),
            confidence=UNDEFINED,
            col_offset=0,
            end_line=8,
            end_col_offset=21,
        ),
    ):
        walker.walk(root_node)


@test.cases(
    test.case("sensor", path="homeassistant.components.sensor"),
    test.case("sensor_entity", path="homeassistant.components.sensor.entity"),
    test.case(
        "pylint_test_entity", path="homeassistant.components.pylint_test.entity"
    ),
)
def enforce_entity_good(
    path: str,
    linter: UnittestLinter = Depends(linter),
    enforce_class_module_checker: BaseChecker = Depends(enforce_class_module_checker),
) -> None:
    """Good test cases."""
    code = """
    class Entity:
        pass

    class CustomEntity(Entity):
        pass
    """
    root_node = astroid.parse(code, path)
    walker = ASTWalker(linter)
    walker.add_checker(enforce_class_module_checker)

    with assert_no_messages(linter):
        walker.walk(root_node)


@test.cases(
    test.case("pylint_test", path="homeassistant.components.pylint_test"),
    test.case(
        "pylint_test_select", path="homeassistant.components.pylint_test.select"
    ),
    test.case(
        "pylint_test_select_entity",
        path="homeassistant.components.pylint_test.select.entity",
    ),
)
def enforce_entity_bad(
    path: str,
    linter: UnittestLinter = Depends(linter),
    enforce_class_module_checker: BaseChecker = Depends(enforce_class_module_checker),
) -> None:
    """Good test cases."""
    code = """
    class Entity:
        pass

    class CustomEntity(Entity):
        pass
    """
    root_node = astroid.parse(code, path)
    walker = ASTWalker(linter)
    walker.add_checker(enforce_class_module_checker)

    with assert_adds_messages(
        linter,
        MessageTest(
            msg_id="hass-enforce-class-module",
            line=5,
            node=root_node.body[1],
            args=("Entity", "entity"),
            confidence=UNDEFINED,
            col_offset=0,
            end_line=5,
            end_col_offset=18,
        ),
    ):
        walker.walk(root_node)
