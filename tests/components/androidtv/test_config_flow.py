"""Tests for the AndroidTV config flow."""

from typing import Any
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.androidtv.config_flow import (
    APPS_NEW_ID,
    CONF_APP_DELETE,
    CONF_APP_ID,
    CONF_APP_NAME,
    CONF_RULE_DELETE,
    CONF_RULE_ID,
    CONF_RULE_VALUES,
    RULES_NEW_ID,
)
from homeassistant.components.androidtv.const import (
    CONF_ADB_SERVER_IP,
    CONF_ADB_SERVER_PORT,
    CONF_ADBKEY,
    CONF_APPS,
    CONF_EXCLUDE_UNNAMED_APPS,
    CONF_GET_SOURCES,
    CONF_SCREENCAP_INTERVAL,
    CONF_STATE_DETECTION_RULES,
    CONF_TURN_OFF_COMMAND,
    CONF_TURN_ON_COMMAND,
    DEFAULT_ADB_SERVER_PORT,
    DEFAULT_PORT,
    DEVICE_ANDROIDTV,
    DOMAIN,
    PROP_ETHMAC,
    PROP_WIFIMAC,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_DEVICE_CLASS, CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    adb_device_tcp_fixture,
    keygen_fixture,
    load_adbkey_fixture,
)
from .patchers import PATCH_ACCESS, PATCH_ISFILE, PATCH_SETUP_ENTRY

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

ADBKEY = "adbkey"
ETH_MAC = "a1:b1:c1:d1:e1:f1"
WIFI_MAC = "a2:b2:c2:d2:e2:f2"
INVALID_MAC = "ff:ff:ff:ff:ff:ff"
HOST = "127.0.0.1"
VALID_DETECT_RULE = [{"paused": {"media_session_state": 3}}]

CONFIG_PYTHON_ADB = {
    CONF_HOST: HOST,
    CONF_PORT: DEFAULT_PORT,
    CONF_DEVICE_CLASS: DEVICE_ANDROIDTV,
}

CONFIG_ADB_SERVER = {
    CONF_HOST: HOST,
    CONF_PORT: DEFAULT_PORT,
    CONF_DEVICE_CLASS: DEVICE_ANDROIDTV,
    CONF_ADB_SERVER_IP: "127.0.0.1",
    CONF_ADB_SERVER_PORT: DEFAULT_ADB_SERVER_PORT,
}

CONNECT_METHOD = (
    "homeassistant.components.androidtv.config_flow.async_connect_androidtv"
)


class MockConfigDevice:
    """Mock class to emulate Android device."""

    def __init__(self, eth_mac=ETH_MAC, wifi_mac=None) -> None:
        """Initialize a fake device to test config flow."""
        self.available = True
        self.device_properties = {PROP_ETHMAC: eth_mac, PROP_WIFIMAC: wifi_mac}

    async def adb_close(self):
        """Fake method to close connection."""
        self.available = False


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _adb: None = Depends(adb_device_tcp_fixture),
    _adbkey: None = Depends(load_adbkey_fixture),
    _keygen: None = Depends(keygen_fixture),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.cases(
    test.case(
        "python_adb_eth", config=CONFIG_PYTHON_ADB, eth_mac=ETH_MAC, wifi_mac=None
    ),
    test.case(
        "adb_server_eth", config=CONFIG_ADB_SERVER, eth_mac=ETH_MAC, wifi_mac=None
    ),
    test.case(
        "python_adb_wifi", config=CONFIG_PYTHON_ADB, eth_mac=None, wifi_mac=WIFI_MAC
    ),
    test.case(
        "adb_server_wifi", config=CONFIG_ADB_SERVER, eth_mac=None, wifi_mac=WIFI_MAC
    ),
    test.case(
        "python_adb_both", config=CONFIG_PYTHON_ADB, eth_mac=ETH_MAC, wifi_mac=WIFI_MAC
    ),
    test.case(
        "adb_server_both", config=CONFIG_ADB_SERVER, eth_mac=ETH_MAC, wifi_mac=WIFI_MAC
    ),
)
async def user(
    config: dict[str, Any],
    eth_mac: str | None,
    wifi_mac: str | None,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user config."""
    flow_result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER, "show_advanced_options": True}
    )
    expect(flow_result["type"]).to_be(FlowResultType.FORM)
    expect(flow_result["step_id"]).to_equal("user")

    with (
        patch(
            CONNECT_METHOD,
            return_value=(MockConfigDevice(eth_mac, wifi_mac), None),
        ),
        PATCH_SETUP_ENTRY as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            flow_result["flow_id"], user_input=config
        )
        await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal(HOST)
        expect(result["data"]).to_equal(config)

        expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def user_adbkey(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user step with adbkey file."""
    config_data = CONFIG_PYTHON_ADB.copy()
    config_data[CONF_ADBKEY] = ADBKEY

    with (
        patch(
            CONNECT_METHOD,
            return_value=(MockConfigDevice(), None),
        ),
        PATCH_ISFILE,
        PATCH_ACCESS,
        PATCH_SETUP_ENTRY as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER, "show_advanced_options": True},
            data=config_data,
        )
        await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal(HOST)
        expect(result["data"]).to_equal(config_data)

        expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def error_both_key_server(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort if both adb key and server are provided."""
    config_data = CONFIG_ADB_SERVER.copy()

    config_data[CONF_ADBKEY] = ADBKEY
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER, "show_advanced_options": True},
        data=config_data,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "key_and_server"})

    with (
        patch(
            CONNECT_METHOD,
            return_value=(MockConfigDevice(), None),
        ),
        PATCH_SETUP_ENTRY,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=CONFIG_ADB_SERVER
        )
        await hass.async_block_till_done()

        expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result2["title"]).to_equal(HOST)
        expect(result2["data"]).to_equal(CONFIG_ADB_SERVER)


@test
async def error_invalid_key(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort if component is already setup."""
    config_data = CONFIG_PYTHON_ADB.copy()
    config_data[CONF_ADBKEY] = ADBKEY
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER, "show_advanced_options": True},
        data=config_data,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "adbkey_not_file"})

    with (
        patch(
            CONNECT_METHOD,
            return_value=(MockConfigDevice(), None),
        ),
        PATCH_SETUP_ENTRY,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=CONFIG_ADB_SERVER
        )
        await hass.async_block_till_done()

        expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result2["title"]).to_equal(HOST)
        expect(result2["data"]).to_equal(CONFIG_ADB_SERVER)


@test.cases(
    test.case(
        "adb_server_no_mac", config=CONFIG_ADB_SERVER, eth_mac=None, wifi_mac=None
    ),
    test.case(
        "python_no_mac", config=CONFIG_PYTHON_ADB, eth_mac=None, wifi_mac=None
    ),
    test.case(
        "adb_server_invalid_eth",
        config=CONFIG_ADB_SERVER,
        eth_mac=INVALID_MAC,
        wifi_mac=None,
    ),
    test.case(
        "python_invalid_eth",
        config=CONFIG_PYTHON_ADB,
        eth_mac=INVALID_MAC,
        wifi_mac=None,
    ),
    test.case(
        "adb_server_invalid_wifi",
        config=CONFIG_ADB_SERVER,
        eth_mac=None,
        wifi_mac=INVALID_MAC,
    ),
    test.case(
        "python_invalid_wifi",
        config=CONFIG_PYTHON_ADB,
        eth_mac=None,
        wifi_mac=INVALID_MAC,
    ),
)
async def invalid_mac(
    config: dict[str, Any],
    eth_mac: str | None,
    wifi_mac: str | None,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test for invalid mac address."""
    with patch(
        CONNECT_METHOD,
        return_value=(MockConfigDevice(eth_mac, wifi_mac), None),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data=config,
        )

        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("invalid_unique_id")


@test
async def abort_if_host_exist(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort if component is already setup."""
    MockConfigEntry(
        domain=DOMAIN, data=CONFIG_ADB_SERVER, unique_id=ETH_MAC
    ).add_to_hass(hass)

    config_data = CONFIG_PYTHON_ADB
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=config_data,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def abort_if_unique_exist(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort if component is already setup."""
    config_data = CONFIG_ADB_SERVER.copy()
    config_data[CONF_HOST] = "127.0.0.2"
    MockConfigEntry(domain=DOMAIN, data=config_data, unique_id=ETH_MAC).add_to_hass(
        hass
    )

    with patch(
        CONNECT_METHOD,
        return_value=(MockConfigDevice(), None),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data=CONFIG_ADB_SERVER,
        )

        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("already_configured")


@test
async def on_connect_failed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test when we have errors connecting the router."""
    flow_result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER, "show_advanced_options": True},
    )

    with patch(CONNECT_METHOD, return_value=(None, "Error")):
        result = await hass.config_entries.flow.async_configure(
            flow_result["flow_id"], user_input=CONFIG_ADB_SERVER
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({"base": "cannot_connect"})

    with patch(
        CONNECT_METHOD,
        side_effect=TypeError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=CONFIG_ADB_SERVER
        )
        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["errors"]).to_equal({"base": "unknown"})

    with (
        patch(
            CONNECT_METHOD,
            return_value=(MockConfigDevice(), None),
        ),
        PATCH_SETUP_ENTRY,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"], user_input=CONFIG_ADB_SERVER
        )
        await hass.async_block_till_done()

        expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result3["title"]).to_equal(HOST)
        expect(result3["data"]).to_equal(CONFIG_ADB_SERVER)


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow options."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG_ADB_SERVER,
        unique_id=ETH_MAC,
        options={
            CONF_APPS: {"app1": "App1"},
            CONF_STATE_DETECTION_RULES: {"com.plexapp.android": VALID_DETECT_RULE},
        },
    )
    config_entry.add_to_hass(hass)

    with PATCH_SETUP_ENTRY:
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        result = await hass.config_entries.options.async_init(config_entry.entry_id)

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_APPS: "app1",
            },
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("apps")

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_APP_NAME: "Appl1",
            },
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_APPS: APPS_NEW_ID,
            },
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("apps")

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_APP_ID: "app2",
                CONF_APP_NAME: "Appl2",
            },
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_APPS: "app1",
            },
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("apps")

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_APP_NAME: "Appl1",
                CONF_APP_DELETE: True,
            },
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_STATE_DETECTION_RULES: "com.plexapp.android",
            },
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("rules")

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_RULE_VALUES: "a",
            },
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("rules")
        expect(result["errors"]).to_equal({"base": "invalid_det_rules"})

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_RULE_VALUES: {"a": "b"},
            },
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("rules")
        expect(result["errors"]).to_equal({"base": "invalid_det_rules"})

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_RULE_VALUES: ["standby"],
            },
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_STATE_DETECTION_RULES: RULES_NEW_ID,
            },
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("rules")

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_RULE_ID: "rule2",
                CONF_RULE_VALUES: VALID_DETECT_RULE,
            },
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_STATE_DETECTION_RULES: "com.plexapp.android",
            },
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("rules")

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_RULE_DELETE: True,
            },
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_GET_SOURCES: True,
                CONF_EXCLUDE_UNNAMED_APPS: True,
                CONF_SCREENCAP_INTERVAL: 1,
                CONF_TURN_OFF_COMMAND: "off",
                CONF_TURN_ON_COMMAND: "on",
            },
        )

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

        apps_options = config_entry.options[CONF_APPS]
        expect(apps_options.get("app1")).to_be(None)
        expect(apps_options["app2"]).to_equal("Appl2")

        expect(config_entry.options[CONF_GET_SOURCES]).to_be(True)
        expect(config_entry.options[CONF_EXCLUDE_UNNAMED_APPS]).to_be(True)
        expect(config_entry.options[CONF_SCREENCAP_INTERVAL]).to_equal(1)
        expect(config_entry.options[CONF_TURN_OFF_COMMAND]).to_equal("off")
        expect(config_entry.options[CONF_TURN_ON_COMMAND]).to_equal("on")
