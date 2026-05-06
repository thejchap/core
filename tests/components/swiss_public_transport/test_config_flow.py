"""Test the swiss_public_transport config flow."""

from unittest.mock import AsyncMock, patch

from opendata_transport.exceptions import (
    OpendataTransportConnectionError,
    OpendataTransportError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.swiss_public_transport import config_flow
from homeassistant.components.swiss_public_transport.const import (
    CONF_DESTINATION,
    CONF_START,
    CONF_TIME_FIXED,
    CONF_TIME_MODE,
    CONF_TIME_OFFSET,
    CONF_TIME_STATION,
    CONF_VIA,
    MAX_VIA,
)
from homeassistant.components.swiss_public_transport.helper import unique_id_from_config
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

MOCK_USER_DATA_STEP = {
    CONF_START: "test_start",
    CONF_DESTINATION: "test_destination",
    CONF_TIME_STATION: "departure",
    CONF_TIME_MODE: "now",
}

MOCK_USER_DATA_STEP_ONE_VIA = {
    **MOCK_USER_DATA_STEP,
    CONF_VIA: ["via_station"],
}

MOCK_USER_DATA_STEP_MANY_VIA = {
    **MOCK_USER_DATA_STEP,
    CONF_VIA: ["via_station_1", "via_station_2", "via_station_3"],
}

MOCK_USER_DATA_STEP_TOO_MANY_STATIONS = {
    **MOCK_USER_DATA_STEP,
    CONF_VIA: MOCK_USER_DATA_STEP_ONE_VIA[CONF_VIA] * (MAX_VIA + 1),
}

MOCK_USER_DATA_STEP_ARRIVAL = {
    **MOCK_USER_DATA_STEP,
    CONF_TIME_STATION: "arrival",
}

MOCK_USER_DATA_STEP_TIME_FIXED = {
    **MOCK_USER_DATA_STEP,
    CONF_TIME_MODE: "fixed",
}

MOCK_USER_DATA_STEP_TIME_FIXED_OFFSET = {
    **MOCK_USER_DATA_STEP,
    CONF_TIME_MODE: "offset",
}

MOCK_USER_DATA_STEP_BAD = {
    **MOCK_USER_DATA_STEP,
    CONF_TIME_MODE: "bad",
}

MOCK_ADVANCED_DATA_STEP_TIME = {
    CONF_TIME_FIXED: "18:03:00",
}

MOCK_ADVANCED_DATA_STEP_TIME_OFFSET = {
    CONF_TIME_OFFSET: {"hours": 0, "minutes": 10, "seconds": 0},
}


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.cases(
    test.case(
        "default",
        user_input=MOCK_USER_DATA_STEP,
        time_mode_input=None,
        config_title="test_start test_destination",
    ),
    test.case(
        "one_via",
        user_input=MOCK_USER_DATA_STEP_ONE_VIA,
        time_mode_input=None,
        config_title="test_start test_destination via via_station",
    ),
    test.case(
        "many_via",
        user_input=MOCK_USER_DATA_STEP_MANY_VIA,
        time_mode_input=None,
        config_title="test_start test_destination via via_station_1, via_station_2, via_station_3",
    ),
    test.case(
        "arrival",
        user_input=MOCK_USER_DATA_STEP_ARRIVAL,
        time_mode_input=None,
        config_title="test_start test_destination arrival",
    ),
    test.case(
        "time_fixed",
        user_input=MOCK_USER_DATA_STEP_TIME_FIXED,
        time_mode_input=MOCK_ADVANCED_DATA_STEP_TIME,
        config_title="test_start test_destination at 18:03:00",
    ),
    test.case(
        "time_fixed_offset",
        user_input=MOCK_USER_DATA_STEP_TIME_FIXED_OFFSET,
        time_mode_input=MOCK_ADVANCED_DATA_STEP_TIME_OFFSET,
        config_title="test_start test_destination in 00:10:00",
    ),
)
async def flow_user_init_data_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    user_input: dict,
    time_mode_input: dict | None,
    config_title: str,
) -> None:
    """Test success response."""
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN, context={"source": "user"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["handler"]).to_equal("swiss_public_transport")
    expect(result["data_schema"]).to_equal(config_flow.USER_DATA_SCHEMA)

    with patch(
        "homeassistant.components.swiss_public_transport.config_flow.OpendataTransport.async_get_data",
        autospec=True,
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=user_input,
        )

        if time_mode_input:
            expect(result["type"]).to_be(FlowResultType.FORM)
            if CONF_TIME_FIXED in time_mode_input:
                expect(result["step_id"]).to_equal("time_fixed")
            if CONF_TIME_OFFSET in time_mode_input:
                expect(result["step_id"]).to_equal("time_offset")
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input=time_mode_input,
            )

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["result"].title).to_equal(config_title)

        expect(result["data"]).to_equal({**user_input, **(time_mode_input or {})})


@test.cases(
    test.case(
        "cannot_connect",
        raise_error=OpendataTransportConnectionError(),
        text_error="cannot_connect",
        user_input_error=MOCK_USER_DATA_STEP,
    ),
    test.case(
        "bad_config",
        raise_error=OpendataTransportError(),
        text_error="bad_config",
        user_input_error=MOCK_USER_DATA_STEP,
    ),
    test.case(
        "too_many_via",
        raise_error=None,
        text_error="too_many_via_stations",
        user_input_error=MOCK_USER_DATA_STEP_TOO_MANY_STATIONS,
    ),
    test.case(
        "unknown",
        raise_error=IndexError(),
        text_error="unknown",
        user_input_error=MOCK_USER_DATA_STEP,
    ),
)
async def flow_user_init_data_error_and_recover_on_step_1(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    raise_error: Exception | None,
    text_error: str,
    user_input_error: dict,
) -> None:
    """Test errors in user step."""
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN, context={"source": "user"}
    )
    with patch(
        "homeassistant.components.swiss_public_transport.config_flow.OpendataTransport.async_get_data",
        autospec=True,
        side_effect=raise_error,
    ) as mock_OpendataTransport:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=user_input_error,
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]["base"]).to_equal(text_error)

        mock_OpendataTransport.side_effect = None
        mock_OpendataTransport.return_value = True
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=MOCK_USER_DATA_STEP,
        )

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["result"].title).to_equal("test_start test_destination")

        expect(result["data"]).to_equal(MOCK_USER_DATA_STEP)


@test.cases(
    test.case(
        "cannot_connect",
        raise_error=OpendataTransportConnectionError(),
        text_error="cannot_connect",
        user_input=MOCK_ADVANCED_DATA_STEP_TIME,
    ),
    test.case(
        "bad_config",
        raise_error=OpendataTransportError(),
        text_error="bad_config",
        user_input=MOCK_ADVANCED_DATA_STEP_TIME,
    ),
    test.case(
        "unknown",
        raise_error=IndexError(),
        text_error="unknown",
        user_input=MOCK_ADVANCED_DATA_STEP_TIME,
    ),
)
async def flow_user_init_data_error_and_recover_on_step_2(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    raise_error: Exception,
    text_error: str,
    user_input: dict,
) -> None:
    """Test errors in time mode step."""
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN, context={"source": "user"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["handler"]).to_equal("swiss_public_transport")
    expect(result["data_schema"]).to_equal(config_flow.USER_DATA_SCHEMA)

    with patch(
        "homeassistant.components.swiss_public_transport.config_flow.OpendataTransport.async_get_data",
        autospec=True,
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=MOCK_USER_DATA_STEP_TIME_FIXED,
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("time_fixed")

    with patch(
        "homeassistant.components.swiss_public_transport.config_flow.OpendataTransport.async_get_data",
        autospec=True,
        side_effect=raise_error,
    ) as mock_OpendataTransport:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=user_input,
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]["base"]).to_equal(text_error)

        mock_OpendataTransport.side_effect = None
        mock_OpendataTransport.return_value = True
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=user_input,
        )

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["result"].title).to_equal(
            "test_start test_destination at 18:03:00"
        )


@test
async def flow_user_init_data_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort user data set when entry is already configured."""

    entry = MockConfigEntry(
        domain=config_flow.DOMAIN,
        data=MOCK_USER_DATA_STEP,
        unique_id=unique_id_from_config(MOCK_USER_DATA_STEP),
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.swiss_public_transport.config_flow.OpendataTransport.async_get_data",
        autospec=True,
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_init(
            config_flow.DOMAIN, context={"source": "user"}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=MOCK_USER_DATA_STEP,
        )

        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("already_configured")
