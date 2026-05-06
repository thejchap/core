"""Test the Sensibo config flow."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

from pysensibo import AuthenticationError, SensiboData, SensiboError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.sensibo.const import DOMAIN
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import get_data, mock_client, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def basic_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    client: MagicMock = Depends(mock_client),
) -> None:
    """Test we get and complete the form."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["step_id"]).to_equal("user")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_API_KEY: "1234567890",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["version"]).to_equal(2)
    expect(result["title"]).to_equal("firstnamelastname")
    expect(result["result"].unique_id).to_equal("firstnamelastname")
    expect(result["data"]).to_equal(
        {
            CONF_API_KEY: "1234567890",
        }
    )

    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("authentication_error", error_message=AuthenticationError, p_error="invalid_auth"),
    test.case("sensibo_error", error_message=SensiboError, p_error="cannot_connect"),
)
async def flow_fails(
    error_message: type[Exception],
    p_error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test config flow errors."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(config_entries.SOURCE_USER)

    client.async_get_devices.side_effect = error_message

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_API_KEY: "1234567890",
        },
    )

    expect(result["errors"]).to_equal({"base": p_error})

    client.async_get_devices.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_API_KEY: "1234567890",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("firstnamelastname")
    expect(result["data"]).to_equal(
        {
            CONF_API_KEY: "1234567890",
        }
    )


@test
async def flow_get_no_devices(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_client),
    data: tuple[SensiboData, dict[str, Any], dict[str, Any]] = Depends(get_data),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test config flow get no devices from api."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(config_entries.SOURCE_USER)

    client.async_get_devices.return_value = {"result": []}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_API_KEY: "1234567890",
        },
    )

    expect(result["errors"]).to_equal({"base": "no_devices"})

    client.async_get_devices.return_value = data[2]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_API_KEY: "1234567890",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("firstnamelastname")
    expect(result["data"]).to_equal(
        {
            CONF_API_KEY: "1234567890",
        }
    )


@test
async def flow_get_no_username(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_client),
    data: tuple[SensiboData, dict[str, Any], dict[str, Any]] = Depends(get_data),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test config flow get no username from api."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(config_entries.SOURCE_USER)

    client.async_get_me.return_value = {"result": {}}

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_API_KEY: "1234567890",
        },
    )

    expect(result2["errors"]).to_equal({"base": "no_username"})

    client.async_get_me.return_value = data[1]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_API_KEY: "1234567890",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("firstnamelastname")
    expect(result["data"]).to_equal(
        {
            CONF_API_KEY: "1234567890",
        }
    )


@test
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test a reauthentication flow."""
    entry = MockConfigEntry(
        version=2,
        domain=DOMAIN,
        unique_id="firstnamelastname",
        data={CONF_API_KEY: "1234567890"},
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "1234567890"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(entry.data).to_equal({CONF_API_KEY: "1234567890"})


@test.cases(
    test.case("authentication_error", sideeffect=AuthenticationError, p_error="invalid_auth"),
    test.case("sensibo_error", sideeffect=SensiboError, p_error="cannot_connect"),
)
async def reauth_flow_error(
    sideeffect: type[Exception],
    p_error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test a reauthentication flow with error."""
    entry = MockConfigEntry(
        version=2,
        domain=DOMAIN,
        unique_id="firstnamelastname",
        data={CONF_API_KEY: "1234567890"},
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)

    client.async_get_devices.side_effect = sideeffect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "1234567890"},
    )

    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": p_error})

    client.async_get_devices.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "1234567890"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(entry.data).to_equal({CONF_API_KEY: "1234567890"})


@test.cases(
    test.case(
        "no_username",
        get_devices={"result": [{"id": "xyzxyz"}, {"id": "abcabc"}]},
        get_me={"result": {}},
        p_error="no_username",
    ),
    test.case(
        "no_devices",
        get_devices={"result": []},
        get_me={"result": {"username": "firstnamelastname"}},
        p_error="no_devices",
    ),
    test.case(
        "incorrect_api_key",
        get_devices={"result": [{"id": "xyzxyz"}, {"id": "abcabc"}]},
        get_me={"result": {"username": "firstnamelastname2"}},
        p_error="incorrect_api_key",
    ),
)
async def flow_reauth_no_username_or_device(
    get_devices: dict[str, Any],
    get_me: dict[str, Any],
    p_error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_client),
    data: tuple[SensiboData, dict[str, Any], dict[str, Any]] = Depends(get_data),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test reauth flow with errors from api."""
    entry = MockConfigEntry(
        version=2,
        domain=DOMAIN,
        unique_id="firstnamelastname",
        data={CONF_API_KEY: "1234567890"},
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    client.async_get_devices.return_value = get_devices
    client.async_get_me.return_value = get_me

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_API_KEY: "1234567890",
        },
    )

    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": p_error})

    client.async_get_devices.return_value = data[2]
    client.async_get_me.return_value = data[1]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "1234567890"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(entry.data).to_equal({CONF_API_KEY: "1234567890"})


@test
async def reconfigure_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test a reconfigure flow."""
    entry = MockConfigEntry(
        version=2,
        domain=DOMAIN,
        unique_id="firstnamelastname",
        data={CONF_API_KEY: "1234567890"},
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "1234567890"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(entry.data).to_equal({CONF_API_KEY: "1234567890"})


@test.cases(
    test.case("authentication_error", sideeffect=AuthenticationError, p_error="invalid_auth"),
    test.case("sensibo_error", sideeffect=SensiboError, p_error="cannot_connect"),
)
async def reconfigure_flow_error(
    sideeffect: type[Exception],
    p_error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test a reconfigure flow with error."""
    entry = MockConfigEntry(
        version=2,
        domain=DOMAIN,
        unique_id="firstnamelastname",
        data={CONF_API_KEY: "1234567890"},
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)

    client.async_get_devices.side_effect = sideeffect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "1234567890"},
    )

    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": p_error})

    client.async_get_devices.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "1234567890"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(entry.data).to_equal({CONF_API_KEY: "1234567890"})


@test.cases(
    test.case(
        "no_username",
        get_devices={"result": [{"id": "xyzxyz"}, {"id": "abcabc"}]},
        get_me={"result": {}},
        p_error="no_username",
    ),
    test.case(
        "no_devices",
        get_devices={"result": []},
        get_me={"result": {"username": "firstnamelastname"}},
        p_error="no_devices",
    ),
    test.case(
        "incorrect_api_key",
        get_devices={"result": [{"id": "xyzxyz"}, {"id": "abcabc"}]},
        get_me={"result": {"username": "firstnamelastname2"}},
        p_error="incorrect_api_key",
    ),
)
async def flow_reconfigure_no_username_or_device(
    get_devices: dict[str, Any],
    get_me: dict[str, Any],
    p_error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_client),
    data: tuple[SensiboData, dict[str, Any], dict[str, Any]] = Depends(get_data),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test reconfigure flow with errors from api."""
    entry = MockConfigEntry(
        version=2,
        domain=DOMAIN,
        unique_id="firstnamelastname",
        data={CONF_API_KEY: "1234567890"},
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    client.async_get_devices.return_value = get_devices
    client.async_get_me.return_value = get_me

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_API_KEY: "1234567890",
        },
    )

    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": p_error})

    client.async_get_devices.return_value = data[2]
    client.async_get_me.return_value = data[1]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "1234567890"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(entry.data).to_equal({CONF_API_KEY: "1234567890"})
