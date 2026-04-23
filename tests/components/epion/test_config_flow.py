"""Tests for the Epion config flow."""

from unittest.mock import MagicMock, patch

from epion import EpionAuthenticationError, EpionConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.epion.const import DOMAIN
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.epion._fixtures import mock_epion
from tests.hass_fixtures import hass, mock_network

API_KEY = "test-key-123"


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def user_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_epion: MagicMock = Depends(mock_epion),
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

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("Epion integration")
    expect(result["data"]).to_equal({CONF_API_KEY: API_KEY})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "auth_error", EpionAuthenticationError("Invalid auth"), "invalid_auth"
    ),
    test.case(
        "connection_error", EpionConnectionError("Timeout error"), "cannot_connect"
    ),
)
async def form_exceptions(
    exception: Exception,
    error: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_epion: MagicMock = Depends(mock_epion),
) -> None:
    """Test we can handle Form exceptions."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_epion.return_value.get_current.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: API_KEY},
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({"base": error})

    mock_epion.return_value.get_current.side_effect = None

    with patch(
        "homeassistant.components.epion.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: API_KEY},
        )
        await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("Epion integration")
    expect(result["data"]).to_equal({CONF_API_KEY: API_KEY})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def duplicate_entry(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_epion: MagicMock = Depends(mock_epion),
) -> None:
    """Test duplicate setup handling."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_API_KEY: API_KEY},
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

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")
