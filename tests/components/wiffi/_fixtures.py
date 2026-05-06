"""Tryke fixtures for the Wiffi integration."""

from collections.abc import Generator
import errno
from unittest.mock import AsyncMock, patch

from tryke import fixture


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.wiffi.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def dummy_tcp_server() -> Generator[object]:
    """Mock a valid WiffiTcpServer."""

    class Dummy:
        async def start_server(self) -> None:
            pass

        async def close_server(self) -> None:
            pass

    server = Dummy()
    with patch(
        "homeassistant.components.wiffi.config_flow.WiffiTcpServer", return_value=server
    ):
        yield server


@fixture
def addr_in_use() -> Generator[object]:
    """Mock a WiffiTcpServer with addr_in_use."""

    class Dummy:
        async def start_server(self) -> None:
            raise OSError(errno.EADDRINUSE, "")

        async def close_server(self) -> None:
            pass

    server = Dummy()
    with patch(
        "homeassistant.components.wiffi.config_flow.WiffiTcpServer", return_value=server
    ):
        yield server


@fixture
def start_server_failed() -> Generator[object]:
    """Mock a WiffiTcpServer with start_server_failed."""

    class Dummy:
        async def start_server(self) -> None:
            raise OSError(errno.EACCES, "")

        async def close_server(self) -> None:
            pass

    server = Dummy()
    with patch(
        "homeassistant.components.wiffi.config_flow.WiffiTcpServer", return_value=server
    ):
        yield server
