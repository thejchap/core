"""Test the Downloader config flow."""

from unittest.mock import MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.downloader.const import CONF_DOWNLOAD_DIR, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.downloader._fixtures import mock_zeroconf
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


CONFIG = {CONF_DOWNLOAD_DIR: "download_dir"}


@test
async def user_form(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=CONFIG,
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)

    with patch("os.path.isdir", return_value=False):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONFIG,
        )
        expect(result["type"] is FlowResultType.FORM).to_be(True)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({"base": "directory_does_not_exist"})

    with (
        patch(
            "homeassistant.components.downloader.async_setup_entry", return_value=True
        ),
        patch(
            "os.path.isdir",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONFIG,
        )
        await hass.async_block_till_done()
        expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
        expect(result["title"]).to_equal("Downloader")
        expect(result["data"]).to_equal({"download_dir": "download_dir"})


@test
async def single_instance_allowed(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test we abort if already setup."""
    mock_config_entry = MockConfigEntry(domain=DOMAIN)
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("single_instance_allowed")
