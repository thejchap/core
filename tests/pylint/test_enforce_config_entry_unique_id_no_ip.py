"""Tests for pylint hass_enforce_config_entry_unique_id_no_ip plugin."""

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
def linter() -> UnittestLinter:
    """Fixture to provide a linter."""
    return UnittestLinter()


@fixture
def hass_enforce_config_entry_unique_id_no_ip() -> ModuleType:
    """Fixture to provide the hass_enforce_config_entry_unique_id_no_ip plugin module."""
    return _load_plugin_from_file(
        "hass_enforce_config_entry_unique_id_no_ip",
        "pylint/plugins/hass_enforce_config_entry_unique_id_no_ip.py",
    )


@fixture
def enforce_config_entry_unique_id_no_ip_checker(
    hass_enforce_config_entry_unique_id_no_ip: ModuleType = Depends(
        hass_enforce_config_entry_unique_id_no_ip
    ),
    linter: UnittestLinter = Depends(linter),
) -> BaseChecker:
    """Fixture to provide a unique_id_no_ip checker."""
    checker = hass_enforce_config_entry_unique_id_no_ip.HassEnforceConfigEntryUniqueIdNoIpChecker(
        linter
    )
    checker.module = "homeassistant.components.pylint_test"
    return checker


@test.cases(
    test.case(
        "mac_address",
        code="""
        unique_id = format_mac(data["mac"])
        """,
        module_name="homeassistant.components.test.config_flow",
    ),
    test.case(
        "serial_number",
        code="""
        unique_id = device_info["serial_number"]
        """,
        module_name="homeassistant.components.test.config_flow",
    ),
    test.case(
        "device_unique_id",
        code="""
        await self.async_set_unique_id(device.unique_id)
        """,
        module_name="homeassistant.components.test.config_flow",
    ),
    test.case(
        "assign_not_checked",
        code="""
        unique_id = data[CONF_HOST]
        """,
        module_name="homeassistant.components.test.config_flow",
    ),
    test.case(
        "async_set_unique_id_safe_value",
        code="""
        await self.async_set_unique_id(device.serial)
        """,
        module_name="homeassistant.components.test.config_flow",
    ),
    test.case(
        "async_set_unique_id_not_config_flow",
        code="""
        await self.async_set_unique_id(data[CONF_HOST])
        """,
        module_name="homeassistant.components.test.sensor",
    ),
)
def enforce_unique_id_no_ip(
    code: str,
    module_name: str,
    linter: UnittestLinter = Depends(linter),
    enforce_config_entry_unique_id_no_ip_checker: BaseChecker = Depends(
        enforce_config_entry_unique_id_no_ip_checker
    ),
) -> None:
    """Good test cases."""
    root_node = astroid.parse(code, module_name)
    walker = ASTWalker(linter)
    walker.add_checker(enforce_config_entry_unique_id_no_ip_checker)

    with assert_no_messages(linter):
        walker.walk(root_node)


@test.cases(
    test.case(
        "async_set_conf_host",
        code="""
        await self.async_set_unique_id(entry.data[CONF_HOST])
        """,
        module_name="homeassistant.components.test.config_flow",
    ),
    test.case(
        "async_set_conf_ip",
        code="""
        await self.async_set_unique_id(data[CONF_IP_ADDRESS])
        """,
        module_name="homeassistant.components.test.config_flow",
    ),
    test.case(
        "async_set_string_host",
        code="""
        await self.async_set_unique_id(user_input["host"])
        """,
        module_name="homeassistant.components.test.config_flow",
    ),
    test.case(
        "async_set_conf_host_keyword",
        code="""
        await self.async_set_unique_id(unique_id=entry.data[CONF_HOST])
        """,
        module_name="homeassistant.components.test.config_flow",
    ),
    test.case(
        "async_set_conf_ip_keyword_raise_on_progress_false",
        code="""
        await self.async_set_unique_id(
            unique_id=data[CONF_IP_ADDRESS], raise_on_progress=False
        )
        """,
        module_name="homeassistant.components.test.config_flow",
    ),
)
def enforce_unique_id_no_ip_bad_call(
    code: str,
    module_name: str,
    linter: UnittestLinter = Depends(linter),
    enforce_config_entry_unique_id_no_ip_checker: BaseChecker = Depends(
        enforce_config_entry_unique_id_no_ip_checker
    ),
) -> None:
    """Bad async_set_unique_id call test cases."""
    root_node = astroid.parse(code, module_name)
    walker = ASTWalker(linter)
    walker.add_checker(enforce_config_entry_unique_id_no_ip_checker)

    walker.walk(root_node)
    messages = linter.release_messages()
    expect(len(messages)).to_equal(1)
    expect(messages[0].msg_id).to_equal("hass-unique-id-ip-based")


@test.cases(
    test.case(
        "variable_from_subscript",
        code="""
async def async_step_user(self, user_input=None):
    unique_id = data[CONF_HOST]
    await self.async_set_unique_id(unique_id)
        """,
        module_name="homeassistant.components.test.config_flow",
    ),
    test.case(
        "variable_from_fstring",
        code="""
async def async_step_user(self, user_input=None):
    unique_id = f"prefix_{data[CONF_HOST]}"
    await self.async_set_unique_id(unique_id)
        """,
        module_name="homeassistant.components.test.config_flow",
    ),
    test.case(
        "variable_from_conditional",
        code="""
async def async_step_user(self, user_input=None):
    if discovered:
        unique_id = device.mac
    else:
        unique_id = data[CONF_HOST]
    await self.async_set_unique_id(unique_id)
        """,
        module_name="homeassistant.components.test.config_flow",
    ),
    test.case(
        "variable_from_dict_get",
        code="""
async def async_step_user(self, user_input=None):
    unique_id = data.get(CONF_HOST)
    await self.async_set_unique_id(unique_id)
        """,
        module_name="homeassistant.components.test.config_flow",
    ),
)
def enforce_unique_id_no_ip_bad_call_variable(
    code: str,
    module_name: str,
    linter: UnittestLinter = Depends(linter),
    enforce_config_entry_unique_id_no_ip_checker: BaseChecker = Depends(
        enforce_config_entry_unique_id_no_ip_checker
    ),
) -> None:
    """Bad async_set_unique_id call test cases."""
    root_node = astroid.parse(code, module_name)
    walker = ASTWalker(linter)
    walker.add_checker(enforce_config_entry_unique_id_no_ip_checker)

    walker.walk(root_node)
    messages = linter.release_messages()
    expect(len(messages)).to_equal(1)
    expect(messages[0].msg_id).to_equal("hass-unique-id-ip-based")
