"""Tests for the Transmission services."""

from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.transmission.const import (
    ATTR_DELETE_DATA,
    ATTR_DOWNLOAD_PATH,
    ATTR_LABELS,
    ATTR_TORRENT,
    ATTR_TORRENT_FILTER,
    ATTR_TORRENTS,
    CONF_ENTRY_ID,
    DOMAIN,
    SERVICE_ADD_TORRENT,
    SERVICE_GET_TORRENTS,
    SERVICE_REMOVE_TORRENT,
    SERVICE_START_TORRENT,
    SERVICE_STOP_TORRENT,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_ID
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError

from ._fixtures import (
    mock_config_entry,
    mock_torrent,
    mock_transmission_client,
    patch_sleep,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _patch_sleep: None = Depends(patch_sleep),
) -> int:
    """Present so tryke builds a fixture executor for this module."""
    return 0


@test
async def service_config_entry_not_loaded_state(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_transmission_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test service call when config entry is in failed state."""
    config_entry.add_to_hass(hass)

    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)

    raised: ServiceValidationError | None = None
    try:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_ADD_TORRENT,
            {
                CONF_ENTRY_ID: config_entry.entry_id,
                ATTR_TORRENT: "magnet:?xt=urn:btih:test",
            },
            blocking=True,
        )
    except ServiceValidationError as exc:
        raised = exc

    expect(raised).not_.to_be_none()
    expect(raised.translation_key).to_equal("service_not_found")


@test
async def service_integration_not_found(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_transmission_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test service call with non-existent config entry."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    raised: ServiceValidationError | None = None
    try:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_ADD_TORRENT,
            {
                CONF_ENTRY_ID: "non_existent_entry_id",
                ATTR_TORRENT: "magnet:?xt=urn:btih:test",
            },
            blocking=True,
        )
    except ServiceValidationError as exc:
        raised = exc

    expect(raised).not_.to_be_none()
    expect(raised.translation_key).to_equal("service_config_entry_not_found")


@test.cases(
    test.case(
        "magnet_with_label",
        payload={ATTR_TORRENT: "magnet:?xt=urn:btih:test", ATTR_LABELS: "Notify"},
        expected_torrent="magnet:?xt=urn:btih:test",
        kwargs={"labels": ["Notify"], "download_dir": None},
    ),
    test.case(
        "magnet_with_labels_and_path",
        payload={
            ATTR_TORRENT: "magnet:?xt=urn:btih:test",
            ATTR_LABELS: "Movies,Notify",
            ATTR_DOWNLOAD_PATH: "/custom/path",
        },
        expected_torrent="magnet:?xt=urn:btih:test",
        kwargs={"labels": ["Movies", "Notify"], "download_dir": "/custom/path"},
    ),
    test.case(
        "http_url",
        payload={ATTR_TORRENT: "http://example.com/test.torrent"},
        expected_torrent="http://example.com/test.torrent",
        kwargs={"labels": None, "download_dir": None},
    ),
    test.case(
        "ftp_url",
        payload={ATTR_TORRENT: "ftp://example.com/test.torrent"},
        expected_torrent="ftp://example.com/test.torrent",
        kwargs={"labels": None, "download_dir": None},
    ),
    test.case(
        "local_path",
        payload={ATTR_TORRENT: "/config/test.torrent"},
        expected_torrent="/config/test.torrent",
        kwargs={"labels": None, "download_dir": None},
    ),
)
async def add_torrent_service_success(
    payload: dict[str, str],
    expected_torrent: str,
    kwargs: dict[str, str | None],
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_class: AsyncMock = Depends(mock_transmission_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test successful torrent addition with url and path sources."""
    client = client_class.return_value
    client.add_torrent.return_value = MagicMock(id=123, name="test_torrent")

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    full_service_data = {CONF_ENTRY_ID: config_entry.entry_id} | payload

    with patch.object(hass.config, "is_allowed_path", return_value=True):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_ADD_TORRENT,
            full_service_data,
            blocking=True,
        )

    client.add_torrent.assert_called_once_with(expected_torrent, **kwargs)


@test
async def add_torrent_service_invalid_path(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_transmission_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test torrent addition with invalid path."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    raised: ServiceValidationError | None = None
    try:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_ADD_TORRENT,
            {
                CONF_ENTRY_ID: config_entry.entry_id,
                ATTR_TORRENT: "/etc/bad.torrent",
            },
            blocking=True,
        )
    except ServiceValidationError as exc:
        raised = exc

    expect(raised).not_.to_be_none()
    expect(raised.translation_key).to_equal("could_not_add_torrent")


@test
async def start_torrent_service_success(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_class: AsyncMock = Depends(mock_transmission_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test successful torrent start."""
    client = client_class.return_value

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN,
        SERVICE_START_TORRENT,
        {
            CONF_ENTRY_ID: config_entry.entry_id,
            CONF_ID: 123,
        },
        blocking=True,
    )

    client.start_torrent.assert_called_once_with(123)


@test
async def stop_torrent_service_success(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_class: AsyncMock = Depends(mock_transmission_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test successful torrent stop."""
    client = client_class.return_value

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN,
        SERVICE_STOP_TORRENT,
        {
            CONF_ENTRY_ID: config_entry.entry_id,
            CONF_ID: 456,
        },
        blocking=True,
    )

    client.stop_torrent.assert_called_once_with(456)


@test
async def remove_torrent_service_success(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_class: AsyncMock = Depends(mock_transmission_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test successful torrent removal without deleting data."""
    client = client_class.return_value

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN,
        SERVICE_REMOVE_TORRENT,
        {
            CONF_ENTRY_ID: config_entry.entry_id,
            CONF_ID: 789,
        },
        blocking=True,
    )

    client.remove_torrent.assert_called_once_with(789, delete_data=False)


@test
async def remove_torrent_service_with_delete_data(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_class: AsyncMock = Depends(mock_transmission_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test successful torrent removal with deleting data."""
    client = client_class.return_value

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN,
        SERVICE_REMOVE_TORRENT,
        {
            CONF_ENTRY_ID: config_entry.entry_id,
            CONF_ID: 789,
            ATTR_DELETE_DATA: True,
        },
        blocking=True,
    )

    client.remove_torrent.assert_called_once_with(789, delete_data=True)


@test.cases(
    test.case("all", filter_mode="all", expected_statuses=["seeding", "downloading", "stopped"], expected_torrents=[1, 2, 3]),
    test.case("started", filter_mode="started", expected_statuses=["downloading"], expected_torrents=[1]),
    test.case("completed", filter_mode="completed", expected_statuses=["seeding"], expected_torrents=[2]),
    test.case("paused", filter_mode="paused", expected_statuses=["stopped"], expected_torrents=[3]),
    test.case("active", filter_mode="active", expected_statuses=["seeding", "downloading"], expected_torrents=[1, 2]),
)
async def get_torrents_service(
    filter_mode: str,
    expected_statuses: list[str],
    expected_torrents: list[int],
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_class: AsyncMock = Depends(mock_transmission_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    make_torrent=Depends(mock_torrent),
) -> None:
    """Test get torrents service with various filter modes."""
    client = client_class.return_value

    downloading_torrent = make_torrent(torrent_id=1, name="Downloading", status=4)
    seeding_torrent = make_torrent(torrent_id=2, name="Seeding", status=6)
    stopped_torrent = make_torrent(torrent_id=3, name="Stopped", status=0)

    client.get_torrents.return_value = [
        downloading_torrent,
        seeding_torrent,
        stopped_torrent,
    ]

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    response = await hass.services.async_call(
        DOMAIN,
        SERVICE_GET_TORRENTS,
        {
            CONF_ENTRY_ID: config_entry.entry_id,
            ATTR_TORRENT_FILTER: filter_mode,
        },
        blocking=True,
        return_response=True,
    )

    expect(response).not_.to_be_none()
    expect(ATTR_TORRENTS in response).to_be_truthy()
    torrents = response[ATTR_TORRENTS]
    expect(isinstance(torrents, dict)).to_be_truthy()

    expect(len(torrents)).to_equal(len(expected_statuses))

    remaining = list(expected_torrents)
    for torrent_name, torrent_data in torrents.items():
        expect(isinstance(torrent_data, dict)).to_be_truthy()
        expect("id" in torrent_data).to_be_truthy()
        expect("name" in torrent_data).to_be_truthy()
        expect("status" in torrent_data).to_be_truthy()
        expect(torrent_data["name"]).to_equal(torrent_name)
        expect(torrent_data["id"] in remaining).to_be_truthy()
        remaining.remove(int(torrent_data["id"]))

    expect(len(remaining)).to_equal(0)
