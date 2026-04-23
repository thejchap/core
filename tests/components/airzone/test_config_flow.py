"""Define tests for the Airzone config flow."""

from unittest.mock import patch

from aioairzone.const import API_MAC, API_SYSTEMS
from aioairzone.exceptions import (
    AirzoneError,
    HotWaterNotAvailable,
    InvalidMethod,
    InvalidSystem,
    SystemOutOfRange,
)
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.airzone.config_flow import short_mac
from homeassistant.components.airzone.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_ID, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass, mock_network

from .util import (
    CONFIG,
    CONFIG_ID1,
    HVAC_DHW_MOCK,
    HVAC_MOCK,
    HVAC_VERSION_MOCK,
    HVAC_WEBSERVER_MOCK,
    USER_INPUT,
)

DHCP_SERVICE_INFO = DhcpServiceInfo(
    hostname="airzone",
    ip="192.168.1.100",
    macaddress=dr.format_mac("E84F25000000").replace(":", ""),
)

TEST_ID = 1
TEST_IP = DHCP_SERVICE_INFO.ip
TEST_PORT = 3000


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def form(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test that the form is served with valid input."""

    with (
        patch(
            "homeassistant.components.airzone.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_dhw",
            return_value=HVAC_DHW_MOCK,
        ),
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_hvac",
            return_value=HVAC_MOCK,
        ),
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_hvac_systems",
            side_effect=SystemOutOfRange,
        ),
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_version",
            return_value=HVAC_VERSION_MOCK,
        ),
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_webserver",
            return_value=HVAC_WEBSERVER_MOCK,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )

        expect(result["type"] is FlowResultType.FORM).to_be(True)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({})

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )

        await hass.async_block_till_done()

        conf_entries = hass.config_entries.async_entries(DOMAIN)
        entry = conf_entries[0]
        expect(entry.state is ConfigEntryState.LOADED).to_be(True)

        expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
        expect(result["title"]).to_equal(
            f"Airzone {CONFIG[CONF_HOST]}:{CONFIG[CONF_PORT]}"
        )
        expect(result["data"][CONF_HOST]).to_equal(CONFIG[CONF_HOST])
        expect(result["data"][CONF_PORT]).to_equal(CONFIG[CONF_PORT])
        expect(result["data"][CONF_ID]).to_equal(CONFIG[CONF_ID])

        expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_invalid_system_id(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test Invalid System ID 0."""

    with (
        patch(
            "homeassistant.components.airzone.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_dhw",
            side_effect=HotWaterNotAvailable,
        ),
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_hvac",
            side_effect=InvalidSystem,
        ) as mock_hvac,
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_hvac_systems",
            side_effect=SystemOutOfRange,
        ),
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_version",
            return_value=HVAC_VERSION_MOCK,
        ),
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_webserver",
            side_effect=InvalidMethod,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=USER_INPUT
        )

        expect(result["type"] is FlowResultType.FORM).to_be(True)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({CONF_ID: "invalid_system_id"})

        mock_hvac.return_value = HVAC_MOCK[API_SYSTEMS][0]
        mock_hvac.side_effect = None

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], CONFIG_ID1
        )

        expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)

        await hass.async_block_till_done()

        conf_entries = hass.config_entries.async_entries(DOMAIN)
        entry = conf_entries[0]
        expect(entry.state is ConfigEntryState.LOADED).to_be(True)

        expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
        expect(result["title"]).to_equal(
            f"Airzone {CONFIG_ID1[CONF_HOST]}:{CONFIG_ID1[CONF_PORT]} #{CONFIG_ID1[CONF_ID]}"
        )
        expect(result["data"][CONF_HOST]).to_equal(CONFIG_ID1[CONF_HOST])
        expect(result["data"][CONF_PORT]).to_equal(CONFIG_ID1[CONF_PORT])
        expect(result["data"][CONF_ID]).to_equal(CONFIG_ID1[CONF_ID])

        mock_setup_entry.assert_called_once()


@test
async def form_duplicated_id(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test setting up duplicated entry."""

    config_entry = MockConfigEntry(
        minor_version=2,
        data=CONFIG,
        domain=DOMAIN,
        unique_id="airzone_unique_id",
    )
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=USER_INPUT
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test
async def connection_error(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test connection to host error."""

    with patch(
        "homeassistant.components.airzone.AirzoneLocalApi.validate",
        side_effect=AirzoneError,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=USER_INPUT
        )

        expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def dhcp_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test that DHCP discovery works."""

    with patch(
        "homeassistant.components.airzone.AirzoneLocalApi.get_version",
        return_value=HVAC_VERSION_MOCK,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            data=DHCP_SERVICE_INFO,
            context={"source": config_entries.SOURCE_DHCP},
        )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("discovered_connection")

    with (
        patch(
            "homeassistant.components.airzone.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_dhw",
            return_value=HVAC_DHW_MOCK,
        ),
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_hvac",
            return_value=HVAC_MOCK,
        ),
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_hvac_systems",
            side_effect=SystemOutOfRange,
        ),
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_version",
            return_value=HVAC_VERSION_MOCK,
        ),
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_webserver",
            return_value=HVAC_WEBSERVER_MOCK,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_PORT: TEST_PORT,
            },
        )

    expect(result2["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result2["data"]).to_equal(
        {
            CONF_HOST: TEST_IP,
            CONF_PORT: TEST_PORT,
        }
    )

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def dhcp_flow_error(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test that DHCP discovery fails."""

    with patch(
        "homeassistant.components.airzone.AirzoneLocalApi.get_version",
        side_effect=AirzoneError,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            data=DHCP_SERVICE_INFO,
            context={"source": config_entries.SOURCE_DHCP},
        )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def dhcp_connection_error(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test DHCP connection to host error."""

    with patch(
        "homeassistant.components.airzone.AirzoneLocalApi.get_version",
        return_value=HVAC_VERSION_MOCK,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            data=DHCP_SERVICE_INFO,
            context={"source": config_entries.SOURCE_DHCP},
        )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("discovered_connection")

    with patch(
        "homeassistant.components.airzone.AirzoneLocalApi.validate",
        side_effect=AirzoneError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_PORT: 3001,
            },
        )

        expect(result["errors"]).to_equal({"base": "cannot_connect"})

    with (
        patch(
            "homeassistant.components.airzone.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_dhw",
            return_value=HVAC_DHW_MOCK,
        ),
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_hvac",
            return_value=HVAC_MOCK,
        ),
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_hvac_systems",
            side_effect=SystemOutOfRange,
        ),
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_version",
            return_value=HVAC_VERSION_MOCK,
        ),
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_webserver",
            return_value=HVAC_WEBSERVER_MOCK,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_PORT: TEST_PORT,
            },
        )

        await hass.async_block_till_done()

        conf_entries = hass.config_entries.async_entries(DOMAIN)
        entry = conf_entries[0]
        expect(entry.state is ConfigEntryState.LOADED).to_be(True)

        expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
        expect(result["title"]).to_equal(
            f"Airzone {short_mac(HVAC_WEBSERVER_MOCK[API_MAC])}"
        )
        expect(result["data"][CONF_HOST]).to_equal(TEST_IP)
        expect(result["data"][CONF_PORT]).to_equal(TEST_PORT)

        mock_setup_entry.assert_called_once()


@test
async def dhcp_invalid_system_id(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test Invalid System ID 0."""

    with patch(
        "homeassistant.components.airzone.AirzoneLocalApi.get_version",
        return_value=HVAC_VERSION_MOCK,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            data=DHCP_SERVICE_INFO,
            context={"source": config_entries.SOURCE_DHCP},
        )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("discovered_connection")

    with (
        patch(
            "homeassistant.components.airzone.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_dhw",
            side_effect=HotWaterNotAvailable,
        ),
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_hvac",
            side_effect=InvalidSystem,
        ) as mock_hvac,
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_hvac_systems",
            side_effect=SystemOutOfRange,
        ),
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_version",
            return_value=HVAC_VERSION_MOCK,
        ),
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_webserver",
            side_effect=InvalidMethod,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_PORT: TEST_PORT,
            },
        )

        expect(result["type"] is FlowResultType.FORM).to_be(True)
        expect(result["step_id"]).to_equal("discovered_connection")
        expect(result["errors"]).to_equal({CONF_ID: "invalid_system_id"})

        mock_hvac.return_value = HVAC_MOCK[API_SYSTEMS][0]
        mock_hvac.side_effect = None

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_PORT: TEST_PORT,
                CONF_ID: TEST_ID,
            },
        )

        await hass.async_block_till_done()

        conf_entries = hass.config_entries.async_entries(DOMAIN)
        entry = conf_entries[0]
        expect(entry.state is ConfigEntryState.LOADED).to_be(True)

        expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
        expect(result["title"]).to_equal(
            f"Airzone {short_mac(DHCP_SERVICE_INFO.macaddress)}"
        )
        expect(result["data"][CONF_HOST]).to_equal(TEST_IP)
        expect(result["data"][CONF_PORT]).to_equal(TEST_PORT)
        expect(result["data"][CONF_ID]).to_equal(TEST_ID)

        mock_setup_entry.assert_called_once()
