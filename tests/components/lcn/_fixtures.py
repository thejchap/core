"""Tryke fixtures for LCN tests."""

import json

from tryke import fixture

from homeassistant.components.lcn.config_flow import LcnFlowHandler
from homeassistant.components.lcn.const import DOMAIN
from homeassistant.const import CONF_ADDRESS, CONF_DEVICES, CONF_ENTITIES, CONF_HOST

from tests.common import MockConfigEntry, load_fixture

LATEST_CONFIG_ENTRY_VERSION = (LcnFlowHandler.VERSION, LcnFlowHandler.MINOR_VERSION)


def create_config_entry(
    name: str, version: tuple[int, int] = LATEST_CONFIG_ENTRY_VERSION
) -> MockConfigEntry:
    """Set up config entries with configuration data."""
    fixture_filename = f"lcn/config_entry_{name}.json"
    entry_data = json.loads(load_fixture(fixture_filename))
    for device in entry_data[CONF_DEVICES]:
        device[CONF_ADDRESS] = tuple(device[CONF_ADDRESS])
    for entity in entry_data[CONF_ENTITIES]:
        entity[CONF_ADDRESS] = tuple(entity[CONF_ADDRESS])

    options: dict[str, object] = {}

    title = entry_data[CONF_HOST]
    return MockConfigEntry(
        entry_id=fixture_filename.replace(".", "_"),
        domain=DOMAIN,
        title=title,
        data=entry_data,
        options=options,
        version=version[0],
        minor_version=version[1],
    )


@fixture
def entry() -> MockConfigEntry:
    """Return one specific config entry."""
    return create_config_entry("pchk")
