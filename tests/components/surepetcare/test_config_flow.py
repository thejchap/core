"""Test the Sure Petcare config flow."""

from unittest.mock import NonCallableMagicMock, patch

from surepy.exceptions import SurePetcareAuthenticationError, SurePetcareError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.surepetcare.const import DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_TOKEN, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import surepetcare as surepetcare_fx

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

INPUT_DATA = {
    "username": "test-username",
    "password": "test-password",
}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _surepetcare: NonCallableMagicMock = Depends(surepetcare_fx),
) -> None:
    """Test we get the form."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_be(False)

    with patch(
        "homeassistant.components.surepetcare.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Sure Petcare")
    expect(result2["data"]).to_equal(
        {
            "username": "test-username",
            "password": "test-password",
            "token": "token",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


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
        "homeassistant.components.surepetcare.config_flow.surepy.client.SureAPIClient.get_token",
        side_effect=SurePetcareAuthenticationError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.surepetcare.config_flow.surepy.client.SureAPIClient.get_token",
        side_effect=SurePetcareError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_unknown_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle unknown error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.surepetcare.config_flow.surepy.client.SureAPIClient.get_token",
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def flow_entry_already_exists(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _surepetcare: NonCallableMagicMock = Depends(surepetcare_fx),
) -> None:
    """Test user input for config_entry that already exists."""
    first_entry = MockConfigEntry(
        domain="surepetcare",
        data={
            "username": "test-username",
            "password": "test-password",
        },
        unique_id="test-username",
    )
    first_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.surepetcare.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={
                "username": "test-username",
                "password": "test-password",
            },
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reauthentication(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    surepetcare: NonCallableMagicMock = Depends(surepetcare_fx),
) -> None:
    """Test surepetcare reauthentication."""
    old_entry = MockConfigEntry(
        domain="surepetcare",
        data={
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
            CONF_TOKEN: "token",
        },
        unique_id="test-username",
    )
    old_entry.add_to_hass(hass)

    result = await old_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    expect(result["step_id"]).to_equal("reauth_confirm")

    surepetcare.get_token.return_value = "token2"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"password": "test-password2"},
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")

    expect(old_entry.data).to_equal(
        {
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password2",
            CONF_TOKEN: "token2",
        }
    )


@test
async def reauthentication_failure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test surepetcare reauthentication failure."""
    old_entry = MockConfigEntry(
        domain="surepetcare",
        data=INPUT_DATA,
        unique_id="USERID",
    )
    old_entry.add_to_hass(hass)

    result = await old_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    expect(result["step_id"]).to_equal("reauth_confirm")

    with patch(
        "homeassistant.components.surepetcare.config_flow.surepy.client.SureAPIClient.get_token",
        side_effect=SurePetcareAuthenticationError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"password": "test-password"},
        )
        await hass.async_block_till_done()

    expect(result2["step_id"]).to_equal("reauth_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]["base"]).to_equal("invalid_auth")


@test
async def reauthentication_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test surepetcare reauthentication failure."""
    old_entry = MockConfigEntry(
        domain="surepetcare",
        data=INPUT_DATA,
        unique_id="USERID",
    )
    old_entry.add_to_hass(hass)

    result = await old_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    expect(result["step_id"]).to_equal("reauth_confirm")

    with patch(
        "homeassistant.components.surepetcare.config_flow.surepy.client.SureAPIClient.get_token",
        side_effect=SurePetcareError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"password": "test-password"},
        )
        await hass.async_block_till_done()

    expect(result2["step_id"]).to_equal("reauth_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]["base"]).to_equal("cannot_connect")


@test
async def reauthentication_unknown_failure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test surepetcare reauthentication failure."""
    old_entry = MockConfigEntry(
        domain="surepetcare",
        data=INPUT_DATA,
        unique_id="USERID",
    )
    old_entry.add_to_hass(hass)

    result = await old_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    expect(result["step_id"]).to_equal("reauth_confirm")

    with patch(
        "homeassistant.components.surepetcare.config_flow.surepy.client.SureAPIClient.get_token",
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"password": "test-password"},
        )
        await hass.async_block_till_done()

    expect(result2["step_id"]).to_equal("reauth_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]["base"]).to_equal("unknown")
