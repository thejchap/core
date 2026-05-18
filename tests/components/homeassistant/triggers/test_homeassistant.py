"""The tests for the Event automation."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import automation
from homeassistant.core import CoreState, HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import async_mock_service
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Anchor fixture - autouse mock_network for every test."""
    return 0


@test
async def if_fires_on_hass_start(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the firing when Home Assistant starts."""
    hass_config = {
        automation.DOMAIN: {
            "alias": "hello",
            "trigger": {"platform": "homeassistant", "event": "start"},
            "action": {
                "service": "test.automation",
                "data_template": {"id": "{{ trigger.id}}"},
            },
        }
    }
    calls = async_mock_service(hass, "test", "automation")
    hass.set_state(CoreState.not_running)

    with patch(
        "homeassistant.config.load_yaml_config_file", return_value=hass_config
    ):
        expect(
            await async_setup_component(hass, automation.DOMAIN, hass_config)
        ).to_be_truthy()
        expect(automation.is_on(hass, "automation.hello")).to_be(True)
        expect(len(calls)).to_equal(0)

        await hass.async_start()
        await hass.async_block_till_done()
        expect(automation.is_on(hass, "automation.hello")).to_be(True)
        expect(len(calls)).to_equal(1)

        await hass.services.async_call(
            automation.DOMAIN, automation.SERVICE_RELOAD, blocking=True
        )

        expect(automation.is_on(hass, "automation.hello")).to_be(True)
        expect(len(calls)).to_equal(1)
        expect(calls[0].data["id"]).to_equal(0)


@test
async def if_fires_on_hass_shutdown(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the firing when Home Assistant shuts down."""
    calls = async_mock_service(hass, "test", "automation")
    hass.set_state(CoreState.not_running)

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "alias": "hello",
                    "trigger": {"platform": "homeassistant", "event": "shutdown"},
                    "action": {
                        "service": "test.automation",
                        "data_template": {"id": "{{ trigger.id}}"},
                    },
                }
            },
        )
    ).to_be_truthy()
    expect(automation.is_on(hass, "automation.hello")).to_be(True)
    expect(len(calls)).to_equal(0)

    await hass.async_start()
    expect(automation.is_on(hass, "automation.hello")).to_be(True)
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(0)

    with patch.object(hass.loop, "stop"):
        await hass.async_stop()
    expect(len(calls)).to_equal(1)
    expect(calls[0].data["id"]).to_equal(0)
