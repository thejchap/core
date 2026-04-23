"""Test the Panasonic Viera config flow."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from panasonic_viera import SOAPError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.panasonic_viera.const import (
    ATTR_DEVICE_INFO,
    DEFAULT_NAME,
    DOMAIN,
    ERROR_INVALID_PIN_CODE,
)
from homeassistant.const import CONF_PIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .conftest import (
    MOCK_BASIC_DATA,
    MOCK_CONFIG_DATA,
    MOCK_DEVICE_INFO,
    MOCK_ENCRYPTION_DATA,
    get_mock_remote,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.panasonic_viera.async_setup_entry",
        return_value=True,
    ) as mock_setup:
        yield mock_setup


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Wire mock_network + mock_setup_entry for every test."""


@test
async def flow_non_encrypted(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test flow without encryption."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    mock_remote = get_mock_remote(encrypted=False)

    with patch(
        "homeassistant.components.panasonic_viera.config_flow.RemoteControl",
        return_value=mock_remote,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {**MOCK_BASIC_DATA},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DEFAULT_NAME)
    expect(result["data"]).to_equal({**MOCK_CONFIG_DATA, ATTR_DEVICE_INFO: MOCK_DEVICE_INFO})


@test
async def flow_not_connected_error(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test flow with connection error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with patch(
        "homeassistant.components.panasonic_viera.config_flow.RemoteControl",
        side_effect=TimeoutError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {**MOCK_BASIC_DATA},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def flow_unknown_abort(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test flow with unknown error abortion."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with patch(
        "homeassistant.components.panasonic_viera.config_flow.RemoteControl",
        side_effect=Exception,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {**MOCK_BASIC_DATA},
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unknown")


@test
async def flow_encrypted_not_connected_pin_code_request(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test pairing-request connection error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    mock_remote = get_mock_remote(encrypted=True, request_error=TimeoutError)

    with patch(
        "homeassistant.components.panasonic_viera.config_flow.RemoteControl",
        return_value=mock_remote,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {**MOCK_BASIC_DATA},
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def flow_encrypted_unknown_pin_code_request(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test pairing-request unknown error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    mock_remote = get_mock_remote(encrypted=True, request_error=Exception)

    with patch(
        "homeassistant.components.panasonic_viera.config_flow.RemoteControl",
        return_value=mock_remote,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {**MOCK_BASIC_DATA},
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unknown")


@test
async def flow_encrypted_valid_pin_code(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test flow with encryption and valid PIN."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    mock_remote = get_mock_remote(
        encrypted=True,
        app_id="mock-app-id",
        encryption_key="mock-encryption-key",
    )

    with patch(
        "homeassistant.components.panasonic_viera.config_flow.RemoteControl",
        return_value=mock_remote,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {**MOCK_BASIC_DATA},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("pairing")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PIN: "1234"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DEFAULT_NAME)
    expect(result["data"]).to_equal(
        {
            **MOCK_CONFIG_DATA,
            **MOCK_ENCRYPTION_DATA,
            ATTR_DEVICE_INFO: MOCK_DEVICE_INFO,
        }
    )


@test
async def flow_encrypted_invalid_pin_code_error(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test pairing invalid PIN error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    mock_remote = get_mock_remote(encrypted=True, authorize_error=SOAPError)

    with patch(
        "homeassistant.components.panasonic_viera.config_flow.RemoteControl",
        return_value=mock_remote,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {**MOCK_BASIC_DATA},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("pairing")

    with patch(
        "homeassistant.components.panasonic_viera.config_flow.RemoteControl",
        return_value=mock_remote,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PIN: "0000"},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("pairing")
    expect(result["errors"]).to_equal({"base": ERROR_INVALID_PIN_CODE})


@test
async def flow_encrypted_not_connected_abort(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test pairing step connection error abortion."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    mock_remote = get_mock_remote(encrypted=True, authorize_error=TimeoutError)

    with patch(
        "homeassistant.components.panasonic_viera.config_flow.RemoteControl",
        return_value=mock_remote,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {**MOCK_BASIC_DATA},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("pairing")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PIN: "0000"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def flow_encrypted_unknown_abort(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test pairing step unknown error abortion."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    mock_remote = get_mock_remote(encrypted=True, authorize_error=Exception)

    with patch(
        "homeassistant.components.panasonic_viera.config_flow.RemoteControl",
        return_value=mock_remote,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {**MOCK_BASIC_DATA},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("pairing")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PIN: "0000"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unknown")


@test
async def flow_non_encrypted_already_configured_abort(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test existing entry abortion."""
    MockConfigEntry(
        domain=DOMAIN,
        unique_id="0.0.0.0",
        data=MOCK_CONFIG_DATA,
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={**MOCK_BASIC_DATA},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def flow_encrypted_already_configured_abort(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test existing encrypted entry abortion."""
    MockConfigEntry(
        domain=DOMAIN,
        unique_id="0.0.0.0",
        data={**MOCK_CONFIG_DATA, **MOCK_ENCRYPTION_DATA},
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={**MOCK_BASIC_DATA},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def imported_flow_non_encrypted(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test imported flow without encryption."""
    mock_remote = get_mock_remote(encrypted=False)

    with patch(
        "homeassistant.components.panasonic_viera.config_flow.RemoteControl",
        return_value=mock_remote,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={**MOCK_CONFIG_DATA},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DEFAULT_NAME)
    expect(result["data"]).to_equal({**MOCK_CONFIG_DATA, ATTR_DEVICE_INFO: MOCK_DEVICE_INFO})


@test
async def imported_flow_encrypted_valid_pin_code(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test imported flow with valid PIN."""
    mock_remote = get_mock_remote(
        encrypted=True,
        app_id="mock-app-id",
        encryption_key="mock-encryption-key",
    )

    with patch(
        "homeassistant.components.panasonic_viera.config_flow.RemoteControl",
        return_value=mock_remote,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={**MOCK_CONFIG_DATA},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("pairing")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PIN: "1234"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DEFAULT_NAME)
    expect(result["data"]).to_equal(
        {
            **MOCK_CONFIG_DATA,
            **MOCK_ENCRYPTION_DATA,
            ATTR_DEVICE_INFO: MOCK_DEVICE_INFO,
        }
    )


@test
async def imported_flow_encrypted_invalid_pin_code_error(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test imported flow with invalid PIN."""
    mock_remote = get_mock_remote(encrypted=True, authorize_error=SOAPError)

    with patch(
        "homeassistant.components.panasonic_viera.config_flow.RemoteControl",
        return_value=mock_remote,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={**MOCK_CONFIG_DATA},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("pairing")

    with patch(
        "homeassistant.components.panasonic_viera.config_flow.RemoteControl",
        return_value=mock_remote,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PIN: "0000"},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("pairing")
    expect(result["errors"]).to_equal({"base": ERROR_INVALID_PIN_CODE})


@test
async def imported_flow_encrypted_not_connected_abort(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test imported flow pairing connection error."""
    mock_remote = get_mock_remote(encrypted=True, authorize_error=TimeoutError)

    with patch(
        "homeassistant.components.panasonic_viera.config_flow.RemoteControl",
        return_value=mock_remote,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={**MOCK_CONFIG_DATA},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("pairing")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PIN: "0000"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def imported_flow_encrypted_unknown_abort(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test imported flow pairing unknown error."""
    mock_remote = get_mock_remote(encrypted=True, authorize_error=Exception)

    with patch(
        "homeassistant.components.panasonic_viera.config_flow.RemoteControl",
        return_value=mock_remote,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={**MOCK_CONFIG_DATA},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("pairing")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PIN: "0000"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unknown")


@test
async def imported_flow_not_connected_error(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test imported flow with connection error."""
    with patch(
        "homeassistant.components.panasonic_viera.config_flow.RemoteControl",
        side_effect=TimeoutError,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={**MOCK_CONFIG_DATA},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def imported_flow_unknown_abort(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test imported flow unknown error abortion."""
    with patch(
        "homeassistant.components.panasonic_viera.config_flow.RemoteControl",
        side_effect=Exception,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={**MOCK_CONFIG_DATA},
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unknown")


@test
async def imported_flow_non_encrypted_already_configured_abort(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test imported flow existing entry abortion."""
    MockConfigEntry(
        domain=DOMAIN,
        unique_id="0.0.0.0",
        data=MOCK_CONFIG_DATA,
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data={**MOCK_BASIC_DATA},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def imported_flow_encrypted_already_configured_abort(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test imported flow existing encrypted entry abortion."""
    MockConfigEntry(
        domain=DOMAIN,
        unique_id="0.0.0.0",
        data={**MOCK_CONFIG_DATA, **MOCK_ENCRYPTION_DATA},
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data={**MOCK_BASIC_DATA},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
