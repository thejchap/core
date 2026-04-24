"""Test the sia config flow."""

from __future__ import annotations

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.sia.config_flow import ACCOUNT_SCHEMA, HUB_SCHEMA
from homeassistant.components.sia.const import (
    CONF_ACCOUNT,
    CONF_ACCOUNTS,
    CONF_ADDITIONAL_ACCOUNTS,
    CONF_ENCRYPTION_KEY,
    CONF_IGNORE_TIMESTAMPS,
    CONF_PING_INTERVAL,
    CONF_ZONES,
    DOMAIN,
)
from homeassistant.const import CONF_PORT, CONF_PROTOCOL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.setup import async_setup_component

from ._fixtures import mock_sia

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

BASIS_CONFIG_ENTRY_ID = "1"
BASIC_CONFIG = {
    CONF_PORT: 7777,
    CONF_PROTOCOL: "TCP",
    CONF_ACCOUNT: "ABCDEF",
    CONF_ENCRYPTION_KEY: "AAAAAAAAAAAAAAAA",
    CONF_PING_INTERVAL: 10,
    CONF_ZONES: 1,
    CONF_ADDITIONAL_ACCOUNTS: False,
}

BASIC_OPTIONS = {CONF_IGNORE_TIMESTAMPS: False, CONF_ZONES: 2}

BASE_OUT = {
    "data": {
        CONF_PORT: 7777,
        CONF_PROTOCOL: "TCP",
        CONF_ACCOUNTS: [
            {
                CONF_ACCOUNT: "ABCDEF",
                CONF_ENCRYPTION_KEY: "AAAAAAAAAAAAAAAA",
                CONF_PING_INTERVAL: 10,
            },
        ],
    },
    "options": {
        CONF_ACCOUNTS: {"ABCDEF": {CONF_IGNORE_TIMESTAMPS: False, CONF_ZONES: 1}}
    },
}

ADDITIONAL_CONFIG_ENTRY_ID = "2"
BASIC_CONFIG_ADDITIONAL = {
    CONF_PORT: 7777,
    CONF_PROTOCOL: "TCP",
    CONF_ACCOUNT: "ABCDEF",
    CONF_ENCRYPTION_KEY: "AAAAAAAAAAAAAAAA",
    CONF_PING_INTERVAL: 10,
    CONF_ZONES: 1,
    CONF_ADDITIONAL_ACCOUNTS: True,
}

ADDITIONAL_ACCOUNT = {
    CONF_ACCOUNT: "ACC2",
    CONF_ENCRYPTION_KEY: "AAAAAAAAAAAAAAAA",
    CONF_PING_INTERVAL: 2,
    CONF_ZONES: 2,
    CONF_ADDITIONAL_ACCOUNTS: False,
}
ADDITIONAL_OUT = {
    "data": {
        CONF_PORT: 7777,
        CONF_PROTOCOL: "TCP",
        CONF_ACCOUNTS: [
            {
                CONF_ACCOUNT: "ABCDEF",
                CONF_ENCRYPTION_KEY: "AAAAAAAAAAAAAAAA",
                CONF_PING_INTERVAL: 10,
            },
            {
                CONF_ACCOUNT: "ACC2",
                CONF_ENCRYPTION_KEY: "AAAAAAAAAAAAAAAA",
                CONF_PING_INTERVAL: 2,
            },
        ],
    },
    "options": {
        CONF_ACCOUNTS: {
            "ABCDEF": {CONF_IGNORE_TIMESTAMPS: False, CONF_ZONES: 1},
            "ACC2": {CONF_IGNORE_TIMESTAMPS: False, CONF_ZONES: 2},
        }
    },
}


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _sia: None = Depends(mock_sia),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


async def setup_sia(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    """Add mock config to HASS."""
    expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()


@test
async def form_start_user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Start the form and check if you get the right id and schema for the user step."""
    flow = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(flow["step_id"]).to_equal("user")
    expect(flow["errors"]).to_be(None)
    expect(flow["data_schema"]).to_be(HUB_SCHEMA)


@test
async def form_start_account(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Start the form and check if you get the right id and schema for the additional account step."""
    flow = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    flow = await hass.config_entries.flow.async_configure(
        flow["flow_id"], BASIC_CONFIG_ADDITIONAL
    )
    expect(flow["step_id"]).to_equal("add_account")
    expect(flow["errors"]).to_be(None)
    expect(flow["data_schema"]).to_be(ACCOUNT_SCHEMA)


@test
async def create(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we create a entry through the form."""
    flow = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch("homeassistant.components.sia.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            flow["flow_id"], BASIC_CONFIG
        )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"SIA Alarm on port {BASIC_CONFIG[CONF_PORT]}")
    expect(result["data"]).to_equal(BASE_OUT["data"])
    expect(result["options"]).to_equal(BASE_OUT["options"])


@test
async def create_additional_account(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we create a config with two accounts."""
    flow = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    flow = await hass.config_entries.flow.async_configure(
        flow["flow_id"], BASIC_CONFIG_ADDITIONAL
    )
    with patch("homeassistant.components.sia.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            flow["flow_id"], ADDITIONAL_ACCOUNT
        )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"SIA Alarm on port {BASIC_CONFIG[CONF_PORT]}")
    expect(result["data"]).to_equal(ADDITIONAL_OUT["data"])
    expect(result["options"]).to_equal(ADDITIONAL_OUT["options"])


@test
async def abort_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test aborting a config that already exists."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=BASE_OUT["data"],
        options=BASE_OUT["options"],
        title="SIA Alarm on port 7777",
        entry_id=BASIS_CONFIG_ENTRY_ID,
        version=1,
    )
    await setup_sia(hass, config_entry)
    start_another_flow = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    get_abort = await hass.config_entries.flow.async_configure(
        start_another_flow["flow_id"], BASIC_CONFIG
    )
    expect(get_abort["type"]).to_be(FlowResultType.ABORT)
    expect(get_abort["reason"]).to_equal("already_configured")


@test.cases(
    test.case("invalid_key_format", field="encryption_key", value="AAAAAAAAAAAAAZZZ", error="invalid_key_format"),
    test.case("invalid_key_length", field="encryption_key", value="AAAAAAAAAAAAA", error="invalid_key_length"),
    test.case("invalid_account_format", field="account", value="ZZZ", error="invalid_account_format"),
    test.case("invalid_account_length", field="account", value="A", error="invalid_account_length"),
    test.case("invalid_ping", field="ping_interval", value=1500, error="invalid_ping"),
    test.case("invalid_zones", field="zones", value=0, error="invalid_zones"),
)
async def validation_errors_user(
    field: str,
    value: object,
    error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle the different invalid inputs, in the user flow."""
    flow = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    config = BASIC_CONFIG.copy()
    config[field] = value
    result_err = await hass.config_entries.flow.async_configure(flow["flow_id"], config)
    expect(result_err["type"]).to_be(FlowResultType.FORM)
    expect(result_err["errors"]).to_equal({"base": error})


@test.cases(
    test.case("invalid_key_format", field="encryption_key", value="AAAAAAAAAAAAAZZZ", error="invalid_key_format"),
    test.case("invalid_key_length", field="encryption_key", value="AAAAAAAAAAAAA", error="invalid_key_length"),
    test.case("invalid_account_format", field="account", value="ZZZ", error="invalid_account_format"),
    test.case("invalid_account_length", field="account", value="A", error="invalid_account_length"),
    test.case("invalid_ping", field="ping_interval", value=1500, error="invalid_ping"),
    test.case("invalid_zones", field="zones", value=0, error="invalid_zones"),
)
async def validation_errors_account(
    field: str,
    value: object,
    error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle the different invalid inputs, in the add_account flow."""
    flow = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    flow_at_add_account_step = await hass.config_entries.flow.async_configure(
        flow["flow_id"], BASIC_CONFIG_ADDITIONAL
    )
    config = ADDITIONAL_ACCOUNT.copy()
    config[field] = value
    result_err = await hass.config_entries.flow.async_configure(
        flow_at_add_account_step["flow_id"], config
    )
    expect(result_err["type"]).to_be(FlowResultType.FORM)
    expect(result_err["errors"]).to_equal({"base": error})


@test
async def unknown_user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test unknown exceptions."""
    flow = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(
        "pysiaalarm.SIAAccount.validate_account",
        side_effect=Exception,
    ):
        config = BASIC_CONFIG
        result_err = await hass.config_entries.flow.async_configure(
            flow["flow_id"], config
        )
        expect(result_err is not None).to_be(True)
        expect(result_err["step_id"]).to_equal("user")
        expect(result_err["errors"]).to_equal({"base": "unknown"})
        expect(result_err["data_schema"]).to_be(HUB_SCHEMA)


@test
async def unknown_account(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test unknown exceptions."""
    flow = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    flow_at_add_account_step = await hass.config_entries.flow.async_configure(
        flow["flow_id"], BASIC_CONFIG_ADDITIONAL
    )
    with patch(
        "pysiaalarm.SIAAccount.validate_account",
        side_effect=Exception,
    ):
        config = ADDITIONAL_ACCOUNT
        result_err = await hass.config_entries.flow.async_configure(
            flow_at_add_account_step["flow_id"], config
        )
        expect(result_err is not None).to_be(True)
        expect(result_err["step_id"]).to_equal("add_account")
        expect(result_err["errors"]).to_equal({"base": "unknown"})
        expect(result_err["data_schema"]).to_be(ACCOUNT_SCHEMA)


@test
async def options_basic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test options flow for single account."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=BASE_OUT["data"],
        options=BASE_OUT["options"],
        title="SIA Alarm on port 7777",
        entry_id=BASIS_CONFIG_ENTRY_ID,
        version=1,
    )
    await setup_sia(hass, config_entry)
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("options")
    expect(result["last_step"]).to_be(True)

    updated = await hass.config_entries.options.async_configure(
        result["flow_id"], BASIC_OPTIONS
    )
    await hass.async_block_till_done()
    expect(updated["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(updated["data"]).to_equal(
        {CONF_ACCOUNTS: {BASIC_CONFIG[CONF_ACCOUNT]: BASIC_OPTIONS}}
    )


@test
async def options_additional(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test options flow for single account."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=ADDITIONAL_OUT["data"],
        options=ADDITIONAL_OUT["options"],
        title="SIA Alarm on port 7777",
        entry_id=ADDITIONAL_CONFIG_ENTRY_ID,
        version=1,
    )
    await setup_sia(hass, config_entry)
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("options")
    expect(result["last_step"]).to_be(False)

    updated = await hass.config_entries.options.async_configure(
        result["flow_id"], BASIC_OPTIONS
    )
    expect(updated["type"]).to_be(FlowResultType.FORM)
    expect(updated["step_id"]).to_equal("options")
    expect(updated["last_step"]).to_be(True)
