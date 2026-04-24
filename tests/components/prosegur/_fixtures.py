"""Tryke fixtures for Prosegur tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from pyprosegur.installation import Camera
from tryke import Depends, fixture

from homeassistant.components.prosegur.const import DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry

CONTRACT = "1234abcd"


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "contract": CONTRACT,
            CONF_USERNAME: "user@email.com",
            CONF_PASSWORD: "password",
            "country": "PT",
        },
    )


@fixture
def mock_list_contracts() -> list[dict[str, str]]:
    """Return list of contracts per user."""
    return [
        {"contractId": "123", "description": "a b c"},
        {"contractId": "456", "description": "x y z"},
    ]


@fixture
def mock_install() -> AsyncMock:
    """Return the mocked alarm install."""
    install = MagicMock()
    install.contract = CONTRACT
    install.cameras = [Camera("1", "test_cam")]
    install.arm = AsyncMock()
    install.disarm = AsyncMock()
    install.arm_partially = AsyncMock()
    install.get_image = AsyncMock(return_value=b"ABC")
    install.request_image = AsyncMock()
    install.data = {"contract": CONTRACT}
    install.activity = AsyncMock(return_value={"event": "armed"})
    return install


@fixture
async def init_integration(
    hass: HomeAssistant,
    _mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_install: AsyncMock = Depends(mock_install),
) -> MockConfigEntry:
    """Set up the Prosegur integration for testing."""
    _mock_config_entry.add_to_hass(hass)

    with (
        patch(
            "pyprosegur.installation.Installation.retrieve", return_value=_mock_install
        ),
        patch("pyprosegur.auth.Auth.login"),
    ):
        await hass.config_entries.async_setup(_mock_config_entry.entry_id)
        await hass.async_block_till_done()

        return _mock_config_entry
