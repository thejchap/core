"""Test the Smappee component config flow module."""

from ipaddress import ip_address
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.smappee.const import (
    CONF_SERIALNUMBER,
    DOMAIN,
    ENV_CLOUD,
    ENV_LOCAL,
)
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture to force tryke to resolve dependencies."""


@test
async def show_user_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the user set up form is served."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result["step_id"]).to_equal("environment")
    expect(result["type"]).to_be(FlowResultType.FORM)


@test
async def show_user_host_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the host form is served after choosing the local option."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["step_id"]).to_equal("environment")
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"environment": ENV_LOCAL}
    )

    expect(result["step_id"]).to_equal(ENV_LOCAL)
    expect(result["type"]).to_be(FlowResultType.FORM)


@test
async def show_zeroconf_connection_error_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the zeroconf confirmation form is served."""
    with patch("pysmappee.api.SmappeeLocalApi.logon", return_value=None):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_ZEROCONF},
            data=ZeroconfServiceInfo(
                ip_address=ip_address("1.2.3.4"),
                ip_addresses=[ip_address("1.2.3.4")],
                port=22,
                hostname="Smappee1006000212.local.",
                type="_ssh._tcp.local.",
                name="Smappee1006000212._ssh._tcp.local.",
                properties={"_raw": {}},
            ),
        )

        expect(result["description_placeholders"]).to_equal(
            {CONF_SERIALNUMBER: "1006000212"}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("zeroconf_confirm")

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "1.2.3.4"}
        )

        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("cannot_connect")
        expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(0)


@test
async def show_zeroconf_connection_error_form_next_generation(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the zeroconf confirmation form is served."""
    with patch("pysmappee.mqtt.SmappeeLocalMqtt.start_attempt", return_value=False):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_ZEROCONF},
            data=ZeroconfServiceInfo(
                ip_address=ip_address("1.2.3.4"),
                ip_addresses=[ip_address("1.2.3.4")],
                port=22,
                hostname="Smappee5001000212.local.",
                type="_ssh._tcp.local.",
                name="Smappee5001000212._ssh._tcp.local.",
                properties={"_raw": {}},
            ),
        )

        expect(result["description_placeholders"]).to_equal(
            {CONF_SERIALNUMBER: "5001000212"}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("zeroconf_confirm")

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "1.2.3.4"}
        )

        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("cannot_connect")
        expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(0)


@test
async def connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we show user form on Smappee connection error."""
    with (
        patch("pysmappee.api.SmappeeLocalApi.logon", return_value=None),
        patch("pysmappee.mqtt.SmappeeLocalMqtt.start_attempt", return_value=None),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
        expect(result["step_id"]).to_equal("environment")
        expect(result["type"]).to_be(FlowResultType.FORM)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"environment": ENV_LOCAL}
        )
        expect(result["step_id"]).to_equal(ENV_LOCAL)
        expect(result["type"]).to_be(FlowResultType.FORM)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "1.2.3.4"}
        )
        expect(result["reason"]).to_equal("cannot_connect")
        expect(result["type"]).to_be(FlowResultType.ABORT)


@test
async def user_local_connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we show user form on Smappee connection error in local next generation option."""
    with (
        patch("pysmappee.api.SmappeeLocalApi.logon", return_value=None),
        patch("pysmappee.mqtt.SmappeeLocalMqtt.start_attempt", return_value=True),
        patch("pysmappee.mqtt.SmappeeLocalMqtt.start", return_value=True),
        patch("pysmappee.mqtt.SmappeeLocalMqtt.stop", return_value=True),
        patch("pysmappee.mqtt.SmappeeLocalMqtt.is_config_ready", return_value=None),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
        expect(result["step_id"]).to_equal("environment")
        expect(result["type"]).to_be(FlowResultType.FORM)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"environment": ENV_LOCAL}
        )
        expect(result["step_id"]).to_equal(ENV_LOCAL)
        expect(result["type"]).to_be(FlowResultType.FORM)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "1.2.3.4"}
        )
        expect(result["reason"]).to_equal("cannot_connect")
        expect(result["type"]).to_be(FlowResultType.ABORT)


@test
async def zeroconf_wrong_mdns(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort if unsupported mDNS name is discovered."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("1.2.3.4"),
            ip_addresses=[ip_address("1.2.3.4")],
            port=22,
            hostname="example.local.",
            type="_ssh._tcp.local.",
            name="example._ssh._tcp.local.",
            properties={"_raw": {}},
        ),
    )

    expect(result["reason"]).to_equal("invalid_mdns")
    expect(result["type"]).to_be(FlowResultType.ABORT)


@test
async def full_user_wrong_mdns(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort user flow if unsupported mDNS name got resolved."""
    with (
        patch("pysmappee.api.SmappeeLocalApi.logon", return_value={}),
        patch(
            "pysmappee.api.SmappeeLocalApi.load_advanced_config",
            return_value=[{"key": "mdnsHostName", "value": "Smappee5100000001"}],
        ),
        patch(
            "pysmappee.api.SmappeeLocalApi.load_command_control_config", return_value=[]
        ),
        patch(
            "pysmappee.api.SmappeeLocalApi.load_instantaneous",
            return_value=[{"key": "phase0ActivePower", "value": 0}],
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
        expect(result["step_id"]).to_equal("environment")
        expect(result["type"]).to_be(FlowResultType.FORM)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"environment": ENV_LOCAL}
        )
        expect(result["step_id"]).to_equal(ENV_LOCAL)
        expect(result["type"]).to_be(FlowResultType.FORM)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "1.2.3.4"}
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("invalid_mdns")


@test
async def user_device_exists_abort(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort user flow if Smappee device already configured."""
    with (
        patch("pysmappee.api.SmappeeLocalApi.logon", return_value={}),
        patch(
            "pysmappee.api.SmappeeLocalApi.load_advanced_config",
            return_value=[{"key": "mdnsHostName", "value": "Smappee1006000212"}],
        ),
        patch(
            "pysmappee.api.SmappeeLocalApi.load_command_control_config", return_value=[]
        ),
        patch(
            "pysmappee.api.SmappeeLocalApi.load_instantaneous",
            return_value=[{"key": "phase0ActivePower", "value": 0}],
        ),
    ):
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            data={"host": "1.2.3.4"},
            unique_id="1006000212",
            source=SOURCE_USER,
        )
        config_entry.add_to_hass(hass)
        expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
        expect(result["step_id"]).to_equal("environment")
        expect(result["type"]).to_be(FlowResultType.FORM)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"environment": ENV_LOCAL}
        )
        expect(result["step_id"]).to_equal(ENV_LOCAL)
        expect(result["type"]).to_be(FlowResultType.FORM)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "1.2.3.4"}
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("already_configured")
        expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)


@test
async def zeroconf_device_exists_abort(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort zeroconf flow if Smappee device already configured."""
    with (
        patch("pysmappee.api.SmappeeLocalApi.logon", return_value={}),
        patch(
            "pysmappee.api.SmappeeLocalApi.load_advanced_config",
            return_value=[{"key": "mdnsHostName", "value": "Smappee1006000212"}],
        ),
        patch(
            "pysmappee.api.SmappeeLocalApi.load_command_control_config", return_value=[]
        ),
        patch(
            "pysmappee.api.SmappeeLocalApi.load_instantaneous",
            return_value=[{"key": "phase0ActivePower", "value": 0}],
        ),
    ):
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            data={"host": "1.2.3.4"},
            unique_id="1006000212",
            source=SOURCE_USER,
        )
        config_entry.add_to_hass(hass)

        expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_ZEROCONF},
            data=ZeroconfServiceInfo(
                ip_address=ip_address("1.2.3.4"),
                ip_addresses=[ip_address("1.2.3.4")],
                port=22,
                hostname="Smappee1006000212.local.",
                type="_ssh._tcp.local.",
                name="Smappee1006000212._ssh._tcp.local.",
                properties={"_raw": {}},
            ),
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("already_configured")
        expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)


@test
async def cloud_device_exists_abort(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort cloud flow if Smappee Cloud device already configured."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="smappeeCloud",
        source=SOURCE_USER,
    )
    config_entry.add_to_hass(hass)

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured_device")
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)


@test
async def zeroconf_abort_if_cloud_device_exists(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort zeroconf flow if Smappee Cloud device already configured."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="smappeeCloud",
        source=SOURCE_USER,
    )
    config_entry.add_to_hass(hass)

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("1.2.3.4"),
            ip_addresses=[ip_address("1.2.3.4")],
            port=22,
            hostname="Smappee1006000212.local.",
            type="_ssh._tcp.local.",
            name="Smappee1006000212._ssh._tcp.local.",
            properties={"_raw": {}},
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured_device")
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)


@test
async def zeroconf_confirm_abort_if_cloud_device_exists(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort zeroconf confirm flow if Smappee Cloud device already configured."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("1.2.3.4"),
            ip_addresses=[ip_address("1.2.3.4")],
            port=22,
            hostname="Smappee1006000212.local.",
            type="_ssh._tcp.local.",
            name="Smappee1006000212._ssh._tcp.local.",
            properties={"_raw": {}},
        ),
    )

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="smappeeCloud",
        source=SOURCE_USER,
    )
    config_entry.add_to_hass(hass)

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured_device")
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)


@test
async def abort_cloud_flow_if_local_device_exists(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort the cloud flow if a Smappee local device already configured."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"host": "1.2.3.4"},
        unique_id="1006000212",
        source=SOURCE_USER,
    )
    config_entry.add_to_hass(hass)

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"environment": ENV_CLOUD}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured_local_device")
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)


@test.skip("requires aioclient_mock + hass_client_no_auth + current_request_with_host (OAuth)")
async def full_user_flow() -> None:
    """OAuth full flow - skipped."""


@test
async def full_zeroconf_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the full zeroconf flow."""
    with (
        patch("pysmappee.api.SmappeeLocalApi.logon", return_value={}),
        patch(
            "pysmappee.api.SmappeeLocalApi.load_advanced_config",
            return_value=[{"key": "mdnsHostName", "value": "Smappee1006000212"}],
        ),
        patch(
            "pysmappee.api.SmappeeLocalApi.load_command_control_config", return_value=[]
        ),
        patch(
            "pysmappee.api.SmappeeLocalApi.load_instantaneous",
            return_value=[{"key": "phase0ActivePower", "value": 0}],
        ),
        patch("homeassistant.components.smappee.async_setup_entry", return_value=True),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_ZEROCONF},
            data=ZeroconfServiceInfo(
                ip_address=ip_address("1.2.3.4"),
                ip_addresses=[ip_address("1.2.3.4")],
                port=22,
                hostname="Smappee1006000212.local.",
                type="_ssh._tcp.local.",
                name="Smappee1006000212._ssh._tcp.local.",
                properties={"_raw": {}},
            ),
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("zeroconf_confirm")
        expect(result["description_placeholders"]).to_equal(
            {CONF_SERIALNUMBER: "1006000212"}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "1.2.3.4"}
        )

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal("smappee1006000212")
        expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)

        entry = hass.config_entries.async_entries(DOMAIN)[0]
        expect(entry.unique_id).to_equal("1006000212")


@test
async def full_user_local_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the full local user flow."""
    with (
        patch("pysmappee.api.SmappeeLocalApi.logon", return_value={}),
        patch(
            "pysmappee.api.SmappeeLocalApi.load_advanced_config",
            return_value=[{"key": "mdnsHostName", "value": "Smappee1006000212"}],
        ),
        patch(
            "pysmappee.api.SmappeeLocalApi.load_command_control_config", return_value=[]
        ),
        patch(
            "pysmappee.api.SmappeeLocalApi.load_instantaneous",
            return_value=[{"key": "phase0ActivePower", "value": 0}],
        ),
        patch("homeassistant.components.smappee.async_setup_entry", return_value=True),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
        expect(result["step_id"]).to_equal("environment")
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["description_placeholders"]).to_be(None)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"environment": ENV_LOCAL},
        )
        expect(result["step_id"]).to_equal(ENV_LOCAL)
        expect(result["type"]).to_be(FlowResultType.FORM)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "1.2.3.4"}
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal("smappee1006000212")
        expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)

        entry = hass.config_entries.async_entries(DOMAIN)[0]
        expect(entry.unique_id).to_equal("1006000212")


@test
async def full_zeroconf_flow_next_generation(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the full zeroconf flow next gen."""
    with (
        patch("pysmappee.mqtt.SmappeeLocalMqtt.start_attempt", return_value=True),
        patch(
            "pysmappee.mqtt.SmappeeLocalMqtt.start",
            return_value=None,
        ),
        patch(
            "pysmappee.mqtt.SmappeeLocalMqtt.is_config_ready",
            return_value=None,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_ZEROCONF},
            data=ZeroconfServiceInfo(
                ip_address=ip_address("1.2.3.4"),
                ip_addresses=[ip_address("1.2.3.4")],
                port=22,
                hostname="Smappee5001000212.local.",
                type="_ssh._tcp.local.",
                name="Smappee5001000212._ssh._tcp.local.",
                properties={"_raw": {}},
            ),
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("zeroconf_confirm")
        expect(result["description_placeholders"]).to_equal(
            {CONF_SERIALNUMBER: "5001000212"}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "1.2.3.4"}
        )

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal("smappee5001000212")
        expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)

        entry = hass.config_entries.async_entries(DOMAIN)[0]
        expect(entry.unique_id).to_equal("5001000212")
