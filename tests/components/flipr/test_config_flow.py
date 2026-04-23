"""Test the Flipr config flow."""

from unittest.mock import AsyncMock

from requests.exceptions import HTTPError, Timeout
from tryke import Depends, expect, fixture, test

from homeassistant.components.flipr.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.components.flipr._fixtures import mock_flipr_client, mock_setup_entry
from tests.hass_fixtures import hass as hass_fixture


@fixture
def _trigger_executor() -> None:
    """Trigger the hook executor path."""
    return None


@test
async def full_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_flipr_client: AsyncMock = Depends(mock_flipr_client),
) -> None:
    """Test the full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_EMAIL: "dummylogin",
            CONF_PASSWORD: "dummypass",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Flipr dummylogin")
    expect(result["result"].unique_id).to_equal("dummylogin")
    expect(result["data"]).to_equal(
        {CONF_EMAIL: "dummylogin", CONF_PASSWORD: "dummypass"}
    )


@test.cases(
    test.case("unknown", exception=Exception("Bad request Boy :) --"), expected={"base": "unknown"}),
    test.case("invalid_auth", exception=HTTPError, expected={"base": "invalid_auth"}),
    test.case("timeout", exception=Timeout, expected={"base": "cannot_connect"}),
    test.case("connection", exception=ConnectionError, expected={"base": "cannot_connect"}),
)
async def errors(
    exception: Exception,
    expected: dict[str, str],
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_flipr_client: AsyncMock = Depends(mock_flipr_client),
) -> None:
    """Test we handle any error."""
    mock_flipr_client.search_all_ids.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_EMAIL: "nada",
            CONF_PASSWORD: "nadap",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal(expected)

    mock_flipr_client.search_all_ids.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "dummylogin",
            CONF_PASSWORD: "dummypass",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Flipr dummylogin")
    expect(result["data"]).to_equal(
        {CONF_EMAIL: "dummylogin", CONF_PASSWORD: "dummypass"}
    )


@test
async def no_flipr_found(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_flipr_client: AsyncMock = Depends(mock_flipr_client),
) -> None:
    """Test the case where there is no flipr found."""
    mock_flipr_client.search_all_ids.return_value = {"flipr": [], "hub": []}

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_EMAIL: "nada",
            CONF_PASSWORD: "nadap",
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "no_flipr_id_found"})

    mock_flipr_client.search_all_ids.return_value = {
        "flipr": ["myfliprid"],
        "hub": [],
    }

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_EMAIL: "dummylogin",
            CONF_PASSWORD: "dummypass",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Flipr dummylogin")
    expect(result["data"]).to_equal(
        {CONF_EMAIL: "dummylogin", CONF_PASSWORD: "dummypass"}
    )
