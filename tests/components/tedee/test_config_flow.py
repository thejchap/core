"""Test the Tedee config flow."""

from unittest.mock import MagicMock, patch

from aiotedee import (
    TedeeClientException,
    TedeeDataUpdateException,
    TedeeLocalAuthException,
)
from aiotedee.models import TedeeBridge
from tryke import Depends, expect, fixture, test

from homeassistant.components.tedee.const import CONF_LOCAL_ACCESS_TOKEN, DOMAIN
from homeassistant.config_entries import SOURCE_USER, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_WEBHOOK_ID
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import WEBHOOK_ID, mock_config_entry, mock_tedee

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

FLOW_UNIQUE_ID = "112233445566778899"
LOCAL_ACCESS_TOKEN = "api_token"


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _tedee: MagicMock = Depends(mock_tedee),
) -> None:
    """Test config flow with one bridge."""
    with patch(
        "homeassistant.components.tedee.config_flow.webhook_generate_id",
        return_value=WEBHOOK_ID,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        await hass.async_block_till_done()
        expect(result["type"]).to_be(FlowResultType.FORM)

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.62",
                CONF_LOCAL_ACCESS_TOKEN: "token",
            },
        )

        expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result2["data"]).to_equal(
            {
                CONF_HOST: "192.168.1.62",
                CONF_LOCAL_ACCESS_TOKEN: "token",
                CONF_WEBHOOK_ID: WEBHOOK_ID,
            }
        )


@test
async def flow_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _tedee: MagicMock = Depends(mock_tedee),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test config flow aborts when already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.1.62",
            CONF_LOCAL_ACCESS_TOKEN: "token",
        },
    )
    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")


@test.cases(
    test.case(
        "invalid_host",
        side_effect=TedeeClientException("boom."),
        error={CONF_HOST: "invalid_host"},
    ),
    test.case(
        "invalid_api_key",
        side_effect=TedeeLocalAuthException("boom."),
        error={CONF_LOCAL_ACCESS_TOKEN: "invalid_api_key"},
    ),
    test.case(
        "cannot_connect",
        side_effect=TedeeDataUpdateException("boom."),
        error={"base": "cannot_connect"},
    ),
)
async def config_flow_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tedee: MagicMock = Depends(mock_tedee),
    *,
    side_effect: Exception,
    error: dict[str, str],
) -> None:
    """Test the config flow errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)

    tedee.get_local_bridge.side_effect = side_effect

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.1.42",
            CONF_LOCAL_ACCESS_TOKEN: "wrong_token",
        },
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal(error)
    expect(len(tedee.get_local_bridge.mock_calls)).to_equal(1)


@test
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _tedee: MagicMock = Depends(mock_tedee),
) -> None:
    """Test that the reauth flow works."""
    config_entry.add_to_hass(hass)

    reauth_result = await config_entry.start_reauth_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        reauth_result["flow_id"],
        {
            CONF_LOCAL_ACCESS_TOKEN: LOCAL_ACCESS_TOKEN,
        },
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


async def _do_reconfigure_flow(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> ConfigFlowResult:
    """Initialize a reconfigure flow."""
    config_entry.add_to_hass(hass)

    reconfigure_result = await config_entry.start_reconfigure_flow(hass)

    expect(reconfigure_result["type"]).to_be(FlowResultType.FORM)
    expect(reconfigure_result["step_id"]).to_equal("reconfigure")

    return await hass.config_entries.flow.async_configure(
        reconfigure_result["flow_id"],
        {CONF_LOCAL_ACCESS_TOKEN: LOCAL_ACCESS_TOKEN, CONF_HOST: "192.168.1.43"},
    )


@test
async def reconfigure_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _tedee: MagicMock = Depends(mock_tedee),
) -> None:
    """Test that the reconfigure flow works."""
    result = await _do_reconfigure_flow(hass, config_entry)

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")

    entry = hass.config_entries.async_get_entry(config_entry.entry_id)
    expect(entry is not None).to_be(True)
    expect(entry.title).to_equal("My Tedee")
    expect(entry.data).to_equal(
        {
            CONF_HOST: "192.168.1.43",
            CONF_LOCAL_ACCESS_TOKEN: LOCAL_ACCESS_TOKEN,
            CONF_WEBHOOK_ID: WEBHOOK_ID,
        }
    )


@test
async def reconfigure_unique_id_mismatch(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    tedee: MagicMock = Depends(mock_tedee),
) -> None:
    """Ensure reconfigure flow aborts when the bride changes."""
    tedee.get_local_bridge.return_value = TedeeBridge(0, "1111-1111", "Bridge-R2D2")

    result = await _do_reconfigure_flow(hass, config_entry)

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unique_id_mismatch")
