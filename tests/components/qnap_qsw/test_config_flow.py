"""Define tests for the QNAP QSW config flow."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from aioqsw.const import API_MAC_ADDR, API_PRODUCT, API_RESULT
from aioqsw.exceptions import LoginError, QswError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.qnap_qsw.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, ConfigEntryState
from homeassistant.const import CONF_PASSWORD, CONF_URL, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from .util import CONFIG, LIVE_MOCK, SYSTEM_BOARD_MOCK, USERS_LOGIN_MOCK

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

DHCP_SERVICE_INFO = DhcpServiceInfo(
    hostname="qsw-m408-4c",
    ip="192.168.1.200",
    macaddress="245ebe000000",
)

TEST_PASSWORD = "test-password"
TEST_URL = f"http://{DHCP_SERVICE_INFO.ip}"
TEST_USERNAME = "test-username"


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def form(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test that the form is served with valid input."""
    with (
        patch(
            "homeassistant.components.qnap_qsw.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.qnap_qsw.QnapQswApi.get_live",
            return_value=LIVE_MOCK,
        ),
        patch(
            "homeassistant.components.qnap_qsw.QnapQswApi.get_system_board",
            return_value=SYSTEM_BOARD_MOCK,
        ),
        patch(
            "homeassistant.components.qnap_qsw.QnapQswApi.post_users_login",
            return_value=USERS_LOGIN_MOCK,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({})

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], CONFIG
        )

        await hass.async_block_till_done()

        conf_entries = hass.config_entries.async_entries(DOMAIN)
        entry = conf_entries[0]
        expect(entry.state).to_be(ConfigEntryState.LOADED)

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal(
            f"QNAP {SYSTEM_BOARD_MOCK[API_RESULT][API_PRODUCT]} {SYSTEM_BOARD_MOCK[API_RESULT][API_MAC_ADDR]}"
        )
        expect(result["data"][CONF_URL]).to_equal(CONFIG[CONF_URL])
        expect(result["data"][CONF_USERNAME]).to_equal(CONFIG[CONF_USERNAME])
        expect(result["data"][CONF_PASSWORD]).to_equal(CONFIG[CONF_PASSWORD])

        expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_duplicated_id(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test setting up duplicated entry."""
    system_board = MagicMock()
    system_board.get_mac = MagicMock(
        return_value=SYSTEM_BOARD_MOCK[API_RESULT][API_MAC_ADDR]
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG,
        unique_id=format_mac(SYSTEM_BOARD_MOCK[API_RESULT][API_MAC_ADDR]),
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.qnap_qsw.QnapQswApi.validate",
        return_value=system_board,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONFIG
        )

        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("already_configured")


@test
async def form_unique_id_error(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test unique ID error."""
    system_board = MagicMock()
    system_board.get_mac = MagicMock(return_value=None)

    with patch(
        "homeassistant.components.qnap_qsw.QnapQswApi.validate",
        return_value=system_board,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONFIG
        )

        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("invalid_id")


@test
async def connection_error(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test connection to host error."""
    with patch(
        "homeassistant.components.qnap_qsw.QnapQswApi.validate",
        side_effect=QswError,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONFIG
        )

        expect(result["errors"]).to_equal({CONF_URL: "cannot_connect"})


@test
async def login_error(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test login error."""
    with patch(
        "homeassistant.components.qnap_qsw.QnapQswApi.validate",
        side_effect=LoginError,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONFIG
        )

        expect(result["errors"]).to_equal({CONF_PASSWORD: "invalid_auth"})


@test
async def dhcp_flow(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test that DHCP discovery works."""
    with patch(
        "homeassistant.components.qnap_qsw.QnapQswApi.get_live",
        return_value=LIVE_MOCK,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            data=DHCP_SERVICE_INFO,
            context={"source": config_entries.SOURCE_DHCP},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovered_connection")

    with (
        patch(
            "homeassistant.components.qnap_qsw.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.qnap_qsw.QnapQswApi.get_live",
            return_value=LIVE_MOCK,
        ),
        patch(
            "homeassistant.components.qnap_qsw.QnapQswApi.get_system_board",
            return_value=SYSTEM_BOARD_MOCK,
        ),
        patch(
            "homeassistant.components.qnap_qsw.QnapQswApi.post_users_login",
            return_value=USERS_LOGIN_MOCK,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: TEST_USERNAME,
                CONF_PASSWORD: TEST_PASSWORD,
            },
        )

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["data"]).to_equal(
        {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_URL: TEST_URL,
        }
    )

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def dhcp_flow_error(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test that DHCP discovery fails."""
    with patch(
        "homeassistant.components.qnap_qsw.QnapQswApi.get_live",
        side_effect=QswError,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            data=DHCP_SERVICE_INFO,
            context={"source": config_entries.SOURCE_DHCP},
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def dhcp_connection_error(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test DHCP connection to host error."""
    with patch(
        "homeassistant.components.qnap_qsw.QnapQswApi.get_live",
        return_value=LIVE_MOCK,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            data=DHCP_SERVICE_INFO,
            context={"source": config_entries.SOURCE_DHCP},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovered_connection")

    with patch(
        "homeassistant.components.qnap_qsw.QnapQswApi.validate",
        side_effect=QswError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: TEST_USERNAME,
                CONF_PASSWORD: TEST_PASSWORD,
            },
        )

        expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def dhcp_login_error(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test DHCP login error."""
    with patch(
        "homeassistant.components.qnap_qsw.QnapQswApi.get_live",
        return_value=LIVE_MOCK,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            data=DHCP_SERVICE_INFO,
            context={"source": config_entries.SOURCE_DHCP},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovered_connection")

    with patch(
        "homeassistant.components.qnap_qsw.QnapQswApi.validate",
        side_effect=LoginError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: TEST_USERNAME,
                CONF_PASSWORD: TEST_PASSWORD,
            },
        )

        expect(result["errors"]).to_equal({CONF_PASSWORD: "invalid_auth"})
