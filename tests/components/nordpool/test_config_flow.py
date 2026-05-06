"""Test the Nord Pool config flow."""

from typing import Any
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

from . import ENTRY_CONFIG
from ._fixtures import (
    get_client,
    load_data,
    load_int,
    load_json,
    load_platforms,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import aioclient_mock, hass as hass_fixture, mock_network
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Module-level fixture priming common mocks."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _entry: MockConfigEntry = Depends(load_int),
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
    test.case(
        "connection_error",
        error_message=NordPoolConnectionError,
        p_error="cannot_connect",
    ),
    test.case(
        "empty_response", error_message=NordPoolEmptyResponseError, p_error="no_data"
    ),
    test.case("base_error", error_message=NordPoolError, p_error="cannot_connect"),
    test.case(
        "response_error",
        error_message=NordPoolResponseError,
        p_error="cannot_connect",
    ),
)
async def cannot_connect(
    error_message: type[Exception],
    p_error: str,
    _trigger: None = Depends(_trigger_executor),
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
async def missing_areas(
    _trigger: None = Depends(_trigger_executor),
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

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_CURRENCY: "SEK",
            },
        )

        expect(result["errors"]).to_equal({CONF_AREAS: "no_areas"})

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=ENTRY_CONFIG,
        )

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal("Nord Pool")
        expect(result["data"]).to_equal({"areas": ["SE3", "SE4"], "currency": "SEK"})


@test
async def reconfigure(
    _trigger: None = Depends(_trigger_executor),
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
    test.case(
        "connection_error",
        error_message=NordPoolConnectionError,
        p_error="cannot_connect",
    ),
    test.case(
        "empty_response", error_message=NordPoolEmptyResponseError, p_error="no_data"
    ),
    test.case("base_error", error_message=NordPoolError, p_error="cannot_connect"),
    test.case(
        "response_error",
        error_message=NordPoolResponseError,
        p_error="cannot_connect",
    ),
)
async def reconfigure_cannot_connect(
    error_message: type[Exception],
    p_error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(load_int),
    _aio: AiohttpClientMocker = Depends(aioclient_mock),
    _json: list[dict[str, Any]] = Depends(load_json),
) -> None:
    """Test cannot connect error in a reeconfigure flow."""
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
