"""Test the Canary config flow."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from requests import ConnectTimeout, HTTPError
from tryke import Depends, expect, fixture, test

from homeassistant.components.canary.const import (
    CONF_FFMPEG_ARGUMENTS,
    DEFAULT_FFMPEG_ARGUMENTS,
    DEFAULT_TIMEOUT,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_TIMEOUT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.components.canary import USER_INPUT, _patch_async_setup_entry, init_integration
from tests.components.canary._fixtures import (
    canary,
    canary_config_flow,
    mock_ffmpeg,
    mock_zeroconf,
)
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def user_form(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_ffmpeg: None = Depends(mock_ffmpeg),
    canary_config_flow: MagicMock = Depends(canary_config_flow),
) -> None:
    """Test we get the user initiated form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({})

    with _patch_async_setup_entry() as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )
        await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("test-username")
    expect(result["data"]).to_equal({**USER_INPUT, CONF_TIMEOUT: DEFAULT_TIMEOUT})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def user_form_cannot_connect(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_ffmpeg: None = Depends(mock_ffmpeg),
    canary_config_flow: MagicMock = Depends(canary_config_flow),
) -> None:
    """Test we handle errors that should trigger the cannot connect error."""
    canary_config_flow.side_effect = HTTPError()

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    canary_config_flow.side_effect = ConnectTimeout()

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def user_form_unexpected_exception(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_ffmpeg: None = Depends(mock_ffmpeg),
    canary_config_flow: MagicMock = Depends(canary_config_flow),
) -> None:
    """Test we handle unexpected exception."""
    canary_config_flow.side_effect = Exception()

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("unknown")


@test
async def user_form_single_instance_allowed(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_ffmpeg: None = Depends(mock_ffmpeg),
    _canary_config_flow: MagicMock = Depends(canary_config_flow),
) -> None:
    """Test that configuring more than one instance is rejected."""
    await init_integration(hass, skip_entry_setup=True)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=USER_INPUT,
    )
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("single_instance_allowed")


@test
async def options_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_ffmpeg: None = Depends(mock_ffmpeg),
    _canary: MagicMock = Depends(canary),
) -> None:
    """Test updating options."""
    with patch("homeassistant.components.canary.PLATFORMS", []):
        entry = await init_integration(hass)

    expect(entry.options[CONF_FFMPEG_ARGUMENTS]).to_equal(DEFAULT_FFMPEG_ARGUMENTS)
    expect(entry.options[CONF_TIMEOUT]).to_equal(DEFAULT_TIMEOUT)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("init")

    with _patch_async_setup_entry():
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_FFMPEG_ARGUMENTS: "-v", CONF_TIMEOUT: 7},
        )
        await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["data"][CONF_FFMPEG_ARGUMENTS]).to_equal("-v")
    expect(result["data"][CONF_TIMEOUT]).to_equal(7)
