"""Tryke fixtures for the wmspro integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import fixture

from homeassistant.components.wmspro.const import DOMAIN
from homeassistant.const import CONF_HOST

from tests.common import MockConfigEntry, load_json_object_fixture


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a dummy config entry."""
    return MockConfigEntry(
        title="WebControl",
        domain=DOMAIN,
        data={CONF_HOST: "webcontrol"},
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.wmspro.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_hub_ping() -> Generator[AsyncMock]:
    """Override WebControlPro.ping."""
    with patch(
        "wmspro.webcontrol.WebControlPro.ping",
        return_value=True,
    ) as mock_hub_ping:
        yield mock_hub_ping


@fixture
def mock_hub_refresh() -> Generator[AsyncMock]:
    """Override WebControlPro.refresh."""
    with patch(
        "wmspro.webcontrol.WebControlPro.refresh",
        return_value=True,
    ) as mock_hub_refresh:
        yield mock_hub_refresh


@fixture
def mock_hub_configuration_test() -> Generator[AsyncMock]:
    """Override WebControlPro.configuration."""
    with patch(
        "wmspro.webcontrol.WebControlPro._getConfiguration",
        return_value=load_json_object_fixture("config_test.json", DOMAIN),
    ) as mock_hub_configuration:
        yield mock_hub_configuration


@fixture
def mock_hub_configuration_prod_awning_dimmer() -> Generator[AsyncMock]:
    """Override WebControlPro._getConfiguration."""
    with patch(
        "wmspro.webcontrol.WebControlPro._getConfiguration",
        return_value=load_json_object_fixture("config_prod_awning_dimmer.json", DOMAIN),
    ) as mock_hub_configuration:
        yield mock_hub_configuration


@fixture
def mock_dest_refresh() -> Generator[AsyncMock]:
    """Override Destination.refresh."""
    with patch(
        "wmspro.destination.Destination.refresh",
        return_value=True,
    ) as mock_hub_status:
        yield mock_hub_status
