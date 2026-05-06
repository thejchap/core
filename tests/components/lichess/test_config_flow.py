"""Test the Lichess config flow."""

from unittest.mock import AsyncMock

from aiolichess.exceptions import AioLichessError, AuthError
from tryke import Depends, expect, fixture, test

from homeassistant.components.lichess.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_config_entry, mock_lichess_client, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _client: AsyncMock = Depends(mock_lichess_client),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _network: None = Depends(mock_network),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_TOKEN: "my_secret_token"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("DrNykterstein")
    expect(result["data"]).to_equal({CONF_API_TOKEN: "my_secret_token"})
    expect(result["result"].unique_id).to_equal("drnykterstien")
    expect(len(setup.mock_calls)).to_equal(1)


@test.cases(
    test.case("invalid_auth", exception=AuthError, error="invalid_auth"),
    test.case("cannot_connect", exception=AioLichessError, error="cannot_connect"),
    test.case("unknown", exception=Exception, error="unknown"),
)
async def form_errors(
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_lichess_client),
    setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we handle form errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    client.get_all.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_TOKEN: "my_secret_token"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    client.get_all.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_TOKEN: "my_secret_token"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(len(setup.mock_calls)).to_equal(1)


@test
async def duplicate_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we handle duplicate entries."""
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_TOKEN: "my_secret_token"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
