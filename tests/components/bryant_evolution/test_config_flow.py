"""Test the Bryant Evolution config flow."""

from unittest.mock import DEFAULT, AsyncMock, patch

from evolutionhttp import BryantEvolutionLocalClient, ZoneInfo
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.bryant_evolution.const import CONF_SYSTEM_ZONE, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_FILENAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    mock_evolution_client_factory,
    mock_evolution_entry,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _factory: AsyncMock = Depends(mock_evolution_client_factory),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch.object(
        BryantEvolutionLocalClient,
        "enumerate_zones",
        return_value=DEFAULT,
    ) as mock_call:
        mock_call.side_effect = lambda system_id, filename: {
            1: [ZoneInfo(1, 1, "S1Z1"), ZoneInfo(1, 2, "S1Z2")],
            2: [ZoneInfo(2, 3, "S2Z2"), ZoneInfo(2, 4, "S2Z3")],
        }.get(system_id, [])
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_FILENAME: "test_form_success",
            },
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("SAM at test_form_success")
    expect(result["data"]).to_equal(
        {
            CONF_FILENAME: "test_form_success",
            CONF_SYSTEM_ZONE: [(1, 1), (1, 2), (2, 3), (2, 4)],
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with patch.object(
        BryantEvolutionLocalClient,
        "enumerate_zones",
        return_value=DEFAULT,
    ) as mock_call:
        mock_call.return_value = []
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_FILENAME: "test_form_cannot_connect",
            },
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({"base": "cannot_connect"})

    with patch.object(
        BryantEvolutionLocalClient,
        "enumerate_zones",
        return_value=DEFAULT,
    ) as mock_call:
        mock_call.side_effect = lambda system_id, filename: {
            1: [ZoneInfo(1, 1, "S1Z1"), ZoneInfo(1, 2, "S1Z2")],
            2: [ZoneInfo(2, 3, "S2Z3"), ZoneInfo(2, 4, "S2Z4")],
        }.get(system_id, [])
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_FILENAME: "some-serial",
            },
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("SAM at some-serial")
    expect(result["data"]).to_equal(
        {
            CONF_FILENAME: "some-serial",
            CONF_SYSTEM_ZONE: [(1, 1), (1, 2), (2, 3), (2, 4)],
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def form_cannot_connect_bad_file(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    factory: AsyncMock = Depends(mock_evolution_client_factory),
) -> None:
    """Test we handle cannot connect error from a missing file."""
    factory.side_effect = FileNotFoundError("test error")
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_FILENAME: "test_form_cannot_connect_bad_file",
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def reconfigure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    evolution_entry: MockConfigEntry = Depends(mock_evolution_entry),
) -> None:
    """Test that reconfigure discovers additional systems and zones."""

    result = await evolution_entry.start_reconfigure_flow(hass)
    with patch.object(
        BryantEvolutionLocalClient,
        "enumerate_zones",
        return_value=DEFAULT,
    ) as mock_call:
        mock_call.side_effect = lambda system_id, filename: {
            1: [ZoneInfo(1, 1, "S1Z1")],
            2: [ZoneInfo(2, 3, "S2Z3"), ZoneInfo(2, 4, "S2Z4"), ZoneInfo(2, 5, "S2Z5")],
        }.get(system_id, [])
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_FILENAME: "test_reconfigure",
            },
        )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    config_entry = hass.config_entries.async_entries()[0]
    expect(config_entry.data[CONF_SYSTEM_ZONE]).to_equal(
        [
            (1, 1),
            (2, 3),
            (2, 4),
            (2, 5),
        ]
    )
