"""Test the FAA Delays config flow."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from aiohttp import ClientConnectionError
import faadelays
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.faa_delays.const import DOMAIN
from homeassistant.const import CONF_ID
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import HomeAssistantError

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

mock_network = mock_network  # noqa: F811


@fixture
def _mock_zeroconf() -> Generator[MagicMock]:
    from zeroconf import DNSCache  # noqa: PLC0415

    with (
        patch("homeassistant.components.zeroconf.HaZeroconf") as mock_zc,
        patch(
            "homeassistant.components.zeroconf.discovery.AsyncServiceBrowser",
        ) as mock_browser,
    ):
        asb = mock_browser.return_value
        asb.async_cancel = AsyncMock()
        zc = mock_zc.return_value
        zc.cache = DNSCache()
        yield mock_zc


@fixture
def _trigger_executor(
    _mn: None = Depends(mock_network),
    _mz: MagicMock = Depends(_mock_zeroconf),
) -> None:
    """Trigger the hook executor path with zeroconf/network mocked."""
    return None


async def mock_valid_airport(self, *args, **kwargs):
    """Return a valid airport."""
    self.code = "test"


@test
async def form(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch.object(faadelays.Airport, "update", new=mock_valid_airport),
        patch(
            "homeassistant.components.faa_delays.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"id": "test"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("test")
    expect(result2["data"]).to_equal({"id": "test"})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def duplicate_error(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test that we handle a duplicate configuration."""
    conf = {CONF_ID: "test"}

    MockConfigEntry(domain=DOMAIN, unique_id="test", data=conf).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=conf
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def form_cannot_connect(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle a connection error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch("faadelays.Airport.update", side_effect=ClientConnectionError):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"id": "test"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_unexpected_exception(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle an unexpected exception."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch("faadelays.Airport.update", side_effect=HomeAssistantError):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"id": "test"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})
