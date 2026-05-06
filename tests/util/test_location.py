"""Test Home Assistant location util methods."""

from collections.abc import Callable, Coroutine
import functools
from typing import Any
from unittest.mock import Mock, patch

import aiohttp
from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import location as location_util

from tests.common import async_load_fixture
from tests.hass_fixtures import aioclient_mock, hass
from tests.test_util.aiohttp import AiohttpClientMocker


def _check_real[**_P, _R](
    func: Callable[_P, Coroutine[Any, Any, _R]],
) -> Callable[_P, Coroutine[Any, Any, _R]]:
    """Force a function to require a keyword _test_real to be passed in.

    Ported from ``tests/conftest.py`` — applied locally since Tryke has
    no conftest equivalent.
    """

    @functools.wraps(func)
    async def guard_func(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        real = kwargs.pop("_test_real", None)
        if not real:
            raise RuntimeError(
                f'Forgot to mock or pass "_test_real=True" to {func.__name__}'
            )
        return await func(*args, **kwargs)

    return guard_func


location_util.async_detect_location_info = _check_real(
    location_util.async_detect_location_info
)

# Paris
COORDINATES_PARIS = (48.864716, 2.349014)
# New York
COORDINATES_NEW_YORK = (40.730610, -73.935242)

# Results for the assertion (vincenty algorithm):
#      Distance [km]   Distance [miles]
# [0]  5846.39         3632.78
# [1]  5851            3635
#
# [0]: http://boulter.com/gps/distance/
# [1]: https://www.wolframalpha.com/input/?i=from+paris+to+new+york
DISTANCE_KM = 5846.39
DISTANCE_MILES = 3632.78


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture so imported `hass` resolves via Depends()."""
    return 0


async def _session(
    hass: HomeAssistant = Depends(hass),
) -> aiohttp.ClientSession:
    """Return aioclient session.

    Not decorated with @fixture so Tryke does not auto-resolve it for
    every test in this module — only tests that explicitly
    Depends(_session) pay for the hass setup it entails.
    """
    return async_get_clientsession(hass)


async def _raising_session() -> Mock:
    """Return an aioclient session that only fails."""
    return Mock(get=Mock(side_effect=aiohttp.ClientError))


@test
def get_distance_to_same_place() -> None:
    """Test getting the distance."""
    meters = location_util.distance(
        COORDINATES_PARIS[0],
        COORDINATES_PARIS[1],
        COORDINATES_PARIS[0],
        COORDINATES_PARIS[1],
    )

    expect(meters).to_equal(0)


@test
def get_distance() -> None:
    """Test getting the distance."""
    meters = location_util.distance(
        COORDINATES_PARIS[0],
        COORDINATES_PARIS[1],
        COORDINATES_NEW_YORK[0],
        COORDINATES_NEW_YORK[1],
    )

    expect(meters / 1000 - DISTANCE_KM < 0.01).to_be(True)


@test
def get_kilometers() -> None:
    """Test getting the distance between given coordinates in km."""
    kilometers = location_util.vincenty(COORDINATES_PARIS, COORDINATES_NEW_YORK)
    expect(round(kilometers, 2)).to_equal(DISTANCE_KM)


@test
def get_miles() -> None:
    """Test getting the distance between given coordinates in miles."""
    miles = location_util.vincenty(COORDINATES_PARIS, COORDINATES_NEW_YORK, miles=True)
    expect(round(miles, 2)).to_equal(DISTANCE_MILES)


@test
async def detect_location_info_whoami(
    hass: HomeAssistant = Depends(hass),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock),
    session: aiohttp.ClientSession = Depends(_session),
) -> None:
    """Test detect location info using services.home-assistant.io/whoami."""
    aioclient_mock.get(
        location_util.WHOAMI_URL,
        text=await async_load_fixture(hass, "whoami.json"),
    )

    with patch("homeassistant.util.location.HA_VERSION", "1.0"):
        info = await location_util.async_detect_location_info(session, _test_real=True)

    expect(str(aioclient_mock.mock_calls[-1][1])).to_equal(location_util.WHOAMI_URL)

    expect(info).not_.to_be(None)
    assert info is not None
    expect(info.ip).to_equal("1.2.3.4")
    expect(info.country_code).to_equal("XX")
    expect(info.currency).to_equal("XXX")
    expect(info.region_code).to_equal("00")
    expect(info.city).to_equal("Gotham")
    expect(info.zip_code).to_equal("12345")
    expect(info.time_zone).to_equal("Earth/Gotham")
    expect(info.latitude).to_equal(12.34567)
    expect(info.longitude).to_equal(12.34567)
    expect(info.use_metric).to_be_truthy()


@test
async def dev_url(
    hass: HomeAssistant = Depends(hass),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock),
    session: aiohttp.ClientSession = Depends(_session),
) -> None:
    """Test usage of dev URL."""
    aioclient_mock.get(
        location_util.WHOAMI_URL_DEV,
        text=await async_load_fixture(hass, "whoami.json"),
    )
    with patch("homeassistant.util.location.HA_VERSION", "1.0.dev0"):
        info = await location_util.async_detect_location_info(session, _test_real=True)

    expect(str(aioclient_mock.mock_calls[-1][1])).to_equal(location_util.WHOAMI_URL_DEV)

    assert info is not None
    expect(info.currency).to_equal("XXX")


@test
async def whoami_query_raises(
    raising_session: Mock = Depends(_raising_session),
) -> None:
    """Test whoami query when the request to API fails."""
    info = await location_util._get_whoami(raising_session)
    expect(info).to_be(None)
