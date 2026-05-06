"""Tests for the Epion config flow."""

from unittest.mock import MagicMock, patch

from epion import EpionAuthenticationError, EpionConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.epion.const import DOMAIN
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_epion

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

API_KEY = "test-key-123"


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _epion: MagicMock = Depends(mock_epion),
) -> None:
    """Test we can handle a regular successflow setup flow."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.epion.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: API_KEY},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Epion integration")
    expect(result["data"]).to_equal({CONF_API_KEY: API_KEY})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "invalid_auth",
        exception=EpionAuthenticationError("Invalid auth"),
        error="invalid_auth",
    ),
    test.case(
        "cannot_connect",
        exception=EpionConnectionError("Timeout error"),
        error="cannot_connect",
    ),
)
async def form_exceptions(
    exception: Exception,
    error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    epion: MagicMock = Depends(mock_epion),
) -> None:
    """Test we can handle Form exceptions."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    epion.return_value.get_current.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: API_KEY},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    epion.return_value.get_current.side_effect = None

    with patch(
        "homeassistant.components.epion.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: API_KEY},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Epion integration")
    expect(result["data"]).to_equal({CONF_API_KEY: API_KEY})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def duplicate_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _epion: MagicMock = Depends(mock_epion),
) -> None:
    """Test duplicate setup handling."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_API_KEY: API_KEY,
        },
        unique_id="account-dupe-123",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: API_KEY},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
