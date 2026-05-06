"""Tryke fixtures for the TelldusLive integration tests."""

from collections.abc import Generator
from unittest.mock import patch

from tryke import fixture


def _make_mock(supports_local_api: bool, authorize: bool):
    """Build the patch context."""
    return (
        patch("homeassistant.components.tellduslive.config_flow.Session"),
        patch("homeassistant.components.tellduslive.config_flow.supports_local_api"),
    )


@fixture
def mock_tellduslive() -> Generator:
    """Mock tellduslive with default supports_local_api=True, authorize=True."""
    with (
        patch("homeassistant.components.tellduslive.config_flow.Session") as Session,
        patch(
            "homeassistant.components.tellduslive.config_flow.supports_local_api"
        ) as tellduslive_supports_local_api,
    ):
        tellduslive_supports_local_api.return_value = True
        Session().authorize.return_value = True
        Session().access_token = "token"
        Session().access_token_secret = "token_secret"
        Session().authorize_url = "https://example.com"
        yield Session, tellduslive_supports_local_api


@fixture
def mock_tellduslive_no_local_api() -> Generator:
    """Mock tellduslive with supports_local_api=False."""
    with (
        patch("homeassistant.components.tellduslive.config_flow.Session") as Session,
        patch(
            "homeassistant.components.tellduslive.config_flow.supports_local_api"
        ) as tellduslive_supports_local_api,
    ):
        tellduslive_supports_local_api.return_value = False
        Session().authorize.return_value = True
        Session().access_token = "token"
        Session().access_token_secret = "token_secret"
        Session().authorize_url = "https://example.com"
        yield Session, tellduslive_supports_local_api


@fixture
def mock_tellduslive_unauthorized() -> Generator:
    """Mock tellduslive with authorize=False."""
    with (
        patch("homeassistant.components.tellduslive.config_flow.Session") as Session,
        patch(
            "homeassistant.components.tellduslive.config_flow.supports_local_api"
        ) as tellduslive_supports_local_api,
    ):
        tellduslive_supports_local_api.return_value = True
        Session().authorize.return_value = False
        Session().access_token = "token"
        Session().access_token_secret = "token_secret"
        Session().authorize_url = "https://example.com"
        yield Session, tellduslive_supports_local_api
