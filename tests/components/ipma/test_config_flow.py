"""Tests for IPMA config flow."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from pyipma import IPMAException
from tryke import Depends, expect, fixture, test

from homeassistant.components.ipma.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.ipma import MockLocation
from tests.components.ipma._fixtures import init_integration
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


@fixture
def ipma_setup() -> Generator[None]:
    """Patch ipma setup entry."""
    with patch("homeassistant.components.ipma.async_setup_entry", return_value=True):
        yield


@test
async def config_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    _ipma_setup: None = Depends(ipma_setup),
) -> None:
    """Test configuration form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    test_data = {CONF_LONGITUDE: 0, CONF_LATITUDE: 0}
    with patch(
        "pyipma.location.Location.get",
        return_value=MockLocation(),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], test_data
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("HomeTown")
    expect(result["data"]).to_equal({CONF_LONGITUDE: 0, CONF_LATITUDE: 0})


@test
async def config_flow_failures(
    hass: HomeAssistant = Depends(hass_fixture),
    _ipma_setup: None = Depends(ipma_setup),
) -> None:
    """Test config flow with failures."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    test_data = {CONF_LONGITUDE: 0, CONF_LATITUDE: 0}
    with patch(
        "pyipma.location.Location.get",
        side_effect=IPMAException(),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], test_data
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "unknown"})
    with patch(
        "pyipma.location.Location.get",
        return_value=MockLocation(),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], test_data
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("HomeTown")
    expect(result["data"]).to_equal({CONF_LONGITUDE: 0, CONF_LATITUDE: 0})


@test
async def flow_entry_already_exists(
    hass: HomeAssistant = Depends(hass_fixture),
    init_integration: MockConfigEntry = Depends(init_integration),
    _ipma_setup: None = Depends(ipma_setup),
) -> None:
    """Test user input for config_entry that already exists."""
    test_data = {
        CONF_NAME: "Home",
        CONF_LONGITUDE: 0,
        CONF_LATITUDE: 0,
    }

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=test_data
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
