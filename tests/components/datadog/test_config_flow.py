"""Tests for the Datadog config flow."""

from unittest.mock import MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.datadog.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .common import MOCK_CONFIG, MOCK_DATA, MOCK_OPTIONS

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user-initiated config flow."""
    with patch(
        "homeassistant.components.datadog.config_flow.DogStatsd"
    ) as mock_dogstatsd:
        mock_instance = MagicMock()
        mock_dogstatsd.return_value = mock_instance

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_CONFIG
        )
        expect(result2["title"]).to_equal(f"Datadog {MOCK_CONFIG['host']}")
        expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result2["data"]).to_equal(MOCK_DATA)
        expect(result2["options"]).to_equal(MOCK_OPTIONS)


@test
async def user_flow_retry_after_connection_fail(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test connection failure."""
    with patch(
        "homeassistant.components.datadog.config_flow.DogStatsd",
        side_effect=OSError("Connection failed"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_CONFIG
        )
        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["errors"]).to_equal({"base": "cannot_connect"})

    with patch(
        "homeassistant.components.datadog.config_flow.DogStatsd",
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_CONFIG
        )
        expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result3["data"]).to_equal(MOCK_DATA)
        expect(result3["options"]).to_equal(MOCK_OPTIONS)


@test
async def user_flow_abort_already_configured_service(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Abort user-initiated config flow if the same host/port is already configured."""
    existing_entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_DATA,
        options=MOCK_OPTIONS,
    )
    existing_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_CONFIG
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def options_flow_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the options flow shows an error when connection fails."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_DATA,
        options=MOCK_OPTIONS,
    )
    mock_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.datadog.config_flow.DogStatsd",
        side_effect=OSError("connection failed"),
    ):
        result = await hass.config_entries.options.async_init(mock_entry.entry_id)
        expect(result["type"]).to_be(FlowResultType.FORM)

        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"], user_input=MOCK_OPTIONS
        )

        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["errors"]).to_equal({"base": "cannot_connect"})

    with patch(
        "homeassistant.components.datadog.config_flow.DogStatsd",
    ):
        result3 = await hass.config_entries.options.async_configure(
            result["flow_id"], user_input=MOCK_OPTIONS
        )
        expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result3["data"]).to_equal(MOCK_OPTIONS)


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test updating options after setup."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_DATA,
        options=MOCK_OPTIONS,
    )
    mock_entry.add_to_hass(hass)

    new_options = {
        "prefix": "updated",
        "rate": 5,
    }

    # OSError case.
    with patch(
        "homeassistant.components.datadog.config_flow.DogStatsd",
        side_effect=OSError,
    ):
        result = await hass.config_entries.options.async_init(mock_entry.entry_id)
        expect(result["type"]).to_be(FlowResultType.FORM)
        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"], user_input=new_options
        )
        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["errors"]).to_equal({"base": "cannot_connect"})

    # ValueError case.
    with patch(
        "homeassistant.components.datadog.config_flow.DogStatsd",
        side_effect=ValueError,
    ):
        result = await hass.config_entries.options.async_init(mock_entry.entry_id)
        expect(result["type"]).to_be(FlowResultType.FORM)
        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"], user_input=new_options
        )
        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["errors"]).to_equal({"base": "cannot_connect"})

    # Success case.
    with patch(
        "homeassistant.components.datadog.config_flow.DogStatsd"
    ) as mock_dogstatsd:
        mock_instance = MagicMock()
        mock_dogstatsd.return_value = mock_instance

        result = await hass.config_entries.options.async_configure(
            result["flow_id"], user_input=new_options
        )

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["data"]).to_equal(new_options)
        mock_instance.increment.assert_called_once_with("connection_test")
