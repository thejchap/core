"""Test the Homeassistant Analytics config flow."""

from typing import Any
from unittest.mock import AsyncMock

from python_homeassistant_analytics import HomeassistantAnalyticsConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.analytics_insights.const import (
    CONF_TRACKED_APPS,
    CONF_TRACKED_CUSTOM_INTEGRATIONS,
    CONF_TRACKED_INTEGRATIONS,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.analytics_insights._fixtures import (
    mock_analytics_client,
    mock_config_entry,
    mock_setup_entry,
    mock_zeroconf,
)
from tests.hass_fixtures import hass, mock_network

from . import setup_integration


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


FULL_INPUT = {
    CONF_TRACKED_APPS: ["core_samba"],
    CONF_TRACKED_INTEGRATIONS: ["youtube"],
    CONF_TRACKED_CUSTOM_INTEGRATIONS: ["hacs"],
}
INTEGRATIONS_ONLY_INPUT = {CONF_TRACKED_INTEGRATIONS: ["youtube"]}
CUSTOM_INTEGRATIONS_ONLY_INPUT = {CONF_TRACKED_CUSTOM_INTEGRATIONS: ["hacs"]}


@test.cases(
    test.case("full", FULL_INPUT, FULL_INPUT),
    test.case(
        "integrations_only",
        INTEGRATIONS_ONLY_INPUT,
        {
            CONF_TRACKED_APPS: [],
            CONF_TRACKED_INTEGRATIONS: ["youtube"],
            CONF_TRACKED_CUSTOM_INTEGRATIONS: [],
        },
    ),
    test.case(
        "custom_integrations_only",
        CUSTOM_INTEGRATIONS_ONLY_INPUT,
        {
            CONF_TRACKED_APPS: [],
            CONF_TRACKED_INTEGRATIONS: [],
            CONF_TRACKED_CUSTOM_INTEGRATIONS: ["hacs"],
        },
    ),
)
async def form(
    user_input: dict[str, Any],
    expected_options: dict[str, Any],
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_analytics_client: AsyncMock = Depends(mock_analytics_client),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input,
    )
    await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("Home Assistant Analytics Insights")
    expect(result["data"]).to_equal({})
    expect(result["options"]).to_equal(expected_options)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "all_empty",
        {
            CONF_TRACKED_APPS: [],
            CONF_TRACKED_INTEGRATIONS: [],
            CONF_TRACKED_CUSTOM_INTEGRATIONS: [],
        },
    ),
    test.case("empty_dict", {}),
)
async def submitting_empty_form(
    user_input: dict[str, Any],
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_analytics_client: AsyncMock = Depends(mock_analytics_client),
) -> None:
    """Test we can't submit an empty form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input,
    )
    await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({"base": "no_integrations_selected"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        FULL_INPUT,
    )
    await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("Home Assistant Analytics Insights")
    expect(result["data"]).to_equal({})
    expect(result["options"]).to_equal(FULL_INPUT)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "cannot_connect", HomeassistantAnalyticsConnectionError, "cannot_connect"
    ),
    test.case("unknown", Exception, "unknown"),
)
async def form_cannot_connect(
    exception: type[Exception],
    reason: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_analytics_client: AsyncMock = Depends(mock_analytics_client),
) -> None:
    """Test we handle cannot connect error."""
    mock_analytics_client.get_integrations.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal(reason)


@test
async def form_already_configured(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we handle cannot connect error."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={
            CONF_TRACKED_APPS: [],
            CONF_TRACKED_INTEGRATIONS: ["youtube", "spotify"],
            CONF_TRACKED_CUSTOM_INTEGRATIONS: [],
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("single_instance_allowed")


@test.cases(
    test.case("full", FULL_INPUT, FULL_INPUT),
    test.case(
        "apps_only",
        {CONF_TRACKED_APPS: ["core_samba"]},
        {
            CONF_TRACKED_APPS: ["core_samba"],
            CONF_TRACKED_INTEGRATIONS: [],
            CONF_TRACKED_CUSTOM_INTEGRATIONS: [],
        },
    ),
    test.case(
        "integrations_only",
        INTEGRATIONS_ONLY_INPUT,
        {
            CONF_TRACKED_APPS: [],
            CONF_TRACKED_INTEGRATIONS: ["youtube"],
            CONF_TRACKED_CUSTOM_INTEGRATIONS: [],
        },
    ),
    test.case(
        "custom_integrations_only",
        CUSTOM_INTEGRATIONS_ONLY_INPUT,
        {
            CONF_TRACKED_APPS: [],
            CONF_TRACKED_INTEGRATIONS: [],
            CONF_TRACKED_CUSTOM_INTEGRATIONS: ["hacs"],
        },
    ),
)
async def options_flow(
    user_input: dict[str, Any],
    expected_options: dict[str, Any],
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: None = Depends(mock_zeroconf),
    mock_analytics_client: AsyncMock = Depends(mock_analytics_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test options flow."""
    await setup_integration(hass, mock_config_entry)
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    expect(result["type"] is FlowResultType.FORM).to_be(True)

    mock_analytics_client.get_integrations.reset_mock()
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input,
    )
    await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["data"]).to_equal(expected_options)
    await hass.async_block_till_done()
    mock_analytics_client.get_integrations.assert_called_once()


@test.cases(
    test.case(
        "all_empty",
        {
            CONF_TRACKED_APPS: [],
            CONF_TRACKED_INTEGRATIONS: [],
            CONF_TRACKED_CUSTOM_INTEGRATIONS: [],
        },
    ),
    test.case("empty_dict", {}),
)
async def submitting_empty_options_flow(
    user_input: dict[str, Any],
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: None = Depends(mock_zeroconf),
    _mock_analytics_client: AsyncMock = Depends(mock_analytics_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test options flow."""
    await setup_integration(hass, mock_config_entry)
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    expect(result["type"] is FlowResultType.FORM).to_be(True)

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input,
    )
    await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({"base": "no_integrations_selected"})

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_TRACKED_APPS: ["core_samba"],
            CONF_TRACKED_INTEGRATIONS: ["youtube", "hue"],
            CONF_TRACKED_CUSTOM_INTEGRATIONS: ["hacs"],
        },
    )
    await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["data"]).to_equal(
        {
            CONF_TRACKED_APPS: ["core_samba"],
            CONF_TRACKED_INTEGRATIONS: ["youtube", "hue"],
            CONF_TRACKED_CUSTOM_INTEGRATIONS: ["hacs"],
        }
    )
    await hass.async_block_till_done()


@test
async def options_flow_cannot_connect(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: None = Depends(mock_zeroconf),
    mock_analytics_client: AsyncMock = Depends(mock_analytics_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we handle cannot connect error."""
    mock_analytics_client.get_integrations.side_effect = (
        HomeassistantAnalyticsConnectionError
    )
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("cannot_connect")
