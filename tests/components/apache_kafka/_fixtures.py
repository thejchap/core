"""Tryke fixtures for the apache_kafka integration tests."""

from asyncio import AbstractEventLoop
from collections.abc import Callable, Generator
from dataclasses import dataclass
from unittest.mock import patch

from tryke import fixture

APACHE_KAFKA_PATH = "homeassistant.components.apache_kafka"
PRODUCER_PATH = f"{APACHE_KAFKA_PATH}.AIOKafkaProducer"


@dataclass
class MockKafkaClient:
    """Mock of the Apache Kafka client for testing."""

    init: Callable[[type[AbstractEventLoop], str, str], None]
    start: Callable[[], None]
    send_and_wait: Callable[[str, str], None]


@fixture
def mock_client() -> Generator[MockKafkaClient]:
    """Mock the apache kafka client."""
    with (
        patch(f"{PRODUCER_PATH}.start") as start,
        patch(f"{PRODUCER_PATH}.send_and_wait") as send_and_wait,
        patch(f"{PRODUCER_PATH}.__init__", return_value=None) as init,
        patch(f"{PRODUCER_PATH}.stop"),
    ):
        yield MockKafkaClient(init, start, send_and_wait)
