"""Define tests for the Sabnzbd config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock

from pysabnzbd import SabnzbdApiException
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.sabnzbd.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_config_entry, mock_sabnzbd, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

VALID_CONFIG = {
    CONF_API_KEY: "edc3eee7330e4fdda04489e3fbc283d0",
    CONF_URL: "http://localhost:8080",
}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def create_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    sabnzbd: AsyncMock = Depends(mock_sabnzbd),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that the user step works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        VALID_CONFIG,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("localhost")
    expect(result["data"]).to_equal(
        {
            CONF_API_KEY: "edc3eee7330e4fdda04489e3fbc283d0",
            CONF_URL: "http://localhost:8080",
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def auth_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    sabnzbd: AsyncMock = Depends(mock_sabnzbd),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test when the user step fails and if we can recover."""
    sabnzbd.check_available.side_effect = SabnzbdApiException("Some error")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=VALID_CONFIG,
    )

    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    sabnzbd.check_available.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        VALID_CONFIG,
    )
    await hass.async_block_till_done()

    expect("errors" not in result).to_be(True)
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("localhost")
    expect(result["data"]).to_equal(
        {
            CONF_API_KEY: "edc3eee7330e4fdda04489e3fbc283d0",
            CONF_URL: "http://localhost:8080",
        }
    )


@test
async def reconfigure_successful(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    sabnzbd: AsyncMock = Depends(mock_sabnzbd),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfiguring a SABnzbd entry."""
    result = await config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_URL: "http://10.10.10.10:8080", CONF_API_KEY: "new_key"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data).to_equal(
        {
            CONF_URL: "http://10.10.10.10:8080",
            CONF_API_KEY: "new_key",
        }
    )


@test
async def reconfigure_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    sabnzbd: AsyncMock = Depends(mock_sabnzbd),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfiguring a SABnzbd entry."""
    result = await config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    sabnzbd.check_available.side_effect = SabnzbdApiException("Some error")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_URL: "http://10.10.10.10:8080", CONF_API_KEY: "new_key"},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    sabnzbd.check_available.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_URL: "http://10.10.10.10:8080", CONF_API_KEY: "new_key"},
    )

    expect("errors" not in result).to_be(True)
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data).to_equal(
        {
            CONF_URL: "http://10.10.10.10:8080",
            CONF_API_KEY: "new_key",
        }
    )


@test
async def abort_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    sabnzbd: AsyncMock = Depends(mock_sabnzbd),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that the flow aborts if SABnzbd instance is already configured."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        VALID_CONFIG,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def abort_reconfigure_successful(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    sabnzbd: AsyncMock = Depends(mock_sabnzbd),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that the reconfigure flow aborts successfully if SABnzbd instance is already configured."""
    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        VALID_CONFIG,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
