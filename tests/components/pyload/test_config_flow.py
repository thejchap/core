"""Test the pyLoad config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock

from pyloadapi.exceptions import CannotConnect, InvalidAuth, ParserError
from tryke import Depends, expect, fixture, test

from homeassistant.components.pyload.const import DEFAULT_NAME, DOMAIN
from homeassistant.config_entries import SOURCE_HASSIO, SOURCE_IGNORE, SOURCE_USER
from homeassistant.const import CONF_PASSWORD, CONF_URL, CONF_USERNAME, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    ADDON_DISCOVERY_INFO,
    ADDON_SERVICE_INFO,
    NEW_INPUT,
    REAUTH_INPUT,
    USER_INPUT,
    config_entry as config_entry_fx,
    mock_async_zeroconf as mock_async_zeroconf_fx,
    mock_pyloadapi as mock_pyloadapi_fx,
    mock_setup_entry as mock_setup_entry_fx,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _zc: object = Depends(mock_async_zeroconf_fx),
) -> None:
    """Wire mock_network + zeroconf for every test."""


@test
async def form(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    _mock_pyloadapi: AsyncMock = Depends(mock_pyloadapi_fx),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DEFAULT_NAME)
    expect(result["data"]).to_equal(USER_INPUT)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("invalid_auth", exception=InvalidAuth, expected_error="invalid_auth"),
    test.case(
        "cannot_connect", exception=CannotConnect, expected_error="cannot_connect"
    ),
    test.case("parser_error", exception=ParserError, expected_error="cannot_connect"),
    test.case("unknown", exception=ValueError, expected_error="unknown"),
)
async def form_errors(
    exception: type[Exception],
    expected_error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_pyloadapi: AsyncMock = Depends(mock_pyloadapi_fx),
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    mock_pyloadapi.get_status.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": expected_error})

    mock_pyloadapi.get_status.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DEFAULT_NAME)
    expect(result["data"]).to_equal(USER_INPUT)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def flow_user_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    _mock_pyloadapi: AsyncMock = Depends(mock_pyloadapi_fx),
) -> None:
    """Test we abort user data set when entry is already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reauth(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    _mock_pyloadapi: AsyncMock = Depends(mock_pyloadapi_fx),
) -> None:
    """Test reauth flow."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        REAUTH_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.data).to_equal(NEW_INPUT)
    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test.cases(
    test.case("invalid_auth", side_effect=InvalidAuth, error_text="invalid_auth"),
    test.case(
        "cannot_connect", side_effect=CannotConnect, error_text="cannot_connect"
    ),
    test.case("unknown", side_effect=IndexError, error_text="unknown"),
)
async def reauth_errors(
    side_effect: type[Exception],
    error_text: str,
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    mock_pyloadapi: AsyncMock = Depends(mock_pyloadapi_fx),
) -> None:
    """Test reauth flow."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    mock_pyloadapi.get_status.side_effect = side_effect
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        REAUTH_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_text})

    mock_pyloadapi.get_status.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        REAUTH_INPUT,
    )

    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.data).to_equal(NEW_INPUT)
    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test
async def reconfiguration(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    _mock_pyloadapi: AsyncMock = Depends(mock_pyloadapi_fx),
) -> None:
    """Test reconfiguration flow."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data).to_equal(USER_INPUT)
    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test.cases(
    test.case("invalid_auth", side_effect=InvalidAuth, error_text="invalid_auth"),
    test.case(
        "cannot_connect", side_effect=CannotConnect, error_text="cannot_connect"
    ),
    test.case("unknown", side_effect=IndexError, error_text="unknown"),
)
async def reconfigure_errors(
    side_effect: type[Exception],
    error_text: str,
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    mock_pyloadapi: AsyncMock = Depends(mock_pyloadapi_fx),
) -> None:
    """Test reconfiguration flow."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    mock_pyloadapi.get_status.side_effect = side_effect
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_text})

    mock_pyloadapi.get_status.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data).to_equal(USER_INPUT)
    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test
async def hassio_discovery(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_pyloadapi: AsyncMock = Depends(mock_pyloadapi_fx),
) -> None:
    """Test flow started from Supervisor discovery."""
    mock_pyloadapi.get_status.side_effect = InvalidAuth

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=ADDON_SERVICE_INFO,
        context={"source": SOURCE_HASSIO},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("hassio_confirm")
    expect(result["errors"]).to_be(None)

    mock_pyloadapi.get_status.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "pyload", CONF_PASSWORD: "pyload"}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("p539df76c_pyload-ng")
    expect(result["data"]).to_equal({**ADDON_DISCOVERY_INFO, CONF_VERIFY_SSL: False})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def hassio_discovery_confirm_only(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    _mock_pyloadapi: AsyncMock = Depends(mock_pyloadapi_fx),
) -> None:
    """Test flow started from Supervisor discovery. Abort with confirm only."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=ADDON_SERVICE_INFO,
        context={"source": SOURCE_HASSIO},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("hassio_confirm")

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("p539df76c_pyload-ng")
    expect(result["data"]).to_equal({**ADDON_DISCOVERY_INFO, CONF_VERIFY_SSL: False})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("invalid_auth", side_effect=InvalidAuth, error_text="invalid_auth"),
    test.case(
        "cannot_connect", side_effect=CannotConnect, error_text="cannot_connect"
    ),
    test.case("unknown", side_effect=IndexError, error_text="unknown"),
)
async def hassio_discovery_errors(
    side_effect: type[Exception],
    error_text: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_pyloadapi: AsyncMock = Depends(mock_pyloadapi_fx),
) -> None:
    """Test flow started from Supervisor discovery."""
    mock_pyloadapi.get_status.side_effect = side_effect

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=ADDON_SERVICE_INFO,
        context={"source": SOURCE_HASSIO},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("hassio_confirm")
    expect(result["errors"]).to_be(None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "pyload", CONF_PASSWORD: "pyload"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_text})

    mock_pyloadapi.get_status.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "pyload", CONF_PASSWORD: "pyload"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("p539df76c_pyload-ng")
    expect(result["data"]).to_equal({**ADDON_DISCOVERY_INFO, CONF_VERIFY_SSL: False})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def hassio_discovery_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_pyloadapi: AsyncMock = Depends(mock_pyloadapi_fx),
) -> None:
    """Test we abort discovery flow if already configured."""
    MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_URL: "http://539df76c-pyload-ng:8000/",
            CONF_USERNAME: "pyload",
            CONF_PASSWORD: "pyload",
        },
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=ADDON_SERVICE_INFO,
        context={"source": SOURCE_HASSIO},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def hassio_discovery_data_update(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_pyloadapi: AsyncMock = Depends(mock_pyloadapi_fx),
) -> None:
    """Test we abort discovery flow if already configured and update entry from discovery data."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_URL: "http://localhost:8000/",
            CONF_USERNAME: "pyload",
            CONF_PASSWORD: "pyload",
        },
        unique_id="1234",
    )

    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=ADDON_SERVICE_INFO,
        context={"source": SOURCE_HASSIO},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(entry.data[CONF_URL]).to_equal("http://539df76c-pyload-ng:8000/")


@test
async def hassio_discovery_ignored(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_pyloadapi: AsyncMock = Depends(mock_pyloadapi_fx),
) -> None:
    """Test we abort discovery flow if discovery was ignored."""
    MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_IGNORE,
        data={},
        unique_id="1234",
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=ADDON_SERVICE_INFO,
        context={"source": SOURCE_HASSIO},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
