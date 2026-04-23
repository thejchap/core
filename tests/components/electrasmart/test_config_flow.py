"""Test the Electra Smart config flow."""

from json import loads
from unittest.mock import MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.electrasmart.config_flow import ElectraApiError
from homeassistant.components.electrasmart.const import (
    CONF_OTP,
    CONF_PHONE_NUMBER,
    DOMAIN,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import async_load_fixture
from tests.components.electrasmart._fixtures import mock_zeroconf
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def form(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test user config."""
    mock_generate_token = loads(
        await async_load_fixture(hass, "generate_token_response.json", DOMAIN)
    )
    with patch(
        "electrasmart.api.ElectraAPI.generate_new_token",
        return_value=mock_generate_token,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=None,
        )

        expect(result["step_id"]).to_equal("user")

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={CONF_PHONE_NUMBER: "0521234567"},
        )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal(CONF_OTP)


@test
async def one_time_password(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test one time password."""
    mock_generate_token = loads(
        await async_load_fixture(hass, "generate_token_response.json", DOMAIN)
    )
    mock_otp_response = loads(
        await async_load_fixture(hass, "otp_response.json", DOMAIN)
    )
    with (
        patch(
            "electrasmart.api.ElectraAPI.generate_new_token",
            return_value=mock_generate_token,
        ),
        patch(
            "electrasmart.api.ElectraAPI.validate_one_time_password",
            return_value=mock_otp_response,
        ),
        patch(
            "electrasmart.api.ElectraAPI.fetch_devices",
            return_value=[],
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={CONF_PHONE_NUMBER: "0521234567", CONF_OTP: "1234"},
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_OTP: "1234"}
        )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)


@test
async def one_time_password_api_error(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test one time password."""
    mock_generate_token = loads(
        await async_load_fixture(hass, "generate_token_response.json", DOMAIN)
    )
    with (
        patch(
            "electrasmart.api.ElectraAPI.generate_new_token",
            return_value=mock_generate_token,
        ),
        patch(
            "electrasmart.api.ElectraAPI.validate_one_time_password",
            side_effect=ElectraApiError,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={CONF_PHONE_NUMBER: "0521234567"},
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_OTP: "1234"}
        )

    expect(result["type"] is FlowResultType.FORM).to_be(True)


@test
async def cannot_connect(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test cannot connect."""
    with patch(
        "electrasmart.api.ElectraAPI.generate_new_token",
        side_effect=ElectraApiError,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={CONF_PHONE_NUMBER: "0521234567"},
        )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def invalid_phone_number(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test invalid phone number."""
    mock_invalid_phone_number_response = loads(
        await async_load_fixture(hass, "invalid_phone_number_response.json", DOMAIN)
    )

    with patch(
        "electrasmart.api.ElectraAPI.generate_new_token",
        return_value=mock_invalid_phone_number_response,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={CONF_PHONE_NUMBER: "0521234567"},
        )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"phone_number": "invalid_phone_number"})


@test
async def invalid_auth(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test invalid auth."""
    mock_generate_token_response = loads(
        await async_load_fixture(hass, "generate_token_response.json", DOMAIN)
    )
    mock_invalid_otp_response = loads(
        await async_load_fixture(hass, "invalid_otp_response.json", DOMAIN)
    )

    with (
        patch(
            "electrasmart.api.ElectraAPI.generate_new_token",
            return_value=mock_generate_token_response,
        ),
        patch(
            "electrasmart.api.ElectraAPI.validate_one_time_password",
            return_value=mock_invalid_otp_response,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={CONF_PHONE_NUMBER: "0521234567", CONF_OTP: "1234"},
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_OTP: "1234"}
        )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal(CONF_OTP)
    expect(result["errors"]).to_equal({CONF_OTP: "invalid_auth"})
