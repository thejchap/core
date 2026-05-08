"""Test EnergyID config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

from aiohttp import ClientError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.energyid.const import (
    CONF_DEVICE_ID,
    CONF_PROVISIONING_KEY,
    CONF_PROVISIONING_SECRET,
    DOMAIN,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_polling_interval, mock_setup_entry

from tests.hass_fixtures import hass as hass_fixture, mock_network

TEST_PROVISIONING_KEY = "test_prov_key"
TEST_PROVISIONING_SECRET = "test_prov_secret"
TEST_RECORD_NUMBER = "site_12345"
TEST_RECORD_NAME = "My Test Site"


@fixture
def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
    _network: None = Depends(mock_network),
    _polling: int = Depends(mock_polling_interval),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> HomeAssistant:
    """Anchor fixture so tryke fully resolves hass."""
    return hass


@test
async def config_flow_user_step_success_claimed(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user step where device is already claimed."""
    mock_client = MagicMock()
    mock_client.authenticate = AsyncMock(return_value=True)
    mock_client.recordNumber = TEST_RECORD_NUMBER
    mock_client.recordName = TEST_RECORD_NAME

    with patch(
        "homeassistant.components.energyid.config_flow.WebhookClient",
        return_value=mock_client,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_PROVISIONING_KEY: TEST_PROVISIONING_KEY,
                CONF_PROVISIONING_SECRET: TEST_PROVISIONING_SECRET,
            },
        )
        await hass.async_block_till_done()

        expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result2["title"]).to_equal(TEST_RECORD_NAME)
        expect(result2["data"][CONF_PROVISIONING_KEY]).to_equal(TEST_PROVISIONING_KEY)
        expect(result2["data"][CONF_PROVISIONING_SECRET]).to_equal(
            TEST_PROVISIONING_SECRET
        )

        entry = hass.config_entries.async_get_entry(result2["result"].entry_id)
        expect(entry.unique_id is not None).to_be(True)
        expect(entry.unique_id.startswith("homeassistant_eid_")).to_be(True)
        expect(CONF_DEVICE_ID in entry.data).to_be(True)
        expect(entry.data[CONF_DEVICE_ID]).to_equal(entry.unique_id)


@test
async def config_flow_connection_error(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test connection error during authentication."""
    with patch(
        "homeassistant.components.energyid.config_flow.WebhookClient.authenticate",
        side_effect=ClientError("Connection failed"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_PROVISIONING_KEY: TEST_PROVISIONING_KEY,
                CONF_PROVISIONING_SECRET: TEST_PROVISIONING_SECRET,
            },
        )
        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["errors"]["base"]).to_equal("cannot_connect")


@test
async def config_flow_unexpected_error(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test unexpected error during authentication."""
    with patch(
        "homeassistant.components.energyid.config_flow.WebhookClient.authenticate",
        side_effect=Exception("Unexpected error"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_PROVISIONING_KEY: TEST_PROVISIONING_KEY,
                CONF_PROVISIONING_SECRET: TEST_PROVISIONING_SECRET,
            },
        )
        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["errors"]["base"]).to_equal("unknown_auth_error")


@test.skip("auth_and_claim_step requires polling logic, not yet ported")
async def config_flow_auth_and_claim_step_success(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test auth_and_claim step where the device becomes claimed after polling."""


@test.skip("auth_and_claim_step requires polling logic, not yet ported")
async def config_flow_claim_timeout(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test claim timeout."""


@test.skip("requires multi-flow with mock state tracking")
async def duplicate_unique_id_prevented(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test duplicate unique id prevention."""


@test.skip("requires multi-flow with mock state tracking")
async def multiple_different_devices_allowed(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test multiple different devices allowed."""


@test.skip("external step polling not yet ported")
async def config_flow_external_step_claimed_during_display(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test external step claimed during display."""


@test.skip("complex polling not yet ported")
async def config_flow_auth_and_claim_step_not_claimed(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test auth_and_claim where device stays not claimed."""


@test.skip("reauth flow not yet ported")
async def config_flow_reauth_success(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test reauth success flow."""


@test.skip("client_response_error parametrize not yet ported")
async def config_flow_client_response_error(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test client response error handling."""


@test.skip("reauth_needs_claim flow not yet ported")
async def config_flow_reauth_needs_claim(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test reauth needs claim."""


@test.skip("subentry types not yet ported")
async def async_get_supported_subentry_types(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test supported subentry types."""


@test.skip("polling stops on auth error not yet ported")
async def polling_stops_on_invalid_auth_error(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test polling stops on invalid auth error."""


@test.skip("polling stops on connect error not yet ported")
async def polling_stops_on_cannot_connect_error(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test polling stops on connect error."""


@test.skip("auth_and_claim subsequent auth error not yet ported")
async def auth_and_claim_subsequent_auth_error(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test auth_and_claim subsequent auth error."""


@test.skip("reauth with error not yet ported")
async def reauth_with_error(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test reauth with error."""
