"""Tests for fritzbox_callmonitor config flow."""

from __future__ import annotations

from unittest.mock import PropertyMock

from fritzconnection.core.exceptions import (
    FritzAuthorizationError,
    FritzConnectionException,
    FritzSecurityError,
)
from requests.exceptions import ConnectionError as RequestsConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.fritzbox_callmonitor.config_flow import ConnectResult
from homeassistant.components.fritzbox_callmonitor.const import (
    CONF_PHONEBOOK,
    CONF_PREFIXES,
    DOMAIN,
    FRITZ_ATTR_NAME,
    SERIAL_NUMBER,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry, patch
from tests.hass_fixtures import hass as hass_fixture, mock_network

MOCK_HOST = "fake_host"
MOCK_PORT = 1234
MOCK_USERNAME = "fake_username"
MOCK_PASSWORD = "fake_password"
MOCK_PHONEBOOK_NAME_1 = "fake_phonebook_name_1"
MOCK_PHONEBOOK_NAME_2 = "fake_phonebook_name_2"
MOCK_PHONEBOOK_ID = 0
MOCK_SERIAL_NUMBER = "fake_serial_number"
MOCK_NAME = "fake_call_monitor_name"

MOCK_USER_DATA = {
    CONF_HOST: MOCK_HOST,
    CONF_PORT: MOCK_PORT,
    CONF_PASSWORD: MOCK_PASSWORD,
    CONF_USERNAME: MOCK_USERNAME,
}
MOCK_CONFIG_ENTRY = {
    CONF_HOST: MOCK_HOST,
    CONF_PORT: MOCK_PORT,
    CONF_PASSWORD: MOCK_PASSWORD,
    CONF_USERNAME: MOCK_USERNAME,
    CONF_PHONEBOOK: MOCK_PHONEBOOK_ID,
    SERIAL_NUMBER: MOCK_SERIAL_NUMBER,
}
MOCK_DEVICE_INFO = {
    "Name": "FRITZ!Box 7590",
    "HW": "226",
    "Version": "100.01.01",
    "Revision": "10000",
    "Serial": MOCK_SERIAL_NUMBER,
    "OEM": "avm",
    "Lang": "de",
    "Annex": "B",
    "Lab": None,
    "Country": "049",
    "Flag": "mesh_master",
    "UpdateConfig": "2",
}
MOCK_PHONEBOOK_INFO_1 = {FRITZ_ATTR_NAME: MOCK_PHONEBOOK_NAME_1}
MOCK_PHONEBOOK_INFO_2 = {FRITZ_ATTR_NAME: MOCK_PHONEBOOK_NAME_2}
MOCK_UNIQUE_ID = f"{MOCK_SERIAL_NUMBER}-{MOCK_PHONEBOOK_ID}"


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def setup_one_phonebook(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setting up manually."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with (
        patch(
            "homeassistant.components.fritzbox_callmonitor.base.FritzPhonebook.__init__",
            return_value=None,
        ),
        patch(
            "homeassistant.components.fritzbox_callmonitor.base.FritzPhonebook.phonebook_ids",
            new_callable=PropertyMock,
            return_value=[0],
        ),
        patch(
            "homeassistant.components.fritzbox_callmonitor.base.FritzPhonebook.phonebook_info",
            return_value=MOCK_PHONEBOOK_INFO_1,
        ),
        patch(
            "homeassistant.components.fritzbox_callmonitor.base.FritzPhonebook.modelname",
            return_value=MOCK_PHONEBOOK_NAME_1,
        ),
        patch(
            "homeassistant.components.fritzbox_callmonitor.config_flow.FritzConnection.__init__",
            return_value=None,
        ),
        patch(
            "homeassistant.components.fritzbox_callmonitor.config_flow.FritzConnection.updatecheck",
            new_callable=PropertyMock,
            return_value=MOCK_DEVICE_INFO,
        ),
        patch(
            "homeassistant.components.fritzbox_callmonitor.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_DATA
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(MOCK_PHONEBOOK_NAME_1)
    expect(result["data"]).to_equal(MOCK_CONFIG_ENTRY)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def setup_multiple_phonebooks(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setting up manually."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with (
        patch(
            "homeassistant.components.fritzbox_callmonitor.base.FritzPhonebook.__init__",
            return_value=None,
        ),
        patch(
            "homeassistant.components.fritzbox_callmonitor.base.FritzPhonebook.phonebook_ids",
            new_callable=PropertyMock,
            return_value=[0, 1],
        ),
        patch(
            "homeassistant.components.fritzbox_callmonitor.config_flow.FritzConnection.__init__",
            return_value=None,
        ),
        patch(
            "homeassistant.components.fritzbox_callmonitor.config_flow.FritzConnection.updatecheck",
            new_callable=PropertyMock,
            return_value=MOCK_DEVICE_INFO,
        ),
        patch(
            "homeassistant.components.fritzbox_callmonitor.base.FritzPhonebook.phonebook_info",
            side_effect=[MOCK_PHONEBOOK_INFO_1, MOCK_PHONEBOOK_INFO_2],
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_DATA
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("phonebook")
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.fritzbox_callmonitor.base.FritzPhonebook.modelname",
            return_value=MOCK_PHONEBOOK_NAME_1,
        ),
        patch(
            "homeassistant.components.fritzbox_callmonitor.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PHONEBOOK: MOCK_PHONEBOOK_NAME_2},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(MOCK_PHONEBOOK_NAME_2)
    expect(result["data"]).to_equal(
        {
            CONF_HOST: MOCK_HOST,
            CONF_PORT: MOCK_PORT,
            CONF_PASSWORD: MOCK_PASSWORD,
            CONF_USERNAME: MOCK_USERNAME,
            CONF_PHONEBOOK: 1,
            SERIAL_NUMBER: MOCK_SERIAL_NUMBER,
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def setup_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    with patch(
        "homeassistant.components.fritzbox_callmonitor.base.FritzPhonebook.__init__",
        side_effect=RequestsConnectionError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_DATA
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(ConnectResult.NO_DEVIES_FOUND)


@test
async def setup_insufficient_permissions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle insufficient permissions."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    with patch(
        "homeassistant.components.fritzbox_callmonitor.base.FritzPhonebook.__init__",
        side_effect=FritzSecurityError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_DATA
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(ConnectResult.INSUFFICIENT_PERMISSIONS)


@test.cases(
    test.case("authorization_error", error=FritzAuthorizationError),
    test.case("connection_exception", error=FritzConnectionException),
)
async def setup_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    error: type[Exception],
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    with patch(
        "homeassistant.components.fritzbox_callmonitor.base.FritzPhonebook.__init__",
        side_effect=error,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_DATA
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": ConnectResult.INVALID_AUTH})


@test
async def reauth_successful(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test starting a reauthentication flow."""
    mock_config = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_ENTRY)
    mock_config.add_to_hass(hass)
    result = await mock_config.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    with (
        patch(
            "homeassistant.components.fritzbox_callmonitor.base.FritzPhonebook.__init__",
            return_value=None,
        ),
        patch(
            "homeassistant.components.fritzbox_callmonitor.base.FritzPhonebook.phonebook_ids",
            new_callable=PropertyMock,
            return_value=[0],
        ),
        patch(
            "homeassistant.components.fritzbox_callmonitor.base.FritzPhonebook.phonebook_info",
            return_value=MOCK_PHONEBOOK_INFO_1,
        ),
        patch(
            "homeassistant.components.fritzbox_callmonitor.base.FritzPhonebook.modelname",
            return_value=MOCK_PHONEBOOK_NAME_1,
        ),
        patch(
            "homeassistant.components.fritzbox_callmonitor.config_flow.FritzConnection.__init__",
            return_value=None,
        ),
        patch(
            "homeassistant.components.fritzbox_callmonitor.config_flow.FritzConnection.updatecheck",
            new_callable=PropertyMock,
            return_value=MOCK_DEVICE_INFO,
        ),
        patch(
            "homeassistant.components.fritzbox_callmonitor.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_USERNAME: "other_fake_user",
                CONF_PASSWORD: "other_fake_password",
            },
        )

        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("reauth_successful")
        expect(mock_config.data).to_equal(
            {
                **MOCK_CONFIG_ENTRY,
                CONF_USERNAME: "other_fake_user",
                CONF_PASSWORD: "other_fake_password",
            }
        )
        expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "invalid_auth",
        side_effect=FritzConnectionException,
        error=ConnectResult.INVALID_AUTH,
    ),
    test.case(
        "insufficient_permissions",
        side_effect=FritzSecurityError,
        error=ConnectResult.INSUFFICIENT_PERMISSIONS,
    ),
)
async def reauth_not_successful(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    side_effect: type[Exception],
    error: str,
) -> None:
    """Test starting a reauthentication flow but no connection found."""
    mock_config = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_ENTRY)
    mock_config.add_to_hass(hass)
    result = await mock_config.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    with patch(
        "homeassistant.components.fritzbox_callmonitor.base.FritzPhonebook.__init__",
        side_effect=side_effect,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_USERNAME: "other_fake_user",
                CONF_PASSWORD: "other_fake_password",
            },
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("reauth_confirm")
        expect(result["errors"]["base"]).to_equal(error)


@test
async def options_flow_correct_prefixes(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow options."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=MOCK_UNIQUE_ID,
        data=MOCK_CONFIG_ENTRY,
        options={CONF_PREFIXES: None},
    )
    config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.fritzbox_callmonitor.async_setup_entry",
        return_value=True,
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        result = await hass.config_entries.options.async_init(config_entry.entry_id)

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")

        result = await hass.config_entries.options.async_configure(
            result["flow_id"], user_input={CONF_PREFIXES: "+49, 491234"}
        )

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(config_entry.options).to_equal({CONF_PREFIXES: ["+49", "491234"]})


@test
async def options_flow_incorrect_prefixes(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow options."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=MOCK_UNIQUE_ID,
        data=MOCK_CONFIG_ENTRY,
        options={CONF_PREFIXES: None},
    )
    config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.fritzbox_callmonitor.async_setup_entry",
        return_value=True,
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        result = await hass.config_entries.options.async_init(config_entry.entry_id)

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")

        result = await hass.config_entries.options.async_configure(
            result["flow_id"], user_input={CONF_PREFIXES: ""}
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({"base": ConnectResult.MALFORMED_PREFIXES})


@test
async def options_flow_no_prefixes(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow options."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=MOCK_UNIQUE_ID,
        data=MOCK_CONFIG_ENTRY,
        options={CONF_PREFIXES: None},
    )
    config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.fritzbox_callmonitor.async_setup_entry",
        return_value=True,
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        result = await hass.config_entries.options.async_init(config_entry.entry_id)

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")

        result = await hass.config_entries.options.async_configure(
            result["flow_id"], user_input={}
        )

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(config_entry.options).to_equal({CONF_PREFIXES: None})
