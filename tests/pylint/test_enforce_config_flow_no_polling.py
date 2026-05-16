"""Tests for pylint hass_enforce_config_flow_no_polling plugin."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from types import ModuleType

import astroid
from pylint.checkers import BaseChecker
from pylint.testutils.unittest_linter import UnittestLinter
from pylint.utils.ast_walker import ASTWalker
from tryke import Depends, expect, fixture, test

from . import assert_no_messages

_BASE_PATH = Path(__file__).parents[2]


def _load_plugin_from_file(module_name: str, file: str) -> ModuleType:
    """Load plugin from file path."""
    spec = spec_from_file_location(
        module_name,
        str(_BASE_PATH.joinpath(file)),
    )
    assert spec and spec.loader

    module = module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@fixture
def linter() -> UnittestLinter:
    """Fixture to provide a unittest linter."""
    return UnittestLinter()


@fixture
def enforce_config_flow_no_polling_checker(
    linter: UnittestLinter = Depends(linter),
) -> BaseChecker:
    """Fixture to provide a config_flow_no_polling checker."""
    module = _load_plugin_from_file(
        "hass_enforce_config_flow_no_polling",
        "pylint/plugins/hass_enforce_config_flow_no_polling.py",
    )
    checker = module.HassEnforceConfigFlowNoPollingChecker(linter)
    checker.module = "homeassistant.components.pylint_test"
    return checker


@test.cases(
    test.case(
        "non_polling_field",
        code="""
        vol.Required(CONF_HOST)
        """,
        module_name="homeassistant.components.test.config_flow",
    ),
    test.case(
        "non_polling_string_field",
        code="""
        vol.Optional("username")
        """,
        module_name="homeassistant.components.test.config_flow",
    ),
    test.case(
        "polling_in_sensor_not_flagged",
        code="""
        vol.Optional(CONF_SCAN_INTERVAL)
        """,
        module_name="homeassistant.components.test.sensor",
    ),
    test.case(
        "outside_components",
        code="""
        vol.Optional(CONF_SCAN_INTERVAL)
        """,
        module_name="some.other.module",
    ),
    test.case(
        "polling_in_init_not_flagged",
        code="""
        vol.Optional("scan_interval", default=30)
        """,
        module_name="homeassistant.components.test",
    ),
    test.case(
        "unknown_interval_field",
        code="""
        vol.Optional("check_interval")
        """,
        module_name="homeassistant.components.test.config_flow",
    ),
    test.case(
        "unknown_frequency_field",
        code="""
        vol.Optional("poll_frequency")
        """,
        module_name="homeassistant.components.test.config_flow",
    ),
)
def enforce_config_flow_no_polling(
    code: str,
    module_name: str,
    linter: UnittestLinter = Depends(linter),
    enforce_config_flow_no_polling_checker: BaseChecker = Depends(
        enforce_config_flow_no_polling_checker
    ),
) -> None:
    """Good test cases."""
    root_node = astroid.parse(code, module_name)
    walker = ASTWalker(linter)
    walker.add_checker(enforce_config_flow_no_polling_checker)

    with assert_no_messages(linter):
        walker.walk(root_node)


@test.cases(
    test.case(
        "conf_scan_interval",
        code="""
        vol.Optional(CONF_SCAN_INTERVAL)
        """,
        module_name="homeassistant.components.test.config_flow",
    ),
    test.case(
        "string_scan_interval",
        code="""
        vol.Optional("scan_interval", default=30)
        """,
        module_name="homeassistant.components.test.config_flow",
    ),
    test.case(
        "update_interval",
        code="""
        vol.Required("update_interval")
        """,
        module_name="homeassistant.components.test.config_flow",
    ),
    test.case(
        "update_frequency",
        code="""
        vol.Optional("update_frequency", default=60)
        """,
        module_name="homeassistant.components.test.config_flow",
    ),
    test.case(
        "refresh_interval",
        code="""
        vol.Optional("refresh_interval")
        """,
        module_name="homeassistant.components.test.config_flow",
    ),
    test.case(
        "conf_update_interval",
        code="""
        vol.Optional(CONF_UPDATE_INTERVAL)
        """,
        module_name="homeassistant.components.test.config_flow",
    ),
)
def enforce_config_flow_no_polling_bad(
    code: str,
    module_name: str,
    linter: UnittestLinter = Depends(linter),
    enforce_config_flow_no_polling_checker: BaseChecker = Depends(
        enforce_config_flow_no_polling_checker
    ),
) -> None:
    """Bad test cases."""
    root_node = astroid.parse(code, module_name)
    walker = ASTWalker(linter)
    walker.add_checker(enforce_config_flow_no_polling_checker)

    walker.walk(root_node)
    messages = linter.release_messages()
    expect(len(messages)).to_equal(1)
    expect(messages[0].msg_id).to_equal("hass-config-flow-polling-field")
