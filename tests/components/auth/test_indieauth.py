"""Tests for the client validator."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.auth import indieauth
from homeassistant.core import HomeAssistant

from ._fixtures import mock_session as mock_session_fx

from tests.hass_fixtures import hass as hass_fx, mock_network
from tests.hass_tryke_helpers import expect_raises_async
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
    return 0


@test
def client_id_scheme() -> None:
    """Test we enforce valid scheme."""
    expect(indieauth._parse_client_id("http://ex.com/")).to_be_truthy()
    expect(indieauth._parse_client_id("https://ex.com/")).to_be_truthy()

    expect(lambda: indieauth._parse_client_id("ftp://ex.com")).to_raise(ValueError)


@test
def client_id_path() -> None:
    """Test we enforce valid path."""
    expect(indieauth._parse_client_id("http://ex.com").path).to_equal("/")
    expect(indieauth._parse_client_id("http://ex.com/hello").path).to_equal("/hello")
    expect(
        indieauth._parse_client_id("http://ex.com/hello/.world").path
    ).to_equal("/hello/.world")
    expect(
        indieauth._parse_client_id("http://ex.com/hello./.world").path
    ).to_equal("/hello./.world")

    expect(lambda: indieauth._parse_client_id("http://ex.com/.")).to_raise(ValueError)
    expect(
        lambda: indieauth._parse_client_id("http://ex.com/hello/./yo")
    ).to_raise(ValueError)
    expect(
        lambda: indieauth._parse_client_id("http://ex.com/hello/../yo")
    ).to_raise(ValueError)


@test
def client_id_fragment() -> None:
    """Test we enforce valid fragment."""
    expect(lambda: indieauth._parse_client_id("http://ex.com/#yoo")).to_raise(
        ValueError
    )


@test
def client_id_user_pass() -> None:
    """Test we enforce valid username/password."""
    expect(lambda: indieauth._parse_client_id("http://user@ex.com/")).to_raise(
        ValueError
    )
    expect(
        lambda: indieauth._parse_client_id("http://user:pass@ex.com/")
    ).to_raise(ValueError)


@test
def client_id_hostname() -> None:
    """Test we enforce valid hostname."""
    expect(indieauth._parse_client_id("http://www.home-assistant.io/")).to_be_truthy()
    expect(indieauth._parse_client_id("http://[::1]")).to_be_truthy()
    expect(indieauth._parse_client_id("http://127.0.0.1")).to_be_truthy()
    expect(indieauth._parse_client_id("http://10.0.0.0")).to_be_truthy()
    expect(indieauth._parse_client_id("http://10.255.255.255")).to_be_truthy()
    expect(indieauth._parse_client_id("http://172.16.0.0")).to_be_truthy()
    expect(indieauth._parse_client_id("http://172.31.255.255")).to_be_truthy()
    expect(indieauth._parse_client_id("http://192.168.0.0")).to_be_truthy()
    expect(indieauth._parse_client_id("http://192.168.255.255")).to_be_truthy()

    expect(
        lambda: indieauth._parse_client_id("http://255.255.255.255/")
    ).to_raise(ValueError)
    expect(lambda: indieauth._parse_client_id("http://11.0.0.0/")).to_raise(ValueError)
    expect(lambda: indieauth._parse_client_id("http://172.32.0.0/")).to_raise(
        ValueError
    )
    expect(lambda: indieauth._parse_client_id("http://192.167.0.0/")).to_raise(
        ValueError
    )


@test
def parse_url_lowercase_host() -> None:
    """Test we update empty paths."""
    expect(indieauth._parse_url("http://ex.com/hello").path).to_equal("/hello")
    expect(indieauth._parse_url("http://EX.COM/hello").hostname).to_equal("ex.com")

    parts = indieauth._parse_url("http://EX.COM:123/HELLO")
    expect(parts.netloc).to_equal("ex.com:123")
    expect(parts.path).to_equal("/HELLO")


@test
def parse_url_path() -> None:
    """Test we update empty paths."""
    expect(indieauth._parse_url("http://ex.com").path).to_equal("/")


@test
async def verify_redirect_uri(
    _trigger: int = Depends(_trigger_executor),
) -> None:
    """Test that we verify redirect uri correctly."""
    expect(
        await indieauth.verify_redirect_uri(
            None, "http://ex.com", "http://ex.com/callback"
        )
    ).to_be_truthy()

    with patch.object(indieauth, "fetch_redirect_uris", return_value=[]):
        # Different domain
        expect(
            await indieauth.verify_redirect_uri(
                None, "http://ex.com", "http://different.com/callback"
            )
        ).to_be_falsy()

        # Different scheme
        expect(
            await indieauth.verify_redirect_uri(
                None, "http://ex.com", "https://ex.com/callback"
            )
        ).to_be_falsy()

        # Different subdomain
        expect(
            await indieauth.verify_redirect_uri(
                None, "https://sub1.ex.com", "https://sub2.ex.com/callback"
            )
        ).to_be_falsy()


@test
async def find_link_tag(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    mock_session: AiohttpClientMocker = Depends(mock_session_fx),
) -> None:
    """Test finding link tag."""
    mock_session.get(
        "http://127.0.0.1:8000",
        text="""
<!doctype html>
<html>
  <head>
    <link rel="redirect_uri" href="hass://oauth2_redirect">
    <link rel="other_value" href="hass://oauth2_redirect">
    <link rel="redirect_uri" href="/beer">
  </head>
  ...
</html>
""",
    )
    redirect_uris = await indieauth.fetch_redirect_uris(hass, "http://127.0.0.1:8000")

    expect(redirect_uris).to_equal(
        ["hass://oauth2_redirect", "http://127.0.0.1:8000/beer"]
    )


@test
async def find_link_tag_max_size(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    mock_session: AiohttpClientMocker = Depends(mock_session_fx),
) -> None:
    """Test finding link tag."""
    text = "".join(
        [
            '<link rel="redirect_uri" href="/wine">',
            ("0" * 1024 * 10),
            '<link rel="redirect_uri" href="/beer">',
        ]
    )
    mock_session.get("http://127.0.0.1:8000", text=text)
    redirect_uris = await indieauth.fetch_redirect_uris(hass, "http://127.0.0.1:8000")

    expect(redirect_uris).to_equal(["http://127.0.0.1:8000/wine"])


@test.cases(
    test.case("android", client_id="https://home-assistant.io/android"),
    test.case("ios", client_id="https://home-assistant.io/iOS"),
)
async def verify_redirect_uri_android_ios(
    client_id: str,
    _trigger: int = Depends(_trigger_executor),
) -> None:
    """Test that we verify redirect uri correctly for Android/iOS."""
    with patch.object(indieauth, "fetch_redirect_uris", return_value=[]):
        expect(
            await indieauth.verify_redirect_uri(
                None, client_id, "homeassistant://auth-callback"
            )
        ).to_be_truthy()

        expect(
            await indieauth.verify_redirect_uri(
                None, client_id, "homeassistant://something-else"
            )
        ).to_be_falsy()

        expect(
            await indieauth.verify_redirect_uri(
                None, "https://incorrect.com", "homeassistant://auth-callback"
            )
        ).to_be_falsy()

        if client_id == "https://home-assistant.io/android":
            expect(
                await indieauth.verify_redirect_uri(
                    None,
                    client_id,
                    "https://wear.googleapis.com/3p_auth/io.homeassistant.companion.android",
                )
            ).to_be_truthy()
            expect(
                await indieauth.verify_redirect_uri(
                    None,
                    client_id,
                    "https://wear.googleapis-cn.com/3p_auth/io.homeassistant.companion.android",
                )
            ).to_be_truthy()
        else:
            expect(
                await indieauth.verify_redirect_uri(
                    None,
                    client_id,
                    "https://wear.googleapis.com/3p_auth/io.homeassistant.companion.android",
                )
            ).to_be_falsy()
            expect(
                await indieauth.verify_redirect_uri(
                    None,
                    client_id,
                    "https://wear.googleapis-cn.com/3p_auth/io.homeassistant.companion.android",
                )
            ).to_be_falsy()
