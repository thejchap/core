"""Test the Vallox integration config flow."""

from typing import Any
from unittest.mock import patch

from tryke import Depends, expect, fixture, test
from vallox_websocket_api import ValloxApiException, ValloxWebsocketException

from homeassistant.components.vallox.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    create_mock_entry,
    do_setup_vallox_entry,
    fetch_metric_data_mock,
    init_reconfigure_flow,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _metrics_mock: Any = Depends(fetch_metric_data_mock),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form_no_input(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the form is returned with no input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)


@test
async def form_create_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that an entry is created with valid input."""
    init = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(init["type"]).to_be(FlowResultType.FORM)
    expect(init["errors"]).to_be(None)

    with (
        patch(
            "homeassistant.components.vallox.config_flow.Vallox.fetch_metric_data",
            return_value=None,
        ),
        patch(
            "homeassistant.components.vallox.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            init["flow_id"],
            {"host": "1.2.3.4"},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Vallox")
    expect(result["data"]).to_equal({"host": "1.2.3.4", "name": "Vallox"})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_invalid_ip(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that invalid IP error is handled."""
    init = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        init["flow_id"],
        {"host": "test.host.com"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"host": "invalid_host"})

    with (
        patch(
            "homeassistant.components.vallox.config_flow.Vallox.fetch_metric_data",
            return_value=None,
        ),
        patch(
            "homeassistant.components.vallox.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            init["flow_id"],
            {"host": "1.2.3.4"},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Vallox")
    expect(result["data"]).to_equal({"host": "1.2.3.4", "name": "Vallox"})


@test
async def form_vallox_api_exception_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that cannot connect error is handled."""
    init = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with patch(
        "homeassistant.components.vallox.config_flow.Vallox.fetch_metric_data",
        side_effect=ValloxApiException,
    ):
        result = await hass.config_entries.flow.async_configure(
            init["flow_id"],
            {"host": "4.3.2.1"},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"host": "cannot_connect"})

    with (
        patch(
            "homeassistant.components.vallox.config_flow.Vallox.fetch_metric_data",
            return_value=None,
        ),
        patch(
            "homeassistant.components.vallox.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            init["flow_id"],
            {"host": "1.2.3.4"},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Vallox")
    expect(result["data"]).to_equal({"host": "1.2.3.4", "name": "Vallox"})


@test
async def form_os_error_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that cannot connect error is handled."""
    init = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with patch(
        "homeassistant.components.vallox.config_flow.Vallox.fetch_metric_data",
        side_effect=ValloxWebsocketException,
    ):
        result = await hass.config_entries.flow.async_configure(
            init["flow_id"],
            {"host": "5.6.7.8"},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"host": "cannot_connect"})

    with (
        patch(
            "homeassistant.components.vallox.config_flow.Vallox.fetch_metric_data",
            return_value=None,
        ),
        patch(
            "homeassistant.components.vallox.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            init["flow_id"],
            {"host": "1.2.3.4"},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Vallox")
    expect(result["data"]).to_equal({"host": "1.2.3.4", "name": "Vallox"})


@test
async def form_unknown_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that unknown exceptions are handled."""
    init = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with patch(
        "homeassistant.components.vallox.config_flow.Vallox.fetch_metric_data",
        side_effect=Exception,
    ):
        result = await hass.config_entries.flow.async_configure(
            init["flow_id"],
            {"host": "54.12.31.41"},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"host": "unknown"})

    with (
        patch(
            "homeassistant.components.vallox.config_flow.Vallox.fetch_metric_data",
            return_value=None,
        ),
        patch(
            "homeassistant.components.vallox.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            init["flow_id"],
            {"host": "1.2.3.4"},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Vallox")
    expect(result["data"]).to_equal({"host": "1.2.3.4", "name": "Vallox"})


@test
async def form_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that already configured error is handled."""
    init = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    create_mock_entry(hass, "20.40.10.30", "Vallox 110 MV")

    result = await hass.config_entries.flow.async_configure(
        init["flow_id"],
        {"host": "20.40.10.30"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reconfigure_host(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    init_flow: tuple[MockConfigEntry, Any] = Depends(init_reconfigure_flow),
) -> None:
    """Test that the host can be reconfigured."""
    entry, init_flow_result = init_flow

    reconfigure_result = await hass.config_entries.flow.async_configure(
        init_flow_result["flow_id"],
        {
            "host": "192.168.100.60",
        },
    )
    await hass.async_block_till_done()
    expect(reconfigure_result["type"]).to_be(FlowResultType.ABORT)
    expect(reconfigure_result["reason"]).to_equal("reconfigure_successful")

    # Changed entry.
    expect(entry.data["host"]).to_equal("192.168.100.60")


@test
async def reconfigure_host_to_same_host_as_another_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    init_flow: tuple[MockConfigEntry, Any] = Depends(init_reconfigure_flow),
) -> None:
    """Test that changing host to a host that already exists fails."""
    entry, init_flow_result = init_flow

    # Create second device.
    create_mock_entry(hass=hass, host="192.168.100.70", name="Vallox 2")
    await do_setup_vallox_entry(hass=hass, host="192.168.100.70", name="Vallox 2")

    reconfigure_result = await hass.config_entries.flow.async_configure(
        init_flow_result["flow_id"],
        {
            "host": "192.168.100.70",
        },
    )
    await hass.async_block_till_done()
    expect(reconfigure_result["type"]).to_be(FlowResultType.ABORT)
    expect(reconfigure_result["reason"]).to_equal("already_configured")

    # Entry not changed.
    expect(entry.data["host"]).to_equal("192.168.100.50")


@test
async def reconfigure_host_to_invalid_ip_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    init_flow: tuple[MockConfigEntry, Any] = Depends(init_reconfigure_flow),
) -> None:
    """Test that an invalid IP error is handled by the reconfigure step."""
    entry, init_flow_result = init_flow

    reconfigure_result = await hass.config_entries.flow.async_configure(
        init_flow_result["flow_id"],
        {
            "host": "test.host.com",
        },
    )
    await hass.async_block_till_done()
    expect(reconfigure_result["type"]).to_be(FlowResultType.FORM)
    expect(reconfigure_result["errors"]).to_equal({"host": "invalid_host"})

    # Entry not changed.
    expect(entry.data["host"]).to_equal("192.168.100.50")

    # Makes sure we can recover and continue.
    reconfigure_result = await hass.config_entries.flow.async_configure(
        init_flow_result["flow_id"],
        {
            "host": "192.168.100.60",
        },
    )
    await hass.async_block_till_done()
    expect(reconfigure_result["type"]).to_be(FlowResultType.ABORT)
    expect(reconfigure_result["reason"]).to_equal("reconfigure_successful")

    # Changed entry.
    expect(entry.data["host"]).to_equal("192.168.100.60")


@test
async def reconfigure_host_vallox_api_exception_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    init_flow: tuple[MockConfigEntry, Any] = Depends(init_reconfigure_flow),
) -> None:
    """Test that cannot connect error is handled by the reconfigure step."""
    entry, init_flow_result = init_flow

    with patch(
        "homeassistant.components.vallox.config_flow.Vallox.fetch_metric_data",
        side_effect=ValloxApiException,
    ):
        reconfigure_result = await hass.config_entries.flow.async_configure(
            init_flow_result["flow_id"],
            {
                "host": "192.168.100.80",
            },
        )
        await hass.async_block_till_done()

    expect(reconfigure_result["type"]).to_be(FlowResultType.FORM)
    expect(reconfigure_result["errors"]).to_equal({"host": "cannot_connect"})

    # Entry not changed.
    expect(entry.data["host"]).to_equal("192.168.100.50")

    # Makes sure we can recover and continue.
    reconfigure_result = await hass.config_entries.flow.async_configure(
        init_flow_result["flow_id"],
        {
            "host": "192.168.100.60",
        },
    )
    await hass.async_block_till_done()
    expect(reconfigure_result["type"]).to_be(FlowResultType.ABORT)
    expect(reconfigure_result["reason"]).to_equal("reconfigure_successful")

    # Changed entry.
    expect(entry.data["host"]).to_equal("192.168.100.60")


@test
async def reconfigure_host_unknown_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    init_flow: tuple[MockConfigEntry, Any] = Depends(init_reconfigure_flow),
) -> None:
    """Test that cannot connect error is handled by the reconfigure step."""
    entry, init_flow_result = init_flow

    with patch(
        "homeassistant.components.vallox.config_flow.Vallox.fetch_metric_data",
        side_effect=Exception,
    ):
        reconfigure_result = await hass.config_entries.flow.async_configure(
            init_flow_result["flow_id"],
            {
                "host": "192.168.100.90",
            },
        )
        await hass.async_block_till_done()

    expect(reconfigure_result["type"]).to_be(FlowResultType.FORM)
    expect(reconfigure_result["errors"]).to_equal({"host": "unknown"})

    # Entry not changed.
    expect(entry.data["host"]).to_equal("192.168.100.50")

    # Makes sure we can recover and continue.
    reconfigure_result = await hass.config_entries.flow.async_configure(
        init_flow_result["flow_id"],
        {
            "host": "192.168.100.60",
        },
    )
    await hass.async_block_till_done()
    expect(reconfigure_result["type"]).to_be(FlowResultType.ABORT)
    expect(reconfigure_result["reason"]).to_equal("reconfigure_successful")

    # Changed entry.
    expect(entry.data["host"]).to_equal("192.168.100.60")
