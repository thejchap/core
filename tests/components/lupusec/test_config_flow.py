"""Unit tests for the Lupusec config flow."""

from json import JSONDecodeError
from unittest.mock import patch

from lupupy import LupusecException
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.lupusec.const import DOMAIN
from homeassistant.const import (
    CONF_HOST,
    CONF_IP_ADDRESS,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass, mock_network

MOCK_DATA_STEP = {
    CONF_HOST: "test-host.lan",
    CONF_USERNAME: "test-username",
    CONF_PASSWORD: "test-password",
}

MOCK_IMPORT_STEP = {
    CONF_IP_ADDRESS: "test-host.lan",
    CONF_USERNAME: "test-username",
    CONF_PASSWORD: "test-password",
}

MOCK_IMPORT_STEP_NAME = {
    CONF_IP_ADDRESS: "test-host.lan",
    CONF_USERNAME: "test-username",
    CONF_PASSWORD: "test-password",
    CONF_NAME: "test-name",
}


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def form_valid_input(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test handling valid user input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.lupusec.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.lupusec.config_flow.lupupy.Lupusec",
        ) as mock_initialize_lupusec,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_DATA_STEP,
        )
    await hass.async_block_till_done()

    expect(result2["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result2["title"]).to_equal(MOCK_DATA_STEP[CONF_HOST])
    expect(result2["data"]).to_equal(MOCK_DATA_STEP)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(len(mock_initialize_lupusec.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "lupusec_exception",
        LupusecException("Test lupusec exception"),
        "cannot_connect",
    ),
    test.case(
        "json_decode",
        JSONDecodeError("Test JSONDecodeError", "test", 1),
        "cannot_connect",
    ),
    test.case("unknown", Exception("Test unknown exception"), "unknown"),
)
async def flow_user_init_data_error_and_recover(
    raise_error: Exception,
    text_error: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test exceptions and recovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.lupusec.config_flow.lupupy.Lupusec",
        side_effect=raise_error,
    ) as mock_initialize_lupusec:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_DATA_STEP,
        )
        await hass.async_block_till_done()

    expect(result2["type"] is FlowResultType.FORM).to_be(True)
    expect(result2["errors"]).to_equal({"base": text_error})

    expect(len(mock_initialize_lupusec.mock_calls)).to_equal(1)

    # Recover
    with (
        patch(
            "homeassistant.components.lupusec.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.lupusec.config_flow.lupupy.Lupusec",
        ) as mock_initialize_lupusec,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_DATA_STEP,
        )

    await hass.async_block_till_done()

    expect(result3["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result3["title"]).to_equal(MOCK_DATA_STEP[CONF_HOST])
    expect(result3["data"]).to_equal(MOCK_DATA_STEP)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(len(mock_initialize_lupusec.mock_calls)).to_equal(1)


@test
async def flow_user_init_data_already_configured(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test duplicate config entry."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        title=MOCK_DATA_STEP[CONF_HOST],
        data=MOCK_DATA_STEP,
    )

    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_DATA_STEP,
    )

    await hass.async_block_till_done()

    expect(result2["type"] is FlowResultType.ABORT).to_be(True)
    expect(result2["reason"]).to_equal("already_configured")
