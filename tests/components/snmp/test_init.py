"""SNMP tests."""

from unittest.mock import patch

from pysnmp.hlapi.v3arch.asyncio import SnmpEngine
from pysnmp.hlapi.v3arch.asyncio.cmdgen import LCD
from tryke import Depends, expect, fixture, test

from homeassistant.components import snmp
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant

from ._fixtures import patch_getaddrinfo

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _addrinfo: None = Depends(patch_getaddrinfo),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def async_get_snmp_engine(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test async_get_snmp_engine."""
    engine = await snmp.async_get_snmp_engine(hass)
    expect(isinstance(engine, SnmpEngine)).to_be(True)
    engine2 = await snmp.async_get_snmp_engine(hass)
    expect(engine is engine2).to_be(True)
    with patch.object(LCD, "unconfigure") as mock_unconfigure:
        hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
        await hass.async_block_till_done()
    expect(mock_unconfigure.called).to_be(True)
