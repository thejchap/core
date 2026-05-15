"""Tryke fixtures for the apache_kafka integration tests."""

from asyncio import AbstractEventLoop
from collections.abc import Callable, Generator
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

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
    """Mock the apache kafka client.

    Replace the AIOKafkaProducer class wholesale so the HA shutdown listener
    (fired during hass teardown after this fixture's context has exited) sees
    a Mock and not a real producer.
    """
    instance = MagicMock()
    instance.start = AsyncMock()
    instance.send_and_wait = AsyncMock()
    instance.stop = AsyncMock()
    producer_cls = MagicMock(return_value=instance)
    with patch(PRODUCER_PATH, producer_cls):
        yield MockKafkaClient(producer_cls, instance.start, instance.send_and_wait)
