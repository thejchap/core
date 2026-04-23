"""Tests for JVC Projector config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

from jvcprojector import JvcProjectorAuthError, JvcProjectorTimeoutError
from tryke import Depends, expect, fixture, test

from homeassistant.components.jvc_projector.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import MOCK_HOST, MOCK_PASSWORD, MOCK_PORT
from ._fixtures import mock_config_entry, mock_device, mock_setup_entry

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


async def _setup_integration(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> MockConfigEntry:
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry


@test
async def user_config_flow_success(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_device: AsyncMock = Depends(mock_device),
) -> None:
    """Test user config flow success."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: MOCK_HOST,
            CONF_PORT: MOCK_PORT,
            CONF_PASSWORD: MOCK_PASSWORD,
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"][CONF_HOST]).to_equal(MOCK_HOST)
    expect(result["data"][CONF_PORT]).to_equal(MOCK_PORT)
    expect(result["data"][CONF_PASSWORD]).to_equal(MOCK_PASSWORD)


@test
async def user_config_flow_bad_connect_errors(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_device: AsyncMock = Depends(mock_device),
) -> None:
    """Test errors when connection error occurs."""
    mock_device.connect.side_effect = JvcProjectorTimeoutError

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: MOCK_HOST, CONF_PORT: MOCK_PORT, CONF_PASSWORD: MOCK_PASSWORD},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    mock_device.connect.side_effect = None

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: MOCK_HOST, CONF_PORT: MOCK_PORT, CONF_PASSWORD: MOCK_PASSWORD},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def user_config_flow_device_exists_abort(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_device: AsyncMock = Depends(mock_device),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test flow aborts when device already configured."""
    await _setup_integration(hass, mock_config_entry)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: MOCK_HOST, CONF_PORT: MOCK_PORT, CONF_PASSWORD: MOCK_PASSWORD},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def user_config_flow_bad_host_errors(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_device: AsyncMock = Depends(mock_device),
) -> None:
    """Test errors when bad host error occurs."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: "", CONF_PORT: MOCK_PORT, CONF_PASSWORD: MOCK_PASSWORD},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "invalid_host"})

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: MOCK_HOST, CONF_PORT: MOCK_PORT, CONF_PASSWORD: MOCK_PASSWORD},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def user_config_flow_bad_auth_errors(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_device: AsyncMock = Depends(mock_device),
) -> None:
    """Test errors when bad auth error occurs."""
    mock_device.connect.side_effect = JvcProjectorAuthError

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: MOCK_HOST, CONF_PORT: MOCK_PORT, CONF_PASSWORD: MOCK_PASSWORD},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    mock_device.connect.side_effect = None

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: MOCK_HOST, CONF_PORT: MOCK_PORT, CONF_PASSWORD: MOCK_PASSWORD},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def reauth_config_flow_success(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_device: AsyncMock = Depends(mock_device),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauth config flow success."""
    mock_integration = await _setup_integration(hass, mock_config_entry)

    result = await mock_integration.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_PASSWORD: MOCK_PASSWORD}
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(mock_integration.data[CONF_HOST]).to_equal(MOCK_HOST)


@test
async def reauth_config_flow_auth_error(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_device: AsyncMock = Depends(mock_device),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauth config flow when connect fails."""
    mock_integration = await _setup_integration(hass, mock_config_entry)

    mock_device.connect.side_effect = JvcProjectorAuthError

    result = await mock_integration.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_PASSWORD: MOCK_PASSWORD}
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    mock_device.connect.side_effect = None

    result = await mock_integration.start_reauth_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_PASSWORD: MOCK_PASSWORD}
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test
async def reauth_config_flow_connect_error(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_device: AsyncMock = Depends(mock_device),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauth config flow when connect fails."""
    mock_integration = await _setup_integration(hass, mock_config_entry)

    mock_device.connect.side_effect = JvcProjectorTimeoutError

    result = await mock_integration.start_reauth_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_PASSWORD: MOCK_PASSWORD}
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    mock_device.connect.side_effect = None

    result = await mock_integration.start_reauth_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_PASSWORD: MOCK_PASSWORD}
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
