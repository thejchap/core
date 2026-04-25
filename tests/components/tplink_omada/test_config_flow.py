"""Test the TP-Link Omada config flows."""

from unittest.mock import MagicMock, patch

from tplink_omada_client import OmadaSite
from tplink_omada_client.exceptions import (
    ConnectionFailed,
    LoginFailed,
    OmadaClientException,
    UnsupportedControllerVersion,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.tplink_omada.config_flow import create_omada_client
from homeassistant.components.tplink_omada.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_config_entry, mock_omada_client, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

MOCK_USER_DATA = {
    "host": "https://fake.omada.host",
    "verify_ssl": True,
    "username": "test-username",
    "password": "test-password",
}

MOCK_ENTRY_DATA = {
    "host": "https://fake.omada.host",
    "verify_ssl": True,
    "site": "SiteId",
    "username": "test-username",
    "password": "test-password",
}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form_single_site(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _omada: MagicMock = Depends(mock_omada_client),
    setup_entry: MagicMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_USER_DATA,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("OC200 (Display Name)")
    expect(result["data"]).to_equal(MOCK_ENTRY_DATA)
    expect(result["result"].unique_id).to_equal("12345")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def form_multiple_sites(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    omada: MagicMock = Depends(mock_omada_client),
    setup_entry: MagicMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    omada.get_sites.return_value = [
        OmadaSite("Site 1", "first"),
        OmadaSite("Site 2", "second"),
    ]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_USER_DATA,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("site")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "site": "second",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("OC200 (Site 2)")
    expect(result["data"]).to_equal(
        {
            "host": "https://fake.omada.host",
            "verify_ssl": True,
            "site": "second",
            "username": "test-username",
            "password": "test-password",
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "invalid_auth",
        side_effect=LoginFailed(-1000, "Invalid username/password"),
        expected_error="invalid_auth",
    ),
    test.case(
        "unknown_omada", side_effect=OmadaClientException(), expected_error="unknown"
    ),
    test.case(
        "unknown_generic",
        side_effect=Exception("Generic error"),
        expected_error="unknown",
    ),
    test.case(
        "unsupported_controller",
        side_effect=UnsupportedControllerVersion("4.0.0"),
        expected_error="unsupported_controller",
    ),
    test.case(
        "cannot_connect",
        side_effect=ConnectionFailed(),
        expected_error="cannot_connect",
    ),
)
async def form_errors_and_recovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    omada: MagicMock = Depends(mock_omada_client),
    setup_entry: MagicMock = Depends(mock_setup_entry),
    *,
    side_effect: Exception,
    expected_error: str,
) -> None:
    """Test we handle various errors and can recover to complete the flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    # First attempt: trigger the error
    omada.login.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_USER_DATA,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": expected_error})

    # Second attempt: clear error and complete successfully
    omada.login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_USER_DATA,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("OC200 (Display Name)")
    expect(result["data"]).to_equal(MOCK_ENTRY_DATA)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def form_no_sites(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    omada: MagicMock = Depends(mock_omada_client),
) -> None:
    """Test we handle the case when no sites are found."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    omada.get_sites.return_value = []

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_USER_DATA,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "no_sites_found"})

    omada.get_sites.return_value = [OmadaSite("Display Name", "SiteId")]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_USER_DATA,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test.cases(
    test.case("matching", controller_id="12345", expected_reason="reauth_successful"),
    test.case(
        "mismatching",
        controller_id="different_controller_id",
        expected_reason="device_mismatch",
    ),
)
async def async_step_reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    omada: MagicMock = Depends(mock_omada_client),
    *,
    controller_id: str,
    expected_reason: str,
) -> None:
    """Test reauth flow with matching and mismatching controller IDs."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    omada.login.return_value = controller_id

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "new_uname", CONF_PASSWORD: "new_passwd"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(expected_reason)


@test.cases(
    test.case(
        "invalid_auth",
        side_effect=LoginFailed(-1000, "Invalid username/password"),
        expected_error="invalid_auth",
    ),
    test.case(
        "unknown_omada", side_effect=OmadaClientException(), expected_error="unknown"
    ),
    test.case(
        "unknown_generic",
        side_effect=Exception("Generic error"),
        expected_error="unknown",
    ),
    test.case(
        "unsupported_controller",
        side_effect=UnsupportedControllerVersion("4.0.0"),
        expected_error="unsupported_controller",
    ),
    test.case(
        "cannot_connect",
        side_effect=ConnectionFailed(),
        expected_error="cannot_connect",
    ),
)
async def async_step_reauth_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    omada: MagicMock = Depends(mock_omada_client),
    *,
    side_effect: Exception,
    expected_error: str,
) -> None:
    """Test reauth handles various exceptions."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    omada.login.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "new_uname", CONF_PASSWORD: "new_passwd"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({"base": expected_error})

    omada.login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "new_uname", CONF_PASSWORD: "new_passwd"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test
async def create_omada_client_parses_args(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config arguments are passed to Omada client."""
    with (
        patch(
            "homeassistant.components.tplink_omada.config_flow.OmadaClient",
            autospec=True,
        ) as mock_client,
        patch(
            "homeassistant.components.tplink_omada.config_flow.async_get_clientsession",
            return_value="ws",
        ) as mock_clientsession,
    ):
        result = await create_omada_client(hass, MOCK_USER_DATA)

    expect(result is not None).to_be(True)
    mock_client.assert_called_once_with(
        "https://fake.omada.host", "test-username", "test-password", "ws"
    )
    mock_clientsession.assert_called_once_with(hass, verify_ssl=True)


@test
async def create_omada_client_adds_missing_scheme(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config arguments are passed to Omada client."""
    with (
        patch(
            "homeassistant.components.tplink_omada.config_flow.OmadaClient",
            autospec=True,
        ) as mock_client,
        patch(
            "homeassistant.components.tplink_omada.config_flow.async_get_clientsession",
            return_value="ws",
        ) as mock_clientsession,
    ):
        result = await create_omada_client(
            hass,
            {
                "host": "fake.omada.host",
                "verify_ssl": True,
                "username": "test-username",
                "password": "test-password",
            },
        )

    expect(result is not None).to_be(True)
    mock_client.assert_called_once_with(
        "https://fake.omada.host", "test-username", "test-password", "ws"
    )
    mock_clientsession.assert_called_once_with(hass, verify_ssl=True)


@test
async def create_omada_client_with_ip_creates_clientsession(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config arguments are passed to Omada client."""
    with (
        patch(
            "homeassistant.components.tplink_omada.config_flow.OmadaClient",
            autospec=True,
        ) as mock_client,
        patch(
            "homeassistant.components.tplink_omada.config_flow.CookieJar", autospec=True
        ) as mock_jar,
        patch(
            "homeassistant.components.tplink_omada.config_flow.async_create_clientsession",
            return_value="ws",
        ) as mock_create_clientsession,
    ):
        result = await create_omada_client(
            hass,
            {
                "host": "10.10.10.10",
                "verify_ssl": True,
                "username": "test-username",
                "password": "test-password",
            },
        )

    expect(result is not None).to_be(True)
    mock_client.assert_called_once_with(
        "https://10.10.10.10", "test-username", "test-password", "ws"
    )
    mock_create_clientsession.assert_called_once_with(
        hass, cookie_jar=mock_jar.return_value, verify_ssl=True
    )
