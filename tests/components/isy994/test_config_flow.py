"""Test the Universal Devices ISY/IoX config flow."""

import re
from unittest.mock import MagicMock, patch

from pyisy import ISYConnectionError, ISYInvalidAuthError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.isy994.const import (
    CONF_TLS_VER,
    DOMAIN,
    ISY_URL_POSTFIX,
    UDN_UUID_PREFIX,
)
from homeassistant.config_entries import SOURCE_DHCP, SOURCE_IGNORE, SOURCE_SSDP
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo
from homeassistant.helpers.service_info.ssdp import (
    ATTR_UPNP_FRIENDLY_NAME,
    ATTR_UPNP_UDN,
    SsdpServiceInfo,
)

from ._fixtures import mock_isy_init

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

MOCK_HOSTNAME = "1.1.1.1"
MOCK_USERNAME = "test-username"
MOCK_PASSWORD = "test-password"

MOCK_TLS_VERSION = 1.2

MOCK_USER_INPUT = {
    CONF_HOST: f"http://{MOCK_HOSTNAME}",
    CONF_USERNAME: MOCK_USERNAME,
    CONF_PASSWORD: MOCK_PASSWORD,
    CONF_TLS_VER: MOCK_TLS_VERSION,
}
MOCK_IOX_USER_INPUT = {
    CONF_HOST: f"http://{MOCK_HOSTNAME}:8080",
    CONF_USERNAME: MOCK_USERNAME,
    CONF_PASSWORD: MOCK_PASSWORD,
    CONF_TLS_VER: MOCK_TLS_VERSION,
}

MOCK_DEVICE_NAME = "Name of the device"
MOCK_UUID = "ce:fb:72:31:b7:b9"
MOCK_MAC = "cefb7231b7b9"
MOCK_POLISY_MAC = "000db9123456"

MOCK_CONFIG_RESPONSE = """<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <app_full_version>5.0.16C</app_full_version>
    <platform>ISY-C-994</platform>
    <root>
        <id>ce:fb:72:31:b7:b9</id>
        <name>Name of the device</name>
    </root>
    <features>
        <feature>
            <id>21040</id>
            <desc>Networking Module</desc>
            <isInstalled>true</isInstalled>
            <isAvailable>true</isAvailable>
        </feature>
    </features>
</configuration>
"""

INTEGRATION = "homeassistant.components.isy994"
PATCH_CONNECTION = f"{INTEGRATION}.config_flow.Connection.test_connection"
PATCH_ASYNC_SETUP = f"{INTEGRATION}.async_setup"
PATCH_ASYNC_SETUP_ENTRY = f"{INTEGRATION}.async_setup_entry"


def _get_schema_default(schema, key_name):
    """Iterate schema to find a key."""
    for schema_key in schema:
        if schema_key == key_name:
            return schema_key.default()
    raise KeyError(f"{key_name} not found in schema")


@fixture
def _trigger_executor(
    _isy: MagicMock = Depends(mock_isy_init),
    _network: None = Depends(mock_network),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(PATCH_CONNECTION, return_value=MOCK_CONFIG_RESPONSE),
        patch(
            PATCH_ASYNC_SETUP_ENTRY,
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_USER_INPUT,
        )
        await hass.async_block_till_done()
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(f"{MOCK_DEVICE_NAME} ({MOCK_HOSTNAME})")
    expect(result2["result"].unique_id).to_equal(MOCK_UUID)
    expect(result2["data"]).to_equal(MOCK_USER_INPUT)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_invalid_host(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid host."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "host": MOCK_HOSTNAME,
            "username": MOCK_USERNAME,
            "password": MOCK_PASSWORD,
            "tls": MOCK_TLS_VERSION,
        },
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_host"})


@test
async def form_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(
        PATCH_CONNECTION,
        side_effect=ISYInvalidAuthError(),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_USER_INPUT,
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({CONF_PASSWORD: "invalid_auth"})


@test
async def form_unknown_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle generic exceptions."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(
        PATCH_CONNECTION,
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_USER_INPUT,
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def form_isy_connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(
        PATCH_CONNECTION,
        side_effect=ISYConnectionError(),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_USER_INPUT,
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_isy_parse_response_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle poorly formatted XML response from ISY."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(
        PATCH_CONNECTION,
        return_value=MOCK_CONFIG_RESPONSE.rsplit("\n", 3)[0],
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_USER_INPUT,
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_no_name_in_response(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid response from ISY with name not set."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(
        PATCH_CONNECTION,
        return_value=re.sub(r"\<name\>.*\n", "", MOCK_CONFIG_RESPONSE),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_USER_INPUT,
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_existing_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if config entry already exists."""
    MockConfigEntry(domain=DOMAIN, unique_id=MOCK_UUID).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(PATCH_CONNECTION, return_value=MOCK_CONFIG_RESPONSE):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_USER_INPUT,
        )
    expect(result2["type"]).to_be(FlowResultType.ABORT)


@test
async def form_ssdp_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test ssdp abort when the serial number is already configured."""
    MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: f"http://{MOCK_HOSTNAME}{ISY_URL_POSTFIX}"},
        unique_id=MOCK_UUID,
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            ssdp_location=f"http://{MOCK_HOSTNAME}{ISY_URL_POSTFIX}",
            upnp={
                ATTR_UPNP_FRIENDLY_NAME: "myisy",
                ATTR_UPNP_UDN: f"{UDN_UUID_PREFIX}{MOCK_UUID}",
            },
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)


@test
async def form_ssdp(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can setup from ssdp."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            ssdp_location=f"http://{MOCK_HOSTNAME}{ISY_URL_POSTFIX}",
            upnp={
                ATTR_UPNP_FRIENDLY_NAME: "myisy",
                ATTR_UPNP_UDN: f"{UDN_UUID_PREFIX}{MOCK_UUID}",
            },
        ),
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    with (
        patch(PATCH_CONNECTION, return_value=MOCK_CONFIG_RESPONSE),
        patch(
            PATCH_ASYNC_SETUP_ENTRY,
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_USER_INPUT,
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(f"{MOCK_DEVICE_NAME} ({MOCK_HOSTNAME})")
    expect(result2["result"].unique_id).to_equal(MOCK_UUID)
    expect(result2["data"]).to_equal(MOCK_USER_INPUT)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_ssdp_existing_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we update the ip of an existing entry from ssdp."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: f"http://{MOCK_HOSTNAME}{ISY_URL_POSTFIX}"},
        unique_id=MOCK_UUID,
    )
    entry.add_to_hass(hass)

    with patch(PATCH_CONNECTION, return_value=MOCK_CONFIG_RESPONSE):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_SSDP},
            data=SsdpServiceInfo(
                ssdp_usn="mock_usn",
                ssdp_st="mock_st",
                ssdp_location=f"http://3.3.3.3{ISY_URL_POSTFIX}",
                upnp={
                    ATTR_UPNP_FRIENDLY_NAME: "myisy",
                    ATTR_UPNP_UDN: f"{UDN_UUID_PREFIX}{MOCK_UUID}",
                },
            ),
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(entry.data[CONF_HOST]).to_equal(f"http://3.3.3.3:80{ISY_URL_POSTFIX}")


@test
async def form_ssdp_existing_entry_with_no_port(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we update the ip of an existing entry from ssdp with no port."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: f"http://{MOCK_HOSTNAME}:1443/{ISY_URL_POSTFIX}"},
        unique_id=MOCK_UUID,
    )
    entry.add_to_hass(hass)

    with patch(PATCH_CONNECTION, return_value=MOCK_CONFIG_RESPONSE):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_SSDP},
            data=SsdpServiceInfo(
                ssdp_usn="mock_usn",
                ssdp_st="mock_st",
                ssdp_location=f"http://3.3.3.3/{ISY_URL_POSTFIX}",
                upnp={
                    ATTR_UPNP_FRIENDLY_NAME: "myisy",
                    ATTR_UPNP_UDN: f"{UDN_UUID_PREFIX}{MOCK_UUID}",
                },
            ),
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(entry.data[CONF_HOST]).to_equal(f"http://3.3.3.3:80/{ISY_URL_POSTFIX}")


@test
async def form_ssdp_existing_entry_with_alternate_port(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we update the ip of an existing entry from ssdp with an alternate port."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: f"http://{MOCK_HOSTNAME}:1443/{ISY_URL_POSTFIX}"},
        unique_id=MOCK_UUID,
    )
    entry.add_to_hass(hass)

    with patch(PATCH_CONNECTION, return_value=MOCK_CONFIG_RESPONSE):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_SSDP},
            data=SsdpServiceInfo(
                ssdp_usn="mock_usn",
                ssdp_st="mock_st",
                ssdp_location=f"http://3.3.3.3:1443/{ISY_URL_POSTFIX}",
                upnp={
                    ATTR_UPNP_FRIENDLY_NAME: "myisy",
                    ATTR_UPNP_UDN: f"{UDN_UUID_PREFIX}{MOCK_UUID}",
                },
            ),
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(entry.data[CONF_HOST]).to_equal(f"http://3.3.3.3:1443/{ISY_URL_POSTFIX}")


@test
async def form_ssdp_existing_entry_no_port_https(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we update the ip of an existing entry from ssdp with no port and https."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: f"https://{MOCK_HOSTNAME}/{ISY_URL_POSTFIX}"},
        unique_id=MOCK_UUID,
    )
    entry.add_to_hass(hass)

    with patch(PATCH_CONNECTION, return_value=MOCK_CONFIG_RESPONSE):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_SSDP},
            data=SsdpServiceInfo(
                ssdp_usn="mock_usn",
                ssdp_st="mock_st",
                ssdp_location=f"https://3.3.3.3/{ISY_URL_POSTFIX}",
                upnp={
                    ATTR_UPNP_FRIENDLY_NAME: "myisy",
                    ATTR_UPNP_UDN: f"{UDN_UUID_PREFIX}{MOCK_UUID}",
                },
            ),
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(entry.data[CONF_HOST]).to_equal(f"https://3.3.3.3:443/{ISY_URL_POSTFIX}")


@test
async def form_dhcp(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can setup from dhcp."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="1.2.3.4",
            hostname="isy994-ems",
            macaddress=MOCK_MAC,
        ),
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    with (
        patch(PATCH_CONNECTION, return_value=MOCK_CONFIG_RESPONSE),
        patch(
            PATCH_ASYNC_SETUP_ENTRY,
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_USER_INPUT,
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(f"{MOCK_DEVICE_NAME} ({MOCK_HOSTNAME})")
    expect(result2["result"].unique_id).to_equal(MOCK_UUID)
    expect(result2["data"]).to_equal(MOCK_USER_INPUT)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_dhcp_with_polisy(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can setup from dhcp with polisy."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="1.2.3.4",
            hostname="polisy",
            macaddress=MOCK_POLISY_MAC,
        ),
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})
    expect(_get_schema_default(result["data_schema"].schema, CONF_HOST)).to_equal(
        "http://1.2.3.4:8080"
    )

    with (
        patch(PATCH_CONNECTION, return_value=MOCK_CONFIG_RESPONSE),
        patch(
            PATCH_ASYNC_SETUP_ENTRY,
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_IOX_USER_INPUT,
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(f"{MOCK_DEVICE_NAME} ({MOCK_HOSTNAME})")
    expect(result2["result"].unique_id).to_equal(MOCK_UUID)
    expect(result2["data"]).to_equal(MOCK_IOX_USER_INPUT)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_dhcp_with_eisy(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can setup from dhcp with eisy."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="1.2.3.4",
            hostname="eisy",
            macaddress=MOCK_MAC,
        ),
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})
    expect(_get_schema_default(result["data_schema"].schema, CONF_HOST)).to_equal(
        "http://1.2.3.4:8080"
    )

    with (
        patch(PATCH_CONNECTION, return_value=MOCK_CONFIG_RESPONSE),
        patch(
            PATCH_ASYNC_SETUP_ENTRY,
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_IOX_USER_INPUT,
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(f"{MOCK_DEVICE_NAME} ({MOCK_HOSTNAME})")
    expect(result2["result"].unique_id).to_equal(MOCK_UUID)
    expect(result2["data"]).to_equal(MOCK_IOX_USER_INPUT)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_dhcp_existing_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we update the ip of an existing entry from dhcp."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: f"http://{MOCK_HOSTNAME}{ISY_URL_POSTFIX}"},
        unique_id=MOCK_UUID,
    )
    entry.add_to_hass(hass)

    with patch(PATCH_CONNECTION, return_value=MOCK_CONFIG_RESPONSE):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_DHCP},
            data=DhcpServiceInfo(
                ip="1.2.3.4",
                hostname="isy994-ems",
                macaddress=MOCK_MAC,
            ),
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(entry.data[CONF_HOST]).to_equal(f"http://1.2.3.4{ISY_URL_POSTFIX}")


@test
async def form_dhcp_existing_entry_preserves_port(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we update the ip of an existing entry from dhcp preserves port."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_USERNAME: "bob",
            CONF_HOST: f"http://{MOCK_HOSTNAME}:1443{ISY_URL_POSTFIX}",
        },
        unique_id=MOCK_UUID,
    )
    entry.add_to_hass(hass)

    with patch(PATCH_CONNECTION, return_value=MOCK_CONFIG_RESPONSE):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_DHCP},
            data=DhcpServiceInfo(
                ip="1.2.3.4",
                hostname="isy994-ems",
                macaddress=MOCK_MAC,
            ),
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(entry.data[CONF_HOST]).to_equal(f"http://1.2.3.4:1443{ISY_URL_POSTFIX}")
    expect(entry.data[CONF_USERNAME]).to_equal("bob")


@test
async def form_dhcp_existing_ignored_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handled an ignored entry from dhcp."""
    entry = MockConfigEntry(
        domain=DOMAIN, data={}, unique_id=MOCK_UUID, source=SOURCE_IGNORE
    )
    entry.add_to_hass(hass)

    with patch(PATCH_CONNECTION, return_value=MOCK_CONFIG_RESPONSE):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_DHCP},
            data=DhcpServiceInfo(
                ip="1.2.3.4",
                hostname="isy994-ems",
                macaddress=MOCK_MAC,
            ),
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can reauth."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_USERNAME: "bob",
            CONF_HOST: f"http://{MOCK_HOSTNAME}:1443{ISY_URL_POSTFIX}",
        },
        unique_id=MOCK_UUID,
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    with patch(
        PATCH_CONNECTION,
        side_effect=ISYInvalidAuthError(),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"password": "invalid_auth"})

    with patch(
        PATCH_CONNECTION,
        side_effect=ISYConnectionError(),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )

    expect(result3["type"]).to_be(FlowResultType.FORM)
    expect(result3["errors"]).to_equal({"base": "cannot_connect"})

    with (
        patch(PATCH_CONNECTION, return_value=MOCK_CONFIG_RESPONSE),
        patch(
            "homeassistant.components.isy994.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result4 = await hass.config_entries.flow.async_configure(
            result3["flow_id"],
            {
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )
        await hass.async_block_till_done()

    expect(mock_setup_entry.called).to_be_truthy()
    expect(result4["type"]).to_be(FlowResultType.ABORT)
    expect(result4["reason"]).to_equal("reauth_successful")


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test option flow."""
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    hass.config_entries.options.async_abort(result["flow_id"])
