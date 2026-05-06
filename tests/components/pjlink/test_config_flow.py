"""Test the PJLink config flow."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.pjlink.const import DOMAIN
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_config_entry, mock_projector, mock_setup_entry
from .const import DEFAULT_DATA, DEFAULT_DATA_W_ENCODING, DEFAULT_DATA_WO_PORT

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
def _trigger_executor(
    _setup: AsyncMock = Depends(mock_setup_entry),
    _projector: MagicMock = Depends(mock_projector),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_flow_creates_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that the user flow creates an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], DEFAULT_DATA
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test name")
    expect(result["data"]).to_equal(DEFAULT_DATA)
    expect(len(setup.mock_calls)).to_equal(1)


@test
async def user_flow_aborts_if_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test user flow aborts if already configured."""
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], DEFAULT_DATA
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("invalid_auth", side_effect=RuntimeError, error_str="invalid_auth"),
    test.case("cannot_connect", side_effect=TimeoutError, error_str="cannot_connect"),
    test.case("unknown", side_effect=Exception, error_str="unknown"),
)
async def form_invalid_inputs(
    side_effect: type[Exception],
    error_str: str,
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(mock_setup_entry),
    projector: MagicMock = Depends(mock_projector),
) -> None:
    """Test we handle invalid inputs."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_instance = projector.from_address.return_value
    mock_instance.authenticate.side_effect = side_effect
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], DEFAULT_DATA
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_str})

    mock_instance.authenticate.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], DEFAULT_DATA
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test name")
    expect(result["data"]).to_equal(DEFAULT_DATA)
    expect(len(setup.mock_calls)).to_equal(1)


@test.cases(
    test.case("default", import_data=DEFAULT_DATA),
    test.case("no_port", import_data=DEFAULT_DATA_WO_PORT),
    test.case("w_encoding", import_data=DEFAULT_DATA_W_ENCODING),
)
async def import_creates_entry(
    import_data: dict[str, Any],
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(mock_setup_entry),
    _projector: MagicMock = Depends(mock_projector),
) -> None:
    """Test importing a YAML config creates an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}, data=import_data
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test name")
    expect(result["data"]).to_equal(DEFAULT_DATA)
    expect(len(setup.mock_calls)).to_equal(1)


@test
async def import_aborts_if_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test importing a YAML config aborts if already configured."""
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}, data=DEFAULT_DATA
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("invalid_auth", side_effect=RuntimeError, error_str="invalid_auth"),
    test.case("cannot_connect", side_effect=TimeoutError, error_str="cannot_connect"),
    test.case("unknown", side_effect=Exception, error_str="unknown"),
)
async def import_invalid_inputs(
    side_effect: type[Exception],
    error_str: str,
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(mock_setup_entry),
    projector: MagicMock = Depends(mock_projector),
) -> None:
    """Test we handle invalid inputs on import."""
    mock_instance = projector.from_address.return_value
    mock_instance.authenticate.side_effect = side_effect
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}, data=DEFAULT_DATA
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(error_str)
    expect(len(setup.mock_calls)).to_equal(0)
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(0)
