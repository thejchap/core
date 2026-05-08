"""Test the mill config flow."""

from unittest.mock import AsyncMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.mill.const import CLOUD, CONNECTION_TYPE, DOMAIN, LOCAL
from homeassistant.const import CONF_IP_ADDRESS, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def show_config_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test show configuration form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")


@test
async def create_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test create entry from user input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONNECTION_TYPE: CLOUD,
        },
    )
    expect(result2["type"]).to_be(FlowResultType.FORM)

    with patch("mill.Mill.connect", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                CONF_USERNAME: "user",
                CONF_PASSWORD: "pswd",
            },
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("user")
    expect(result["data"]).to_equal(
        {
            CONF_USERNAME: "user",
            CONF_PASSWORD: "pswd",
            CONNECTION_TYPE: CLOUD,
        }
    )


@test
async def flow_entry_already_exists(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user input for config_entry that already exists."""
    test_data = {
        CONF_USERNAME: "user",
        CONF_PASSWORD: "pswd",
    }

    first_entry = MockConfigEntry(
        domain="mill",
        data=test_data,
        unique_id=test_data[CONF_USERNAME],
    )
    first_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONNECTION_TYPE: CLOUD,
        },
    )
    expect(result2["type"]).to_be(FlowResultType.FORM)

    with patch("mill.Mill.connect", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            test_data,
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test connection error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONNECTION_TYPE: CLOUD,
        },
    )
    expect(result2["type"]).to_be(FlowResultType.FORM)

    with patch("mill.Mill.connect", return_value=False):
        result = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                CONF_USERNAME: "user",
                CONF_PASSWORD: "pswd",
            },
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def local_create_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test create entry from user input (local)."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONNECTION_TYPE: LOCAL,
        },
    )
    expect(result2["type"]).to_be(FlowResultType.FORM)

    test_data = {
        CONF_IP_ADDRESS: "192.168.1.59",
    }

    with patch(
        "mill_local.Mill.connect",
        return_value={
            "name": "panel heater gen. 3",
            "version": "0x210927",
            "operation_key": "",
            "status": "ok",
        },
    ):
        result = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            test_data,
        )

    test_data[CONNECTION_TYPE] = LOCAL
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(test_data[CONF_IP_ADDRESS])
    expect(result["data"]).to_equal(test_data)


@test
async def local_flow_entry_already_exists(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user input for config_entry that already exists (local)."""
    test_data = {
        CONF_IP_ADDRESS: "192.168.1.59",
    }

    first_entry = MockConfigEntry(
        domain="mill",
        data=test_data,
        unique_id=test_data[CONF_IP_ADDRESS],
    )
    first_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONNECTION_TYPE: LOCAL,
        },
    )
    expect(result2["type"]).to_be(FlowResultType.FORM)

    test_data = {
        CONF_IP_ADDRESS: "192.168.1.59",
    }

    with patch(
        "mill_local.Mill.connect",
        return_value={
            "name": "panel heater gen. 3",
            "version": "0x210927",
            "operation_key": "",
            "status": "ok",
        },
    ):
        result = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            test_data,
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def local_connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test connection error (local)."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONNECTION_TYPE: LOCAL,
        },
    )
    expect(result2["type"]).to_be(FlowResultType.FORM)

    test_data = {
        CONF_IP_ADDRESS: "192.168.1.59",
    }

    with patch(
        "mill_local.Mill.connect",
        return_value=None,
    ):
        result = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            test_data,
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})
