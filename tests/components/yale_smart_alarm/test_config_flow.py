"""Test the Yale Smart Living config flow."""

from __future__ import annotations

from unittest.mock import patch

from tryke import Depends, expect, fixture, test
from yalesmartalarmclient.exceptions import AuthenticationError, UnknownError

from homeassistant import config_entries
from homeassistant.components.yale_smart_alarm.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


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
        patch(
            "homeassistant.components.yale_smart_alarm.config_flow.YaleSmartAlarmClient",
        ),
        patch(
            "homeassistant.components.yale_smart_alarm.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "test-username", "password": "test-password", "area_id": "1"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("test-username")
    expect(result2["data"]).to_equal(
        {"username": "test-username", "password": "test-password", "area_id": "1"}
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("invalid_auth", sideeffect=AuthenticationError, p_error="invalid_auth"),
    test.case("connection", sideeffect=ConnectionError, p_error="cannot_connect"),
    test.case("timeout", sideeffect=TimeoutError, p_error="cannot_connect"),
    test.case("unknown", sideeffect=UnknownError, p_error="cannot_connect"),
)
async def form_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    sideeffect: type[Exception],
    p_error: str,
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.yale_smart_alarm.config_flow.YaleSmartAlarmClient",
        side_effect=sideeffect,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "test-username", "password": "test-password", "area_id": "1"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": p_error})

    with (
        patch(
            "homeassistant.components.yale_smart_alarm.config_flow.YaleSmartAlarmClient",
        ),
        patch(
            "homeassistant.components.yale_smart_alarm.async_setup_entry",
            return_value=True,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "test-username", "password": "test-password", "area_id": "1"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("test-username")
    expect(result2["data"]).to_equal(
        {"username": "test-username", "password": "test-password", "area_id": "1"}
    )


@test
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a reauthentication flow."""
    entry = MockConfigEntry(
        title="test-username",
        domain=DOMAIN,
        unique_id="test-username",
        data={"username": "test-username", "password": "test-password", "area_id": "1"},
        version=2,
        minor_version=2,
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.yale_smart_alarm.config_flow.YaleSmartAlarmClient",
        ) as mock_yale,
        patch(
            "homeassistant.components.yale_smart_alarm.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"password": "new-test-password"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")
    expect(entry.data).to_equal(
        {"username": "test-username", "password": "new-test-password", "area_id": "1"}
    )

    expect(len(mock_yale.mock_calls)).to_equal(1)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("invalid_auth", sideeffect=AuthenticationError, p_error="invalid_auth"),
    test.case("connection", sideeffect=ConnectionError, p_error="cannot_connect"),
    test.case("timeout", sideeffect=TimeoutError, p_error="cannot_connect"),
    test.case("unknown", sideeffect=UnknownError, p_error="cannot_connect"),
)
async def reauth_flow_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    sideeffect: type[Exception],
    p_error: str,
) -> None:
    """Test a reauthentication flow."""
    entry = MockConfigEntry(
        title="test-username",
        domain=DOMAIN,
        unique_id="test-username",
        data={"username": "test-username", "password": "test-password", "area_id": "1"},
        version=2,
        minor_version=2,
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)

    with patch(
        "homeassistant.components.yale_smart_alarm.config_flow.YaleSmartAlarmClient",
        side_effect=sideeffect,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"password": "wrong-password"},
        )
        await hass.async_block_till_done()

    expect(result2["step_id"]).to_equal("reauth_confirm")
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": p_error})

    with (
        patch(
            "homeassistant.components.yale_smart_alarm.config_flow.YaleSmartAlarmClient",
            return_value="",
        ),
        patch(
            "homeassistant.components.yale_smart_alarm.async_setup_entry",
            return_value=True,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"password": "new-test-password"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")
    expect(entry.data).to_equal(
        {"username": "test-username", "password": "new-test-password", "area_id": "1"}
    )


@test
async def reconfigure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfigure config flow."""
    entry = MockConfigEntry(
        title="test-username",
        domain=DOMAIN,
        unique_id="test-username",
        data={"username": "test-username", "password": "test-password", "area_id": "1"},
        version=2,
        minor_version=2,
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)

    with (
        patch(
            "homeassistant.components.yale_smart_alarm.config_flow.YaleSmartAlarmClient",
            return_value="",
        ),
        patch(
            "homeassistant.components.yale_smart_alarm.async_setup_entry",
            return_value=True,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "new-test-password",
                "area_id": "2",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reconfigure_successful")
    expect(entry.data).to_equal(
        {"username": "test-username", "password": "new-test-password", "area_id": "2"}
    )


@test
async def reconfigure_username_exist(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfigure config flow abort other username already exist."""
    entry = MockConfigEntry(
        title="test-username",
        domain=DOMAIN,
        unique_id="test-username",
        data={"username": "test-username", "password": "test-password", "area_id": "1"},
        version=2,
        minor_version=2,
    )
    entry.add_to_hass(hass)
    entry2 = MockConfigEntry(
        title="other-username",
        domain=DOMAIN,
        unique_id="other-username",
        data={
            "username": "other-username",
            "password": "test-password",
            "area_id": "1",
        },
        version=2,
        minor_version=2,
    )
    entry2.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)

    with (
        patch(
            "homeassistant.components.yale_smart_alarm.config_flow.YaleSmartAlarmClient",
            return_value="",
        ),
        patch(
            "homeassistant.components.yale_smart_alarm.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "other-username", "password": "test-password", "area_id": "1"},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "unique_id_exists"})

    with (
        patch(
            "homeassistant.components.yale_smart_alarm.config_flow.YaleSmartAlarmClient",
            return_value="",
        ),
        patch(
            "homeassistant.components.yale_smart_alarm.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "other-new-username",
                "password": "test-password",
                "area_id": "1",
            },
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(entry.data).to_equal(
        {"username": "other-new-username", "password": "test-password", "area_id": "1"}
    )


@test.cases(
    test.case("invalid_auth", sideeffect=AuthenticationError, p_error="invalid_auth"),
    test.case("connection", sideeffect=ConnectionError, p_error="cannot_connect"),
    test.case("timeout", sideeffect=TimeoutError, p_error="cannot_connect"),
    test.case("unknown", sideeffect=UnknownError, p_error="cannot_connect"),
)
async def reconfigure_flow_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    sideeffect: type[Exception],
    p_error: str,
) -> None:
    """Test a reauthentication flow."""
    entry = MockConfigEntry(
        title="test-username",
        domain=DOMAIN,
        unique_id="test-username",
        data={"username": "test-username", "password": "test-password", "area_id": "1"},
        version=2,
        minor_version=2,
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)

    with patch(
        "homeassistant.components.yale_smart_alarm.config_flow.YaleSmartAlarmClient",
        side_effect=sideeffect,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "update-password",
                "area_id": "1",
            },
        )
        await hass.async_block_till_done()

    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": p_error})

    with (
        patch(
            "homeassistant.components.yale_smart_alarm.config_flow.YaleSmartAlarmClient",
            return_value="",
        ),
        patch(
            "homeassistant.components.yale_smart_alarm.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "new-test-password",
                "area_id": "1",
            },
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(entry.data).to_equal(
        {"username": "test-username", "password": "new-test-password", "area_id": "1"}
    )


@test.skip("options_flow uses load_config_entry conftest fixture not in tryke")
@test
async def options_flow() -> None:
    """Test options config flow - skipped."""
