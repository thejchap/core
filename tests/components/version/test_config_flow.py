"""Test the Version config flow."""

from unittest.mock import patch

from pyhaversion.consts import HaVersionChannel, HaVersionSource
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.version.const import (
    CONF_BETA,
    CONF_BOARD,
    CONF_CHANNEL,
    CONF_IMAGE,
    CONF_VERSION_SOURCE,
    DEFAULT_CONFIGURATION,
    DOMAIN,
    UPDATE_COORDINATOR_UPDATE_INTERVAL,
    VERSION_SOURCE_DOCKER_HUB,
    VERSION_SOURCE_PYPI,
    VERSION_SOURCE_VERSIONS,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_SOURCE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.util import dt as dt_util

from .common import MOCK_VERSION, MOCK_VERSION_DATA, setup_version_integration

from tests.common import async_fire_time_changed
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def reload_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reloading the config entry."""
    config_entry = await setup_version_integration(hass)
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    with patch(
        "pyhaversion.HaVersion.get_version",
        return_value=(MOCK_VERSION, MOCK_VERSION_DATA),
    ):
        expect(bool(await hass.config_entries.async_reload(config_entry.entry_id))).to_be(True)
        async_fire_time_changed(
            hass, dt_util.utcnow() + UPDATE_COORDINATOR_UPDATE_INTERVAL
        )
        await hass.async_block_till_done()

    entry = hass.config_entries.async_get_entry(config_entry.entry_id)
    expect(entry.state).to_be(ConfigEntryState.LOADED)


@test
async def basic_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER, "show_advanced_options": False},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    with patch(
        "homeassistant.components.version.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_VERSION_SOURCE: VERSION_SOURCE_DOCKER_HUB},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(VERSION_SOURCE_DOCKER_HUB)
    expect(result2["data"]).to_equal(
        {
            **DEFAULT_CONFIGURATION,
            CONF_SOURCE: HaVersionSource.CONTAINER,
            CONF_VERSION_SOURCE: VERSION_SOURCE_DOCKER_HUB,
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def advanced_form_pypi(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Show advanced form when pypi is selected."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER, "show_advanced_options": True},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_VERSION_SOURCE: VERSION_SOURCE_PYPI},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("version_source")

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("version_source")

    with patch(
        "homeassistant.components.version.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_BETA: True}
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(VERSION_SOURCE_PYPI)
    expect(result["data"]).to_equal(
        {
            **DEFAULT_CONFIGURATION,
            CONF_BETA: True,
            CONF_SOURCE: HaVersionSource.PYPI,
            CONF_VERSION_SOURCE: VERSION_SOURCE_PYPI,
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def advanced_form_container(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Show advanced form when container source is selected."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER, "show_advanced_options": True},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_VERSION_SOURCE: VERSION_SOURCE_DOCKER_HUB},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("version_source")

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("version_source")

    with patch(
        "homeassistant.components.version.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_IMAGE: "odroid-n2-homeassistant"}
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(VERSION_SOURCE_DOCKER_HUB)
    expect(result["data"]).to_equal(
        {
            **DEFAULT_CONFIGURATION,
            CONF_IMAGE: "odroid-n2-homeassistant",
            CONF_SOURCE: HaVersionSource.CONTAINER,
            CONF_VERSION_SOURCE: VERSION_SOURCE_DOCKER_HUB,
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def advanced_form_supervisor(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Show advanced form when docker source is selected."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER, "show_advanced_options": True},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_VERSION_SOURCE: VERSION_SOURCE_VERSIONS},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("version_source")

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("version_source")

    with patch(
        "homeassistant.components.version.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_CHANNEL: "Dev", CONF_IMAGE: "odroid-n2", CONF_BOARD: "ODROID N2"},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"{VERSION_SOURCE_VERSIONS} Dev")
    expect(result["data"]).to_equal(
        {
            **DEFAULT_CONFIGURATION,
            CONF_IMAGE: "odroid-n2",
            CONF_BOARD: "ODROID N2",
            CONF_CHANNEL: HaVersionChannel.DEV,
            CONF_SOURCE: HaVersionSource.SUPERVISOR,
            CONF_VERSION_SOURCE: VERSION_SOURCE_VERSIONS,
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
