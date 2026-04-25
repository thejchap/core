"""Tests for the OpenEVSE config flow."""

from ipaddress import ip_address
from unittest.mock import AsyncMock, MagicMock

from openevsehttp.exceptions import AuthenticationError, MissingSerial
from tryke import Depends, expect, fixture, test

from homeassistant.components.openevse.const import DOMAIN
from homeassistant.config_entries import SOURCE_IMPORT, SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._fixtures import mock_charger, mock_config_entry, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _charger: MagicMock = Depends(mock_charger),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test user flow create entry with bad charger."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "10.0.0.131"}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("OpenEVSE 10.0.0.131")
    expect(result["data"]).to_equal({CONF_HOST: "10.0.0.131"})
    expect(result["result"].unique_id).to_equal("deadbeeffeed")


@test
async def user_flow_flaky(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    charger: MagicMock = Depends(mock_charger),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test user flow create entry with flaky charger."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    charger.test_and_get.side_effect = TimeoutError
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "10.0.0.131"}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    charger.test_and_get.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "10.0.0.131"}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("OpenEVSE 10.0.0.131")
    expect(result["data"]).to_equal({CONF_HOST: "10.0.0.131"})
    expect(result["result"].unique_id).to_equal("deadbeeffeed")


@test
async def user_flow_duplicate(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _charger: MagicMock = Depends(mock_charger),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test user flow aborts when config entry already exists."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def user_flow_no_serial(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    charger: MagicMock = Depends(mock_charger),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test user flow handles missing serial gracefully."""
    charger.test_and_get.side_effect = [{}, MissingSerial]

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "10.0.0.131"}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("OpenEVSE 10.0.0.131")
    expect(result["result"].unique_id).to_be(None)


@test
async def import_flow_no_serial(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    charger: MagicMock = Depends(mock_charger),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test import flow handles missing serial gracefully."""
    charger.test_and_get.side_effect = [{}, MissingSerial]

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}, data={CONF_HOST: "10.0.0.131"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("OpenEVSE 10.0.0.131")
    expect(result["result"].unique_id).to_be(None)


@test
async def user_flow_with_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    charger: MagicMock = Depends(mock_charger),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test user flow create entry with authentication."""
    charger.test_and_get.side_effect = [
        AuthenticationError,
        {"serial": "deadbeeffeed"},
    ]
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "10.0.0.131"}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("auth")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "fakeuser", CONF_PASSWORD: "muchpassword"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("OpenEVSE 10.0.0.131")
    expect(result["data"]).to_equal(
        {
            CONF_HOST: "10.0.0.131",
            CONF_USERNAME: "fakeuser",
            CONF_PASSWORD: "muchpassword",
        }
    )
    expect(result["result"].unique_id).to_equal("deadbeeffeed")


@test
async def user_flow_with_auth_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    charger: MagicMock = Depends(mock_charger),
) -> None:
    """Test user flow create entry with authentication error."""
    charger.test_and_get.side_effect = [
        AuthenticationError,
        AuthenticationError,
        {},
    ]
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "10.0.0.131"},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("auth")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "fakeuser", CONF_PASSWORD: "muchpassword"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal("invalid_auth")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "fakeuser", CONF_PASSWORD: "muchpassword"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def user_flow_with_missing_serial(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    charger: MagicMock = Depends(mock_charger),
) -> None:
    """Test user flow create entry with authentication error."""
    charger.test_and_get.side_effect = [AuthenticationError, MissingSerial]
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "10.0.0.131"}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("auth")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "fakeuser", CONF_PASSWORD: "muchpassword"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("OpenEVSE 10.0.0.131")
    expect(result["data"]).to_equal(
        {
            CONF_HOST: "10.0.0.131",
            CONF_USERNAME: "fakeuser",
            CONF_PASSWORD: "muchpassword",
        }
    )
    expect(result["result"].unique_id).to_be(None)


@test
async def import_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _charger: MagicMock = Depends(mock_charger),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test import flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}, data={CONF_HOST: "10.0.0.131"}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("OpenEVSE 10.0.0.131")
    expect(result["data"]).to_equal({CONF_HOST: "10.0.0.131"})
    expect(result["result"].unique_id).to_equal("deadbeeffeed")


@test
async def import_flow_bad(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    charger: MagicMock = Depends(mock_charger),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test import flow with bad charger."""
    charger.test_and_get.side_effect = TimeoutError

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}, data={CONF_HOST: "10.0.0.131"}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unavailable_host")


@test
async def import_flow_duplicate(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _charger: MagicMock = Depends(mock_charger),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test import flow aborts when config entry already exists."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={CONF_HOST: "192.168.1.100"},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def zeroconf_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _charger: MagicMock = Depends(mock_charger),
) -> None:
    """Test zeroconf discovery."""
    discovery_info = ZeroconfServiceInfo(
        ip_address=ip_address("192.168.1.123"),
        ip_addresses=[ip_address("192.168.1.123")],
        hostname="openevse-deadbeeffeed.local.",
        name="openevse-deadbeeffeed._openevse._tcp.local.",
        port=80,
        properties={"id": "deadbeeffeed", "type": "openevse"},
        type="_openevse._tcp.local.",
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=discovery_info,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")
    expect(result["description_placeholders"]).to_equal(
        {"name": "OpenEVSE openevse-deadbeeffeed"}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("OpenEVSE openevse-deadbeeffeed")
    expect(result["data"]).to_equal({CONF_HOST: "192.168.1.123"})
    expect(result["result"].unique_id).to_equal("deadbeeffeed")


@test
async def zeroconf_already_configured_unique_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _charger: MagicMock = Depends(mock_charger),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test zeroconf discovery updates info if unique_id is already configured."""
    config_entry.add_to_hass(hass)

    discovery_info = ZeroconfServiceInfo(
        ip_address=ip_address("192.168.1.124"),
        ip_addresses=[ip_address("192.168.1.124"), ip_address("2001:db8::1")],
        hostname="openevse-deadbeeffeed.local.",
        name="openevse-deadbeeffeed._openevse._tcp.local.",
        port=80,
        properties={"id": "deadbeeffeed", "type": "openevse"},
        type="_openevse._tcp.local.",
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=discovery_info,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")

    expect(config_entry.data["host"]).to_equal("192.168.1.124")


@test
async def zeroconf_connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    charger: MagicMock = Depends(mock_charger),
) -> None:
    """Test zeroconf discovery with connection failure."""
    charger.test_and_get.side_effect = TimeoutError
    discovery_info = ZeroconfServiceInfo(
        ip_address=ip_address("192.168.1.123"),
        ip_addresses=[ip_address("192.168.1.123"), ip_address("2001:db8::1")],
        hostname="openevse-deadbeeffeed.local.",
        name="openevse-deadbeeffeed._openevse._tcp.local.",
        port=80,
        properties={"id": "deadbeeffeed", "type": "openevse"},
        type="_openevse._tcp.local.",
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=discovery_info,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unavailable_host")


@test
async def zeroconf_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    charger: MagicMock = Depends(mock_charger),
) -> None:
    """Test zeroconf discovery with connection failure."""
    charger.test_and_get.side_effect = [AuthenticationError, {}]
    discovery_info = ZeroconfServiceInfo(
        ip_address=ip_address("192.168.1.123"),
        ip_addresses=[ip_address("192.168.1.123"), ip_address("2001:db8::1")],
        hostname="openevse-deadbeeffeed.local.",
        name="openevse-deadbeeffeed._openevse._tcp.local.",
        port=80,
        properties={"id": "deadbeeffeed", "type": "openevse"},
        type="_openevse._tcp.local.",
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=discovery_info,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("auth")
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "fakeuser", CONF_PASSWORD: "muchpassword"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            CONF_HOST: "192.168.1.123",
            CONF_USERNAME: "fakeuser",
            CONF_PASSWORD: "muchpassword",
        }
    )


@test
async def zeroconf_auth_failure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    charger: MagicMock = Depends(mock_charger),
) -> None:
    """Test zeroconf discovery with connection failure."""
    charger.test_and_get.side_effect = [
        AuthenticationError,
        AuthenticationError,
        {},
    ]
    discovery_info = ZeroconfServiceInfo(
        ip_address=ip_address("192.168.1.123"),
        ip_addresses=[ip_address("192.168.1.123"), ip_address("2001:db8::1")],
        hostname="openevse-deadbeeffeed.local.",
        name="openevse-deadbeeffeed._openevse._tcp.local.",
        port=80,
        properties={"id": "deadbeeffeed", "type": "openevse"},
        type="_openevse._tcp.local.",
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=discovery_info,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("auth")
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "fakeuser", CONF_PASSWORD: "muchpassword"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("auth")
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "fakeuser", CONF_PASSWORD: "muchpassword"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            CONF_HOST: "192.168.1.123",
            CONF_USERNAME: "fakeuser",
            CONF_PASSWORD: "muchpassword",
        }
    )


@test
async def zeroconf_already_configured_host(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test zeroconf discovery aborts if host is already configured."""
    config_entry.add_to_hass(hass)

    discovery_info = ZeroconfServiceInfo(
        ip_address=ip_address("192.168.1.100"),
        ip_addresses=[ip_address("192.168.1.100"), ip_address("2001:db8::1")],
        hostname="openevse-deadbeeffeed.local.",
        name="openevse-deadbeeffeed._openevse._tcp.local.",
        port=80,
        properties={"id": "deadbeeffeed", "type": "openevse"},
        type="_openevse._tcp.local.",
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=discovery_info,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
