"""Test the Evil Genius Labs config flow."""

import logging
from typing import Any
from unittest.mock import MagicMock, patch

import aiohttp
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.evil_genius_labs.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.util.json import JsonObjectType

from tests.components.evil_genius_labs._fixtures import (
    all_fixture,
    info_fixture,
    mock_zeroconf,
    product_fixture,
)
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def form(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    all_fixture: dict[str, Any] = Depends(all_fixture),
    info_fixture: JsonObjectType = Depends(info_fixture),
    product_fixture: dict[str, str] = Depends(product_fixture),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"] is None).to_be(True)

    with (
        patch(
            "pyevilgenius.EvilGeniusDevice.get_all",
            return_value=all_fixture,
        ),
        patch(
            "pyevilgenius.EvilGeniusDevice.get_info",
            return_value=info_fixture,
        ),
        patch(
            "pyevilgenius.EvilGeniusDevice.get_product",
            return_value=product_fixture,
        ),
        patch(
            "homeassistant.components.evil_genius_labs.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result2["title"]).to_equal("Fibonacci256-23D4")
    expect(result2["data"]).to_equal({"host": "1.1.1.1"})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_cannot_connect(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    records: list[logging.LogRecord] = []

    class _Handler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    handler = _Handler(level=logging.DEBUG)
    root = logging.getLogger()
    root.addHandler(handler)
    prev_level = root.level
    root.setLevel(logging.DEBUG)
    try:
        with patch(
            "pyevilgenius.EvilGeniusDevice.get_all",
            side_effect=aiohttp.ClientError,
        ):
            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    "host": "1.1.1.1",
                },
            )
    finally:
        root.removeHandler(handler)
        root.setLevel(prev_level)

    expect(result2["type"] is FlowResultType.FORM).to_be(True)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})
    expect(
        any("Unable to connect" in record.getMessage() for record in records)
    ).to_be(True)


@test
async def form_timeout(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test we handle timeout error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "pyevilgenius.EvilGeniusDevice.get_all",
        side_effect=TimeoutError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
            },
        )

    expect(result2["type"] is FlowResultType.FORM).to_be(True)
    expect(result2["errors"]).to_equal({"base": "timeout"})


@test
async def form_unknown(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test we handle unknown error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "pyevilgenius.EvilGeniusDevice.get_all",
        side_effect=ValueError("BOOM"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
            },
        )

    expect(result2["type"] is FlowResultType.FORM).to_be(True)
    expect(result2["errors"]).to_equal({"base": "unknown"})
