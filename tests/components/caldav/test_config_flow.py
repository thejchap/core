"""Test the CalDAV config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, Mock

import requests
from caldav.lib.error import AuthorizationError, DAVError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.caldav.const import DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_URL, CONF_USERNAME, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.caldav._fixtures import (
    TEST_PASSWORD,
    TEST_URL,
    TEST_USERNAME,
    config_entry,
    dav_client,
    mock_patch_platforms,
    mock_setup_entry,
    mock_zeroconf,
)
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def form(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_patch_platforms: None = Depends(mock_patch_platforms),
    _dav_client: Mock = Depends(dav_client),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test successful config flow setup."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result.get("type") is FlowResultType.FORM).to_be(True)
    expect(bool(result.get("errors"))).to_be(False)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_URL: TEST_URL,
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_VERIFY_SSL: False,
        },
    )
    await hass.async_block_till_done()

    expect(result2.get("type") is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result2.get("title")).to_equal(TEST_USERNAME)
    expect(result2.get("data")).to_equal(
        {
            CONF_URL: TEST_URL,
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_VERIFY_SSL: False,
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("unknown", Exception(), "unknown"),
    test.case("cannot_connect_connection", requests.ConnectionError(), "cannot_connect"),
    test.case("cannot_connect_dav", DAVError(), "cannot_connect"),
    test.case(
        "invalid_auth",
        AuthorizationError(reason="Unauthorized"),
        "invalid_auth",
    ),
    test.case(
        "cannot_connect_auth_other",
        AuthorizationError(reason="Other"),
        "cannot_connect",
    ),
)
async def caldav_client_error(
    side_effect: Exception,
    expected_error: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_patch_platforms: None = Depends(mock_patch_platforms),
    dav_client: Mock = Depends(dav_client),
) -> None:
    """Test CalDav client errors during configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    dav_client.return_value.principal.side_effect = side_effect

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_URL: TEST_URL,
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
        },
    )
    await hass.async_block_till_done()

    expect(result2.get("type") is FlowResultType.FORM).to_be(True)
    expect(result2.get("errors")).to_equal({"base": expected_error})


@test
async def reauth_success(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_patch_platforms: None = Depends(mock_patch_platforms),
    _dav_client: Mock = Depends(dav_client),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test reauthentication configuration flow."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "password-2"},
    )
    await hass.async_block_till_done()

    expect(result2.get("type") is FlowResultType.ABORT).to_be(True)
    expect(result2.get("reason")).to_equal("reauth_successful")

    expect(dict(config_entry.data)).to_equal(
        {
            CONF_URL: "https://example.com/url-1",
            CONF_USERNAME: "username-1",
            CONF_PASSWORD: "password-2",
            CONF_VERIFY_SSL: True,
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def reauth_failure(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_patch_platforms: None = Depends(mock_patch_platforms),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(config_entry),
    dav_client: Mock = Depends(dav_client),
) -> None:
    """Test a failure during reauthentication configuration flow."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reauth_confirm")

    dav_client.return_value.principal.side_effect = DAVError

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "password-2"},
    )
    await hass.async_block_till_done()

    expect(result2.get("type") is FlowResultType.FORM).to_be(True)
    expect(result2.get("errors")).to_equal({"base": "cannot_connect"})

    dav_client.return_value.principal.side_effect = None
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "password-3"},
    )
    await hass.async_block_till_done()

    expect(result2.get("type") is FlowResultType.ABORT).to_be(True)
    expect(result2.get("reason")).to_equal("reauth_successful")

    expect(dict(config_entry.data)).to_equal(
        {
            CONF_URL: "https://example.com/url-1",
            CONF_USERNAME: "username-1",
            CONF_PASSWORD: "password-3",
            CONF_VERIFY_SSL: True,
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "different_path",
        {
            CONF_URL: f"{TEST_URL}/different-path",
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
        },
    ),
    test.case(
        "different_user",
        {
            CONF_URL: TEST_URL,
            CONF_USERNAME: f"{TEST_USERNAME}-different-user",
            CONF_PASSWORD: TEST_PASSWORD,
        },
    ),
)
async def multiple_config_entries(
    user_input: dict[str, str],
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_patch_platforms: None = Depends(mock_patch_platforms),
    _dav_client: Mock = Depends(dav_client),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test multiple configuration entries with unique settings."""
    config_entry.add_to_hass(hass)
    entries = hass.config_entries.async_entries(DOMAIN)
    expect(len(entries)).to_equal(1)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result.get("type") is FlowResultType.FORM).to_be(True)
    expect(bool(result.get("errors"))).to_be(False)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input,
    )
    await hass.async_block_till_done()

    expect(result2.get("type") is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result2.get("title")).to_equal(user_input[CONF_USERNAME])
    expect(result2.get("data")).to_equal({**user_input, CONF_VERIFY_SSL: True})
    expect(len(mock_setup_entry.mock_calls)).to_equal(2)
    entries = hass.config_entries.async_entries(DOMAIN)
    expect(len(entries)).to_equal(2)


@test.cases(
    test.case(
        "same_password",
        {
            CONF_URL: TEST_URL,
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
        },
    ),
    test.case(
        "different_password",
        {
            CONF_URL: TEST_URL,
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: f"{TEST_PASSWORD}-different",
        },
    ),
)
async def duplicate_config_entries(
    user_input: dict[str, str],
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_patch_platforms: None = Depends(mock_patch_platforms),
    _dav_client: Mock = Depends(dav_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test multiple configuration entries with the same settings."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result.get("type") is FlowResultType.FORM).to_be(True)
    expect(bool(result.get("errors"))).to_be(False)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input,
    )
    await hass.async_block_till_done()

    expect(result2.get("type") is FlowResultType.ABORT).to_be(True)
    expect(result2.get("reason")).to_equal("already_configured")
