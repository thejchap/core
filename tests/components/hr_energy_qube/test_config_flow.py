"""Test the Qube Heat Pump config flow."""

from unittest.mock import AsyncMock, MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.hr_energy_qube.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_config_entry, mock_qube_client, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    qube_client: MagicMock = Depends(mock_qube_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test successful config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "qube.local"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Qube heat pump")
    expect(result["data"]).to_equal({CONF_HOST: "qube.local", CONF_PORT: 502})


@test.cases(
    test.case(
        "cannot_connect_returns_false",
        connect_side_effect=None,
        connect_result=False,
        version_result="2.15",
        error="cannot_connect",
    ),
    test.case(
        "cannot_connect_oserror",
        connect_side_effect=OSError,
        connect_result=None,
        version_result="2.15",
        error="cannot_connect",
    ),
    test.case(
        "not_qube_device",
        connect_side_effect=None,
        connect_result=True,
        version_result=None,
        error="not_qube_device",
    ),
)
async def flow_errors(
    *,
    connect_side_effect: type[Exception] | None,
    connect_result: bool | None,
    version_result: str | None,
    error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    qube_client: MagicMock = Depends(mock_qube_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test flow error handling with recovery."""
    qube_client.connect = AsyncMock(
        side_effect=connect_side_effect, return_value=connect_result
    )
    qube_client.async_get_software_version = AsyncMock(return_value=version_result)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "1.2.3.4"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    # Reset mocks for successful retry
    qube_client.connect = AsyncMock(return_value=True)
    qube_client.async_get_software_version = AsyncMock(return_value="2.15")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "1.2.3.4"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    qube_client: MagicMock = Depends(mock_qube_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we abort when device is already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "1.2.3.4"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
