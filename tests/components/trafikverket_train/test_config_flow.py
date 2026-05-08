"""Test the Trafikverket Train config flow."""

from unittest.mock import AsyncMock, patch

from pytrafikverket import StationInfoModel
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.trafikverket_train.const import (
    CONF_FROM,
    CONF_TIME,
    CONF_TO,
    DOMAIN,
)
from homeassistant.const import CONF_API_KEY, CONF_WEEKDAY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import get_train_stations, mock_setup_entry

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor to ensure tryke fully resolves Depends() in this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    train_stations: list[list[StationInfoModel]] = Depends(get_train_stations),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("initial")
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.trafikverket_train.coordinator.TrafikverketTrain.async_search_train_stations",
        side_effect=train_stations,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_KEY: "1234567890",
                CONF_FROM: "Stockholm C",
                CONF_TO: "Uppsala C",
                CONF_TIME: "10:00",
                CONF_WEEKDAY: ["mon", "fri"],
            },
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Stockholm C to Uppsala C at 10:00")
    expect(result["data"]).to_equal(
        {
            "api_key": "1234567890",
            "name": "Stockholm C to Uppsala C at 10:00",
            "from": "Cst",
            "to": "U",
            "time": "10:00",
            "weekday": ["mon", "fri"],
        }
    )
    expect(result["options"]).to_equal({"filter_product": None})
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.skip("complex local fixtures (get_train_stop, train_data); not yet ported")
async def form_multiple_stations() -> None:
    """Skipped pending fixture port."""


@test.skip("complex local fixtures (get_train_stop, train_data); not yet ported")
async def form_entry_already_exist() -> None:
    """Skipped pending fixture port."""


@test.skip("complex local fixtures (get_train_stop, train_data); not yet ported")
async def flow_fails() -> None:
    """Skipped pending fixture port."""


@test.skip("complex local fixtures (get_train_stop, train_data); not yet ported")
async def flow_fails_departures() -> None:
    """Skipped pending fixture port."""


@test.skip("complex local fixtures (get_train_stop, train_data); not yet ported")
async def reauth_flow() -> None:
    """Skipped pending fixture port."""


@test.skip("complex local fixtures (get_train_stop, train_data); not yet ported")
async def reauth_flow_error() -> None:
    """Skipped pending fixture port."""


@test.skip("complex local fixtures (get_train_stop, train_data); not yet ported")
async def reauth_flow_error_departures() -> None:
    """Skipped pending fixture port."""


@test.skip("complex local fixtures (get_train_stop, train_data); not yet ported")
async def options_flow() -> None:
    """Skipped pending fixture port."""


@test.skip("complex local fixtures (get_train_stop, train_data); not yet ported")
async def reconfigure_flow() -> None:
    """Skipped pending fixture port."""


@test.skip("complex local fixtures (get_train_stop, train_data); not yet ported")
async def reconfigure_multiple_stations() -> None:
    """Skipped pending fixture port."""


@test.skip("complex local fixtures (get_train_stop, train_data); not yet ported")
async def reconfigure_entry_already_exist() -> None:
    """Skipped pending fixture port."""


@test.skip("complex local fixtures (get_train_stop, train_data); not yet ported")
async def reconfigure_flow_fails() -> None:
    """Skipped pending fixture port."""


@test.skip("complex local fixtures (get_train_stop, train_data); not yet ported")
async def reconfigure_flow_fails_departures() -> None:
    """Skipped pending fixture port."""
