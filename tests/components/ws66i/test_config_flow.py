"""Test the WS66i 6-Zone Amplifier config flow."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.ws66i.const import (
    CONF_SOURCE_1,
    CONF_SOURCE_2,
    CONF_SOURCE_3,
    CONF_SOURCE_4,
    CONF_SOURCE_5,
    CONF_SOURCE_6,
    CONF_SOURCES,
    DOMAIN,
    INIT_OPTIONS_DEFAULT,
)
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .test_media_player import AttrDict

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

CONFIG = {CONF_IP_ADDRESS: "1.1.1.1"}


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

    with (
        patch(
            "homeassistant.components.ws66i.config_flow.get_ws66i",
        ) as mock_ws66i,
        patch(
            "homeassistant.components.ws66i.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        ws66i_instance = mock_ws66i.return_value

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], CONFIG
        )
        await hass.async_block_till_done()

        ws66i_instance.open.assert_called_once()
        ws66i_instance.close.assert_called_once()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("WS66i Amp")
    expect(result2["data"]).to_equal({CONF_IP_ADDRESS: CONFIG[CONF_IP_ADDRESS]})

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch("homeassistant.components.ws66i.config_flow.get_ws66i") as mock_ws66i:
        ws66i_instance = mock_ws66i.return_value
        ws66i_instance.open.side_effect = ConnectionError
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], CONFIG
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_wrong_ip(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test cannot connect error with bad IP."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch("homeassistant.components.ws66i.config_flow.get_ws66i") as mock_ws66i:
        ws66i_instance = mock_ws66i.return_value
        ws66i_instance.zone_status.return_value = None
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], CONFIG
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def generic_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test generic exception."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch("homeassistant.components.ws66i.config_flow.get_ws66i") as mock_ws66i:
        ws66i_instance = mock_ws66i.return_value
        ws66i_instance.open.side_effect = Exception
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], CONFIG
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow options."""
    conf = {CONF_IP_ADDRESS: "1.1.1.1", CONF_SOURCES: INIT_OPTIONS_DEFAULT}

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=conf,
        options={CONF_SOURCES: INIT_OPTIONS_DEFAULT},
    )
    config_entry.add_to_hass(hass)

    with patch("homeassistant.components.ws66i.get_ws66i") as mock_ws66i:
        ws66i_instance = mock_ws66i.return_value
        ws66i_instance.zone_status.return_value = AttrDict(
            power=True, volume=0, mute=True, source=1, treble=0, bass=0, balance=10
        )
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

        result = await hass.config_entries.options.async_init(config_entry.entry_id)

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_SOURCE_1: "one",
                CONF_SOURCE_2: "too",
                CONF_SOURCE_3: "tree",
                CONF_SOURCE_4: "for",
                CONF_SOURCE_5: "feeve",
                CONF_SOURCE_6: "roku",
            },
        )

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(config_entry.options[CONF_SOURCES]).to_equal(
            {
                "1": "one",
                "2": "too",
                "3": "tree",
                "4": "for",
                "5": "feeve",
                "6": "roku",
            }
        )
