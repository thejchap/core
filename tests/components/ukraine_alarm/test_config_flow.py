"""Test the Ukraine Alarm config flow."""

from unittest.mock import AsyncMock, patch

from aiohttp import ClientConnectionError, ClientError, ClientResponseError, RequestInfo
from tryke import Depends, expect, fixture, test
from yarl import URL

from homeassistant import config_entries
from homeassistant.components.ukraine_alarm.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_get_regions

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _regions: AsyncMock = Depends(mock_get_regions),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def state_district(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can create entry for state + district."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result2 = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result2["type"]).to_be(FlowResultType.FORM)

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "region": "2",
        },
    )
    expect(result3["type"]).to_be(FlowResultType.FORM)

    with patch(
        "homeassistant.components.ukraine_alarm.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result4 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "region": "2.2",
            },
        )
        await hass.async_block_till_done()

    expect(result4["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result4["title"]).to_equal("District 2.2")
    expect(result4["data"]).to_equal(
        {
            "region": "2.2",
            "name": result4["title"],
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def state_district_community(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can create entry for state + district + community."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
    )
    expect(result2["type"]).to_be(FlowResultType.FORM)

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "region": "3",
        },
    )
    expect(result3["type"]).to_be(FlowResultType.FORM)

    result4 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "region": "3.2",
        },
    )
    expect(result4["type"]).to_be(FlowResultType.FORM)

    with patch(
        "homeassistant.components.ukraine_alarm.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result5 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "region": "3.2.1",
            },
        )
        await hass.async_block_till_done()

    expect(result5["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result5["title"]).to_equal("Community 3.2.1")
    expect(result5["data"]).to_equal(
        {
            "region": "3.2.1",
            "name": result5["title"],
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def max_regions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test max regions config."""
    for i in range(5):
        MockConfigEntry(
            domain=DOMAIN,
            unique_id=i,
        ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("max_regions")


@test
async def rate_limit(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    regions: AsyncMock = Depends(mock_get_regions),
) -> None:
    """Test rate limit error."""
    regions.side_effect = ClientResponseError(None, None, status=429)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("rate_limit")


@test
async def server_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    regions: AsyncMock = Depends(mock_get_regions),
) -> None:
    """Test server error."""
    regions.side_effect = ClientResponseError(
        RequestInfo(None, None, None, real_url=URL("/regions")), None, status=500
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unknown")


@test
async def cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    regions: AsyncMock = Depends(mock_get_regions),
) -> None:
    """Test connection error."""
    regions.side_effect = ClientConnectionError
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def unknown_client_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    regions: AsyncMock = Depends(mock_get_regions),
) -> None:
    """Test client error."""
    regions.side_effect = ClientError
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unknown")


@test
async def timeout_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    regions: AsyncMock = Depends(mock_get_regions),
) -> None:
    """Test timeout error."""
    regions.side_effect = TimeoutError
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("timeout")


@test
async def no_regions_returned(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    regions: AsyncMock = Depends(mock_get_regions),
) -> None:
    """Test regions not returned."""
    regions.return_value = {}
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unknown")
