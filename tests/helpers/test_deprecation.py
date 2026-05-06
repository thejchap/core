"""Test deprecation helpers."""

from enum import StrEnum
import logging
import sys
from typing import Any
from unittest.mock import MagicMock, Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.helpers.deprecation import (
    DeprecatedAlias,
    DeprecatedConstant,
    DeprecatedConstantEnum,
    EnumWithDeprecatedMembers,
    check_if_deprecated_constant,
    deprecated_class,
    deprecated_function,
    deprecated_hass_argument,
    deprecated_substitute,
    dir_with_deprecated_constants,
    get_deprecated,
)
from homeassistant.helpers.frame import MissingIntegrationFrame

from tests.common import MockModule, extract_stack_to_frame, mock_integration
from tests.hass_fixtures import LogCapture, caplog, hass


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


class MockBaseClassDeprecatedProperty:
    """Mock base class for deprecated testing."""

    @property
    @deprecated_substitute("old_property")
    def new_property(self):
        """Test property to fetch."""
        return "default_new"


@test
@patch("logging.getLogger")
def deprecated_substitute_old_class(mock_get_logger) -> None:
    """Test deprecated class object."""

    class MockDeprecatedClass(MockBaseClassDeprecatedProperty):
        """Mock deprecated class object."""

        @property
        def old_property(self):
            """Test property to fetch."""
            return "old"

    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger

    mock_object = MockDeprecatedClass()
    expect(mock_object.new_property).to_equal("old")
    expect(mock_logger.warning.called).to_be_truthy()
    expect(len(mock_logger.warning.mock_calls)).to_equal(1)


@test
@patch("logging.getLogger")
def deprecated_substitute_default_class(mock_get_logger) -> None:
    """Test deprecated class object."""

    class MockDefaultClass(MockBaseClassDeprecatedProperty):
        """Mock updated class object."""

    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger

    mock_object = MockDefaultClass()
    expect(mock_object.new_property).to_equal("default_new")
    expect(mock_logger.warning.called).to_be_falsy()


@test
@patch("logging.getLogger")
def deprecated_substitute_new_class(mock_get_logger) -> None:
    """Test deprecated class object."""

    class MockUpdatedClass(MockBaseClassDeprecatedProperty):
        """Mock updated class object."""

        @property
        def new_property(self):
            """Test property to fetch."""
            return "new"

    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger

    mock_object = MockUpdatedClass()
    expect(mock_object.new_property).to_equal("new")
    expect(mock_logger.warning.called).to_be_falsy()


@test
@patch("logging.getLogger")
def config_get_deprecated_old(mock_get_logger) -> None:
    """Test deprecated config."""
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger

    config = {"old_name": True}
    expect(get_deprecated(config, "new_name", "old_name")).to_be(True)
    expect(mock_logger.warning.called).to_be_truthy()
    expect(len(mock_logger.warning.mock_calls)).to_equal(1)


@test
@patch("logging.getLogger")
def config_get_deprecated_new(mock_get_logger) -> None:
    """Test deprecated config."""
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger

    config = {"new_name": True}
    expect(get_deprecated(config, "new_name", "old_name")).to_be(True)
    expect(mock_logger.warning.called).to_be_falsy()


@deprecated_class("homeassistant.blah.NewClass")
class MockDeprecatedClass:
    """Mock class for deprecated testing."""


@test
@patch("logging.getLogger")
def deprecated_class_test(mock_get_logger) -> None:
    """Test deprecated class."""
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger

    MockDeprecatedClass()
    expect(mock_logger.warning.called).to_be_truthy()
    expect(len(mock_logger.warning.mock_calls)).to_equal(1)


@test.cases(
    test.case("no_version", breaks_in_ha_version=None, extra_msg=""),
    test.case(
        "with_version",
        breaks_in_ha_version="2099.1",
        extra_msg=" It will be removed in HA Core 2099.1.",
    ),
)
def deprecated_function_test(
    breaks_in_ha_version: str | None,
    extra_msg: str,
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test deprecated_function decorator.

    This tests the behavior when the calling integration is not known.
    """

    @deprecated_function("new_function", breaks_in_ha_version=breaks_in_ha_version)
    def mock_deprecated_function():
        pass

    mock_deprecated_function()
    expect(caplog.text).to_contain(
        "The deprecated function mock_deprecated_function was called."
        f"{extra_msg}"
        " Use new_function instead"
    )


@test.cases(
    test.case("no_version", breaks_in_ha_version=None, extra_msg=""),
    test.case(
        "with_version",
        breaks_in_ha_version="2099.1",
        extra_msg=" It will be removed in HA Core 2099.1.",
    ),
)
def deprecated_function_called_from_built_in_integration(
    breaks_in_ha_version: str | None,
    extra_msg: str,
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test deprecated_function decorator.

    This tests the behavior when the calling integration is built-in.
    """

    @deprecated_function("new_function", breaks_in_ha_version=breaks_in_ha_version)
    def mock_deprecated_function():
        pass

    with (
        patch(
            "homeassistant.helpers.frame.linecache.getline",
            return_value="await session.close()",
        ),
        patch(
            "homeassistant.helpers.frame.get_current_frame",
            return_value=extract_stack_to_frame(
                [
                    Mock(
                        filename="/home/paulus/homeassistant/core.py",
                        lineno="23",
                        line="do_something()",
                    ),
                    Mock(
                        filename="/home/paulus/homeassistant/components/hue/light.py",
                        lineno="23",
                        line="await session.close()",
                    ),
                    Mock(
                        filename="/home/paulus/aiohue/lights.py",
                        lineno="2",
                        line="something()",
                    ),
                ]
            ),
        ),
    ):
        mock_deprecated_function()
    expect(caplog.text).to_contain(
        "The deprecated function mock_deprecated_function was called from hue."
        f"{extra_msg}"
        " Use new_function instead"
    )


@test.cases(
    test.case("no_version", breaks_in_ha_version=None, extra_msg=""),
    test.case(
        "with_version",
        breaks_in_ha_version="2099.1",
        extra_msg=" It will be removed in HA Core 2099.1.",
    ),
)
def deprecated_function_called_from_custom_integration(
    breaks_in_ha_version: str | None,
    extra_msg: str,
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test deprecated_function decorator.

    This tests the behavior when the calling integration is custom.
    """

    mock_integration(hass, MockModule("hue"), built_in=False)

    @deprecated_function("new_function", breaks_in_ha_version=breaks_in_ha_version)
    def mock_deprecated_function():
        pass

    with (
        patch(
            "homeassistant.helpers.frame.linecache.getline",
            return_value="await session.close()",
        ),
        patch(
            "homeassistant.helpers.frame.get_current_frame",
            return_value=extract_stack_to_frame(
                [
                    Mock(
                        filename="/home/paulus/homeassistant/core.py",
                        lineno="23",
                        line="do_something()",
                    ),
                    Mock(
                        filename="/home/paulus/config/custom_components/hue/light.py",
                        lineno="23",
                        line="await session.close()",
                    ),
                    Mock(
                        filename="/home/paulus/aiohue/lights.py",
                        lineno="2",
                        line="something()",
                    ),
                ]
            ),
        ),
    ):
        mock_deprecated_function()
    expect(caplog.text).to_contain(
        "The deprecated function mock_deprecated_function was called from hue."
        f"{extra_msg}"
        " Use new_function instead, please report it to the author of the "
        "'hue' custom integration"
    )


class TestDeprecatedConstantEnum(StrEnum):
    """Test deprecated constant enum."""

    __test__ = False  # prevent test collection of class by pytest

    TEST = "value"


def _get_value(
    obj: DeprecatedConstant
    | DeprecatedConstantEnum
    | DeprecatedAlias
    | tuple[Any, ...],
) -> Any:
    if isinstance(obj, DeprecatedConstant):
        return obj.value

    if isinstance(obj, DeprecatedConstantEnum):
        return obj.enum

    if isinstance(obj, DeprecatedAlias):
        return obj.value

    if len(obj) == 2:
        return obj[0].value

    return obj[0]


_CHECK_CONSTANT_CASES = [
    (
        DeprecatedConstant("value", "NEW_CONSTANT", None),
        ". Use NEW_CONSTANT instead",
        "constant",
    ),
    (
        DeprecatedConstant(1, "NEW_CONSTANT", "2099.1"),
        ". It will be removed in HA Core 2099.1. Use NEW_CONSTANT instead",
        "constant",
    ),
    (
        DeprecatedConstantEnum(TestDeprecatedConstantEnum.TEST, None),
        ". Use TestDeprecatedConstantEnum.TEST instead",
        "constant",
    ),
    (
        DeprecatedConstantEnum(TestDeprecatedConstantEnum.TEST, "2099.1"),
        ". It will be removed in HA Core 2099.1. Use TestDeprecatedConstantEnum.TEST instead",
        "constant",
    ),
    (
        DeprecatedAlias(1, "new_alias", None),
        ". Use new_alias instead",
        "alias",
    ),
    (
        DeprecatedAlias(1, "new_alias", "2099.1"),
        ". It will be removed in HA Core 2099.1. Use new_alias instead",
        "alias",
    ),
]

_CHECK_CONSTANT_MODULE_CASES = [
    ("homeassistant.components.hue.light", ""),
    (
        "config.custom_components.hue.light",
        ", please report it to the author of the 'hue' custom integration",
    ),
]


def _case_label(constant_label: str, module_label: str) -> str:
    return f"{constant_label}_{module_label}"


_CONSTANT_LABELS = [
    "constant_value_no_version",
    "constant_int_with_version",
    "constant_enum_no_version",
    "constant_enum_with_version",
    "alias_no_version",
    "alias_with_version",
]
_MODULE_LABELS = ["builtin", "custom"]


@test.cases(
    test.case(
        "constant_value_no_version_builtin",
        deprecated_constant=_CHECK_CONSTANT_CASES[0][0],
        extra_msg=_CHECK_CONSTANT_CASES[0][1],
        description=_CHECK_CONSTANT_CASES[0][2],
        module_name=_CHECK_CONSTANT_MODULE_CASES[0][0],
        extra_extra_msg=_CHECK_CONSTANT_MODULE_CASES[0][1],
    ),
    test.case(
        "constant_value_no_version_custom",
        deprecated_constant=_CHECK_CONSTANT_CASES[0][0],
        extra_msg=_CHECK_CONSTANT_CASES[0][1],
        description=_CHECK_CONSTANT_CASES[0][2],
        module_name=_CHECK_CONSTANT_MODULE_CASES[1][0],
        extra_extra_msg=_CHECK_CONSTANT_MODULE_CASES[1][1],
    ),
    test.case(
        "constant_int_with_version_builtin",
        deprecated_constant=_CHECK_CONSTANT_CASES[1][0],
        extra_msg=_CHECK_CONSTANT_CASES[1][1],
        description=_CHECK_CONSTANT_CASES[1][2],
        module_name=_CHECK_CONSTANT_MODULE_CASES[0][0],
        extra_extra_msg=_CHECK_CONSTANT_MODULE_CASES[0][1],
    ),
    test.case(
        "constant_int_with_version_custom",
        deprecated_constant=_CHECK_CONSTANT_CASES[1][0],
        extra_msg=_CHECK_CONSTANT_CASES[1][1],
        description=_CHECK_CONSTANT_CASES[1][2],
        module_name=_CHECK_CONSTANT_MODULE_CASES[1][0],
        extra_extra_msg=_CHECK_CONSTANT_MODULE_CASES[1][1],
    ),
    test.case(
        "constant_enum_no_version_builtin",
        deprecated_constant=_CHECK_CONSTANT_CASES[2][0],
        extra_msg=_CHECK_CONSTANT_CASES[2][1],
        description=_CHECK_CONSTANT_CASES[2][2],
        module_name=_CHECK_CONSTANT_MODULE_CASES[0][0],
        extra_extra_msg=_CHECK_CONSTANT_MODULE_CASES[0][1],
    ),
    test.case(
        "constant_enum_no_version_custom",
        deprecated_constant=_CHECK_CONSTANT_CASES[2][0],
        extra_msg=_CHECK_CONSTANT_CASES[2][1],
        description=_CHECK_CONSTANT_CASES[2][2],
        module_name=_CHECK_CONSTANT_MODULE_CASES[1][0],
        extra_extra_msg=_CHECK_CONSTANT_MODULE_CASES[1][1],
    ),
    test.case(
        "constant_enum_with_version_builtin",
        deprecated_constant=_CHECK_CONSTANT_CASES[3][0],
        extra_msg=_CHECK_CONSTANT_CASES[3][1],
        description=_CHECK_CONSTANT_CASES[3][2],
        module_name=_CHECK_CONSTANT_MODULE_CASES[0][0],
        extra_extra_msg=_CHECK_CONSTANT_MODULE_CASES[0][1],
    ),
    test.case(
        "constant_enum_with_version_custom",
        deprecated_constant=_CHECK_CONSTANT_CASES[3][0],
        extra_msg=_CHECK_CONSTANT_CASES[3][1],
        description=_CHECK_CONSTANT_CASES[3][2],
        module_name=_CHECK_CONSTANT_MODULE_CASES[1][0],
        extra_extra_msg=_CHECK_CONSTANT_MODULE_CASES[1][1],
    ),
    test.case(
        "alias_no_version_builtin",
        deprecated_constant=_CHECK_CONSTANT_CASES[4][0],
        extra_msg=_CHECK_CONSTANT_CASES[4][1],
        description=_CHECK_CONSTANT_CASES[4][2],
        module_name=_CHECK_CONSTANT_MODULE_CASES[0][0],
        extra_extra_msg=_CHECK_CONSTANT_MODULE_CASES[0][1],
    ),
    test.case(
        "alias_no_version_custom",
        deprecated_constant=_CHECK_CONSTANT_CASES[4][0],
        extra_msg=_CHECK_CONSTANT_CASES[4][1],
        description=_CHECK_CONSTANT_CASES[4][2],
        module_name=_CHECK_CONSTANT_MODULE_CASES[1][0],
        extra_extra_msg=_CHECK_CONSTANT_MODULE_CASES[1][1],
    ),
    test.case(
        "alias_with_version_builtin",
        deprecated_constant=_CHECK_CONSTANT_CASES[5][0],
        extra_msg=_CHECK_CONSTANT_CASES[5][1],
        description=_CHECK_CONSTANT_CASES[5][2],
        module_name=_CHECK_CONSTANT_MODULE_CASES[0][0],
        extra_extra_msg=_CHECK_CONSTANT_MODULE_CASES[0][1],
    ),
    test.case(
        "alias_with_version_custom",
        deprecated_constant=_CHECK_CONSTANT_CASES[5][0],
        extra_msg=_CHECK_CONSTANT_CASES[5][1],
        description=_CHECK_CONSTANT_CASES[5][2],
        module_name=_CHECK_CONSTANT_MODULE_CASES[1][0],
        extra_extra_msg=_CHECK_CONSTANT_MODULE_CASES[1][1],
    ),
)
def check_if_deprecated_constant_test(
    deprecated_constant: DeprecatedConstant
    | DeprecatedConstantEnum
    | DeprecatedAlias
    | tuple,
    extra_msg: str,
    module_name: str,
    extra_extra_msg: str,
    description: str,
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test check_if_deprecated_constant."""
    module_globals = {
        "__name__": module_name,
        "_DEPRECATED_TEST_CONSTANT": deprecated_constant,
    }
    filename = f"/home/paulus/{module_name.replace('.', '/')}.py"

    # mock sys.modules for homeassistant/helpers/frame.py#get_integration_frame
    with (
        patch.dict(sys.modules, {module_name: Mock(__file__=filename)}),
        patch(
            "homeassistant.helpers.frame.linecache.getline",
            return_value="await session.close()",
        ),
        patch(
            "homeassistant.helpers.frame.get_current_frame",
            return_value=extract_stack_to_frame(
                [
                    Mock(
                        filename="/home/paulus/homeassistant/core.py",
                        lineno="23",
                        line="do_something()",
                    ),
                    Mock(
                        filename=filename,
                        lineno="23",
                        line="await session.close()",
                    ),
                    Mock(
                        filename="/home/paulus/aiohue/lights.py",
                        lineno="2",
                        line="something()",
                    ),
                ]
            ),
        ),
    ):
        value = check_if_deprecated_constant("TEST_CONSTANT", module_globals)
        expect(value).to_equal(_get_value(deprecated_constant))

    record_tuples = [(r.name, r.levelno, r.getMessage()) for r in caplog.records]
    expect(record_tuples).to_contain(
        (
            module_name,
            logging.WARNING,
            f"The deprecated {description} TEST_CONSTANT was used from hue{extra_msg}{extra_extra_msg}",
        )
    )


_NOT_FOUND_CONSTANT_CASES = [
    (
        DeprecatedConstant("value", "NEW_CONSTANT", None),
        ". Use NEW_CONSTANT instead",
        "constant",
    ),
    (
        DeprecatedConstant(1, "NEW_CONSTANT", "2099.1"),
        " which will be removed in HA Core 2099.1. Use NEW_CONSTANT instead",
        "constant",
    ),
    (
        DeprecatedConstantEnum(TestDeprecatedConstantEnum.TEST, None),
        ". Use TestDeprecatedConstantEnum.TEST instead",
        "constant",
    ),
    (
        DeprecatedConstantEnum(TestDeprecatedConstantEnum.TEST, "2099.1"),
        " which will be removed in HA Core 2099.1. Use TestDeprecatedConstantEnum.TEST instead",
        "constant",
    ),
    (
        DeprecatedAlias(1, "new_alias", None),
        ". Use new_alias instead",
        "alias",
    ),
    (
        DeprecatedAlias(1, "new_alias", "2099.1"),
        " which will be removed in HA Core 2099.1. Use new_alias instead",
        "alias",
    ),
]

_NOT_FOUND_MODULE_CASES = [
    "homeassistant.components.hue.light",
    "config.custom_components.hue.light",
]


@test.cases(
    test.case(
        "constant_value_no_version_builtin",
        deprecated_constant=_NOT_FOUND_CONSTANT_CASES[0][0],
        extra_msg=_NOT_FOUND_CONSTANT_CASES[0][1],
        description=_NOT_FOUND_CONSTANT_CASES[0][2],
        module_name=_NOT_FOUND_MODULE_CASES[0],
    ),
    test.case(
        "constant_value_no_version_custom",
        deprecated_constant=_NOT_FOUND_CONSTANT_CASES[0][0],
        extra_msg=_NOT_FOUND_CONSTANT_CASES[0][1],
        description=_NOT_FOUND_CONSTANT_CASES[0][2],
        module_name=_NOT_FOUND_MODULE_CASES[1],
    ),
    test.case(
        "constant_int_with_version_builtin",
        deprecated_constant=_NOT_FOUND_CONSTANT_CASES[1][0],
        extra_msg=_NOT_FOUND_CONSTANT_CASES[1][1],
        description=_NOT_FOUND_CONSTANT_CASES[1][2],
        module_name=_NOT_FOUND_MODULE_CASES[0],
    ),
    test.case(
        "constant_int_with_version_custom",
        deprecated_constant=_NOT_FOUND_CONSTANT_CASES[1][0],
        extra_msg=_NOT_FOUND_CONSTANT_CASES[1][1],
        description=_NOT_FOUND_CONSTANT_CASES[1][2],
        module_name=_NOT_FOUND_MODULE_CASES[1],
    ),
    test.case(
        "constant_enum_no_version_builtin",
        deprecated_constant=_NOT_FOUND_CONSTANT_CASES[2][0],
        extra_msg=_NOT_FOUND_CONSTANT_CASES[2][1],
        description=_NOT_FOUND_CONSTANT_CASES[2][2],
        module_name=_NOT_FOUND_MODULE_CASES[0],
    ),
    test.case(
        "constant_enum_no_version_custom",
        deprecated_constant=_NOT_FOUND_CONSTANT_CASES[2][0],
        extra_msg=_NOT_FOUND_CONSTANT_CASES[2][1],
        description=_NOT_FOUND_CONSTANT_CASES[2][2],
        module_name=_NOT_FOUND_MODULE_CASES[1],
    ),
    test.case(
        "constant_enum_with_version_builtin",
        deprecated_constant=_NOT_FOUND_CONSTANT_CASES[3][0],
        extra_msg=_NOT_FOUND_CONSTANT_CASES[3][1],
        description=_NOT_FOUND_CONSTANT_CASES[3][2],
        module_name=_NOT_FOUND_MODULE_CASES[0],
    ),
    test.case(
        "constant_enum_with_version_custom",
        deprecated_constant=_NOT_FOUND_CONSTANT_CASES[3][0],
        extra_msg=_NOT_FOUND_CONSTANT_CASES[3][1],
        description=_NOT_FOUND_CONSTANT_CASES[3][2],
        module_name=_NOT_FOUND_MODULE_CASES[1],
    ),
    test.case(
        "alias_no_version_builtin",
        deprecated_constant=_NOT_FOUND_CONSTANT_CASES[4][0],
        extra_msg=_NOT_FOUND_CONSTANT_CASES[4][1],
        description=_NOT_FOUND_CONSTANT_CASES[4][2],
        module_name=_NOT_FOUND_MODULE_CASES[0],
    ),
    test.case(
        "alias_no_version_custom",
        deprecated_constant=_NOT_FOUND_CONSTANT_CASES[4][0],
        extra_msg=_NOT_FOUND_CONSTANT_CASES[4][1],
        description=_NOT_FOUND_CONSTANT_CASES[4][2],
        module_name=_NOT_FOUND_MODULE_CASES[1],
    ),
    test.case(
        "alias_with_version_builtin",
        deprecated_constant=_NOT_FOUND_CONSTANT_CASES[5][0],
        extra_msg=_NOT_FOUND_CONSTANT_CASES[5][1],
        description=_NOT_FOUND_CONSTANT_CASES[5][2],
        module_name=_NOT_FOUND_MODULE_CASES[0],
    ),
    test.case(
        "alias_with_version_custom",
        deprecated_constant=_NOT_FOUND_CONSTANT_CASES[5][0],
        extra_msg=_NOT_FOUND_CONSTANT_CASES[5][1],
        description=_NOT_FOUND_CONSTANT_CASES[5][2],
        module_name=_NOT_FOUND_MODULE_CASES[1],
    ),
)
def check_if_deprecated_constant_integration_not_found(
    deprecated_constant: DeprecatedConstant
    | DeprecatedConstantEnum
    | DeprecatedAlias
    | tuple,
    extra_msg: str,
    module_name: str,
    description: str,
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test check_if_deprecated_constant."""
    module_globals = {
        "__name__": module_name,
        "_DEPRECATED_TEST_CONSTANT": deprecated_constant,
    }

    with patch(
        "homeassistant.helpers.frame.get_current_frame",
        side_effect=MissingIntegrationFrame,
    ):
        value = check_if_deprecated_constant("TEST_CONSTANT", module_globals)
        expect(value).to_equal(_get_value(deprecated_constant))

    record_tuples = [(r.name, r.levelno, r.getMessage()) for r in caplog.records]
    expect(record_tuples).not_.to_contain(
        (
            module_name,
            logging.WARNING,
            f"TEST_CONSTANT is a deprecated {description}{extra_msg}",
        )
    )


@test
def check_if_deprecated_constant_invalid(
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test check_if_deprecated_constant error handling.

    Test check_if_deprecated_constant raises an attribute error and creates a log entry
    on an invalid deprecation type.
    """
    module_name = "homeassistant.components.hue.light"
    module_globals = {"__name__": module_name, "_DEPRECATED_TEST_CONSTANT": 1}
    name = "TEST_CONSTANT"

    excepted_msg = (
        f"Value of _DEPRECATED_{name} is an instance of <class 'int'> but an instance "
        "of DeprecatedAlias, DeferredDeprecatedAlias, DeprecatedConstant or "
        "DeprecatedConstantEnum is required"
    )

    expect(lambda: check_if_deprecated_constant(name, module_globals)).to_raise(
        AttributeError, match=excepted_msg
    )

    record_tuples = [(r.name, r.levelno, r.getMessage()) for r in caplog.records]
    expect(record_tuples).to_contain((module_name, logging.DEBUG, excepted_msg))


@test.cases(
    test.case("constant_only", module_globals={"CONSTANT": 1}, expected=["CONSTANT"]),
    test.case(
        "with_deprecated",
        module_globals={"_DEPRECATED_CONSTANT": 1},
        expected=["_DEPRECATED_CONSTANT", "CONSTANT"],
    ),
    test.case(
        "with_deprecated_and_other",
        module_globals={"_DEPRECATED_CONSTANT": 1, "SOMETHING": 2},
        expected=["_DEPRECATED_CONSTANT", "SOMETHING", "CONSTANT"],
    ),
)
def dir_with_deprecated_constants_test(
    module_globals: dict[str, Any], expected: list[str]
) -> None:
    """Test dir() with deprecated constants."""
    expect(dir_with_deprecated_constants([*module_globals.keys()])).to_equal(expected)


@test.cases(
    test.case(
        "builtin", module_name="homeassistant.components.hue.light", extra_extra_msg=""
    ),
    test.case(
        "custom",
        module_name="config.custom_components.hue.light",
        extra_extra_msg=", please report it to the author of the 'hue' custom integration",
    ),
)
def enum_with_deprecated_members(
    module_name: str,
    extra_extra_msg: str,
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test EnumWithDeprecatedMembers."""
    filename = f"/home/paulus/{module_name.replace('.', '/')}.py"

    class TestEnum(
        StrEnum,
        metaclass=EnumWithDeprecatedMembers,
        deprecated={
            "CATS": ("TestEnum.CATS_PER_CM", "2025.11.0"),
            "DOGS": ("TestEnum.DOGS_PER_CM", None),
        },
    ):
        """Zoo units."""

        CATS_PER_CM = "cats/cm"
        DOGS_PER_CM = "dogs/cm"
        CATS = "cats/cm"
        DOGS = "dogs/cm"

    # mock sys.modules for homeassistant/helpers/frame.py#get_integration_frame
    with (
        patch.dict(sys.modules, {module_name: Mock(__file__=filename)}),
        patch(
            "homeassistant.helpers.frame.linecache.getline",
            return_value="await session.close()",
        ),
        patch(
            "homeassistant.helpers.frame.get_current_frame",
            return_value=extract_stack_to_frame(
                [
                    Mock(
                        filename="/home/paulus/homeassistant/core.py",
                        lineno="23",
                        line="do_something()",
                    ),
                    Mock(
                        filename=filename,
                        lineno="23",
                        line="await session.close()",
                    ),
                    Mock(
                        filename="/home/paulus/aiohue/lights.py",
                        lineno="2",
                        line="something()",
                    ),
                ]
            ),
        ),
    ):
        TestEnum.CATS  # noqa: B018
        TestEnum.DOGS  # noqa: B018

    record_tuples = [(r.name, r.levelno, r.getMessage()) for r in caplog.records]
    expect(len(record_tuples)).to_equal(2)
    expect(record_tuples).to_contain(
        (
            "tests.helpers.test_deprecation",
            logging.WARNING,
            (
                "The deprecated enum member TestEnum.CATS was used from hue. It "
                "will be removed in HA Core 2025.11.0. Use TestEnum.CATS_PER_CM instead"
                f"{extra_extra_msg}"
            ),
        )
    )
    expect(record_tuples).to_contain(
        (
            "tests.helpers.test_deprecation",
            logging.WARNING,
            (
                "The deprecated enum member TestEnum.DOGS was used from hue. Use "
                f"TestEnum.DOGS_PER_CM instead{extra_extra_msg}"
            ),
        )
    )


@test
def enum_with_deprecated_members_integration_not_found(
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test check_if_deprecated_constant."""

    class TestEnum(
        StrEnum,
        metaclass=EnumWithDeprecatedMembers,
        deprecated={
            "CATS": ("TestEnum.CATS_PER_CM", "2025.11.0"),
            "DOGS": ("TestEnum.DOGS_PER_CM", None),
        },
    ):
        """Zoo units."""

        CATS_PER_CM = "cats/cm"
        DOGS_PER_CM = "dogs/cm"
        CATS = "cats/cm"
        DOGS = "dogs/cm"

    with patch(
        "homeassistant.helpers.frame.get_current_frame",
        side_effect=MissingIntegrationFrame,
    ):
        TestEnum.CATS  # noqa: B018
        TestEnum.DOGS  # noqa: B018

    expect(len(caplog.records)).to_equal(0)


_HASS_ARG_POSITIONAL = [
    ([], {}),
    (["first_arg"], {}),
    (["first_arg", "second_arg"], {}),
    ([], {"first_kwarg": "first_value"}),
    (["first_arg"], {"first_kwarg": "first_value"}),
    (["first_arg", "second_arg"], {"first_kwarg": "first_value"}),
    ([], {"first_kwarg": "first_value", "second_kwarg": "second_value"}),
    (["first_arg"], {"first_kwarg": "first_value", "second_kwarg": "second_value"}),
    (
        ["first_arg", "second_arg"],
        {"first_kwarg": "first_value", "second_kwarg": "second_value"},
    ),
]

_HASS_ARG_POSITIONAL_LABELS = [
    "no_args_no_kwargs",
    "one_arg_no_kwargs",
    "two_args_no_kwargs",
    "no_args_one_kwarg",
    "one_arg_one_kwarg",
    "two_args_one_kwarg",
    "no_args_two_kwargs",
    "one_arg_two_kwargs",
    "two_args_two_kwargs",
]

_HASS_ARG_VERSION = [
    (None, ""),
    ("2099.1", " It will be removed in HA Core 2099.1."),
]

_HASS_ARG_VERSION_LABELS = ["no_version", "with_version"]


@test.cases(
    test.case(
        "no_args_no_kwargs_no_version",
        positional_arguments=_HASS_ARG_POSITIONAL[0][0],
        keyword_arguments=_HASS_ARG_POSITIONAL[0][1],
        breaks_in_ha_version=_HASS_ARG_VERSION[0][0],
        extra_msg=_HASS_ARG_VERSION[0][1],
    ),
    test.case(
        "no_args_no_kwargs_with_version",
        positional_arguments=_HASS_ARG_POSITIONAL[0][0],
        keyword_arguments=_HASS_ARG_POSITIONAL[0][1],
        breaks_in_ha_version=_HASS_ARG_VERSION[1][0],
        extra_msg=_HASS_ARG_VERSION[1][1],
    ),
    test.case(
        "one_arg_no_kwargs_no_version",
        positional_arguments=_HASS_ARG_POSITIONAL[1][0],
        keyword_arguments=_HASS_ARG_POSITIONAL[1][1],
        breaks_in_ha_version=_HASS_ARG_VERSION[0][0],
        extra_msg=_HASS_ARG_VERSION[0][1],
    ),
    test.case(
        "one_arg_no_kwargs_with_version",
        positional_arguments=_HASS_ARG_POSITIONAL[1][0],
        keyword_arguments=_HASS_ARG_POSITIONAL[1][1],
        breaks_in_ha_version=_HASS_ARG_VERSION[1][0],
        extra_msg=_HASS_ARG_VERSION[1][1],
    ),
    test.case(
        "two_args_no_kwargs_no_version",
        positional_arguments=_HASS_ARG_POSITIONAL[2][0],
        keyword_arguments=_HASS_ARG_POSITIONAL[2][1],
        breaks_in_ha_version=_HASS_ARG_VERSION[0][0],
        extra_msg=_HASS_ARG_VERSION[0][1],
    ),
    test.case(
        "two_args_no_kwargs_with_version",
        positional_arguments=_HASS_ARG_POSITIONAL[2][0],
        keyword_arguments=_HASS_ARG_POSITIONAL[2][1],
        breaks_in_ha_version=_HASS_ARG_VERSION[1][0],
        extra_msg=_HASS_ARG_VERSION[1][1],
    ),
    test.case(
        "no_args_one_kwarg_no_version",
        positional_arguments=_HASS_ARG_POSITIONAL[3][0],
        keyword_arguments=_HASS_ARG_POSITIONAL[3][1],
        breaks_in_ha_version=_HASS_ARG_VERSION[0][0],
        extra_msg=_HASS_ARG_VERSION[0][1],
    ),
    test.case(
        "no_args_one_kwarg_with_version",
        positional_arguments=_HASS_ARG_POSITIONAL[3][0],
        keyword_arguments=_HASS_ARG_POSITIONAL[3][1],
        breaks_in_ha_version=_HASS_ARG_VERSION[1][0],
        extra_msg=_HASS_ARG_VERSION[1][1],
    ),
    test.case(
        "one_arg_one_kwarg_no_version",
        positional_arguments=_HASS_ARG_POSITIONAL[4][0],
        keyword_arguments=_HASS_ARG_POSITIONAL[4][1],
        breaks_in_ha_version=_HASS_ARG_VERSION[0][0],
        extra_msg=_HASS_ARG_VERSION[0][1],
    ),
    test.case(
        "one_arg_one_kwarg_with_version",
        positional_arguments=_HASS_ARG_POSITIONAL[4][0],
        keyword_arguments=_HASS_ARG_POSITIONAL[4][1],
        breaks_in_ha_version=_HASS_ARG_VERSION[1][0],
        extra_msg=_HASS_ARG_VERSION[1][1],
    ),
    test.case(
        "two_args_one_kwarg_no_version",
        positional_arguments=_HASS_ARG_POSITIONAL[5][0],
        keyword_arguments=_HASS_ARG_POSITIONAL[5][1],
        breaks_in_ha_version=_HASS_ARG_VERSION[0][0],
        extra_msg=_HASS_ARG_VERSION[0][1],
    ),
    test.case(
        "two_args_one_kwarg_with_version",
        positional_arguments=_HASS_ARG_POSITIONAL[5][0],
        keyword_arguments=_HASS_ARG_POSITIONAL[5][1],
        breaks_in_ha_version=_HASS_ARG_VERSION[1][0],
        extra_msg=_HASS_ARG_VERSION[1][1],
    ),
    test.case(
        "no_args_two_kwargs_no_version",
        positional_arguments=_HASS_ARG_POSITIONAL[6][0],
        keyword_arguments=_HASS_ARG_POSITIONAL[6][1],
        breaks_in_ha_version=_HASS_ARG_VERSION[0][0],
        extra_msg=_HASS_ARG_VERSION[0][1],
    ),
    test.case(
        "no_args_two_kwargs_with_version",
        positional_arguments=_HASS_ARG_POSITIONAL[6][0],
        keyword_arguments=_HASS_ARG_POSITIONAL[6][1],
        breaks_in_ha_version=_HASS_ARG_VERSION[1][0],
        extra_msg=_HASS_ARG_VERSION[1][1],
    ),
    test.case(
        "one_arg_two_kwargs_no_version",
        positional_arguments=_HASS_ARG_POSITIONAL[7][0],
        keyword_arguments=_HASS_ARG_POSITIONAL[7][1],
        breaks_in_ha_version=_HASS_ARG_VERSION[0][0],
        extra_msg=_HASS_ARG_VERSION[0][1],
    ),
    test.case(
        "one_arg_two_kwargs_with_version",
        positional_arguments=_HASS_ARG_POSITIONAL[7][0],
        keyword_arguments=_HASS_ARG_POSITIONAL[7][1],
        breaks_in_ha_version=_HASS_ARG_VERSION[1][0],
        extra_msg=_HASS_ARG_VERSION[1][1],
    ),
    test.case(
        "two_args_two_kwargs_no_version",
        positional_arguments=_HASS_ARG_POSITIONAL[8][0],
        keyword_arguments=_HASS_ARG_POSITIONAL[8][1],
        breaks_in_ha_version=_HASS_ARG_VERSION[0][0],
        extra_msg=_HASS_ARG_VERSION[0][1],
    ),
    test.case(
        "two_args_two_kwargs_with_version",
        positional_arguments=_HASS_ARG_POSITIONAL[8][0],
        keyword_arguments=_HASS_ARG_POSITIONAL[8][1],
        breaks_in_ha_version=_HASS_ARG_VERSION[1][0],
        extra_msg=_HASS_ARG_VERSION[1][1],
    ),
)
def deprecated_hass_argument_test(
    positional_arguments: list[str],
    keyword_arguments: dict[str, str],
    breaks_in_ha_version: str | None,
    extra_msg: str,
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test deprecated_hass_argument decorator."""

    calls = []

    @deprecated_hass_argument(breaks_in_ha_version=breaks_in_ha_version)
    def mock_deprecated_function(*args: str, **kwargs: str) -> None:
        calls.append((args, kwargs))

    mock_deprecated_function(*positional_arguments, **keyword_arguments)
    expect(caplog.text).not_.to_contain(
        "The deprecated argument hass was passed to mock_deprecated_function."
        f"{extra_msg}"
        " Use mock_deprecated_function without hass argument instead"
    )
    expect(len(calls)).to_equal(1)

    mock_deprecated_function(hass, *positional_arguments, **keyword_arguments)
    expect(caplog.text).to_contain(
        "The deprecated argument hass was passed to mock_deprecated_function."
        f"{extra_msg}"
        " Use mock_deprecated_function without hass argument instead"
    )
    expect(len(calls)).to_equal(2)

    caplog.clear()
    mock_deprecated_function(*positional_arguments, hass=hass, **keyword_arguments)
    expect(caplog.text).to_contain(
        "The deprecated argument hass was passed to mock_deprecated_function."
        f"{extra_msg}"
        " Use mock_deprecated_function without hass argument instead"
    )
    expect(len(calls)).to_equal(3)

    # Ensure that the two calls are the same, as the second call should have been
    # modified to remove the hass argument.
    expect(calls[0]).to_equal(calls[1])
    expect(calls[0]).to_equal(calls[2])
