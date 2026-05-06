"""Test the World Air Quality Index (WAQI) config flow."""

from unittest.mock import AsyncMock

from aiowaqi import WAQIAuthenticationError, WAQIConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.waqi.const import CONF_STATION_NUMBER, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import (
    ATTR_LATITUDE,
    ATTR_LOCATION,
    ATTR_LONGITUDE,
    CONF_API_KEY,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    mock_config_entry,
    mock_setup_entry,
    mock_waqi,
    second_mock_config_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    _waqi: AsyncMock = Depends(mock_waqi),
) -> None:
    """Test full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: "asd"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("World Air Quality Index")
    expect(result["data"]).to_equal({CONF_API_KEY: "asd"})
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("invalid_auth", exception=WAQIAuthenticationError("Test error"), error="invalid_auth"),
    test.case("cannot_connect", exception=WAQIConnectionError("Test error"), error="cannot_connect"),
    test.case("unknown", exception=Exception("Test error"), error="unknown"),
)
async def entry_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    waqi: AsyncMock = Depends(mock_waqi),
    *,
    exception: Exception,
    error: str,
) -> None:
    """Test full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(bool(result["errors"])).to_be(False)

    waqi.get_by_ip.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: "asd"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})
    expect(result["step_id"]).to_equal("user")

    waqi.get_by_ip.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: "asd"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def duplicate_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _waqi: AsyncMock = Depends(mock_waqi),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test duplicate entry handling."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: "asd"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def full_map_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _waqi: AsyncMock = Depends(mock_waqi),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we get the form."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.subentries.async_init(
        (config_entry.entry_id, "station"),
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {"next_step_id": "map"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("map")
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            ATTR_LOCATION: {ATTR_LATITUDE: 50.0, ATTR_LONGITUDE: 10.0},
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("de Jongweg, Utrecht")
    expect(result["data"]).to_equal({CONF_STATION_NUMBER: 4584})
    expect(list(config_entry.subentries.values())[1].unique_id).to_equal("4584")


@test.cases(
    test.case("cannot_connect", exception=WAQIConnectionError("Test error"), error="cannot_connect"),
    test.case("unknown", exception=Exception("Test error"), error="unknown"),
)
async def map_flow_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    waqi: AsyncMock = Depends(mock_waqi),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    *,
    exception: Exception,
    error: str,
) -> None:
    """Test we get the form."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.subentries.async_init(
        (config_entry.entry_id, "station"),
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {"next_step_id": "map"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("map")
    expect(bool(result["errors"])).to_be(False)

    waqi.get_by_coordinates.side_effect = exception

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            ATTR_LOCATION: {ATTR_LATITUDE: 50.0, ATTR_LONGITUDE: 10.0},
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("map")
    expect(result["errors"]).to_equal({"base": error})

    waqi.get_by_coordinates.side_effect = None

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            ATTR_LOCATION: {ATTR_LATITUDE: 50.0, ATTR_LONGITUDE: 10.0},
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def map_duplicate(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _waqi: AsyncMock = Depends(mock_waqi),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    second_config_entry: MockConfigEntry = Depends(second_mock_config_entry),
) -> None:
    """Test duplicate location handling."""
    config_entry.add_to_hass(hass)
    second_config_entry.add_to_hass(hass)
    result = await hass.config_entries.subentries.async_init(
        (config_entry.entry_id, "station"),
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {"next_step_id": "map"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("map")
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            ATTR_LOCATION: {ATTR_LATITUDE: 50.0, ATTR_LONGITUDE: 10.0},
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def full_station_number_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _waqi: AsyncMock = Depends(mock_waqi),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the station number flow."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.subentries.async_init(
        (config_entry.entry_id, "station"),
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {"next_step_id": "station_number"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("station_number")
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {CONF_STATION_NUMBER: 4584},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("de Jongweg, Utrecht")
    expect(result["data"]).to_equal({CONF_STATION_NUMBER: 4584})
    expect(list(config_entry.subentries.values())[1].unique_id).to_equal("4584")


@test.cases(
    test.case("cannot_connect", exception=WAQIConnectionError("Test error"), error="cannot_connect"),
    test.case("unknown", exception=Exception("Test error"), error="unknown"),
)
async def station_number_flow_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    waqi: AsyncMock = Depends(mock_waqi),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    *,
    exception: Exception,
    error: str,
) -> None:
    """Test we get the form."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.subentries.async_init(
        (config_entry.entry_id, "station"),
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {"next_step_id": "station_number"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("station_number")
    expect(bool(result["errors"])).to_be(False)

    waqi.get_by_station_number.side_effect = exception

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {CONF_STATION_NUMBER: 4584},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("station_number")
    expect(result["errors"]).to_equal({"base": error})

    waqi.get_by_station_number.side_effect = None

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {CONF_STATION_NUMBER: 4584},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def station_number_duplicate(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _waqi: AsyncMock = Depends(mock_waqi),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    second_config_entry: MockConfigEntry = Depends(second_mock_config_entry),
) -> None:
    """Test duplicate station number handling."""
    config_entry.add_to_hass(hass)
    second_config_entry.add_to_hass(hass)
    result = await hass.config_entries.subentries.async_init(
        (config_entry.entry_id, "station"),
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {"next_step_id": "station_number"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("station_number")
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {CONF_STATION_NUMBER: 4584},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
