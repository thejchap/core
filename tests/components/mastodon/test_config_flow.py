"""Tests for the Mastodon config flow."""

from unittest.mock import AsyncMock, patch

from mastodon.Mastodon import (
    MastodonNetworkError,
    MastodonNotFoundError,
    MastodonUnauthorizedError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.mastodon.const import CONF_BASE_URL, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_config_entry, mock_mastodon_client, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _mn: None = Depends(mock_network),
    _mmc: AsyncMock = Depends(mock_mastodon_client),
    _mse: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Trigger the hook executor path."""
    return None


@test
async def full_flow(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_BASE_URL: "https://mastodon.social",
            CONF_CLIENT_ID: "client_id",
            CONF_CLIENT_SECRET: "client_secret",
            CONF_ACCESS_TOKEN: "access_token",
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("@trwnh@mastodon.social")
    expect(result["data"]).to_equal(
        {
            CONF_BASE_URL: "https://mastodon.social",
            CONF_CLIENT_ID: "client_id",
            CONF_CLIENT_SECRET: "client_secret",
            CONF_ACCESS_TOKEN: "access_token",
        }
    )
    expect(result["result"].unique_id).to_equal("trwnh_mastodon_social")


@test
async def full_flow_with_path(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test full flow, where a path is accidentally specified."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_BASE_URL: "https://mastodon.social/home",
            CONF_CLIENT_ID: "client_id",
            CONF_CLIENT_SECRET: "client_secret",
            CONF_ACCESS_TOKEN: "access_token",
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("@trwnh@mastodon.social")
    expect(result["data"]).to_equal(
        {
            CONF_BASE_URL: "https://mastodon.social",
            CONF_CLIENT_ID: "client_id",
            CONF_CLIENT_SECRET: "client_secret",
            CONF_ACCESS_TOKEN: "access_token",
        }
    )
    expect(result["result"].unique_id).to_equal("trwnh_mastodon_social")


@test
async def full_flow_fallback_to_instance_v1(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_client: AsyncMock = Depends(mock_mastodon_client),
) -> None:
    """Test full flow where instance_v2 fails and falls back to instance_v1."""
    mock_client.instance_v2.side_effect = MastodonNotFoundError(
        "Instance API v2 not found"
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_BASE_URL: "https://mastodon.social",
            CONF_CLIENT_ID: "client_id",
            CONF_CLIENT_SECRET: "client_secret",
            CONF_ACCESS_TOKEN: "access_token",
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("@trwnh@mastodon.social")
    expect(result["data"]).to_equal(
        {
            CONF_BASE_URL: "https://mastodon.social",
            CONF_CLIENT_ID: "client_id",
            CONF_CLIENT_SECRET: "client_secret",
            CONF_ACCESS_TOKEN: "access_token",
        }
    )
    expect(result["result"].unique_id).to_equal("trwnh_mastodon_social")

    mock_client.instance_v2.assert_called_once()
    mock_client.instance_v1.assert_called_once()


@test.cases(
    test.case("network_error", MastodonNetworkError, "network_error"),
    test.case("unauthorized_error", MastodonUnauthorizedError, "unauthorized_error"),
    test.case("unknown", Exception, "unknown"),
)
async def flow_errors(
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_client: AsyncMock = Depends(mock_mastodon_client),
) -> None:
    """Test flow errors."""
    mock_client.account_verify_credentials.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_BASE_URL: "https://mastodon.social",
            CONF_CLIENT_ID: "client_id",
            CONF_CLIENT_SECRET: "client_secret",
            CONF_ACCESS_TOKEN: "access_token",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    mock_client.account_verify_credentials.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_BASE_URL: "https://mastodon.social",
            CONF_CLIENT_ID: "client_id",
            CONF_CLIENT_SECRET: "client_secret",
            CONF_ACCESS_TOKEN: "access_token",
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def duplicate(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test duplicate flow."""
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_BASE_URL: "https://mastodon.social",
            CONF_CLIENT_ID: "client_id",
            CONF_CLIENT_SECRET: "client_secret",
            CONF_ACCESS_TOKEN: "access_token",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reauth_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauth flow."""
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_ACCESS_TOKEN: "token2"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(entry.data[CONF_ACCESS_TOKEN]).to_equal("token2")


@test
async def reauth_flow_wrong_account(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauth flow with wrong account."""
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    with patch(
        "homeassistant.components.mastodon.config_flow.construct_mastodon_username",
        return_value="BAD_USERNAME",
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ACCESS_TOKEN: "token2"},
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("wrong_account")


@test.cases(
    test.case("network_error", MastodonNetworkError, "network_error"),
    test.case("unauthorized_error", MastodonUnauthorizedError, "unauthorized_error"),
    test.case("unknown", Exception, "unknown"),
)
async def reauth_flow_exceptions(
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_client: AsyncMock = Depends(mock_mastodon_client),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauth flow errors."""
    entry.add_to_hass(hass)
    mock_client.account_verify_credentials.side_effect = exception

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_ACCESS_TOKEN: "token"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({"base": error})

    mock_client.account_verify_credentials.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_ACCESS_TOKEN: "token"},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test
async def reconfigure_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfigure flow."""
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_CLIENT_ID: "client_id2",
            CONF_CLIENT_SECRET: "client_secret2",
            CONF_ACCESS_TOKEN: "access_token2",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(entry.data[CONF_BASE_URL]).to_equal("https://mastodon.social")
    expect(entry.data[CONF_CLIENT_ID]).to_equal("client_id2")
    expect(entry.data[CONF_CLIENT_SECRET]).to_equal("client_secret2")
    expect(entry.data[CONF_ACCESS_TOKEN]).to_equal("access_token2")


@test
async def reconfigure_flow_wrong_account(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfigure flow with wrong account."""
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    with patch(
        "homeassistant.components.mastodon.config_flow.construct_mastodon_username",
        return_value="WRONG_USERNAME",
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CLIENT_ID: "client_id",
                CONF_CLIENT_SECRET: "client_secret",
                CONF_ACCESS_TOKEN: "access_token2",
            },
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("wrong_account")


@test.cases(
    test.case("network_error", MastodonNetworkError, "network_error"),
    test.case("unauthorized_error", MastodonUnauthorizedError, "unauthorized_error"),
    test.case("unknown", Exception, "unknown"),
)
async def reconfigure_flow_exceptions(
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_client: AsyncMock = Depends(mock_mastodon_client),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfigure flow errors."""
    entry.add_to_hass(hass)
    mock_client.account_verify_credentials.side_effect = exception

    result = await entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_CLIENT_ID: "client_id",
            CONF_CLIENT_SECRET: "client_secret",
            CONF_ACCESS_TOKEN: "access_token",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["errors"]).to_equal({"base": error})

    mock_client.account_verify_credentials.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_CLIENT_ID: "client_id",
            CONF_CLIENT_SECRET: "client_secret",
            CONF_ACCESS_TOKEN: "access_token",
        },
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
