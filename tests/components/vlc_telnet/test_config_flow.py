"""Test the VLC media player Telnet config flow."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from aiovlc.exceptions import AuthError, ConnectError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.vlc_telnet.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.hassio import HassioServiceInfo

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.cases(
    test.case(
        "with_full_input",
        input_data={
            "password": "test-password",
            "host": "1.1.1.1",
            "port": 8888,
        },
        entry_data={
            "password": "test-password",
            "host": "1.1.1.1",
            "port": 8888,
        },
    ),
    test.case(
        "with_password_only",
        input_data={"password": "test-password"},
        entry_data={
            "password": "test-password",
            "host": "localhost",
            "port": 4212,
        },
    ),
)
async def user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    input_data: dict[str, Any],
    entry_data: dict[str, Any],
) -> None:
    """Test successful user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with (
        patch("homeassistant.components.vlc_telnet.config_flow.Client.connect"),
        patch("homeassistant.components.vlc_telnet.config_flow.Client.login"),
        patch("homeassistant.components.vlc_telnet.config_flow.Client.disconnect"),
        patch(
            "homeassistant.components.vlc_telnet.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            input_data,
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(entry_data["host"])
    expect(dict(result["data"])).to_equal(entry_data)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def abort_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle already configured host."""
    entry_data = {
        "password": "test-password",
        "host": "1.1.1.1",
        "port": 8888,
        "name": "custom name",
    }

    entry = MockConfigEntry(domain=DOMAIN, data=entry_data)
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=entry_data,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case(
        "invalid_auth",
        error="invalid_auth",
        connect_side_effect=None,
        login_side_effect=AuthError,
    ),
    test.case(
        "cannot_connect",
        error="cannot_connect",
        connect_side_effect=ConnectError,
        login_side_effect=None,
    ),
    test.case(
        "unknown",
        error="unknown",
        connect_side_effect=Exception,
        login_side_effect=None,
    ),
)
async def errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    error: str,
    connect_side_effect: Exception | None,
    login_side_effect: Exception | None,
) -> None:
    """Test we handle form errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with (
        patch(
            "homeassistant.components.vlc_telnet.config_flow.Client.connect",
            side_effect=connect_side_effect,
        ),
        patch(
            "homeassistant.components.vlc_telnet.config_flow.Client.login",
            side_effect=login_side_effect,
        ),
        patch(
            "homeassistant.components.vlc_telnet.config_flow.Client.disconnect",
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"password": "test-password"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": error})


@test
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test successful reauth flow."""
    entry_data: dict[str, Any] = {
        "password": "old-password",
        "host": "1.1.1.1",
        "port": 8888,
        "name": "custom name",
    }

    entry = MockConfigEntry(domain=DOMAIN, data=entry_data)
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)

    with (
        patch("homeassistant.components.vlc_telnet.config_flow.Client.connect"),
        patch("homeassistant.components.vlc_telnet.config_flow.Client.login"),
        patch("homeassistant.components.vlc_telnet.config_flow.Client.disconnect"),
        patch(
            "homeassistant.components.vlc_telnet.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"password": "new-password"},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(dict(entry.data)).to_equal({**entry_data, "password": "new-password"})


@test.cases(
    test.case(
        "invalid_auth",
        error="invalid_auth",
        connect_side_effect=None,
        login_side_effect=AuthError,
    ),
    test.case(
        "cannot_connect",
        error="cannot_connect",
        connect_side_effect=ConnectError,
        login_side_effect=None,
    ),
    test.case(
        "unknown",
        error="unknown",
        connect_side_effect=Exception,
        login_side_effect=None,
    ),
)
async def reauth_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    error: str,
    connect_side_effect: Exception | None,
    login_side_effect: Exception | None,
) -> None:
    """Test we handle reauth errors."""
    entry_data = {
        "password": "old-password",
        "host": "1.1.1.1",
        "port": 8888,
        "name": "custom name",
    }

    entry = MockConfigEntry(domain=DOMAIN, data=entry_data)
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)

    with (
        patch(
            "homeassistant.components.vlc_telnet.config_flow.Client.connect",
            side_effect=connect_side_effect,
        ),
        patch(
            "homeassistant.components.vlc_telnet.config_flow.Client.login",
            side_effect=login_side_effect,
        ),
        patch(
            "homeassistant.components.vlc_telnet.config_flow.Client.disconnect",
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"password": "test-password"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": error})


@test
async def hassio_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test successful hassio flow."""
    with (
        patch("homeassistant.components.vlc_telnet.config_flow.Client.connect"),
        patch("homeassistant.components.vlc_telnet.config_flow.Client.login"),
        patch("homeassistant.components.vlc_telnet.config_flow.Client.disconnect"),
        patch(
            "homeassistant.components.vlc_telnet.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        test_data = HassioServiceInfo(
            config={
                "password": "test-password",
                "host": "1.1.1.1",
                "port": 8888,
                "name": "custom name",
                "addon": "VLC",
            },
            name="VLC",
            slug="vlc",
            uuid="1234",
        )

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_HASSIO},
            data=test_data,
        )
        await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.FORM)

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {}
        )

        expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result2["title"]).to_equal(test_data.config["name"])
        expect(dict(result2["data"])).to_equal(test_data.config)
        expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def hassio_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test successful hassio flow."""
    entry_data = {
        "password": "test-password",
        "host": "1.1.1.1",
        "port": 8888,
        "name": "custom name",
        "addon": "vlc",
    }

    entry = MockConfigEntry(domain=DOMAIN, data=entry_data, unique_id="hassio")
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_HASSIO},
        data=HassioServiceInfo(config=entry_data, name="VLC", slug="vlc", uuid="1234"),
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)


@test.cases(
    test.case(
        "invalid_auth",
        error="invalid_auth",
        connect_side_effect=None,
        login_side_effect=AuthError,
    ),
    test.case(
        "cannot_connect",
        error="cannot_connect",
        connect_side_effect=ConnectError,
        login_side_effect=None,
    ),
    test.case(
        "unknown",
        error="unknown",
        connect_side_effect=Exception,
        login_side_effect=None,
    ),
)
async def hassio_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    error: str,
    connect_side_effect: Exception | None,
    login_side_effect: Exception | None,
) -> None:
    """Test we handle hassio errors."""
    with (
        patch(
            "homeassistant.components.vlc_telnet.config_flow.Client.connect",
            side_effect=connect_side_effect,
        ),
        patch(
            "homeassistant.components.vlc_telnet.config_flow.Client.login",
            side_effect=login_side_effect,
        ),
        patch(
            "homeassistant.components.vlc_telnet.config_flow.Client.disconnect",
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_HASSIO},
            data=HassioServiceInfo(
                config={
                    "password": "test-password",
                    "host": "1.1.1.1",
                    "port": 8888,
                    "name": "custom name",
                    "addon": "VLC",
                },
                name="VLC",
                slug="vlc",
                uuid="1234",
            ),
        )
        await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.FORM)

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {}
        )

        expect(result2["type"]).to_be(FlowResultType.ABORT)
        expect(result2["reason"]).to_equal(error)
