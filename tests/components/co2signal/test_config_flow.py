"""Test the CO2 Signal config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from aioelectricitymaps import (
    ElectricityMapsConnectionError,
    ElectricityMapsError,
    ElectricityMapsInvalidTokenError,
    ElectricityMapsNoDataError,
)
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.co2signal import config_flow
from homeassistant.components.co2signal.const import DOMAIN
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.co2signal._fixtures import (
    config_entry,
    electricity_maps,
    mock_zeroconf,
)
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def form_home(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _electricity_maps: MagicMock = Depends(electricity_maps),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"] is None).to_be(True)

    with patch(
        "homeassistant.components.co2signal.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "location": config_flow.TYPE_USE_HOME,
                "api_key": "api_key",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result2["title"]).to_equal("Electricity Maps")
    expect(result2["data"]).to_equal({"api_key": "api_key"})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_coordinates(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _electricity_maps: MagicMock = Depends(electricity_maps),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"] is None).to_be(True)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "location": config_flow.TYPE_SPECIFY_COORDINATES,
            "api_key": "api_key",
        },
    )
    expect(result2["type"] is FlowResultType.FORM).to_be(True)

    with patch(
        "homeassistant.components.co2signal.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {"latitude": 12.3, "longitude": 45.6},
        )
        await hass.async_block_till_done()

    expect(result3["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result3["title"]).to_equal("12.3, 45.6")
    expect(result3["data"]).to_equal(
        {"latitude": 12.3, "longitude": 45.6, "api_key": "api_key"}
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_country(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _electricity_maps: MagicMock = Depends(electricity_maps),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"] is None).to_be(True)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "location": config_flow.TYPE_SPECIFY_COUNTRY,
            "api_key": "api_key",
        },
    )
    expect(result2["type"] is FlowResultType.FORM).to_be(True)

    with patch(
        "homeassistant.components.co2signal.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {"country_code": "fr"},
        )
        await hass.async_block_till_done()

    expect(result3["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result3["title"]).to_equal("fr")
    expect(result3["data"]).to_equal({"country_code": "fr", "api_key": "api_key"})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("invalid_auth", ElectricityMapsInvalidTokenError, "invalid_auth"),
    test.case("generic_error", ElectricityMapsError("Something else"), "unknown"),
    test.case("connection_error", ElectricityMapsConnectionError("Boom"), "unknown"),
    test.case("no_data_error", ElectricityMapsNoDataError("I have no data"), "no_data"),
)
async def form_error_handling(
    side_effect: Exception,
    err_code: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    electricity_maps: AsyncMock = Depends(electricity_maps),
) -> None:
    """Test we handle expected errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    electricity_maps.carbon_intensity_for_home_assistant.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "location": config_flow.TYPE_USE_HOME,
            "api_key": "api_key",
        },
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({"base": err_code})

    electricity_maps.carbon_intensity_for_home_assistant.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "location": config_flow.TYPE_USE_HOME,
            "api_key": "api_key",
        },
    )
    await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("Electricity Maps")
    expect(result["data"]).to_equal({"api_key": "api_key"})


@test
async def reauth(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    config_entry: MockConfigEntry = Depends(config_entry),
    _electricity_maps: AsyncMock = Depends(electricity_maps),
) -> None:
    """Test reauth flow."""
    config_entry.add_to_hass(hass)

    init_result = await config_entry.start_reauth_flow(hass)

    expect(init_result["type"] is FlowResultType.FORM).to_be(True)
    expect(init_result["step_id"]).to_equal("reauth_confirm")

    with patch(
        "homeassistant.components.co2signal.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        configure_result = await hass.config_entries.flow.async_configure(
            init_result["flow_id"],
            {CONF_API_KEY: "api_key2"},
        )
        await hass.async_block_till_done()

    expect(configure_result["type"] is FlowResultType.ABORT).to_be(True)
    expect(configure_result["reason"]).to_equal("reauth_successful")
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
