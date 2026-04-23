"""Test the OctoPrint config flow."""

from __future__ import annotations

from ipaddress import ip_address
from unittest.mock import patch

from pyoctoprintapi import ApiError, DiscoverySettings
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.octoprint.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.ssdp import SsdpServiceInfo
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def form(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_equal(False)

    with patch(
        "pyoctoprintapi.OctoprintClient.request_app_key", return_value="test-key"
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "testuser",
                "host": "1.1.1.1",
                "name": "Printer",
                "port": 81,
                "ssl": True,
                "path": "/",
            },
        )
        await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)

    with (
        patch(
            "pyoctoprintapi.OctoprintClient.get_server_info",
            return_value=True,
        ),
        patch(
            "pyoctoprintapi.OctoprintClient.get_discovery_info",
            return_value=DiscoverySettings({"upnpUuid": "uuid"}),
        ),
        patch(
            "homeassistant.components.octoprint.async_setup", return_value=True
        ) as mock_setup,
        patch(
            "homeassistant.components.octoprint.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("1.1.1.1")
    expect(result2["data"]).to_equal(
        {
            "username": "testuser",
            "host": "1.1.1.1",
            "api_key": "test-key",
            "name": "Printer",
            "port": 81,
            "ssl": True,
            "path": "/",
            "verify_ssl": True,
        }
    )
    expect(len(mock_setup.mock_calls)).to_equal(1)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_cannot_connect(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "username": "testuser",
            "host": "1.1.1.1",
            "name": "Printer",
            "port": 81,
            "ssl": True,
            "path": "/",
        },
    )
    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)

    with patch(
        "pyoctoprintapi.OctoprintClient.request_app_key", return_value="test-key"
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
        )
        await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)

    with patch(
        "pyoctoprintapi.OctoprintClient.get_discovery_info",
        side_effect=ApiError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "testuser",
                "host": "1.1.1.1",
                "name": "Printer",
                "port": 81,
                "ssl": True,
                "verify_ssl": True,
                "path": "/",
                "api_key": "test-key",
            },
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal("cannot_connect")


@test
async def form_unknown_exception(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle a random error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "username": "testuser",
            "host": "1.1.1.1",
            "name": "Printer",
            "port": 81,
            "ssl": True,
            "path": "/",
        },
    )
    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)

    with patch(
        "pyoctoprintapi.OctoprintClient.request_app_key", return_value="test-key"
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
        )
        await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)

    with patch(
        "pyoctoprintapi.OctoprintClient.get_discovery_info",
        side_effect=Exception,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "testuser",
                "host": "1.1.1.1",
                "name": "Printer",
                "port": 81,
                "ssl": True,
                "path": "/",
                "api_key": "test-key",
                "verify_ssl": True,
            },
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal("unknown")


@test
async def show_zerconf_form(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test that the zeroconf confirmation form is served."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("192.168.1.123"),
            ip_addresses=[ip_address("192.168.1.123")],
            hostname="example.local.",
            name="mock_name",
            port=80,
            properties={"uuid": "83747482", "path": "/foo/"},
            type="mock_type",
        ),
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_equal(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "username": "testuser",
        },
    )
    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)

    with patch(
        "pyoctoprintapi.OctoprintClient.request_app_key", return_value="test-key"
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)

    with (
        patch(
            "pyoctoprintapi.OctoprintClient.get_server_info",
            return_value=True,
        ),
        patch(
            "pyoctoprintapi.OctoprintClient.get_discovery_info",
            return_value=DiscoverySettings({"upnpUuid": "uuid"}),
        ),
        patch("homeassistant.components.octoprint.async_setup", return_value=True),
        patch(
            "homeassistant.components.octoprint.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "testuser",
                "host": "1.1.1.1",
                "name": "Printer",
                "port": 81,
                "ssl": True,
                "path": "/",
                "api_key": "test-key",
            },
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def show_ssdp_form(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test that the ssdp confirmation form is served."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            upnp={
                "presentationURL": "http://192.168.1.123:80/discovery/device.xml",
                "port": 80,
                "UDN": "uuid:83747482",
            },
        ),
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_equal(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "username": "testuser",
        },
    )
    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)

    with patch(
        "pyoctoprintapi.OctoprintClient.request_app_key", return_value="test-key"
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)

    with (
        patch(
            "pyoctoprintapi.OctoprintClient.get_server_info",
            return_value=True,
        ),
        patch(
            "pyoctoprintapi.OctoprintClient.get_discovery_info",
            return_value=DiscoverySettings({"upnpUuid": "uuid"}),
        ),
        patch("homeassistant.components.octoprint.async_setup", return_value=True),
        patch(
            "homeassistant.components.octoprint.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "testuser",
                "host": "1.1.1.1",
                "name": "Printer",
                "port": 81,
                "ssl": True,
                "path": "/",
                "api_key": "test-key",
            },
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def import_yaml(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test that the yaml import works."""
    with (
        patch(
            "pyoctoprintapi.OctoprintClient.get_server_info",
            return_value=True,
        ),
        patch(
            "pyoctoprintapi.OctoprintClient.get_discovery_info",
            return_value=DiscoverySettings({"upnpUuid": "uuid"}),
        ),
        patch(
            "pyoctoprintapi.OctoprintClient.request_app_key", return_value="test-key"
        ),
        patch("homeassistant.components.octoprint.async_setup", return_value=True),
        patch(
            "homeassistant.components.octoprint.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={
                "host": "1.1.1.1",
                "api_key": "test-key",
                "name": "Printer",
                "port": 81,
                "ssl": True,
                "path": "/",
            },
        )
        await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect("errors" not in result).to_equal(True)


@test
async def import_duplicate_yaml(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test that the yaml import of duplicate entry aborts."""
    MockConfigEntry(
        domain=DOMAIN,
        data={"host": "192.168.1.123"},
        source=config_entries.SOURCE_IMPORT,
        unique_id="uuid",
    ).add_to_hass(hass)

    with (
        patch(
            "pyoctoprintapi.OctoprintClient.get_discovery_info",
            return_value=DiscoverySettings({"upnpUuid": "uuid"}),
        ),
        patch(
            "pyoctoprintapi.OctoprintClient.request_app_key", return_value="test-key"
        ) as request_app_key,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={
                "host": "1.1.1.1",
                "api_key": "test-key",
                "name": "Printer",
                "port": 81,
                "ssl": True,
                "path": "/",
            },
        )
        await hass.async_block_till_done()
        expect(len(request_app_key.mock_calls)).to_equal(0)

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def failed_auth(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we abort if the app key request fails with ApiError."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "username": "testuser",
            "host": "1.1.1.1",
            "name": "Printer",
            "port": 81,
            "ssl": True,
            "path": "/",
        },
    )
    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)

    with patch("pyoctoprintapi.OctoprintClient.request_app_key", side_effect=ApiError):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("auth_failed")


@test
async def failed_auth_unexpected_error(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort if the app key request fails with unexpected error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "username": "testuser",
            "host": "1.1.1.1",
            "name": "Printer",
            "port": 81,
            "ssl": True,
            "path": "/",
        },
    )
    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)

    with patch("pyoctoprintapi.OctoprintClient.request_app_key", side_effect=Exception):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("auth_failed")


@test
async def user_duplicate_entry(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test that duplicate entries abort."""
    MockConfigEntry(
        domain=DOMAIN,
        data={"host": "192.168.1.123"},
        source=config_entries.SOURCE_IMPORT,
        unique_id="uuid",
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_equal(False)

    with patch(
        "pyoctoprintapi.OctoprintClient.request_app_key", return_value="test-key"
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "testuser",
                "host": "1.1.1.1",
                "name": "Printer",
                "port": 81,
                "ssl": True,
                "path": "/",
            },
        )
        await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)

    with (
        patch(
            "pyoctoprintapi.OctoprintClient.get_server_info",
            return_value=True,
        ),
        patch(
            "pyoctoprintapi.OctoprintClient.get_discovery_info",
            return_value=DiscoverySettings({"upnpUuid": "uuid"}),
        ),
        patch(
            "homeassistant.components.octoprint.async_setup", return_value=True
        ) as mock_setup,
        patch(
            "homeassistant.components.octoprint.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")
    expect(len(mock_setup.mock_calls)).to_equal(0)
    expect(len(mock_setup_entry.mock_calls)).to_equal(0)


@test
async def duplicate_zerconf_ignored(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the duplicate zeroconf is not shown."""
    MockConfigEntry(
        domain=DOMAIN,
        data={"host": "192.168.1.123"},
        source=config_entries.SOURCE_IMPORT,
        unique_id="83747482",
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("192.168.1.123"),
            ip_addresses=[ip_address("192.168.1.123")],
            hostname="example.local.",
            name="mock_name",
            port=80,
            properties={"uuid": "83747482", "path": "/foo/"},
            type="mock_type",
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def duplicate_ssdp_ignored(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test that duplicate ssdp form is not shown."""
    MockConfigEntry(
        domain=DOMAIN,
        data={"host": "192.168.1.123"},
        source=config_entries.SOURCE_IMPORT,
        unique_id="83747482",
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            upnp={
                "presentationURL": "http://192.168.1.123:80/discovery/device.xml",
                "port": 80,
                "UDN": "uuid:83747482",
            },
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reauth_form(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we get the reauth form."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "username": "testuser",
            "host": "1.1.1.1",
            "name": "Printer",
            "port": 81,
            "ssl": True,
            "path": "/",
        },
        unique_id="1234",
    )
    entry.add_to_hass(hass)
    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_equal(False)

    with patch(
        "pyoctoprintapi.OctoprintClient.request_app_key", return_value="test-key"
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "testuser",
            },
        )
        await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)

    with patch(
        "homeassistant.components.octoprint.async_setup_entry",
        return_value=True,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")
