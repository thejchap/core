"""Tryke fixtures for Azure Data Explorer."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import fixture

from .const import AZURE_DATA_EXPLORER_PATH


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock the setup entry call, used for config flow tests."""
    with patch(
        f"{AZURE_DATA_EXPLORER_PATH}.async_setup_entry", return_value=True
    ) as setup_entry:
        yield setup_entry


@fixture
def mock_managed_streaming() -> Generator[MagicMock]:
    """Mock ManagedStreamingIngestClient.ingest_from_stream."""
    with patch(
        "azure.kusto.ingest.ManagedStreamingIngestClient.ingest_from_stream",
        return_value=True,
    ) as ingest_from_stream:
        yield ingest_from_stream


@fixture
def mock_queued_ingest() -> Generator[MagicMock]:
    """Mock QueuedIngestClient.ingest_from_stream."""
    with patch(
        "azure.kusto.ingest.QueuedIngestClient.ingest_from_stream",
        return_value=True,
    ) as ingest_from_stream:
        yield ingest_from_stream


@fixture
def mock_execute_query() -> Generator[MagicMock]:
    """Mock KustoClient execute_query."""
    with patch(
        "azure.kusto.data.KustoClient.execute_query",
        return_value=True,
    ) as execute_query:
        yield execute_query
