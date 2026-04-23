"""Test the Aquacell config flow."""

from unittest.mock import AsyncMock

from aioaquacell import ApiException, AuthenticationFailed
from tryke import Depends, expect, fixture, test

from homeassistant.components.aquacell.const import (
    CONF_BRAND,
    CONF_REFRESH_TOKEN,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.aquacell._fixtures import mock_aquacell_api, mock_setup_entry
from tests.hass_fixtures import hass, mock_network

from . import TEST_CONFIG_ENTRY, TEST_USER_INPUT


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def config_flow_already_configured(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test already configured."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            **TEST_CONFIG_ENTRY,
        },
        unique_id=TEST_CONFIG_ENTRY[CONF_EMAIL],
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_USER_INPUT,
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test
async def full_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_aquacell_api: AsyncMock = Depends(mock_aquacell_api),
) -> None:
    """Test the full config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_USER_INPUT,
    )
    await hass.async_block_till_done()

    expect(result2["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result2["title"]).to_equal(TEST_CONFIG_ENTRY[CONF_EMAIL])
    expect(result2["data"][CONF_EMAIL]).to_equal(TEST_CONFIG_ENTRY[CONF_EMAIL])
    expect(result2["data"][CONF_PASSWORD]).to_equal(TEST_CONFIG_ENTRY[CONF_PASSWORD])
    expect(result2["data"][CONF_REFRESH_TOKEN]).to_equal(
        TEST_CONFIG_ENTRY[CONF_REFRESH_TOKEN]
    )
    expect(result2["data"][CONF_BRAND]).to_equal(TEST_CONFIG_ENTRY[CONF_BRAND])
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("api_exception", ApiException, "cannot_connect"),
    test.case("timeout", TimeoutError, "cannot_connect"),
    test.case("auth_failed", AuthenticationFailed, "invalid_auth"),
    test.case("unknown", Exception, "unknown"),
)
async def form_exceptions(
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_aquacell_api: AsyncMock = Depends(mock_aquacell_api),
) -> None:
    """Test we handle form exceptions."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    mock_aquacell_api.authenticate.side_effect = exception
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )

    expect(result2["type"] is FlowResultType.FORM).to_be(True)
    expect(result2["errors"]).to_equal({"base": error})

    mock_aquacell_api.authenticate.side_effect = None

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_USER_INPUT,
    )
    await hass.async_block_till_done()

    expect(result3["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result3["title"]).to_equal(TEST_CONFIG_ENTRY[CONF_EMAIL])
    expect(result3["data"][CONF_EMAIL]).to_equal(TEST_CONFIG_ENTRY[CONF_EMAIL])
    expect(result3["data"][CONF_PASSWORD]).to_equal(TEST_CONFIG_ENTRY[CONF_PASSWORD])
    expect(result3["data"][CONF_REFRESH_TOKEN]).to_equal(
        TEST_CONFIG_ENTRY[CONF_REFRESH_TOKEN]
    )
    expect(result3["data"][CONF_BRAND]).to_equal(TEST_CONFIG_ENTRY[CONF_BRAND])
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
