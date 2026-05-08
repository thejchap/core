"""Tryke fixtures for the PlayStation Network integration."""

from collections.abc import Generator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

from psnawp_api.models import User
from psnawp_api.models.group.group import Group
from psnawp_api.models.trophies import (
    PlatformType,
    TrophySet,
    TrophySummary,
    TrophyTitle,
)
from tryke import Depends, fixture

from homeassistant.components.playstation_network.const import CONF_NPSSO, DOMAIN
from homeassistant.config_entries import ConfigSubentryData

from tests.common import MockConfigEntry

NPSSO_TOKEN: str = "npsso-token"
NPSSO_TOKEN_INVALID_JSON: str = "{'npsso': 'npsso-token'"
PSN_ID: str = "my-psn-id"


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Mock PlayStation Network configuration entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="test-user",
        data={
            CONF_NPSSO: NPSSO_TOKEN,
        },
        unique_id=PSN_ID,
        subentries_data=[
            ConfigSubentryData(
                data={},
                subentry_id="ABCDEF",
                subentry_type="friend",
                title="PublicUniversalFriend",
                unique_id="fren-psn-id",
            )
        ],
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.playstation_network.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_user() -> Generator[MagicMock]:
    """Mock psnawp_api User object."""
    with patch(
        "homeassistant.components.playstation_network.helpers.User",
        autospec=True,
    ) as mock_client:
        client = mock_client.return_value

        client.account_id = PSN_ID
        client.online_id = "testuser"

        client.get_presence.return_value = {
            "basicPresence": {
                "availability": "availableToPlay",
                "primaryPlatformInfo": {"onlineStatus": "online", "platform": "PS5"},
                "gameTitleInfoList": [],
                "lastAvailableDate": "2025-06-30T01:42:15.391Z",
            }
        }
        yield client


@fixture
def mock_psnawpapi(
    mock_user: MagicMock = Depends(mock_user),
) -> Generator[MagicMock]:
    """Mock psnawp_api."""
    with patch(
        "homeassistant.components.playstation_network.helpers.PSNAWP",
        autospec=True,
    ) as mock_client:
        client = mock_client.return_value

        client.user.return_value = mock_user
        client.me.return_value.get_account_devices.return_value = [
            {"deviceType": "PSVITA"},
        ]
        client.me.return_value.trophy_summary.return_value = TrophySummary(
            PSN_ID, 1079, 19, 10, TrophySet(14450, 8722, 11754, 1398)
        )
        client.user.return_value.profile.return_value = {
            "onlineId": "testuser",
            "personalDetail": {
                "firstName": "Rick",
                "lastName": "Astley",
                "profilePictures": [
                    {"size": "xl", "url": "http://example.com/xl.png"}
                ],
            },
            "aboutMe": "",
            "avatars": [{"size": "xl", "url": "http://example.com/xl.png"}],
            "languages": ["en-US"],
            "isPlus": True,
            "isOfficiallyVerified": False,
            "isMe": True,
        }
        client.user.return_value.trophy_titles.return_value = []
        client.me.return_value.get_profile_legacy.return_value = {
            "profile": {"presences": []}
        }
        client.me.return_value.get_shareable_profile_link.return_value = {
            "shareImageUrl": "https://example.com/profile.png"
        }
        group = MagicMock(spec=Group, group_id="test-groupid")
        group.get_group_information.return_value = {
            "groupName": {"value": ""},
            "members": [],
        }
        client.me.return_value.get_groups.return_value = [group]
        fren = MagicMock(
            spec=User, account_id="fren-psn-id", online_id="PublicUniversalFriend"
        )
        fren.get_presence.return_value = mock_user.get_presence.return_value
        fren.trophy_summary.return_value = TrophySummary(
            "fren-psn-id", 420, 20, 5, TrophySet(4782, 1245, 437, 96)
        )
        client.user.return_value.friends_list.return_value = [fren]
        yield client


@fixture
def mock_psnawp_npsso() -> Generator[MagicMock]:
    """Mock npsso parsing."""
    with patch(
        "homeassistant.components.playstation_network.config_flow.parse_npsso_token",
        side_effect=lambda token: token,
    ) as npsso:
        yield npsso
