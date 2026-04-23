"""Tryke fixtures for NextDNS tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from nextdns import (
    AnalyticsDnssec,
    AnalyticsEncryption,
    AnalyticsIpVersions,
    AnalyticsProtocols,
    AnalyticsStatus,
    ConnectionStatus,
    ProfileInfo,
    Settings,
)
from tryke import Depends, fixture

from homeassistant.components.nextdns.const import CONF_PROFILE_ID, DOMAIN
from homeassistant.const import CONF_API_KEY

from tests.common import (
    MockConfigEntry,
    load_json_array_fixture,
    load_json_object_fixture,
)

ANALYTICS = load_json_object_fixture("analytics.json", DOMAIN)
ANALYTICS_DNSSEC = AnalyticsDnssec(**ANALYTICS["dnssec"])
ANALYTICS_ENCRYPTION = AnalyticsEncryption(**ANALYTICS["encryption"])
ANALYTICS_IP_VERSIONS = AnalyticsIpVersions(**ANALYTICS["ip_versions"])
ANALYTICS_PROTOCOLS = AnalyticsProtocols(**ANALYTICS["protocols"])
ANALYTICS_STATUS = AnalyticsStatus(**ANALYTICS["status"])
CONNECTION_STATUS = ConnectionStatus(
    **load_json_object_fixture("connection_status.json", DOMAIN)
)
PROFILES = load_json_array_fixture("profiles.json", DOMAIN)
SETTINGS = Settings(**load_json_object_fixture("settings.json", DOMAIN))


@fixture
def mock_async_zeroconf() -> Generator[MagicMock]:
    """Mock zeroconf to prevent cross-test teardown issues."""
    from zeroconf import DNSCache, Zeroconf
    from zeroconf.asyncio import AsyncZeroconf

    with patch(
        "homeassistant.components.zeroconf.HaAsyncZeroconf", spec=AsyncZeroconf
    ) as mock_aiozc:
        zc = mock_aiozc.return_value
        zc.async_unregister_service = AsyncMock()
        zc.async_register_service = AsyncMock()
        zc.async_update_service = AsyncMock()
        zc.zeroconf = Mock(spec=Zeroconf)
        zc.zeroconf.async_wait_for_start = AsyncMock()
        zc.zeroconf.cache = DNSCache()
        zc.zeroconf.done = False
        zc.async_close = AsyncMock()
        zc.ha_async_close = AsyncMock()
        yield zc


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.nextdns.async_setup_entry", return_value=True
    ) as mock:
        yield mock


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Fake Profile",
        unique_id="xyz12",
        data={CONF_API_KEY: "fake_api_key", CONF_PROFILE_ID: "xyz12"},
        entry_id="d9aa37407ddac7b964a99e86312288d6",
    )


@fixture
def mock_nextdns() -> Generator[AsyncMock]:
    """Mock the NextDns class."""
    with (
        patch(
            "homeassistant.components.nextdns.NextDns", autospec=True
        ) as mock_class,
        patch(
            "homeassistant.components.nextdns.config_flow.NextDns", new=mock_class
        ),
    ):
        yield mock_class


@fixture
def mock_nextdns_client(mock_nextdns_: AsyncMock = Depends(mock_nextdns)) -> AsyncMock:
    """Mock a NextDNS client instance."""
    client = mock_nextdns_.create.return_value
    client.clear_logs.return_value = True
    client.connection_status.return_value = CONNECTION_STATUS
    client.get_analytics_dnssec.return_value = ANALYTICS_DNSSEC
    client.get_analytics_encryption.return_value = ANALYTICS_ENCRYPTION
    client.get_analytics_ip_versions.return_value = ANALYTICS_IP_VERSIONS
    client.get_analytics_protocols.return_value = ANALYTICS_PROTOCOLS
    client.get_analytics_status.return_value = ANALYTICS_STATUS
    client.get_profile_id = Mock(return_value="xyz12")
    client.get_profile_name = Mock(return_value="Fake Profile")
    client.get_profiles.return_value = PROFILES
    client.get_settings.return_value = SETTINGS
    client.set_setting.return_value = True
    client.profiles = [ProfileInfo(**PROFILES[0])]
    return client
