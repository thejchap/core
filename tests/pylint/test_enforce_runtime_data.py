"""Tests for pylint hass_enforce_runtime_data plugin."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from types import ModuleType

import astroid
from pylint.checkers import BaseChecker
from pylint.testutils.unittest_linter import UnittestLinter
from pylint.utils.ast_walker import ASTWalker
from tryke import Depends, expect, fixture, test

from tests.hass_fixtures import tmp_path

from . import assert_no_messages

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
def hass_enforce_runtime_data() -> ModuleType:
    """Fixture to the content for the hass_enforce_runtime_data check."""
    return _load_plugin_from_file(
        "hass_enforce_runtime_data",
        "pylint/plugins/hass_enforce_runtime_data.py",
    )


@fixture
def linter() -> UnittestLinter:
    """Fixture to provide a linter."""
    return UnittestLinter()


@fixture
def enforce_runtime_data_checker(
    hass_enforce_runtime_data: ModuleType = Depends(hass_enforce_runtime_data),
    linter: UnittestLinter = Depends(linter),
) -> BaseChecker:
    """Fixture to provide a hass_enforce_runtime_data checker."""
    # Clear the config flow cache between tests
    hass_enforce_runtime_data._has_config_flow_cache.clear()
    enforce_runtime_data_checker = (
        hass_enforce_runtime_data.HassEnforceRuntimeDataChecker(linter)
    )
    enforce_runtime_data_checker.module = "homeassistant.components.pylint_test"
    return enforce_runtime_data_checker


@test.cases(
    test.case(
        "non_domain_key",
        code="""
        hass.data[DATA_KEY] = some_value
        """,
        module_name="homeassistant.components.test",
    ),
    test.case(
        "outside_components",
        code="""
        hass.data[DOMAIN] = some_value
        """,
        module_name="some.other.module",
    ),
    test.case(
        "config_flow",
        code="""
        hass.data[DOMAIN] = some_value
        """,
        module_name="homeassistant.components.test.config_flow",
    ),
    test.case(
        "const",
        code="""
        hass.data[DOMAIN] = some_value
        """,
        module_name="homeassistant.components.test.const",
    ),
    test.case(
        "diagnostics",
        code="""
        hass.data[DOMAIN] = some_value
        """,
        module_name="homeassistant.components.test.diagnostics",
    ),
    test.case(
        "application_credentials",
        code="""
        hass.data[DOMAIN] = some_value
        """,
        module_name="homeassistant.components.test.application_credentials",
    ),
    test.case(
        "async_unload_entry",
        code="""
        async def async_unload_entry(hass, entry):
            hass.data[DOMAIN].pop(entry.entry_id)
        """,
        module_name="homeassistant.components.test",
    ),
    test.case(
        "async_remove_entry",
        code="""
        async def async_remove_entry(hass, entry):
            hass.data[DOMAIN].pop(entry.entry_id)
        """,
        module_name="homeassistant.components.test",
    ),
    test.case(
        "async_migrate_entry",
        code="""
        async def async_migrate_entry(hass, entry):
            old = hass.data[DOMAIN]
        """,
        module_name="homeassistant.components.test",
    ),
    test.case(
        "del_hass_data",
        code="""
        del hass.data[DOMAIN]
        """,
        module_name="homeassistant.components.test",
    ),
    test.case(
        "pop_from_hass_data",
        code="""
        hass.data[DOMAIN].pop(entry.entry_id)
        """,
        module_name="homeassistant.components.test",
    ),
)
def enforce_runtime_data(
    code: str,
    module_name: str,
    linter: UnittestLinter = Depends(linter),
    enforce_runtime_data_checker: BaseChecker = Depends(enforce_runtime_data_checker),
) -> None:
    """Good test cases."""
    root_node = astroid.parse(code, module_name)
    walker = ASTWalker(linter)
    walker.add_checker(enforce_runtime_data_checker)

    with assert_no_messages(linter):
        walker.walk(root_node)


@test.cases(
    test.case(
        "init_hass_data_domain",
        code="""
        hass.data[DOMAIN] = some_value
        """,
        module_name="homeassistant.components.test",
    ),
    test.case(
        "init_hass_data_domain_nested",
        code="""
        hass.data[DOMAIN][entry.entry_id] = some_value
        """,
        module_name="homeassistant.components.test",
    ),
    test.case(
        "sensor_hass_data_domain",
        code="""
        value = hass.data[DOMAIN]
        """,
        module_name="homeassistant.components.test.sensor",
    ),
    test.case(
        "self_hass_data_domain",
        code="""
        value = self.hass.data[DOMAIN]
        """,
        module_name="homeassistant.components.test.sensor",
    ),
    test.case(
        "async_setup_entry",
        code="""
        async def async_setup_entry(hass, entry):
            hass.data[DOMAIN] = {}
        """,
        module_name="homeassistant.components.test",
    ),
)
def enforce_runtime_data_bad(
    code: str,
    module_name: str,
    linter: UnittestLinter = Depends(linter),
    enforce_runtime_data_checker: BaseChecker = Depends(enforce_runtime_data_checker),
) -> None:
    """Bad test cases."""
    root_node = astroid.parse(code, module_name)
    walker = ASTWalker(linter)
    walker.add_checker(enforce_runtime_data_checker)

    walker.walk(root_node)
    messages = linter.release_messages()
    expect(len(messages)).to_equal(1)
    expect(messages[0].msg_id).to_equal("hass-use-runtime-data")


@test
def enforce_runtime_data_no_config_flow(
    linter: UnittestLinter = Depends(linter),
    enforce_runtime_data_checker: BaseChecker = Depends(enforce_runtime_data_checker),
    tmp_path: Path = Depends(tmp_path),
) -> None:
    """Test that integrations without config_flow.py are not flagged."""
    # Create a fake integration directory without config_flow.py
    integration_dir = tmp_path / "homeassistant" / "components" / "yaml_only"
    integration_dir.mkdir(parents=True)
    init_file = integration_dir / "__init__.py"
    init_file.touch()

    code = """
    hass.data[DOMAIN] = some_value
    """
    root_node = astroid.parse(code, "homeassistant.components.yaml_only")
    root_node.file = str(init_file)

    walker = ASTWalker(linter)
    walker.add_checker(enforce_runtime_data_checker)

    with assert_no_messages(linter):
        walker.walk(root_node)


@test
def enforce_runtime_data_with_config_flow(
    linter: UnittestLinter = Depends(linter),
    enforce_runtime_data_checker: BaseChecker = Depends(enforce_runtime_data_checker),
    tmp_path: Path = Depends(tmp_path),
) -> None:
    """Test that integrations with config_flow.py are flagged."""
    # Create a fake integration directory with config_flow.py
    integration_dir = tmp_path / "homeassistant" / "components" / "modern"
    integration_dir.mkdir(parents=True)
    init_file = integration_dir / "__init__.py"
    init_file.touch()
    (integration_dir / "config_flow.py").touch()

    code = """
    hass.data[DOMAIN] = some_value
    """
    root_node = astroid.parse(code, "homeassistant.components.modern")
    root_node.file = str(init_file)

    walker = ASTWalker(linter)
    walker.add_checker(enforce_runtime_data_checker)

    walker.walk(root_node)
    messages = linter.release_messages()
    expect(len(messages)).to_equal(1)
    expect(messages[0].msg_id).to_equal("hass-use-runtime-data")
