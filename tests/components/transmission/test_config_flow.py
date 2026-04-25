"""Tests for Transmission config flow."""

from unittest.mock import AsyncMock, patch

from transmission_rpc.error import (
    TransmissionAuthError,
    TransmissionConnectError,
    TransmissionError,
)
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components import transmission
from homeassistant.components.transmission.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import MOCK_CONFIG_DATA, setup_integration
from ._fixtures import (
    mock_config_entry,
    mock_setup_entry,
    mock_transmission_client,
    patch_sleep,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _patch_sleep: None = Depends(patch_sleep),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_transmission_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_CONFIG_DATA,
    )

    expect(len(setup_entry.mock_calls)).to_equal(1)
    expect(result["title"]).to_equal("Transmission")
    expect(result["data"]).to_equal(MOCK_CONFIG_DATA)
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def device_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test aborting if the device is already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_CONFIG_DATA,
    )
    await hass.async_block_till_done()

    expect(result["reason"]).to_equal("already_configured")
    expect(result["type"]).to_be(FlowResultType.ABORT)


@test
async def options(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test updating options."""
    entry = MockConfigEntry(
        domain=transmission.DOMAIN,
        data=MOCK_CONFIG_DATA,
        options={"limit": 10, "order": "oldest_first"},
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.transmission.async_setup_entry",
        return_value=True,
    ):
        expect(bool(await hass.config_entries.async_setup(entry.entry_id))).to_be(True)
        await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"limit": 20}
    )

    expect(result["data"]["limit"]).to_equal(20)
    expect(result["data"]["order"]).to_equal("oldest_first")
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def error_on_wrong_credentials(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_transmission_client),
) -> None:
    """Test we handle invalid credentials."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    client.side_effect = TransmissionAuthError()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_CONFIG_DATA,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal(
        {
            "username": "invalid_auth",
            "password": "invalid_auth",
        }
    )

    client.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_CONFIG_DATA,
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test.cases(
    test.case(
        "transmission_error", exception=TransmissionError, error="cannot_connect"
    ),
    test.case(
        "connect_error", exception=TransmissionConnectError, error="cannot_connect"
    ),
)
async def flow_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_transmission_client),
    *,
    exception: type[Exception],
    error: str,
) -> None:
    """Test flow errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    client.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_CONFIG_DATA,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    client.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_CONFIG_DATA,
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def reauth_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_transmission_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we can reauth."""
    await setup_integration(hass, config_entry)

    result = await config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["description_placeholders"]).to_equal(
        {
            "username": "user",
            "name": "Transmission",
        }
    )

    with patch(
        "homeassistant.components.transmission.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "password": "test-password",
            },
        )

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(result["type"]).to_be(FlowResultType.ABORT)


@test.cases(
    test.case(
        "transmission_error",
        exception=TransmissionError,
        field="base",
        error="cannot_connect",
    ),
    test.case(
        "connect_error",
        exception=TransmissionConnectError,
        field="base",
        error="cannot_connect",
    ),
    test.case(
        "auth_error",
        exception=TransmissionAuthError,
        field="password",
        error="invalid_auth",
    ),
)
async def reauth_flow_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_transmission_client),
    *,
    exception: type[Exception],
    field: str,
    error: str,
) -> None:
    """Test flow errors."""
    entry = MockConfigEntry(
        domain=transmission.DOMAIN,
        data=MOCK_CONFIG_DATA,
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["description_placeholders"]).to_equal(
        {
            "username": "user",
            "name": "Mock Title",
        }
    )

    client.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "password": "wrong-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({field: error})

    client.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "password": "correct-password",
        },
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
