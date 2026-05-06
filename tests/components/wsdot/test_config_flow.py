"""Define tests for the wsdot config flow."""

from typing import Any
from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test
from wsdot import WsdotTravelError

from homeassistant.components.wsdot.const import (
    CONF_TRAVEL_TIMES,
    DOMAIN,
    SUBENTRY_TRAVEL_TIMES,
)
from homeassistant.config_entries import SOURCE_IMPORT, SOURCE_USER
from homeassistant.const import CONF_API_KEY, CONF_ID, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    init_integration,
    mock_config_data,
    mock_config_entry,
    mock_setup_entry,
    mock_travel_time,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

VALID_USER_CONFIG = {
    CONF_API_KEY: "abcd-1234",
}

VALID_USER_TRAVEL_TIME_CONFIG = {
    CONF_NAME: "Seattle-Bellevue via I-90 (EB AM)",
}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def create_user_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _travel_time: AsyncMock = Depends(mock_travel_time),
) -> None:
    """Test that the user step works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=VALID_USER_CONFIG,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DOMAIN)
    expect(result["data"][CONF_API_KEY]).to_equal("abcd-1234")


@test.cases(
    test.case(
        "invalid_api_key",
        failed_travel_time_status=400,
        errors={CONF_API_KEY: "invalid_api_key"},
    ),
    test.case(
        "cannot_connect",
        failed_travel_time_status=404,
        errors={"base": "cannot_connect"},
    ),
)
async def errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    travel_time: AsyncMock = Depends(mock_travel_time),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    *,
    failed_travel_time_status: int,
    errors: dict[str, str],
) -> None:
    """Test that the user step works."""
    travel_time.get_all_travel_times.side_effect = WsdotTravelError(
        status=failed_travel_time_status
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=VALID_USER_CONFIG,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal(errors)

    travel_time.get_all_travel_times.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=VALID_USER_CONFIG,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test.cases(
    test.case(
        "with_int_id",
        import_config={
            CONF_API_KEY: "abcd-5678",
            CONF_TRAVEL_TIMES: [{CONF_ID: 96, CONF_NAME: "I-90 EB"}],
        },
    ),
    test.case(
        "with_str_id",
        import_config={
            CONF_API_KEY: "abcd-5678",
            CONF_TRAVEL_TIMES: [{CONF_ID: "96", CONF_NAME: "I-90 EB"}],
        },
    ),
)
async def create_import_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _travel_time: AsyncMock = Depends(mock_travel_time),
    *,
    import_config: dict[str, str | int],
) -> None:
    """Test that the yaml import works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data=import_config,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("wsdot")
    expect(result["data"][CONF_API_KEY]).to_equal("abcd-5678")

    entry = result["result"]
    expect(entry is not None).to_be(True)
    expect(len(entry.subentries)).to_equal(1)
    subentry = next(iter(entry.subentries.values()))
    expect(subentry.subentry_type).to_equal(SUBENTRY_TRAVEL_TIMES)
    expect(subentry.title).to_equal("Seattle-Bellevue via I-90 (EB AM)")
    expect(subentry.data[CONF_NAME]).to_equal("Seattle-Bellevue via I-90 (EB AM)")
    expect(subentry.data[CONF_ID]).to_equal(96)


@test.cases(
    test.case(
        "invalid_api_key",
        failed_travel_time_status=400,
        abort_reason="invalid_api_key",
    ),
    test.case(
        "cannot_connect", failed_travel_time_status=404, abort_reason="cannot_connect"
    ),
)
async def failed_import_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    travel_time: AsyncMock = Depends(mock_travel_time),
    config_data: dict[str, Any] = Depends(mock_config_data),
    *,
    failed_travel_time_status: int,
    abort_reason: str,
) -> None:
    """Test the failure modes of a yaml import."""
    travel_time.get_travel_time.side_effect = WsdotTravelError(
        status=failed_travel_time_status
    )
    travel_time.get_all_travel_times.side_effect = WsdotTravelError(
        status=failed_travel_time_status
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data=config_data,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(abort_reason)


@test
async def incorrect_import_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _travel_time: AsyncMock = Depends(mock_travel_time),
) -> None:
    """Test a yaml import of a non-existent route."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={
            CONF_API_KEY: "abcd-5678",
            CONF_TRAVEL_TIMES: [{CONF_ID: "100001", CONF_NAME: "nowhere"}],
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("invalid_travel_time_id")


@test
async def import_integration_already_exists(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _travel_time: AsyncMock = Depends(mock_travel_time),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _entry: MockConfigEntry = Depends(mock_config_entry),
    init: MockConfigEntry = Depends(init_integration),
) -> None:
    """Test we only allow one entry per API key."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={
            CONF_API_KEY: "abcd-1234",
            CONF_TRAVEL_TIMES: [{CONF_ID: "100001", CONF_NAME: "nowhere"}],
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    _ = init


@test
async def integration_already_exists(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _travel_time: AsyncMock = Depends(mock_travel_time),
    init: MockConfigEntry = Depends(init_integration),
) -> None:
    """Test we only allow one entry per API key."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=VALID_USER_CONFIG,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    _ = init


@test
async def travel_route_already_exists(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _travel_time: AsyncMock = Depends(mock_travel_time),
    init: MockConfigEntry = Depends(init_integration),
) -> None:
    """Test we only allow choosing a travel time route once."""
    result = await hass.config_entries.subentries.async_init(
        (init.entry_id, SUBENTRY_TRAVEL_TIMES),
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input=VALID_USER_TRAVEL_TIME_CONFIG,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.skip("test relies on parametrize override of mock_subentries fixture")
async def create_travel_time_subentry() -> None:
    """Test that the user step for Travel Time works."""
