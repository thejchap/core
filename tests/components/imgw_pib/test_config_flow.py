"""Test the IMGW-PIB config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

from aiohttp import ClientError
from imgw_pib.exceptions import ApiError
from tryke import Depends, expect, fixture, test

from homeassistant.components.imgw_pib.const import CONF_STATION_ID, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.components.imgw_pib._fixtures import mock_imgw_pib_client, mock_setup_entry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _mock_zeroconf() -> MagicMock:
    """Patch zeroconf so tests don't require a real zeroconf instance."""
    from zeroconf import DNSCache

    with (
        patch("homeassistant.components.zeroconf.HaZeroconf") as mock_zc,
        patch("homeassistant.components.zeroconf.discovery.AsyncServiceBrowser"),
    ):
        zc = mock_zc.return_value
        zc.async_add_service_listener = AsyncMock()
        zc.async_remove_service_listener = AsyncMock()
        zc.async_register_service = AsyncMock()
        zc.async_update_service = AsyncMock()
        zc.cache = DNSCache()
        yield mock_zc


@fixture
def _trigger_executor(
    _mn: None = Depends(mock_network),
    _mz: MagicMock = Depends(_mock_zeroconf),
) -> None:
    """Trigger the hook executor path."""
    return None


@test
async def create_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_imgw_pib_client: AsyncMock = Depends(mock_imgw_pib_client),
) -> None:
    """Test that the user step works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_STATION_ID: "123"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("River Name (Station Name)")
    expect(result["data"]).to_equal({CONF_STATION_ID: "123"})
    expect(result["context"]["unique_id"]).to_equal("123")
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("api_error", exc=ApiError("API Error")),
    test.case("client_error", exc=ClientError),
    test.case("timeout", exc=TimeoutError),
)
async def form_no_station_list(
    exc: type[Exception] | Exception,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_imgw_pib_client: AsyncMock = Depends(mock_imgw_pib_client),
) -> None:
    """Test aborting the flow when we cannot get the list of hydrological stations."""
    mock_imgw_pib_client.update_hydrological_stations.side_effect = exc
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test.cases(
    test.case("unknown", exc=Exception, base_error="unknown"),
    test.case("api_error", exc=ApiError("API Error"), base_error="cannot_connect"),
    test.case("client_error", exc=ClientError, base_error="cannot_connect"),
    test.case("timeout", exc=TimeoutError, base_error="cannot_connect"),
)
async def form_with_exceptions(
    exc: type[Exception] | Exception,
    base_error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_imgw_pib_client: AsyncMock = Depends(mock_imgw_pib_client),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    mock_imgw_pib_client.get_hydrological_data.side_effect = exc
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_STATION_ID: "123"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": base_error})

    mock_imgw_pib_client.get_hydrological_data.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_STATION_ID: "123"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("River Name (Station Name)")
    expect(result["data"]).to_equal({CONF_STATION_ID: "123"})
    expect(result["context"]["unique_id"]).to_equal("123")
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
