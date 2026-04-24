"""Test the Risco config flow."""

from __future__ import annotations

from unittest.mock import PropertyMock, patch

import voluptuous as vol
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.risco.config_flow import (
    CannotConnectError,
    UnauthorizedError,
)
from homeassistant.components.risco.const import CONF_COMMUNICATION_DELAY, DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import cloud_config_entry as cloud_config_entry_fx

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

TEST_SITE_NAME = "test-site-name"
TEST_CLOUD_DATA = {
    "username": "test-username",
    "password": "test-password",
    "pin": "1234",
}

TEST_LOCAL_DATA = {
    "host": "test-host",
    "port": 5004,
    "pin": "1234",
}

TEST_RISCO_TO_HA = {
    "arm": "armed_away",
    "partial_arm": "armed_home",
    "A": "armed_home",
    "B": "armed_home",
    "C": "armed_night",
    "D": "armed_night",
}

TEST_HA_TO_RISCO = {
    "armed_away": "arm",
    "armed_home": "partial_arm",
    "armed_night": "C",
}

TEST_OPTIONS = {
    "code_arm_required": True,
    "code_disarm_required": True,
}

TEST_ADVANCED_OPTIONS = {
    "scan_interval": 10,
    "concurrency": 3,
}


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def cloud_form(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we get the cloud form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.MENU)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "cloud"}
    )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.risco.config_flow.RiscoCloud.login",
            return_value=True,
        ),
        patch(
            "homeassistant.components.risco.config_flow.RiscoCloud.site_name",
            new_callable=PropertyMock(return_value=TEST_SITE_NAME),
        ),
        patch(
            "homeassistant.components.risco.config_flow.RiscoCloud.close"
        ) as mock_close,
        patch(
            "homeassistant.components.risco.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"], TEST_CLOUD_DATA
        )
        await hass.async_block_till_done()

    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3["title"]).to_equal(TEST_SITE_NAME)
    expect(result3["data"]).to_equal(TEST_CLOUD_DATA)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    mock_close.assert_awaited_once()


@test.cases(
    test.case("invalid_auth", exception=UnauthorizedError, error="invalid_auth"),
    test.case("cannot_connect", exception=CannotConnectError, error="cannot_connect"),
    test.case("unknown", exception=Exception, error="unknown"),
)
async def cloud_error(
    *,
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle config flow errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "cloud"}
    )

    with (
        patch(
            "homeassistant.components.risco.RiscoCloud.login", side_effect=exception
        ),
        patch(
            "homeassistant.components.risco.config_flow.RiscoCloud.close"
        ) as mock_close,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"], TEST_CLOUD_DATA
        )

    mock_close.assert_awaited_once()
    expect(result3["type"]).to_be(FlowResultType.FORM)
    expect(result3["errors"]).to_equal({"base": error})


@test
async def form_cloud_already_exists(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test that a flow with an existing username aborts."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_CLOUD_DATA["username"],
        data=TEST_CLOUD_DATA,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "cloud"}
    )
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"], TEST_CLOUD_DATA
    )
    expect(result3["type"]).to_be(FlowResultType.ABORT)
    expect(result3["reason"]).to_equal("already_configured")


@test
async def form_reauth(
    hass: HomeAssistant = Depends(hass_fixture),
    cloud_entry: MockConfigEntry = Depends(cloud_config_entry_fx),
) -> None:
    """Test reauthenticate."""
    result = await cloud_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.risco.config_flow.RiscoCloud.login",
            return_value=True,
        ),
        patch(
            "homeassistant.components.risco.config_flow.RiscoCloud.site_name",
            new_callable=PropertyMock(return_value=TEST_SITE_NAME),
        ),
        patch(
            "homeassistant.components.risco.config_flow.RiscoCloud.close",
        ),
        patch(
            "homeassistant.components.risco.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {**TEST_CLOUD_DATA, CONF_PASSWORD: "new_password"}
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")
    expect(cloud_entry.data[CONF_PASSWORD]).to_equal("new_password")
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_reauth_with_new_username(
    hass: HomeAssistant = Depends(hass_fixture),
    cloud_entry: MockConfigEntry = Depends(cloud_config_entry_fx),
) -> None:
    """Test reauthenticate with new username."""
    result = await cloud_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.risco.config_flow.RiscoCloud.login",
            return_value=True,
        ),
        patch(
            "homeassistant.components.risco.config_flow.RiscoCloud.site_name",
            new_callable=PropertyMock(return_value=TEST_SITE_NAME),
        ),
        patch(
            "homeassistant.components.risco.config_flow.RiscoCloud.close",
        ),
        patch(
            "homeassistant.components.risco.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {**TEST_CLOUD_DATA, CONF_USERNAME: "new_user"}
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")
    expect(cloud_entry.data[CONF_USERNAME]).to_equal("new_user")
    expect(cloud_entry.unique_id).to_equal("new_user")
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def local_form(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we get the local form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.MENU)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "local"}
    )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.risco.config_flow.RiscoLocal.connect",
            return_value=True,
        ),
        patch(
            "homeassistant.components.risco.config_flow.RiscoLocal.id",
            new_callable=PropertyMock(return_value=TEST_SITE_NAME),
        ),
        patch(
            "homeassistant.components.risco.config_flow.RiscoLocal.disconnect"
        ) as mock_close,
        patch(
            "homeassistant.components.risco.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"], TEST_LOCAL_DATA
        )
        await hass.async_block_till_done()

    expected_data = {
        **TEST_LOCAL_DATA,
        "type": "local",
        CONF_COMMUNICATION_DELAY: 0,
    }
    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3["title"]).to_equal(TEST_SITE_NAME)
    expect(result3["data"]).to_equal(expected_data)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    mock_close.assert_awaited_once()


@test.cases(
    test.case("invalid_auth", exception=UnauthorizedError, error="invalid_auth"),
    test.case("cannot_connect", exception=CannotConnectError, error="cannot_connect"),
    test.case("unknown", exception=Exception, error="unknown"),
)
async def local_error(
    *,
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle config flow errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "local"}
    )

    with patch(
        "homeassistant.components.risco.RiscoLocal.connect",
        side_effect=exception,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"], TEST_LOCAL_DATA
        )

    expect(result3["type"]).to_be(FlowResultType.FORM)
    expect(result3["errors"]).to_equal({"base": error})


@test
async def form_local_already_exists(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that a flow with an existing host aborts."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_SITE_NAME,
        data=TEST_LOCAL_DATA,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "local"}
    )

    with (
        patch(
            "homeassistant.components.risco.config_flow.RiscoLocal.connect",
            return_value=True,
        ),
        patch(
            "homeassistant.components.risco.config_flow.RiscoLocal.id",
            new_callable=PropertyMock(return_value=TEST_SITE_NAME),
        ),
        patch(
            "homeassistant.components.risco.config_flow.RiscoLocal.disconnect",
        ),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"], TEST_LOCAL_DATA
        )

    expect(result3["type"]).to_be(FlowResultType.ABORT)
    expect(result3["reason"]).to_equal("already_configured")


@test
async def options_flow(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test options flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_CLOUD_DATA["username"],
        data=TEST_CLOUD_DATA,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input=TEST_OPTIONS
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("risco_to_ha")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input=TEST_RISCO_TO_HA
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("ha_to_risco")

    with patch("homeassistant.components.risco.async_setup_entry", return_value=True):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], user_input=TEST_HA_TO_RISCO
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(entry.options).to_equal(
        {
            **TEST_OPTIONS,
            "risco_states_to_ha": TEST_RISCO_TO_HA,
            "ha_states_to_risco": TEST_HA_TO_RISCO,
        }
    )


@test
async def advanced_options_flow(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test options flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_CLOUD_DATA["username"],
        data=TEST_CLOUD_DATA,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(
        entry.entry_id, context={"show_advanced_options": True}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")
    expect("concurrency" in result["data_schema"].schema).to_be(True)
    expect("scan_interval" in result["data_schema"].schema).to_be(True)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={**TEST_OPTIONS, **TEST_ADVANCED_OPTIONS}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("risco_to_ha")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input=TEST_RISCO_TO_HA
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("ha_to_risco")

    with patch("homeassistant.components.risco.async_setup_entry", return_value=True):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], user_input=TEST_HA_TO_RISCO
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(entry.options).to_equal(
        {
            **TEST_OPTIONS,
            **TEST_ADVANCED_OPTIONS,
            "risco_states_to_ha": TEST_RISCO_TO_HA,
            "ha_states_to_risco": TEST_HA_TO_RISCO,
        }
    )


@test
async def ha_to_risco_schema(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test that the schema for the ha-to-risco mapping step is generated properly."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_CLOUD_DATA["username"],
        data=TEST_CLOUD_DATA,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input=TEST_OPTIONS
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input=TEST_RISCO_TO_HA
    )

    raised_custom_bypass = False
    try:
        await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={**TEST_HA_TO_RISCO, "armed_custom_bypass": "D"},
        )
    except vol.error.Invalid:
        raised_custom_bypass = True
    expect(raised_custom_bypass).to_be(True)

    raised_armed_night = False
    try:
        await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={**TEST_HA_TO_RISCO, "armed_night": "A"},
        )
    except vol.error.Invalid:
        raised_armed_night = True
    expect(raised_armed_night).to_be(True)
