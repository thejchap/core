"""Test the Hi-Link HLK-SW16 config flow."""

import asyncio
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.hlk_sw16.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network


class MockSW16Client:
    """Class to mock the SW16Client client."""

    def __init__(self, fail) -> None:
        """Initialise client with failure modes."""
        self.fail = fail
        self.disconnect_callback = None
        self.in_transaction = False
        self.active_transaction = None

    async def setup(self):
        """Mock successful setup."""
        fut = asyncio.Future()
        fut.set_result(True)
        return fut

    async def status(self):
        """Mock status based on failure mode."""
        self.in_transaction = True
        self.active_transaction = asyncio.Future()
        if self.fail:
            if self.disconnect_callback:
                self.disconnect_callback()
            return await self.active_transaction
        self.active_transaction.set_result(True)
        return self.active_transaction

    def stop(self):
        """Mock client stop."""
        self.in_transaction = False
        self.active_transaction = None


async def create_mock_hlk_sw16_connection(fail):
    """Create a mock HLK-SW16 client."""
    client = MockSW16Client(fail)
    await client.setup()
    return client


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    conf = {
        "host": "127.0.0.1",
        "port": 8080,
    }

    mock_hlk_sw16_connection = await create_mock_hlk_sw16_connection(False)

    with (
        patch(
            "homeassistant.components.hlk_sw16.config_flow.create_hlk_sw16_connection",
            return_value=mock_hlk_sw16_connection,
        ),
        patch(
            "homeassistant.components.hlk_sw16.async_setup", return_value=True
        ) as mock_setup,
        patch(
            "homeassistant.components.hlk_sw16.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            conf,
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("127.0.0.1:8080")
    expect(result2["data"]).to_equal(
        {
            "host": "127.0.0.1",
            "port": 8080,
        }
    )
    expect(len(mock_setup.mock_calls)).to_equal(1)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)

    mock_hlk_sw16_connection = await create_mock_hlk_sw16_connection(False)

    with patch(
        "homeassistant.components.hlk_sw16.config_flow.create_hlk_sw16_connection",
        return_value=mock_hlk_sw16_connection,
    ):
        result3 = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result3["type"]).to_be(FlowResultType.FORM)
    expect(result3["errors"]).to_equal({})

    result4 = await hass.config_entries.flow.async_configure(
        result3["flow_id"],
        conf,
    )

    expect(result4["type"]).to_be(FlowResultType.ABORT)
    expect(result4["reason"]).to_equal("already_configured")


@test
async def form_import(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_IMPORT}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    conf = {
        "host": "127.0.0.1",
        "port": 8080,
    }

    mock_hlk_sw16_connection = await create_mock_hlk_sw16_connection(False)

    with (
        patch(
            "homeassistant.components.hlk_sw16.config_flow.connect_client",
            return_value=mock_hlk_sw16_connection,
        ),
        patch(
            "homeassistant.components.hlk_sw16.async_setup", return_value=True
        ) as mock_setup,
        patch(
            "homeassistant.components.hlk_sw16.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            conf,
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("127.0.0.1:8080")
    expect(result2["data"]).to_equal(
        {
            "host": "127.0.0.1",
            "port": 8080,
        }
    )
    expect(len(mock_setup.mock_calls)).to_equal(1)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_invalid_data(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_hlk_sw16_connection = await create_mock_hlk_sw16_connection(True)

    conf = {
        "host": "127.0.0.1",
        "port": 8080,
    }

    with patch(
        "homeassistant.components.hlk_sw16.config_flow.connect_client",
        return_value=mock_hlk_sw16_connection,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            conf,
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    conf = {
        "host": "127.0.0.1",
        "port": 8080,
    }

    with patch(
        "homeassistant.components.hlk_sw16.config_flow.connect_client",
        side_effect=TimeoutError,
        return_value=None,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            conf,
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})
