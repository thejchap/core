"""Test the Scrape config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.rest.data import (  # pylint: disable=hass-component-root-import
    DEFAULT_TIMEOUT,
)
from homeassistant.components.rest.schema import (  # pylint: disable=hass-component-root-import
    DEFAULT_METHOD,
)
from homeassistant.components.scrape import DOMAIN
from homeassistant.components.scrape.const import (
    CONF_ADVANCED,
    CONF_AUTH,
    CONF_ENCODING,
    CONF_INDEX,
    CONF_SELECT,
    DEFAULT_ENCODING,
    DEFAULT_VERIFY_SSL,
)
from homeassistant.const import (
    CONF_METHOD,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PAYLOAD,
    CONF_RESOURCE,
    CONF_TIMEOUT,
    CONF_USERNAME,
    CONF_VALUE_TEMPLATE,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import HomeAssistantError

from . import MockRestData
from ._fixtures import get_data, loaded_entry, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def entry_and_subentry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    data: MockRestData = Depends(get_data),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["step_id"]).to_equal("user")
    expect(result["type"]).to_be(FlowResultType.FORM)

    with patch(
        "homeassistant.components.rest.RestData",
        return_value=data,
    ) as mock_data:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_RESOURCE: "https://www.home-assistant.io",
                CONF_METHOD: "GET",
                CONF_AUTH: {},
                CONF_ADVANCED: {
                    CONF_VERIFY_SSL: True,
                    CONF_TIMEOUT: 10.0,
                },
            },
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["version"]).to_equal(2)
    expect(result["options"]).to_equal(
        {
            CONF_RESOURCE: "https://www.home-assistant.io",
            CONF_METHOD: "GET",
            CONF_AUTH: {},
            CONF_ADVANCED: {
                CONF_VERIFY_SSL: True,
                CONF_TIMEOUT: 10.0,
                CONF_ENCODING: "UTF-8",
            },
        }
    )

    expect(len(mock_data.mock_calls)).to_equal(1)
    expect(len(setup_entry.mock_calls)).to_equal(1)
    await hass.async_block_till_done(wait_background_tasks=True)

    subentry_flows = hass.config_entries.subentries.async_progress()
    expect(len(subentry_flows)).to_equal(1)

    result = await hass.config_entries.subentries.async_configure(
        subentry_flows[0]["flow_id"],
        {
            CONF_NAME: "Current version",
            CONF_INDEX: 0,
            CONF_SELECT: ".current-version h1",
            CONF_ADVANCED: {},
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Current version")
    expect(result["data"]).to_equal(
        {
            CONF_INDEX: 0,
            CONF_SELECT: ".current-version h1",
            CONF_ADVANCED: {},
        }
    )


@test
async def form_with_post(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    data: MockRestData = Depends(get_data),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form using POST method."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["step_id"]).to_equal("user")
    expect(result["type"]).to_be(FlowResultType.FORM)

    with patch(
        "homeassistant.components.rest.RestData",
        return_value=data,
    ) as mock_data:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_RESOURCE: "https://www.home-assistant.io",
                CONF_METHOD: "GET",
                CONF_PAYLOAD: "POST",
                CONF_AUTH: {},
                CONF_ADVANCED: {
                    CONF_VERIFY_SSL: True,
                    CONF_TIMEOUT: 10.0,
                },
            },
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["version"]).to_equal(2)
    expect(result["options"]).to_equal(
        {
            CONF_RESOURCE: "https://www.home-assistant.io",
            CONF_METHOD: "GET",
            CONF_PAYLOAD: "POST",
            CONF_AUTH: {},
            CONF_ADVANCED: {
                CONF_VERIFY_SSL: True,
                CONF_TIMEOUT: 10.0,
                CONF_ENCODING: "UTF-8",
            },
        }
    )

    expect(len(mock_data.mock_calls)).to_equal(1)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def flow_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    data: MockRestData = Depends(get_data),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test config flow error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(config_entries.SOURCE_USER)

    with patch(
        "homeassistant.components.rest.RestData",
        side_effect=HomeAssistantError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_RESOURCE: "https://www.home-assistant.io",
                CONF_METHOD: "GET",
                CONF_AUTH: {},
                CONF_ADVANCED: {
                    CONF_VERIFY_SSL: True,
                    CONF_TIMEOUT: 10.0,
                },
            },
        )

    expect(result["errors"]).to_equal({"base": "resource_error"})

    with patch(
        "homeassistant.components.rest.RestData",
        return_value=MockRestData("test_scrape_sensor_no_data"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_RESOURCE: "https://www.home-assistant.io",
                CONF_METHOD: "GET",
                CONF_AUTH: {},
                CONF_ADVANCED: {
                    CONF_VERIFY_SSL: True,
                    CONF_TIMEOUT: 10.0,
                },
            },
        )

    expect(result["errors"]).to_equal({"base": "no_data"})

    with patch(
        "homeassistant.components.rest.RestData",
        return_value=data,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_RESOURCE: "https://www.home-assistant.io",
                CONF_METHOD: "GET",
                CONF_AUTH: {},
                CONF_ADVANCED: {
                    CONF_VERIFY_SSL: True,
                    CONF_TIMEOUT: 10.0,
                },
            },
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("https://www.home-assistant.io")
    expect(result["options"]).to_equal(
        {
            CONF_RESOURCE: "https://www.home-assistant.io",
            CONF_METHOD: "GET",
            CONF_AUTH: {},
            CONF_ADVANCED: {
                CONF_VERIFY_SSL: True,
                CONF_TIMEOUT: 10.0,
                CONF_ENCODING: "UTF-8",
            },
        }
    )


@test
async def options_resource_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(loaded_entry),
) -> None:
    """Test options flow for a resource."""
    state = hass.states.get("sensor.current_version")
    expect(state.state).to_equal("Current Version: 2021.12.10")

    result = await hass.config_entries.options.async_init(entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    mocker = MockRestData("test_scrape_sensor2")
    with patch("homeassistant.components.rest.RestData", return_value=mocker):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_RESOURCE: "https://www.home-assistant.io",
                CONF_METHOD: DEFAULT_METHOD,
                CONF_AUTH: {
                    CONF_USERNAME: "secret_username",
                    CONF_PASSWORD: "secret_password",
                },
                CONF_ADVANCED: {
                    CONF_VERIFY_SSL: DEFAULT_VERIFY_SSL,
                    CONF_TIMEOUT: DEFAULT_TIMEOUT,
                    CONF_ENCODING: DEFAULT_ENCODING,
                },
            },
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            CONF_RESOURCE: "https://www.home-assistant.io",
            CONF_METHOD: "GET",
            CONF_AUTH: {
                CONF_USERNAME: "secret_username",
                CONF_PASSWORD: "secret_password",
            },
            CONF_ADVANCED: {
                CONF_VERIFY_SSL: True,
                CONF_TIMEOUT: 10.0,
                CONF_ENCODING: "UTF-8",
            },
        }
    )

    await hass.async_block_till_done()

    # Check the entity was updated, no new entity was created.
    expect(len(hass.states.async_all())).to_equal(1)

    # Check the state of the entity has changed as expected.
    state = hass.states.get("sensor.current_version")
    expect(state.state).to_equal("Hidden Version: 2021.12.10")


@test
async def reconfigure_sensor_subentry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(loaded_entry),
    data: MockRestData = Depends(get_data),
) -> None:
    """Test reconfiguring a sensor subentry."""
    state = hass.states.get("sensor.current_version")
    expect(state.state).to_equal("Current Version: 2021.12.10")

    subentry_id = list(entry.subentries)[0]

    result = await entry.start_subentry_reconfigure_flow(hass, subentry_id=subentry_id)
    with patch(
        "homeassistant.components.rest.RestData",
        return_value=data,
    ):
        await hass.config_entries.subentries.async_configure(
            result["flow_id"],
            {
                CONF_ADVANCED: {
                    CONF_VALUE_TEMPLATE: "{{ value.split(':')[1] }}",
                },
                CONF_INDEX: 0,
                CONF_SELECT: ".current-version h1",
            },
        )
        await hass.async_block_till_done()

    state = hass.states.get("sensor.current_version")
    expect(state.state).to_equal("2021.12.10")
