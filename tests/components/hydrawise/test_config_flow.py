"""Test the Hydrawise config flow."""

from unittest.mock import AsyncMock

from aiohttp import ClientError
from pydrawise.exceptions import NotAuthorizedError
from pydrawise.schema import User
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.hydrawise.const import DOMAIN
from homeassistant.const import CONF_API_KEY, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_auth, mock_pydrawise, mock_setup_entry, user

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Apply autouse-equivalent fixtures."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    auth: AsyncMock = Depends(mock_auth),
    pydrawise: AsyncMock = Depends(mock_pydrawise),
    user_obj: User = Depends(user),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "asdf@asdf.com",
            CONF_PASSWORD: "__password__",
            CONF_API_KEY: "__api-key__",
        },
    )
    pydrawise.get_user.return_value = user_obj
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("asdf@asdf.com")
    expect(result["data"]).to_equal(
        {
            CONF_USERNAME: "asdf@asdf.com",
            CONF_PASSWORD: "__password__",
            CONF_API_KEY: "__api-key__",
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)
    auth.check.assert_awaited_once_with()
    pydrawise.get_user.assert_awaited_once_with(fetch_zones=False)


@test
async def form_api_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _auth: AsyncMock = Depends(mock_auth),
    pydrawise: AsyncMock = Depends(mock_pydrawise),
    user_obj: User = Depends(user),
) -> None:
    """Test we handle API errors."""
    pydrawise.get_user.side_effect = ClientError("XXX")

    init_result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    data = {
        CONF_USERNAME: "asdf@asdf.com",
        CONF_PASSWORD: "__password__",
        CONF_API_KEY: "__api-key__",
    }
    result = await hass.config_entries.flow.async_configure(
        init_result["flow_id"], data
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    pydrawise.get_user.reset_mock(side_effect=True)
    pydrawise.get_user.return_value = user_obj
    result = await hass.config_entries.flow.async_configure(result["flow_id"], data)
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def form_auth_connect_timeout(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    auth: AsyncMock = Depends(mock_auth),
    _pydrawise: AsyncMock = Depends(mock_pydrawise),
) -> None:
    """Test we handle connection timeout errors."""
    auth.check.side_effect = TimeoutError
    init_result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    data = {
        CONF_USERNAME: "asdf@asdf.com",
        CONF_PASSWORD: "__password__",
        CONF_API_KEY: "__api-key__",
    }
    result = await hass.config_entries.flow.async_configure(
        init_result["flow_id"], data
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "timeout_connect"})

    auth.check.reset_mock(side_effect=True)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], data)
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def form_client_connect_timeout(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _auth: AsyncMock = Depends(mock_auth),
    pydrawise: AsyncMock = Depends(mock_pydrawise),
    user_obj: User = Depends(user),
) -> None:
    """Test we handle API errors."""
    pydrawise.get_user.side_effect = TimeoutError
    init_result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    data = {
        CONF_USERNAME: "asdf@asdf.com",
        CONF_PASSWORD: "__password__",
        CONF_API_KEY: "__api-key__",
    }
    result = await hass.config_entries.flow.async_configure(
        init_result["flow_id"], data
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "timeout_connect"})

    pydrawise.get_user.reset_mock(side_effect=True)
    pydrawise.get_user.return_value = user_obj
    result = await hass.config_entries.flow.async_configure(result["flow_id"], data)
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def form_not_authorized_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    auth: AsyncMock = Depends(mock_auth),
    _pydrawise: AsyncMock = Depends(mock_pydrawise),
) -> None:
    """Test we handle API errors."""
    auth.check.side_effect = NotAuthorizedError

    init_result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    data = {
        CONF_USERNAME: "asdf@asdf.com",
        CONF_PASSWORD: "__password__",
        CONF_API_KEY: "__api-key__",
    }
    result = await hass.config_entries.flow.async_configure(
        init_result["flow_id"], data
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    auth.check.reset_mock(side_effect=True)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], data)
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    user_obj: User = Depends(user),
    _auth: AsyncMock = Depends(mock_auth),
    pydrawise: AsyncMock = Depends(mock_pydrawise),
) -> None:
    """Test that re-authorization works."""
    mock_config_entry = MockConfigEntry(
        title="Hydrawise",
        domain=DOMAIN,
        data={
            CONF_USERNAME: "asdf@asdf.com",
            CONF_PASSWORD: "bad-password",
            CONF_API_KEY: "__api-key__",
        },
        unique_id="hydrawise-12345",
    )
    mock_config_entry.add_to_hass(hass)

    mock_config_entry.async_start_reauth(hass)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)
    [result] = flows
    expect(result["step_id"]).to_equal("reauth_confirm")

    pydrawise.get_user.return_value = user_obj
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_PASSWORD: "__password__",
            CONF_API_KEY: "__api-key__",
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test
async def reauth_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    auth: AsyncMock = Depends(mock_auth),
    pydrawise: AsyncMock = Depends(mock_pydrawise),
    user_obj: User = Depends(user),
) -> None:
    """Test that the reauth flow handles API errors."""
    mock_config_entry = MockConfigEntry(
        title="Hydrawise",
        domain=DOMAIN,
        data={
            CONF_USERNAME: "asdf@asdf.com",
            CONF_PASSWORD: "bad-password",
            CONF_API_KEY: "__api-key__",
        },
        unique_id="hydrawise-12345",
    )
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result["step_id"]).to_equal("reauth_confirm")

    auth.check.side_effect = NotAuthorizedError
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_PASSWORD: "__password__",
            CONF_API_KEY: "__api-key__",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    auth.check.reset_mock(side_effect=True)
    pydrawise.get_user.return_value = user_obj
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_PASSWORD: "__password__",
            CONF_API_KEY: "__api-key__",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
