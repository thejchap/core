"""The tests for generic camera component."""

from datetime import timedelta
from http import HTTPStatus
import io

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.core_config import async_process_ha_core_config
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from tests.common import async_fire_time_changed
from tests.hass_fixtures import (
    ClientSessionGenerator,
    hass as hass_fixture,
    hass_client_no_auth as hass_client_no_auth_fixture,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def bad_posting(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fixture),
) -> None:
    """Test that posting to wrong api endpoint fails."""
    await async_process_ha_core_config(
        hass,
        {"external_url": "http://example.com"},
    )

    await async_setup_component(
        hass,
        "camera",
        {
            "camera": {
                "platform": "push",
                "name": "config_test",
                "webhook_id": "camera.config_test",
            }
        },
    )
    await hass.async_block_till_done()
    expect(hass.states.get("camera.config_test") is not None).to_be(True)

    client = await hass_client_no_auth()

    async with client.post("/api/webhook/camera.config_test") as resp:
        expect(resp.status).to_equal(HTTPStatus.OK)

    camera_state = hass.states.get("camera.config_test")
    expect(camera_state.state).to_equal("idle")


@test
async def posting_url(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fixture),
) -> None:
    """Test that posting to api endpoint works."""
    await async_process_ha_core_config(
        hass,
        {"external_url": "http://example.com"},
    )

    await async_setup_component(
        hass,
        "camera",
        {
            "camera": {
                "platform": "push",
                "name": "config_test",
                "webhook_id": "camera.config_test",
            }
        },
    )
    await hass.async_block_till_done()

    client = await hass_client_no_auth()
    files = {"image": io.BytesIO(b"fake")}

    camera_state = hass.states.get("camera.config_test")
    expect(camera_state.state).to_equal("idle")

    resp = await client.post("/api/webhook/camera.config_test", data=files)
    expect(resp.status).to_equal(HTTPStatus.OK)

    camera_state = hass.states.get("camera.config_test")
    expect(camera_state.state).to_equal("recording")

    shifted_time = dt_util.utcnow() + timedelta(seconds=15)
    async_fire_time_changed(hass, shifted_time)
    await hass.async_block_till_done()

    camera_state = hass.states.get("camera.config_test")
    expect(camera_state.state).to_equal("idle")
