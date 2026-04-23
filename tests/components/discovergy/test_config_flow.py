"""Test the Discovergy config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

from pydiscovergy.error import DiscovergyClientError, HTTPError, InvalidLogin
from tryke import Depends, expect, fixture, test

from homeassistant.components.discovergy.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.discovergy._fixtures import (
    config_entry,
    discovergy,
    mock_zeroconf,
)
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def form(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    discovergy: AsyncMock = Depends(discovergy),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.discovergy.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_EMAIL: "test@example.com",
                CONF_PASSWORD: "test-password",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result2["title"]).to_equal("test@example.com")
    expect(result2["data"]).to_equal(
        {
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "test-password",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def reauth(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    config_entry: MockConfigEntry = Depends(config_entry),
    _discovergy: AsyncMock = Depends(discovergy),
) -> None:
    """Test reauth flow."""
    config_entry.add_to_hass(hass)
    init_result = await config_entry.start_reauth_flow(hass)
    expect(init_result["type"] is FlowResultType.FORM).to_be(True)
    expect(init_result["step_id"]).to_equal("user")

    with patch(
        "homeassistant.components.discovergy.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        configure_result = await hass.config_entries.flow.async_configure(
            init_result["flow_id"],
            {
                CONF_EMAIL: "user@example.org",
                CONF_PASSWORD: "test-password",
            },
        )
        await hass.async_block_till_done()

        expect(configure_result["type"] is FlowResultType.ABORT).to_be(True)
        expect(configure_result["reason"]).to_equal("reauth_successful")
        expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("invalid_login", InvalidLogin, "invalid_auth"),
    test.case("http_error", HTTPError, "cannot_connect"),
    test.case("client_error", DiscovergyClientError, "cannot_connect"),
    test.case("unknown", Exception, "unknown"),
)
async def form_fail(
    error: type[Exception],
    message: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    discovergy: AsyncMock = Depends(discovergy),
) -> None:
    """Test to handle exceptions."""
    discovergy.meters.side_effect = error
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": message})

    # Reset and test for success.
    discovergy.meters.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("test@example.com")
    expect("errors" not in result).to_be(True)


@test
async def reauth_unique_id_mismatch(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    config_entry: MockConfigEntry = Depends(config_entry),
    _discovergy: AsyncMock = Depends(discovergy),
) -> None:
    """Test reauth flow with unique id mismatch."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    with patch(
        "homeassistant.components.discovergy.async_setup_entry",
        return_value=True,
    ):
        configure_result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_EMAIL: "user2@example.org",
                CONF_PASSWORD: "test-password",
            },
        )
        await hass.async_block_till_done()

        expect(configure_result["type"] is FlowResultType.ABORT).to_be(True)
        expect(configure_result["reason"]).to_equal("account_mismatch")
