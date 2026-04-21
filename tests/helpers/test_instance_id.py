"""Tests for instance ID helper."""

from json import JSONDecodeError
from typing import Any
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.helpers import instance_id

from tests.hass_fixtures import LogCapture, caplog, hass, hass_storage


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def get_id_empty(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Get unique ID."""
    uuid = await instance_id.async_get(hass)
    expect(uuid).not_.to_be_none()
    # Assert it's stored
    expect(hass_storage["core.uuid"]["data"]["uuid"]).to_equal(uuid)


@test
async def get_id_load_fail(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Migrate existing file with error."""
    hass_storage["core.uuid"] = None  # Invalid, will make store.async_load raise

    uuid = await instance_id.async_get(hass)

    expect(uuid).not_.to_be_none()

    # Assert it's stored
    expect(hass_storage["core.uuid"]["data"]["uuid"]).to_equal(uuid)

    expect(
        "Could not read hass instance ID from 'core.uuid' or '.uuid', a "
        "new instance ID will be generated" in caplog.text
    ).to_be(True)


@test
async def get_id_migrate(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Migrate existing file."""
    with (
        patch("homeassistant.util.json.load_json", return_value={"uuid": "1234"}),
        patch("os.path.isfile", return_value=True),
        patch("os.remove") as mock_remove,
    ):
        uuid = await instance_id.async_get(hass)

    expect(uuid).to_equal("1234")

    # Assert it's stored
    expect(hass_storage["core.uuid"]["data"]["uuid"]).to_equal(uuid)

    # assert old deleted
    expect(len(mock_remove.mock_calls)).to_equal(1)


@test
async def get_id_migrate_fail(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Migrate existing file with error."""
    with (
        patch(
            "homeassistant.util.json.load_json",
            side_effect=JSONDecodeError("test_error", "test", 1),
        ),
        patch("os.path.isfile", return_value=True),
        patch("os.remove") as mock_remove,
    ):
        uuid = await instance_id.async_get(hass)

    expect(uuid).not_.to_be_none()

    # Assert it's stored
    expect(hass_storage["core.uuid"]["data"]["uuid"]).to_equal(uuid)

    # assert old not deleted
    expect(len(mock_remove.mock_calls)).to_equal(0)

    expect(
        "Could not read hass instance ID from 'core.uuid' or '.uuid', a "
        "new instance ID will be generated" in caplog.text
    ).to_be(True)


@test
async def async_recreate(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test recreating instance ID."""
    uuid1 = await instance_id.async_get(hass)
    uuid2 = await instance_id.async_recreate(hass)
    expect(uuid1 != uuid2).to_be(True)

    # Assert it's stored
    expect(hass_storage["core.uuid"]["data"]["uuid"]).to_equal(uuid2)
