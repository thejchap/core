"""Test the Tessie config flow."""

from unittest.mock import AsyncMock

from tesla_fleet_api.exceptions import InvalidToken, MissingToken, TeslaFleetError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.tessie.const import DOMAIN
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    mock_async_setup_entry,
    mock_config_flow_list_vehicles,
    mock_energy_history,
    mock_get_state,
    mock_get_state_of_all_vehicles,
    mock_live_status,
    mock_products,
    mock_request,
    mock_scopes,
    mock_site_info,
)
from .common import ERROR_CONNECTION, TEST_CONFIG

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _gs: AsyncMock = Depends(mock_get_state),
    _gsv: AsyncMock = Depends(mock_get_state_of_all_vehicles),
    _ms: AsyncMock = Depends(mock_scopes),
    _mp: AsyncMock = Depends(mock_products),
    _mr: AsyncMock = Depends(mock_request),
    _mls: AsyncMock = Depends(mock_live_status),
    _msi: AsyncMock = Depends(mock_site_info),
    _meh: AsyncMock = Depends(mock_energy_history),
) -> None:
    """Apply autouse mocks via this trigger fixture."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    list_vehicles: AsyncMock = Depends(mock_config_flow_list_vehicles),
    setup_entry: AsyncMock = Depends(mock_async_setup_entry),
) -> None:
    """Test we get the form."""
    result1 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result1["type"]).to_be(FlowResultType.FORM)
    expect(bool(result1["errors"])).to_be(False)

    result2 = await hass.config_entries.flow.async_configure(
        result1["flow_id"],
        TEST_CONFIG,
    )
    await hass.async_block_till_done()
    expect(len(setup_entry.mock_calls)).to_equal(1)
    expect(len(list_vehicles.mock_calls)).to_equal(1)

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Tessie")
    expect(result2["data"]).to_equal(TEST_CONFIG)


@test
async def abort(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _list_vehicles: AsyncMock = Depends(mock_config_flow_list_vehicles),
    _setup_entry: AsyncMock = Depends(mock_async_setup_entry),
) -> None:
    """Test a duplicate entry aborts."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data=TEST_CONFIG,
    )
    mock_entry.add_to_hass(hass)

    result1 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result1["flow_id"],
        TEST_CONFIG,
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")


@test.cases(
    test.case(
        "invalid_token",
        side_effect=InvalidToken(),
        error={CONF_ACCESS_TOKEN: "invalid_access_token"},
    ),
    test.case(
        "missing_token",
        side_effect=MissingToken(),
        error={CONF_ACCESS_TOKEN: "invalid_access_token"},
    ),
    test.case("unknown", side_effect=TeslaFleetError(), error={"base": "unknown"}),
    test.case(
        "cannot_connect", side_effect=ERROR_CONNECTION, error={"base": "cannot_connect"}
    ),
)
async def form_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    list_vehicles: AsyncMock = Depends(mock_config_flow_list_vehicles),
    _setup_entry: AsyncMock = Depends(mock_async_setup_entry),
    *,
    side_effect: BaseException,
    error: dict[str, str],
) -> None:
    """Test errors are handled."""
    result1 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    list_vehicles.side_effect = side_effect
    result2 = await hass.config_entries.flow.async_configure(
        result1["flow_id"],
        TEST_CONFIG,
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal(error)

    list_vehicles.side_effect = None
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        TEST_CONFIG,
    )
    expect("errors" not in result3).to_be(True)
    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    list_vehicles: AsyncMock = Depends(mock_config_flow_list_vehicles),
    setup_entry: AsyncMock = Depends(mock_async_setup_entry),
) -> None:
    """Test reauth flow."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data=TEST_CONFIG,
    )
    mock_entry.add_to_hass(hass)

    result1 = await mock_entry.start_reauth_flow(hass)

    expect(result1["type"]).to_be(FlowResultType.FORM)
    expect(result1["step_id"]).to_equal("reauth_confirm")
    expect(bool(result1["errors"])).to_be(False)

    result2 = await hass.config_entries.flow.async_configure(
        result1["flow_id"],
        TEST_CONFIG,
    )
    await hass.async_block_till_done()
    expect(len(setup_entry.mock_calls)).to_equal(1)
    expect(len(list_vehicles.mock_calls)).to_equal(1)

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")
    expect(mock_entry.data).to_equal(TEST_CONFIG)


@test.cases(
    test.case(
        "invalid_token",
        side_effect=InvalidToken(),
        error={CONF_ACCESS_TOKEN: "invalid_access_token"},
    ),
    test.case(
        "missing_token",
        side_effect=MissingToken(),
        error={CONF_ACCESS_TOKEN: "invalid_access_token"},
    ),
    test.case("unknown", side_effect=TeslaFleetError(), error={"base": "unknown"}),
    test.case(
        "cannot_connect", side_effect=ERROR_CONNECTION, error={"base": "cannot_connect"}
    ),
)
async def reauth_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    list_vehicles: AsyncMock = Depends(mock_config_flow_list_vehicles),
    setup_entry: AsyncMock = Depends(mock_async_setup_entry),
    *,
    side_effect: BaseException,
    error: dict[str, str],
) -> None:
    """Test reauth flows that fail."""
    list_vehicles.side_effect = side_effect

    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data=TEST_CONFIG,
    )
    mock_entry.add_to_hass(hass)

    result1 = await mock_entry.start_reauth_flow(hass)

    result2 = await hass.config_entries.flow.async_configure(
        result1["flow_id"],
        TEST_CONFIG,
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal(error)

    list_vehicles.side_effect = None
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        TEST_CONFIG,
    )
    expect("errors" not in result3).to_be(True)
    expect(result3["type"]).to_be(FlowResultType.ABORT)
    expect(result3["reason"]).to_equal("reauth_successful")
    expect(mock_entry.data).to_equal(TEST_CONFIG)
    expect(len(setup_entry.mock_calls)).to_equal(1)
