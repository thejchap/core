"""Test the Aussie Broadband config flow."""

from unittest.mock import patch

from aiohttp import ClientConnectionError
from aussiebb.asyncio import AuthenticationException
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.aussie_broadband.const import DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .common import FAKE_DATA, FAKE_SERVICES

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass, mock_network

TEST_USERNAME = FAKE_DATA[CONF_USERNAME]
TEST_PASSWORD = FAKE_DATA[CONF_PASSWORD]


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def form(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test we get the form."""
    result1 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result1["type"] is FlowResultType.FORM).to_be(True)
    expect(result1["errors"] is None).to_be(True)

    with (
        patch("aussiebb.asyncio.AussieBB.__init__", return_value=None),
        patch("aussiebb.asyncio.AussieBB.login", return_value=True),
        patch("aussiebb.asyncio.AussieBB.get_services", return_value=FAKE_SERVICES),
        patch(
            "homeassistant.components.aussie_broadband.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result1["flow_id"],
            FAKE_DATA,
        )
        await hass.async_block_till_done()

    expect(result2["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result2["title"]).to_equal(TEST_USERNAME)
    expect(result2["data"]).to_equal(FAKE_DATA)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def already_configured(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test already configured."""
    result1 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with (
        patch("aussiebb.asyncio.AussieBB.__init__", return_value=None),
        patch("aussiebb.asyncio.AussieBB.login", return_value=True),
        patch(
            "aussiebb.asyncio.AussieBB.get_services", return_value=[FAKE_SERVICES[0]]
        ),
        patch(
            "homeassistant.components.aussie_broadband.async_setup_entry",
            return_value=True,
        ),
    ):
        await hass.config_entries.flow.async_configure(
            result1["flow_id"],
            FAKE_DATA,
        )
        await hass.async_block_till_done()

    result3 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with (
        patch("aussiebb.asyncio.AussieBB.__init__", return_value=None),
        patch("aussiebb.asyncio.AussieBB.login", return_value=True),
        patch(
            "aussiebb.asyncio.AussieBB.get_services", return_value=[FAKE_SERVICES[0]]
        ),
        patch(
            "homeassistant.components.aussie_broadband.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result4 = await hass.config_entries.flow.async_configure(
            result3["flow_id"],
            FAKE_DATA,
        )
        await hass.async_block_till_done()

    expect(result4["type"] is FlowResultType.ABORT).to_be(True)
    expect(len(mock_setup_entry.mock_calls)).to_equal(0)


@test
async def no_services(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test when there are no services."""
    result1 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result1["type"] is FlowResultType.FORM).to_be(True)
    expect(result1["errors"] is None).to_be(True)

    with (
        patch("aussiebb.asyncio.AussieBB.__init__", return_value=None),
        patch("aussiebb.asyncio.AussieBB.login", return_value=True),
        patch("aussiebb.asyncio.AussieBB.get_services", return_value=[]),
        patch(
            "homeassistant.components.aussie_broadband.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result1["flow_id"],
            FAKE_DATA,
        )
        await hass.async_block_till_done()

    expect(result2["type"] is FlowResultType.ABORT).to_be(True)
    expect(result2["reason"]).to_equal("no_services_found")
    expect(len(mock_setup_entry.mock_calls)).to_equal(0)


@test
async def form_invalid_auth(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test invalid auth is handled."""
    result1 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with (
        patch("aussiebb.asyncio.AussieBB.__init__", return_value=None),
        patch("aussiebb.asyncio.AussieBB.login", side_effect=AuthenticationException()),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result1["flow_id"],
            FAKE_DATA,
        )

    expect(result2["type"] is FlowResultType.FORM).to_be(True)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def form_network_issue(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test network issues are handled."""
    result1 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with (
        patch("aussiebb.asyncio.AussieBB.__init__", return_value=None),
        patch("aussiebb.asyncio.AussieBB.login", side_effect=ClientConnectionError()),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result1["flow_id"],
            FAKE_DATA,
        )

    expect(result2["type"] is FlowResultType.FORM).to_be(True)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def reauth(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test reauth flow."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data=FAKE_DATA,
        unique_id=FAKE_DATA[CONF_USERNAME],
    )
    mock_entry.add_to_hass(hass)

    result5 = await mock_entry.start_reauth_flow(hass)
    expect(result5["step_id"]).to_equal("reauth_confirm")

    with (
        patch("aussiebb.asyncio.AussieBB.__init__", return_value=None),
        patch("aussiebb.asyncio.AussieBB.login", side_effect=AuthenticationException()),
        patch(
            "aussiebb.asyncio.AussieBB.get_services", return_value=[FAKE_SERVICES[0]]
        ),
    ):
        result6 = await hass.config_entries.flow.async_configure(
            result5["flow_id"],
            {
                CONF_PASSWORD: "test-wrongpassword",
            },
        )
        await hass.async_block_till_done()

        expect(result6["step_id"]).to_equal("reauth_confirm")

    with (
        patch("aussiebb.asyncio.AussieBB.__init__", return_value=None),
        patch("aussiebb.asyncio.AussieBB.login", return_value=True),
        patch(
            "aussiebb.asyncio.AussieBB.get_services", return_value=[FAKE_SERVICES[0]]
        ),
    ):
        result7 = await hass.config_entries.flow.async_configure(
            result6["flow_id"],
            {
                CONF_PASSWORD: "test-newpassword",
            },
        )
        await hass.async_block_till_done()

        expect(result7["type"] is FlowResultType.ABORT).to_be(True)
        expect(result7["reason"]).to_equal("reauth_successful")
