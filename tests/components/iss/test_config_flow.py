"""Test iss config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.iss.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_SHOW_ON_MAP
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
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
async def create_entry(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we can finish a config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    with patch("homeassistant.components.iss.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {}
        )

        expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
        expect(result.get("result").data).to_equal({})


@test
async def integration_already_exists(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we only allow a single config flow."""
    MockConfigEntry(domain=DOMAIN, data={}).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={}
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("single_instance_allowed")


@test
async def options(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test options flow."""
    config_entry = MockConfigEntry(domain=DOMAIN, data={})
    config_entry.add_to_hass(hass)

    with patch("homeassistant.components.iss.async_setup_entry", return_value=True):
        assert await hass.config_entries.async_setup(config_entry.entry_id)

        optionflow = await hass.config_entries.options.async_init(
            config_entry.entry_id
        )

        configured = await hass.config_entries.options.async_configure(
            optionflow["flow_id"],
            user_input={CONF_SHOW_ON_MAP: True},
        )

        expect(configured.get("type")).to_be(FlowResultType.CREATE_ENTRY)
        expect(config_entry.options).to_equal({CONF_SHOW_ON_MAP: True})
