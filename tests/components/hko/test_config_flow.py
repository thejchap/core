"""Test the Hong Kong Observatory config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

from hko import HKOError
from tryke import Depends, expect, fixture, test

from homeassistant.components.hko.const import DEFAULT_LOCATION, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_LOCATION
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

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
async def config_flow_default(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test user config flow with default fields."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(SOURCE_USER)
    expect("flow_id" in result).to_be(True)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_LOCATION: DEFAULT_LOCATION},
    )

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(DEFAULT_LOCATION)
    expect(result2["result"].unique_id).to_equal(DEFAULT_LOCATION)
    expect(result2["data"][CONF_LOCATION]).to_equal(DEFAULT_LOCATION)


@test
async def config_flow_cannot_connect(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user config flow without connection to the API."""
    with patch("homeassistant.components.hko.config_flow.HKO.weather") as client_mock:
        client_mock.side_effect = HKOError()
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={CONF_LOCATION: DEFAULT_LOCATION},
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]["base"]).to_equal("cannot_connect")

        client_mock.side_effect = None

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={CONF_LOCATION: DEFAULT_LOCATION},
        )

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["result"].unique_id).to_equal(DEFAULT_LOCATION)
        expect(result["data"][CONF_LOCATION]).to_equal(DEFAULT_LOCATION)


@test
async def config_flow_timeout(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test user config flow with timedout connection to the API."""
    with patch("homeassistant.components.hko.config_flow.HKO.weather") as client_mock:
        client_mock.side_effect = TimeoutError()
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={CONF_LOCATION: DEFAULT_LOCATION},
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]["base"]).to_equal("unknown")

        client_mock.side_effect = None

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={CONF_LOCATION: DEFAULT_LOCATION},
        )

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["result"].unique_id).to_equal(DEFAULT_LOCATION)
        expect(result["data"][CONF_LOCATION]).to_equal(DEFAULT_LOCATION)


@test
async def config_flow_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user config flow with two equal entries."""
    r1 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(r1["type"]).to_be(FlowResultType.FORM)
    expect(r1["step_id"]).to_equal(SOURCE_USER)
    expect("flow_id" in r1).to_be(True)
    result1 = await hass.config_entries.flow.async_configure(
        r1["flow_id"],
        user_input={CONF_LOCATION: DEFAULT_LOCATION},
    )
    expect(result1["type"]).to_be(FlowResultType.CREATE_ENTRY)

    r2 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(r2["type"]).to_be(FlowResultType.FORM)
    expect(r2["step_id"]).to_equal(SOURCE_USER)
    expect("flow_id" in r2).to_be(True)
    result2 = await hass.config_entries.flow.async_configure(
        r2["flow_id"],
        user_input={CONF_LOCATION: DEFAULT_LOCATION},
    )
    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")
