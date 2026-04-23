"""Test the Picnic config flow."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from python_picnic_api2.session import (
    Picnic2FAError,
    Picnic2FARequired,
    PicnicAuthError,
)
import requests
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.picnic.const import DOMAIN
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_COUNTRY_CODE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

from ._fixtures import picnic_api as picnic_api_fx


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _api: MagicMock = Depends(picnic_api_fx),
) -> None:
    """Wire mock_network and picnic_api for every test."""


@test
async def form(
    hass: HomeAssistant = Depends(hass_fixture),
    picnic_api: MagicMock = Depends(picnic_api_fx),
) -> None:
    """Test we get the form and a config entry is created."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_be(None)

    with patch(
        "homeassistant.components.picnic.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
                "country_code": "NL",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Picnic")
    expect(result2["data"]).to_equal(
        {
            CONF_ACCESS_TOKEN: picnic_api().session.auth_token,
            CONF_COUNTRY_CODE: "NL",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_2fa_required(
    hass: HomeAssistant = Depends(hass_fixture),
    picnic_api: MagicMock = Depends(picnic_api_fx),
) -> None:
    """Test the full 2FA flow."""
    picnic_api.return_value.login.side_effect = Picnic2FARequired

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.picnic.async_setup_entry",
        return_value=True,
    ):
        result_step_user = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
                "country_code": "NL",
            },
        )
        expect(result_step_user["type"]).to_be(FlowResultType.FORM)
        expect(result_step_user["step_id"]).to_equal("2fa_channel")

        result_step_2fa_channel = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"two_fa_channel": "sms"},
        )
        expect(result_step_2fa_channel["type"]).to_be(FlowResultType.FORM)
        expect(result_step_2fa_channel["step_id"]).to_equal("2fa")

        result_step_2fa_verify = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"two_fa_code": "123456"},
        )
        await hass.async_block_till_done()

    expect(result_step_2fa_verify["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result_step_2fa_verify["title"]).to_equal("Picnic")
    expect(result_step_2fa_verify["data"]).to_equal(
        {
            CONF_ACCESS_TOKEN: picnic_api().session.auth_token,
            CONF_COUNTRY_CODE: "NL",
        }
    )
    expect(picnic_api.return_value.generate_2fa_code.call_count).to_equal(1)
    expect(picnic_api.return_value.generate_2fa_code.call_args[0]).to_equal(("SMS",))
    expect(picnic_api.return_value.verify_2fa_code.call_count).to_equal(1)
    expect(picnic_api.return_value.verify_2fa_code.call_args[0]).to_equal(("123456",))


@test
async def form_2fa_channel_cannot_connect(
    hass: HomeAssistant = Depends(hass_fixture),
    picnic_api: MagicMock = Depends(picnic_api_fx),
) -> None:
    """Test we handle connection errors in the first 2fa step."""
    picnic_api.return_value.login.side_effect = Picnic2FARequired
    picnic_api.return_value.generate_2fa_code.side_effect = (
        requests.exceptions.ConnectionError
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.picnic.async_setup_entry",
        return_value=True,
    ):
        result_step_user = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
                "country_code": "NL",
            },
        )
        expect(result_step_user["type"]).to_be(FlowResultType.FORM)
        expect(result_step_user["step_id"]).to_equal("2fa_channel")

        result_step_2fa_channel = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"two_fa_channel": "sms"},
        )
        await hass.async_block_till_done()

    expect(result_step_2fa_channel["type"]).to_be(FlowResultType.FORM)
    expect(result_step_2fa_channel["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_2fa_channel_exception(
    hass: HomeAssistant = Depends(hass_fixture),
    picnic_api: MagicMock = Depends(picnic_api_fx),
) -> None:
    """Test we handle random exceptions in the first 2fa step."""
    picnic_api.return_value.login.side_effect = Picnic2FARequired
    picnic_api.return_value.generate_2fa_code.side_effect = Exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.picnic.async_setup_entry",
        return_value=True,
    ):
        result_step_user = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
                "country_code": "NL",
            },
        )
        expect(result_step_user["type"]).to_be(FlowResultType.FORM)
        expect(result_step_user["step_id"]).to_equal("2fa_channel")

        result_step_2fa_channel = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"two_fa_channel": "sms"},
        )
        await hass.async_block_till_done()

    expect(result_step_2fa_channel["type"]).to_be(FlowResultType.FORM)
    expect(result_step_2fa_channel["errors"]).to_equal({"base": "unknown"})


@test
async def form_2fa_wrong_code(
    hass: HomeAssistant = Depends(hass_fixture),
    picnic_api: MagicMock = Depends(picnic_api_fx),
) -> None:
    """Test the full 2FA flow with incorrect code."""
    picnic_api.return_value.login.side_effect = Picnic2FARequired
    picnic_api.return_value.verify_2fa_code.side_effect = Picnic2FAError

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.picnic.async_setup_entry",
        return_value=True,
    ):
        result_step_user = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
                "country_code": "NL",
            },
        )
        expect(result_step_user["type"]).to_be(FlowResultType.FORM)
        expect(result_step_user["step_id"]).to_equal("2fa_channel")

        result_step_2fa_channel = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"two_fa_channel": "sms"},
        )
        expect(result_step_2fa_channel["type"]).to_be(FlowResultType.FORM)
        expect(result_step_2fa_channel["step_id"]).to_equal("2fa")

        result_step_2fa_verify = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"two_fa_code": "654321"},
        )
        await hass.async_block_till_done()

    expect(result_step_2fa_verify["type"]).to_be(FlowResultType.FORM)
    expect(result_step_2fa_verify["errors"]).to_equal({"base": "invalid_2fa_code"})


@test
async def form_2fa_cannot_connect(
    hass: HomeAssistant = Depends(hass_fixture),
    picnic_api: MagicMock = Depends(picnic_api_fx),
) -> None:
    """Test we handle connection errors in the last 2fa step."""
    picnic_api.return_value.login.side_effect = Picnic2FARequired
    picnic_api.return_value.verify_2fa_code.side_effect = (
        requests.exceptions.ConnectionError
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.picnic.async_setup_entry",
        return_value=True,
    ):
        result_step_user = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
                "country_code": "NL",
            },
        )
        expect(result_step_user["type"]).to_be(FlowResultType.FORM)
        expect(result_step_user["step_id"]).to_equal("2fa_channel")

        result_step_2fa_channel = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"two_fa_channel": "sms"},
        )
        expect(result_step_2fa_channel["type"]).to_be(FlowResultType.FORM)
        expect(result_step_2fa_channel["step_id"]).to_equal("2fa")

        result_step_2fa_verify = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"two_fa_code": "123456"},
        )
        await hass.async_block_till_done()

    expect(result_step_2fa_verify["type"]).to_be(FlowResultType.FORM)
    expect(result_step_2fa_verify["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_2fa_exception(
    hass: HomeAssistant = Depends(hass_fixture),
    picnic_api: MagicMock = Depends(picnic_api_fx),
) -> None:
    """Test we handle random exceptions in the last 2fa step."""
    picnic_api.return_value.login.side_effect = Picnic2FARequired
    picnic_api.return_value.verify_2fa_code.side_effect = Exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.picnic.async_setup_entry",
        return_value=True,
    ):
        result_step_user = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
                "country_code": "NL",
            },
        )
        expect(result_step_user["type"]).to_be(FlowResultType.FORM)
        expect(result_step_user["step_id"]).to_equal("2fa_channel")

        result_step_2fa_channel = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"two_fa_channel": "sms"},
        )
        expect(result_step_2fa_channel["type"]).to_be(FlowResultType.FORM)
        expect(result_step_2fa_channel["step_id"]).to_equal("2fa")

        result_step_2fa_verify = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"two_fa_code": "123456"},
        )
        await hass.async_block_till_done()

    expect(result_step_2fa_verify["type"]).to_be(FlowResultType.FORM)
    expect(result_step_2fa_verify["errors"]).to_equal({"base": "unknown"})


@test
async def form_invalid_auth(
    hass: HomeAssistant = Depends(hass_fixture),
    picnic_api: MagicMock = Depends(picnic_api_fx),
) -> None:
    """Test we handle invalid authentication."""
    picnic_api.return_value.login.side_effect = PicnicAuthError

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "username": "test-username",
            "password": "test-password",
            "country_code": "NL",
        },
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def form_cannot_connect(
    hass: HomeAssistant = Depends(hass_fixture),
    picnic_api: MagicMock = Depends(picnic_api_fx),
) -> None:
    """Test we handle connection errors."""
    picnic_api.return_value.login.side_effect = requests.exceptions.ConnectionError

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "username": "test-username",
            "password": "test-password",
            "country_code": "NL",
        },
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_exception(
    hass: HomeAssistant = Depends(hass_fixture),
    picnic_api: MagicMock = Depends(picnic_api_fx),
) -> None:
    """Test we handle random exceptions."""
    picnic_api.return_value.login.side_effect = Exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "username": "test-username",
            "password": "test-password",
            "country_code": "NL",
        },
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def form_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    picnic_api: MagicMock = Depends(picnic_api_fx),
) -> None:
    """Test that an entry with unique id can only be added once."""
    MockConfigEntry(
        domain=DOMAIN,
        unique_id=picnic_api().get_user()["user_id"],
        data={CONF_ACCESS_TOKEN: "a3p98fsen.a39p3fap", CONF_COUNTRY_CODE: "NL"},
    ).add_to_hass(hass)

    result_init = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result_configure = await hass.config_entries.flow.async_configure(
        result_init["flow_id"],
        {
            "username": "test-username",
            "password": "test-password",
            "country_code": "NL",
        },
    )
    await hass.async_block_till_done()

    expect(result_configure["type"]).to_be(FlowResultType.ABORT)
    expect(result_configure["reason"]).to_equal("already_configured")


@test
async def step_reauth(
    hass: HomeAssistant = Depends(hass_fixture),
    picnic_api: MagicMock = Depends(picnic_api_fx),
) -> None:
    """Test the re-auth flow."""
    conf = {CONF_ACCESS_TOKEN: "a3p98fsen.a39p3fap", CONF_COUNTRY_CODE: "NL"}

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=picnic_api().get_user()["user_id"],
        data=conf,
    )
    entry.add_to_hass(hass)

    result_init = await entry.start_reauth_flow(hass)
    expect(result_init["type"]).to_be(FlowResultType.FORM)
    expect(result_init["step_id"]).to_equal("user")

    with patch(
        "homeassistant.components.picnic.async_setup_entry",
        return_value=True,
    ):
        result_configure = await hass.config_entries.flow.async_configure(
            result_init["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
                "country_code": "NL",
            },
        )
        await hass.async_block_till_done()

    expect(result_configure["type"]).to_be(FlowResultType.ABORT)
    expect(result_configure["reason"]).to_equal("reauth_successful")

    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test
async def step_reauth_failed(
    hass: HomeAssistant = Depends(hass_fixture),
    picnic_api: MagicMock = Depends(picnic_api_fx),
) -> None:
    """Test the re-auth flow when authentication fails."""
    picnic_api.return_value.login.side_effect = PicnicAuthError

    user_id = "f29-2a6-o32n"
    conf = {CONF_ACCESS_TOKEN: "a3p98fsen.a39p3fap", CONF_COUNTRY_CODE: "NL"}

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=user_id,
        data=conf,
    )
    entry.add_to_hass(hass)

    result_init = await entry.start_reauth_flow(hass)
    expect(result_init["type"]).to_be(FlowResultType.FORM)
    expect(result_init["step_id"]).to_equal("user")

    result_configure = await hass.config_entries.flow.async_configure(
        result_init["flow_id"],
        {
            "username": "test-username",
            "password": "test-password",
            "country_code": "NL",
        },
    )
    await hass.async_block_till_done()

    expect(result_configure["type"]).to_be(FlowResultType.FORM)
    expect(result_configure["errors"]).to_equal({"base": "invalid_auth"})

    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test
async def step_reauth_different_account(
    hass: HomeAssistant = Depends(hass_fixture),
    picnic_api: MagicMock = Depends(picnic_api_fx),
) -> None:
    """Test the re-auth flow when authentication is done with a different account."""
    conf = {CONF_ACCESS_TOKEN: "a3p98fsen.a39p3fap", CONF_COUNTRY_CODE: "NL"}

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="3fpawh-ues-af3ho",
        data=conf,
    )
    entry.add_to_hass(hass)

    result_init = await entry.start_reauth_flow(hass)
    expect(result_init["type"]).to_be(FlowResultType.FORM)
    expect(result_init["step_id"]).to_equal("user")

    with patch(
        "homeassistant.components.picnic.async_setup_entry",
        return_value=True,
    ):
        result_configure = await hass.config_entries.flow.async_configure(
            result_init["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
                "country_code": "NL",
            },
        )
        await hass.async_block_till_done()

    expect(result_configure["type"]).to_be(FlowResultType.FORM)
    expect(result_configure["errors"]).to_equal({"base": "different_account"})

    expect(len(hass.config_entries.async_entries())).to_equal(1)
