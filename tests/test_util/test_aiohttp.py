"""Tests for our aiohttp mocker."""

from tryke import expect, test

from .aiohttp import AiohttpClientMocker


@test
async def matching_url() -> None:
    """Test we can match urls."""
    mocker = AiohttpClientMocker()
    mocker.get("http://example.com")
    await mocker.match_request("get", "http://example.com/")

    mocker.clear_requests()

    async def _expect_raises() -> None:
        try:
            await mocker.match_request("get", "http://example.com/")
        except AssertionError:
            return
        raise AssertionError("expected AssertionError")

    await _expect_raises()

    mocker.clear_requests()

    mocker.get("http://example.com?a=1")
    await mocker.match_request("get", "http://example.com/", params={"a": 1, "b": 2})
