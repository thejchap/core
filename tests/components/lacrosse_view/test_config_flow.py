"""Test the LaCrosse View config flow."""

from unittest.mock import AsyncMock, patch

from lacrosse_view import Location, LoginError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.lacrosse_view.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _mn: None = Depends(mock_network),
    _mse: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Trigger the hook executor path."""
    return None


@test
async def form(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with (
        patch("lacrosse_view.LaCrosse.login", return_value=True),
        patch(
            "lacrosse_view.LaCrosse.get_locations",
            return_value=[Location(id="1", name="Test")],
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("location")
    expect(result2["errors"]).to_be(None)

    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        {"location": "1"},
    )
    await hass.async_block_till_done()

    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3["title"]).to_equal("Test")
    expect(result3["data"]).to_equal(
        {
            "username": "test-username",
            "password": "test-password",
            "id": "1",
            "name": "Test",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_auth_false(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle invalid auth (login returns False)."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch("lacrosse_view.LaCrosse.login", return_value=False):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "test-username", "password": "test-password"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def form_invalid_auth(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle invalid auth (login raises LoginError)."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch("lacrosse_view.LaCrosse.login", side_effect=LoginError):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "test-username", "password": "test-password"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def form_login_first(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle invalid auth at get_locations."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with (
        patch("lacrosse_view.LaCrosse.login", return_value=True),
        patch("lacrosse_view.LaCrosse.get_locations", side_effect=LoginError),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "test-username", "password": "test-password"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def form_no_locations(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle no locations."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with (
        patch("lacrosse_view.LaCrosse.login", return_value=True),
        patch("lacrosse_view.LaCrosse.get_locations", return_value=None),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "test-username", "password": "test-password"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "no_locations"})


@test
async def form_unexpected_error(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle unexpected errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.lacrosse_view.config_flow.validate_input",
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "test-username", "password": "test-password"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def already_configured_device(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test abort for already configured device."""
    mock_config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "username": "test-username",
            "password": "test-password",
            "id": "1",
            "name": "Test",
        },
        unique_id="1",
    )
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with (
        patch("lacrosse_view.LaCrosse.login", return_value=True),
        patch(
            "lacrosse_view.LaCrosse.get_locations",
            return_value=[Location(id="1", name="Test")],
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "test-username", "password": "test-password"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("location")

    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        {"location": "1"},
    )
    await hass.async_block_till_done()

    expect(result3["type"]).to_be(FlowResultType.ABORT)
    expect(result3["reason"]).to_equal("already_configured")
    expect(len(mock_setup_entry.mock_calls)).to_equal(0)


@test
async def reauth(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test reauthentication."""
    data = {
        "username": "test-username",
        "password": "test-password",
        "id": "1",
        "name": "Test",
    }
    mock_config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=data,
        unique_id="1",
        title="Test",
    )
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    new_username = "new-username"
    new_password = "new-password"

    with (
        patch("lacrosse_view.LaCrosse.login", return_value=True),
        patch(
            "lacrosse_view.LaCrosse.get_locations",
            return_value=[Location(id="1", name="Test")],
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": new_username, "password": new_password},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")

    expect(len(hass.config_entries.async_entries())).to_equal(1)
    expect(hass.config_entries.async_entries()[0].data).to_equal(
        {
            "username": new_username,
            "password": new_password,
            "id": "1",
            "name": "Test",
        }
    )
