"""Test the JustNimbus config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

from justnimbus.exceptions import InvalidClientID, JustNimbusError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.justnimbus.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .conftest import FIXTURE_OLD_USER_INPUT, FIXTURE_UNIQUE_ID, FIXTURE_USER_INPUT

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


async def _set_up_justnimbus(hass: HomeAssistant, flow_id: str) -> None:
    """Reusable successful setup of JustNimbus sensor."""
    with (
        patch("justnimbus.JustNimbusClient.get_data"),
        patch(
            "homeassistant.components.justnimbus.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            flow_id=flow_id,
            user_input=FIXTURE_USER_INPUT,
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("JustNimbus")
    expect(result2["data"]).to_equal(FIXTURE_USER_INPUT)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    await _set_up_justnimbus(hass=hass, flow_id=result["flow_id"])


@test.cases(
    test.case("invalid_client_id", side_effect=InvalidClientID(client_id="test_id"), errors={"base": "invalid_auth"}),
    test.case("justnimbus_error", side_effect=JustNimbusError, errors={"base": "cannot_connect"}),
    test.case("runtime_error", side_effect=RuntimeError, errors={"base": "unknown"}),
)
async def form_errors(
    side_effect: Exception,
    errors: dict,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "justnimbus.JustNimbusClient.get_data",
        side_effect=side_effect,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            flow_id=result["flow_id"],
            user_input=FIXTURE_USER_INPUT,
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal(errors)

    await _set_up_justnimbus(hass=hass, flow_id=result["flow_id"])


@test
async def abort_already_configured(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we abort when the device is already configured."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="JustNimbus",
        data=FIXTURE_USER_INPUT,
        unique_id=FIXTURE_UNIQUE_ID,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_be(None)

    result2 = await hass.config_entries.flow.async_configure(
        flow_id=result["flow_id"],
        user_input=FIXTURE_USER_INPUT,
    )
    expect(result2.get("type")).to_be(FlowResultType.ABORT)
    expect(result2.get("reason")).to_equal("already_configured")


@test
async def reauth_flow(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test reauth works."""
    with patch(
        "homeassistant.components.justnimbus.config_flow.justnimbus.JustNimbusClient.get_data",
        return_value=False,
    ):
        mock_config = MockConfigEntry(
            domain=DOMAIN, unique_id=FIXTURE_UNIQUE_ID, data=FIXTURE_OLD_USER_INPUT
        )
        mock_config.add_to_hass(hass)

        result = await mock_config.start_reauth_flow(hass)
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")

    with patch(
        "homeassistant.components.justnimbus.config_flow.justnimbus.JustNimbusClient.get_data",
        return_value=MagicMock(api_version="1.0.0"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], FIXTURE_USER_INPUT
        )
        await hass.async_block_till_done()

        expect(result2["type"]).to_be(FlowResultType.ABORT)
        expect(result2["reason"]).to_equal("reauth_successful")
        expect(mock_config.data).to_equal(FIXTURE_USER_INPUT)
