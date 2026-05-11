"""Test pushbullet notification platform."""

from http import HTTPStatus

from requests_mock import Mocker
from tryke import Depends, expect, fixture, test

from homeassistant.components.notify import DOMAIN as NOTIFY_DOMAIN
from homeassistant.components.pushbullet.const import DOMAIN
from homeassistant.core import HomeAssistant

from . import MOCK_CONFIG
from ._fixtures import requests_mock_fixture

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
def _trigger_executor(
    _rm: Mocker = Depends(requests_mock_fixture),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def pushbullet_push_default(
    hass: HomeAssistant = Depends(hass_fixture),
    requests_mock: Mocker = Depends(requests_mock_fixture),
) -> None:
    """Test pushbullet push to default target."""
    requests_mock.register_uri(
        "POST",
        "https://api.pushbullet.com/v2/pushes",
        status_code=HTTPStatus.OK,
        json={"mock_response": "Ok"},
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
    )
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    data = {"title": "Test Title", "message": "Test Message"}
    await hass.services.async_call(NOTIFY_DOMAIN, "pushbullet", data)
    await hass.async_block_till_done()

    expected_body = {"body": "Test Message", "title": "Test Title", "type": "note"}
    expect(requests_mock.last_request).not_.to_be(None)
    expect(requests_mock.last_request.json()).to_equal(expected_body)


@test
async def pushbullet_push_device(
    hass: HomeAssistant = Depends(hass_fixture),
    requests_mock: Mocker = Depends(requests_mock_fixture),
) -> None:
    """Test pushbullet push to default target."""
    requests_mock.register_uri(
        "POST",
        "https://api.pushbullet.com/v2/pushes",
        status_code=HTTPStatus.OK,
        json={"mock_response": "Ok"},
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
    )
    entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    data = {
        "title": "Test Title",
        "message": "Test Message",
        "target": ["device/DESKTOP"],
    }
    await hass.services.async_call(NOTIFY_DOMAIN, "pushbullet", data)
    await hass.async_block_till_done()

    expected_body = {
        "body": "Test Message",
        "device_iden": "identity1",
        "title": "Test Title",
        "type": "note",
    }
    expect(requests_mock.last_request.json()).to_equal(expected_body)


@test
async def pushbullet_push_devices(
    hass: HomeAssistant = Depends(hass_fixture),
    requests_mock: Mocker = Depends(requests_mock_fixture),
) -> None:
    """Test pushbullet push to default target."""
    requests_mock.register_uri(
        "POST",
        "https://api.pushbullet.com/v2/pushes",
        status_code=HTTPStatus.OK,
        json={"mock_response": "Ok"},
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
    )
    entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    data = {
        "title": "Test Title",
        "message": "Test Message",
        "target": ["device/DESKTOP", "device/My iPhone"],
    }
    await hass.services.async_call(NOTIFY_DOMAIN, "pushbullet", data)
    await hass.async_block_till_done()

    expected_body = {
        "body": "Test Message",
        "device_iden": "identity1",
        "title": "Test Title",
        "type": "note",
    }
    expect(requests_mock.request_history[-2].json()).to_equal(expected_body)
    expected_body = {
        "body": "Test Message",
        "device_iden": "identity2",
        "title": "Test Title",
        "type": "note",
    }
    expect(requests_mock.request_history[-1].json()).to_equal(expected_body)


@test
async def pushbullet_push_email(
    hass: HomeAssistant = Depends(hass_fixture),
    requests_mock: Mocker = Depends(requests_mock_fixture),
) -> None:
    """Test pushbullet push to default target."""
    requests_mock.register_uri(
        "POST",
        "https://api.pushbullet.com/v2/pushes",
        status_code=HTTPStatus.OK,
        json={"mock_response": "Ok"},
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
    )
    entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    data = {
        "title": "Test Title",
        "message": "Test Message",
        "target": ["email/user@host.net"],
    }
    await hass.services.async_call(NOTIFY_DOMAIN, "pushbullet", data)
    await hass.async_block_till_done()

    expected_body = {
        "body": "Test Message",
        "email": "user@host.net",
        "title": "Test Title",
        "type": "note",
    }
    expect(requests_mock.last_request.json()).to_equal(expected_body)


@test
async def pushbullet_push_mixed(
    hass: HomeAssistant = Depends(hass_fixture),
    requests_mock: Mocker = Depends(requests_mock_fixture),
) -> None:
    """Test pushbullet push to default target."""
    requests_mock.register_uri(
        "POST",
        "https://api.pushbullet.com/v2/pushes",
        status_code=HTTPStatus.OK,
        json={"mock_response": "Ok"},
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
    )
    entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    data = {
        "title": "Test Title",
        "message": "Test Message",
        "target": ["device/DESKTOP", "email/user@host.net"],
    }

    await hass.services.async_call(NOTIFY_DOMAIN, "pushbullet", data)
    await hass.async_block_till_done()

    expected_body = {
        "body": "Test Message",
        "device_iden": "identity1",
        "title": "Test Title",
        "type": "note",
    }
    expect(requests_mock.request_history[-2].json()).to_equal(expected_body)
    expected_body = {
        "body": "Test Message",
        "email": "user@host.net",
        "title": "Test Title",
        "type": "note",
    }
    expect(requests_mock.request_history[-1].json()).to_equal(expected_body)
