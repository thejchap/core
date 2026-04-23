"""Test the Nord Pool config flow."""

from __future__ import annotations

from unittest.mock import patch

from freezegun import freeze_time
from pynordpool import (
    NordPoolClient,
    NordPoolConnectionError,
    NordPoolEmptyResponseError,
    NordPoolError,
    NordPoolResponseError,
)
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.nordpool.const import CONF_AREAS, DOMAIN
from homeassistant.const import CONF_CURRENCY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.nordpool import ENTRY_CONFIG
from tests.components.nordpool._fixtures import (
    get_client,
    load_data,
    load_int,
    load_json,
)
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def form(
    hass: HomeAssistant = Depends(hass_fixture),
    _client: NordPoolClient = Depends(get_client),
) -> None:
    """Test we get the form."""
    with freeze_time("2025-10-01T18:00:00+00:00"):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        expect(result["step_id"]).to_equal("user")
        expect(result["type"]).to_be(FlowResultType.FORM)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            ENTRY_CONFIG,
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["version"]).to_equal(1)
    expect(result["title"]).to_equal("Nord Pool")
    expect(result["data"]).to_equal({"areas": ["SE3", "SE4"], "currency": "SEK"})


@test
async def single_config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    _load: None = Depends(load_int),
    _client: NordPoolClient = Depends(get_client),
) -> None:
    """Test abort for single config entry."""
    with freeze_time("2025-10-01T18:00:00+00:00"):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")


@test.cases(
    test.case("connection", NordPoolConnectionError, "cannot_connect"),
    test.case("empty", NordPoolEmptyResponseError, "no_data"),
    test.case("generic", NordPoolError, "cannot_connect"),
    test.case("response", NordPoolResponseError, "cannot_connect"),
)
async def cannot_connect(
    error_message: type[Exception],
    p_error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    _client: NordPoolClient = Depends(get_client),
) -> None:
    """Test cannot connect error."""
    with freeze_time("2025-10-01T18:00:00+00:00"):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal(config_entries.SOURCE_USER)

        with patch(
            "homeassistant.components.nordpool.coordinator.NordPoolClient.async_get_delivery_period",
            side_effect=error_message,
        ):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input=ENTRY_CONFIG,
            )

        expect(result["errors"]).to_equal({"base": p_error})

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=ENTRY_CONFIG,
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Nord Pool")
    expect(result["data"]).to_equal({"areas": ["SE3", "SE4"], "currency": "SEK"})


@test
async def reconfigure(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(load_int),
) -> None:
    """Test reconfiguration."""
    with freeze_time("2025-10-01T18:00:00+00:00"):
        result = await entry.start_reconfigure_flow(hass)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_AREAS: ["SE3"],
                CONF_CURRENCY: "EUR",
            },
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(entry.data).to_equal(
        {
            "areas": ["SE3"],
            "currency": "EUR",
        }
    )


@test.cases(
    test.case("connection", NordPoolConnectionError, "cannot_connect"),
    test.case("empty", NordPoolEmptyResponseError, "no_data"),
    test.case("generic", NordPoolError, "cannot_connect"),
    test.case("response", NordPoolResponseError, "cannot_connect"),
)
async def reconfigure_cannot_connect(
    error_message: type[Exception],
    p_error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(load_int),
) -> None:
    """Test cannot connect error in a reconfigure flow."""
    with freeze_time("2025-10-01T18:00:00+00:00"):
        result = await entry.start_reconfigure_flow(hass)

        with patch(
            "homeassistant.components.nordpool.coordinator.NordPoolClient.async_get_delivery_period",
            side_effect=error_message,
        ):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={
                    CONF_AREAS: ["SE3"],
                    CONF_CURRENCY: "EUR",
                },
            )

        expect(result["errors"]).to_equal({"base": p_error})

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_AREAS: ["SE3"],
                CONF_CURRENCY: "EUR",
            },
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(entry.data).to_equal(
        {
            "areas": ["SE3"],
            "currency": "EUR",
        }
    )
