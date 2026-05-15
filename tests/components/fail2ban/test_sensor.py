"""The tests for local file sensor platform."""

from unittest.mock import Mock, mock_open, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.fail2ban.sensor import (
    STATE_ALL_BANS,
    STATE_CURRENT_BANS,
    BanLogParser,
    BanSensor,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import assert_setup_component
from tests.hass_fixtures import hass as hass_fixture, mock_network


def fake_log(log_key):
    """Return a fake fail2ban log."""
    fake_log_dict = {
        "single_ban": (
            "2017-01-01 12:23:35 fail2ban.actions [111]: "
            "NOTICE [jail_one] Ban 111.111.111.111"
        ),
        "ipv6_ban": (
            "2017-01-01 12:23:35 fail2ban.actions [111]: "
            "NOTICE [jail_one] Ban 2607:f0d0:1002:51::4"
        ),
        "multi_ban": (
            "2017-01-01 12:23:35 fail2ban.actions [111]: "
            "NOTICE [jail_one] Ban 111.111.111.111\n"
            "2017-01-01 12:23:35 fail2ban.actions [111]: "
            "NOTICE [jail_one] Ban 222.222.222.222"
        ),
        "multi_jail": (
            "2017-01-01 12:23:35 fail2ban.actions [111]: "
            "NOTICE [jail_one] Ban 111.111.111.111\n"
            "2017-01-01 12:23:35 fail2ban.actions [111]: "
            "NOTICE [jail_two] Ban 222.222.222.222"
        ),
        "unban_all": (
            "2017-01-01 12:23:35 fail2ban.actions [111]: "
            "NOTICE [jail_one] Ban 111.111.111.111\n"
            "2017-01-01 12:23:35 fail2ban.actions [111]: "
            "NOTICE [jail_one] Unban 111.111.111.111\n"
            "2017-01-01 12:23:35 fail2ban.actions [111]: "
            "NOTICE [jail_one] Ban 222.222.222.222\n"
            "2017-01-01 12:23:35 fail2ban.actions [111]: "
            "NOTICE [jail_one] Unban 222.222.222.222"
        ),
        "unban_one": (
            "2017-01-01 12:23:35 fail2ban.actions [111]: "
            "NOTICE [jail_one] Ban 111.111.111.111\n"
            "2017-01-01 12:23:35 fail2ban.actions [111]: "
            "NOTICE [jail_one] Ban 222.222.222.222\n"
            "2017-01-01 12:23:35 fail2ban.actions [111]: "
            "NOTICE [jail_one] Unban 111.111.111.111"
        ),
    }
    return fake_log_dict[log_key]


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture so tryke fully resolves Depends across the module."""


@test
async def setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that sensor can be setup."""
    config = {"sensor": {"platform": "fail2ban", "jails": ["jail_one"]}}
    mock_fh = mock_open()
    with (
        patch("os.path.isfile", Mock(return_value=True)),
        patch("homeassistant.components.fail2ban.sensor.open", mock_fh, create=True),
    ):
        expect(await async_setup_component(hass, "sensor", config)).to_be(True)
        await hass.async_block_till_done()
    assert_setup_component(1, "sensor")


@test
async def multi_jails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that multiple jails can be set up as sensors.."""
    config = {"sensor": {"platform": "fail2ban", "jails": ["jail_one", "jail_two"]}}
    mock_fh = mock_open()
    with (
        patch("os.path.isfile", Mock(return_value=True)),
        patch("homeassistant.components.fail2ban.sensor.open", mock_fh, create=True),
    ):
        expect(await async_setup_component(hass, "sensor", config)).to_be(True)
        await hass.async_block_till_done()
    assert_setup_component(2, "sensor")


@test
async def single_ban(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that log is parsed correctly for single ban."""
    log_parser = BanLogParser("/test/fail2ban.log")
    sensor = BanSensor("fail2ban", "jail_one", log_parser)
    sensor.hass = hass
    expect(sensor.name).to_equal("fail2ban jail_one")
    mock_fh = mock_open(read_data=fake_log("single_ban"))
    with patch("homeassistant.components.fail2ban.sensor.open", mock_fh, create=True):
        sensor.update()

    expect(sensor.state).to_equal("111.111.111.111")
    expect(sensor.extra_state_attributes[STATE_CURRENT_BANS]).to_equal(
        ["111.111.111.111"]
    )
    expect(sensor.extra_state_attributes[STATE_ALL_BANS]).to_equal(["111.111.111.111"])


@test
async def ipv6_ban(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that log is parsed correctly for IPV6 bans."""
    log_parser = BanLogParser("/test/fail2ban.log")
    sensor = BanSensor("fail2ban", "jail_one", log_parser)
    sensor.hass = hass
    expect(sensor.name).to_equal("fail2ban jail_one")
    mock_fh = mock_open(read_data=fake_log("ipv6_ban"))
    with patch("homeassistant.components.fail2ban.sensor.open", mock_fh, create=True):
        sensor.update()

    expect(sensor.state).to_equal("2607:f0d0:1002:51::4")
    expect(sensor.extra_state_attributes[STATE_CURRENT_BANS]).to_equal(
        ["2607:f0d0:1002:51::4"]
    )
    expect(sensor.extra_state_attributes[STATE_ALL_BANS]).to_equal(
        ["2607:f0d0:1002:51::4"]
    )


@test
async def multiple_ban(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that log is parsed correctly for multiple ban."""
    log_parser = BanLogParser("/test/fail2ban.log")
    sensor = BanSensor("fail2ban", "jail_one", log_parser)
    sensor.hass = hass
    expect(sensor.name).to_equal("fail2ban jail_one")
    mock_fh = mock_open(read_data=fake_log("multi_ban"))
    with patch("homeassistant.components.fail2ban.sensor.open", mock_fh, create=True):
        sensor.update()

    expect(sensor.state).to_equal("222.222.222.222")
    expect(sensor.extra_state_attributes[STATE_CURRENT_BANS]).to_equal(
        ["111.111.111.111", "222.222.222.222"]
    )
    expect(sensor.extra_state_attributes[STATE_ALL_BANS]).to_equal(
        ["111.111.111.111", "222.222.222.222"]
    )


@test
async def unban_all(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that log is parsed correctly when unbanning."""
    log_parser = BanLogParser("/test/fail2ban.log")
    sensor = BanSensor("fail2ban", "jail_one", log_parser)
    sensor.hass = hass
    expect(sensor.name).to_equal("fail2ban jail_one")
    mock_fh = mock_open(read_data=fake_log("unban_all"))
    with patch("homeassistant.components.fail2ban.sensor.open", mock_fh, create=True):
        sensor.update()

    expect(sensor.state).to_equal("None")
    expect(sensor.extra_state_attributes[STATE_CURRENT_BANS]).to_equal([])
    expect(sensor.extra_state_attributes[STATE_ALL_BANS]).to_equal(
        ["111.111.111.111", "222.222.222.222"]
    )


@test
async def unban_one(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that log is parsed correctly when unbanning one ip."""
    log_parser = BanLogParser("/test/fail2ban.log")
    sensor = BanSensor("fail2ban", "jail_one", log_parser)
    sensor.hass = hass
    expect(sensor.name).to_equal("fail2ban jail_one")
    mock_fh = mock_open(read_data=fake_log("unban_one"))
    with patch("homeassistant.components.fail2ban.sensor.open", mock_fh, create=True):
        sensor.update()

    expect(sensor.state).to_equal("222.222.222.222")
    expect(sensor.extra_state_attributes[STATE_CURRENT_BANS]).to_equal(
        ["222.222.222.222"]
    )
    expect(sensor.extra_state_attributes[STATE_ALL_BANS]).to_equal(
        ["111.111.111.111", "222.222.222.222"]
    )


@test
async def multi_jail(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that log is parsed correctly when using multiple jails."""
    log_parser = BanLogParser("/test/fail2ban.log")
    sensor1 = BanSensor("fail2ban", "jail_one", log_parser)
    sensor2 = BanSensor("fail2ban", "jail_two", log_parser)
    sensor1.hass = hass
    sensor2.hass = hass
    expect(sensor1.name).to_equal("fail2ban jail_one")
    expect(sensor2.name).to_equal("fail2ban jail_two")
    mock_fh = mock_open(read_data=fake_log("multi_jail"))
    with patch("homeassistant.components.fail2ban.sensor.open", mock_fh, create=True):
        sensor1.update()
        sensor2.update()

    expect(sensor1.state).to_equal("111.111.111.111")
    expect(sensor1.extra_state_attributes[STATE_CURRENT_BANS]).to_equal(
        ["111.111.111.111"]
    )
    expect(sensor1.extra_state_attributes[STATE_ALL_BANS]).to_equal(
        ["111.111.111.111"]
    )
    expect(sensor2.state).to_equal("222.222.222.222")
    expect(sensor2.extra_state_attributes[STATE_CURRENT_BANS]).to_equal(
        ["222.222.222.222"]
    )
    expect(sensor2.extra_state_attributes[STATE_ALL_BANS]).to_equal(
        ["222.222.222.222"]
    )


@test
async def ban_active_after_update(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that ban persists after subsequent update."""
    log_parser = BanLogParser("/test/fail2ban.log")
    sensor = BanSensor("fail2ban", "jail_one", log_parser)
    sensor.hass = hass
    expect(sensor.name).to_equal("fail2ban jail_one")
    mock_fh = mock_open(read_data=fake_log("single_ban"))
    with patch("homeassistant.components.fail2ban.sensor.open", mock_fh, create=True):
        sensor.update()
        expect(sensor.state).to_equal("111.111.111.111")
        sensor.update()
        expect(sensor.state).to_equal("111.111.111.111")
    expect(sensor.extra_state_attributes[STATE_CURRENT_BANS]).to_equal(
        ["111.111.111.111"]
    )
    expect(sensor.extra_state_attributes[STATE_ALL_BANS]).to_equal(["111.111.111.111"])
