"""Test the todoist config flow."""

from http import HTTPStatus
from unittest.mock import AsyncMock

from requests.exceptions import HTTPError
from requests.models import Response
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.todoist.const import DOMAIN
from homeassistant.const import CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.setup import async_setup_component

from ._fixtures import (
    TOKEN,
    mock_api,
    mock_setup_entry,
    mock_todoist_config_entry,
    patch_api,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _patched: AsyncMock = Depends(patch_api),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


def _set_status(api: AsyncMock, status: HTTPStatus) -> None:
    response = Response()
    response.status_code = status
    api.get_tasks.side_effect = HTTPError(response=response)


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(bool(result.get("errors"))).to_be(False)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_TOKEN: TOKEN,
        },
    )
    await hass.async_block_till_done()

    expect(result2.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2.get("title")).to_equal("Todoist")
    expect(result2.get("data")).to_equal(
        {
            CONF_TOKEN: TOKEN,
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def form_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    api: AsyncMock = Depends(mock_api),
) -> None:
    """Test we handle invalid auth."""
    _set_status(api, HTTPStatus.UNAUTHORIZED)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_TOKEN: TOKEN,
        },
    )

    expect(result2.get("type")).to_be(FlowResultType.FORM)
    expect(result2.get("errors")).to_equal({"base": "invalid_api_key"})


@test
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    api: AsyncMock = Depends(mock_api),
) -> None:
    """Test we handle cannot connect error."""
    _set_status(api, HTTPStatus.INTERNAL_SERVER_ERROR)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_TOKEN: TOKEN,
        },
    )

    expect(result2.get("type")).to_be(FlowResultType.FORM)
    expect(result2.get("errors")).to_equal({"base": "cannot_connect"})


@test
async def unknown_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    api: AsyncMock = Depends(mock_api),
) -> None:
    """Test we handle unknown error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    api.get_tasks.side_effect = ValueError("unexpected")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_TOKEN: TOKEN,
        },
    )

    expect(result2.get("type")).to_be(FlowResultType.FORM)
    expect(result2.get("errors")).to_equal({"base": "unknown"})


@test
async def already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    api: AsyncMock = Depends(mock_api),
    config_entry: MockConfigEntry = Depends(mock_todoist_config_entry),
) -> None:
    """Test that only a single instance can be configured."""
    config_entry.add_to_hass(hass)
    from unittest.mock import patch as _patch

    with (
        _patch("homeassistant.components.todoist.TodoistAPIAsync", return_value=api),
        _patch("homeassistant.components.todoist.PLATFORMS", []),
    ):
        expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)
        await hass.async_block_till_done()

        entries = hass.config_entries.async_entries(DOMAIN)
        expect(len(entries)).to_equal(1)

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        expect(result.get("type")).to_be(FlowResultType.ABORT)
        expect(result.get("reason")).to_equal("single_instance_allowed")
