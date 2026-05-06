"""Test the Ping (ICMP) config flow."""

from icmplib import Host
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.ping import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import patch_ping, patch_setup

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
def _trigger_executor(
    _setup: None = Depends(patch_setup),
    _ping: Host = Depends(patch_ping),
) -> None:
    """Module-level fixture priming common mocks."""


@test.cases(
    test.case("ip", host="192.618.178.1", expected="192.618.178.1"),
    test.case("ip_padded", host=" 192.618.178.1 ", expected="192.618.178.1"),
    test.case("hostname_padded", host=" demo.host ", expected="demo.host"),
)
async def form(
    host: str,
    expected: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["step_id"]).to_equal("user")
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "host": host,
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(expected)
    expect(result["data"]).to_equal({})
    expect(result["options"]).to_equal(
        {
            "count": 5,
            "host": expected,
            "consider_home": 180,
        }
    )


@test.cases(
    test.case("ip", host="192.618.178.1", expected_host="192.618.178.1"),
    test.case("ip_padded", host=" 192.618.178.1 ", expected_host="192.618.178.1"),
    test.case("hostname_padded", host=" demo.host ", expected_host="demo.host"),
)
async def options(
    host: str,
    expected_host: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test options flow."""
    config_entry = MockConfigEntry(
        version=1,
        source=config_entries.SOURCE_USER,
        data={},
        domain=DOMAIN,
        options={"count": 1, "host": "192.168.1.1", "consider_home": 180},
        title="192.168.1.1",
    )
    config_entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "host": host,
            "count": 10,
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            "count": 10,
            "host": expected_host,
            "consider_home": 180,
        }
    )
