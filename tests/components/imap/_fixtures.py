"""Tryke fixtures for the imap integration."""

from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

from aioimaplib import AUTH, LOGOUT, NONAUTH, SELECTED, STARTED, Response
from tryke import Depends, fixture

from .const import EMPTY_SEARCH_RESPONSE, TEST_FETCH_RESPONSE_TEXT_PLAIN


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.imap.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def imap_has_capability() -> bool:
    """Fixture to set the imap capabilities."""
    return True


@fixture
def imap_login_state() -> str:
    """Fixture to set the imap state after login."""
    return AUTH


@fixture
def imap_select_state() -> str:
    """Fixture to set the imap capabilities."""
    return SELECTED


@fixture
def imap_search() -> tuple[str, list[bytes]]:
    """Fixture to set the imap search response."""
    return EMPTY_SEARCH_RESPONSE


@fixture
def imap_fetch() -> tuple[str, list[bytes | bytearray]]:
    """Fixture to set the imap fetch response."""
    return TEST_FETCH_RESPONSE_TEXT_PLAIN


@fixture
def imap_pending_idle() -> bool:
    """Fixture to set the imap pending idle feature."""
    return True


@fixture
async def mock_imap_protocol(
    imap_search: tuple[str, list[bytes]] = Depends(imap_search),
    imap_fetch: tuple[str, list[bytes | bytearray]] = Depends(imap_fetch),
    imap_has_capability: bool = Depends(imap_has_capability),
    imap_pending_idle: bool = Depends(imap_pending_idle),
    imap_login_state: str = Depends(imap_login_state),
    imap_select_state: str = Depends(imap_select_state),
) -> AsyncGenerator[MagicMock]:
    """Mock the aioimaplib IMAP protocol handler."""
    with patch(
        "homeassistant.components.imap.coordinator.IMAP4_SSL", autospec=True
    ) as imap_mock:
        imap_mock = imap_mock.return_value

        async def login(user: str, password: str) -> Response:
            imap_mock.protocol.state = imap_login_state
            if imap_login_state != AUTH:
                return Response("BAD", [])
            return Response("OK", [b"CAPABILITY IMAP4rev1 ...", b"Logged in"])

        async def close() -> Response:
            return Response("OK", [])

        async def store(uid: str, flags: str) -> Response:
            return Response("OK", [])

        async def copy(uid: str, folder: str) -> Response:
            return Response("OK", [])

        async def logout() -> Response:
            imap_mock.protocol.state = LOGOUT
            return Response("OK", [])

        async def select(mailbox: str = "INBOX") -> Response:
            imap_mock.protocol.state = imap_select_state
            if imap_login_state != SELECTED:
                return Response("BAD", [])
            return Response("OK", [])

        async def wait_hello_from_server() -> None:
            imap_mock.protocol.state = NONAUTH

        imap_mock.has_pending_idle.return_value = imap_pending_idle
        imap_mock.protocol = MagicMock()
        imap_mock.protocol.state = STARTED
        imap_mock.protocol.expunge = AsyncMock()
        imap_mock.protocol.expunge.return_value = Response("OK", [])
        imap_mock.has_capability.return_value = imap_has_capability
        imap_mock.login.side_effect = login
        imap_mock.close.side_effect = close
        imap_mock.copy.side_effect = copy
        imap_mock.logout.side_effect = logout
        imap_mock.select.side_effect = select
        imap_mock.search.return_value = Response(*imap_search)
        imap_mock.store.side_effect = store
        imap_mock.fetch.return_value = Response(*imap_fetch)
        imap_mock.wait_hello_from_server.side_effect = wait_hello_from_server
        imap_mock.timeout = 3
        yield imap_mock
