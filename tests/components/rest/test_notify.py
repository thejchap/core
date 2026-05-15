"""The tests for the rest.notify platform."""

from unittest.mock import patch

import respx
from tryke import Depends, expect, fixture, test

from homeassistant import config as hass_config
from homeassistant.components import notify
from homeassistant.components.rest import DOMAIN
from homeassistant.const import SERVICE_RELOAD
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import get_fixture_path
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def reload_notify(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Verify we can reload the notify service."""
    with respx.mock:
        respx.get("http://localhost") % 200

        expect(
            await async_setup_component(
                hass,
                notify.DOMAIN,
                {
                    notify.DOMAIN: [
                        {
                            "name": DOMAIN,
                            "platform": DOMAIN,
                            "resource": "http://127.0.0.1/off",
                        },
                    ]
                },
            )
        ).to_be_truthy()
        await hass.async_block_till_done()

        expect(hass.services.has_service(notify.DOMAIN, DOMAIN)).to_be(True)

        yaml_path = get_fixture_path("configuration.yaml", "rest")

        with patch.object(hass_config, "YAML_CONFIG_FILE", yaml_path):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_RELOAD,
                {},
                blocking=True,
            )
            await hass.async_block_till_done()

        expect(hass.services.has_service(notify.DOMAIN, DOMAIN)).to_be(False)
        expect(hass.services.has_service(notify.DOMAIN, "rest_reloaded")).to_be(True)
