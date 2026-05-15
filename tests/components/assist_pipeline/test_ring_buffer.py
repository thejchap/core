"""Tests for audio ring buffer."""

from tryke import expect, test

from homeassistant.components.assist_pipeline.ring_buffer import RingBuffer


@test
def ring_buffer_empty() -> None:
    """Test empty ring buffer."""
    rb = RingBuffer(10)
    expect(rb.maxlen).to_equal(10)
    expect(rb.pos).to_equal(0)
    expect(rb.getvalue()).to_equal(b"")


@test
def ring_buffer_put_1() -> None:
    """Test putting some data smaller than the maximum length."""
    rb = RingBuffer(10)
    rb.put(bytes([1, 2, 3, 4, 5]))
    expect(len(rb)).to_equal(5)
    expect(rb.pos).to_equal(5)
    expect(rb.getvalue()).to_equal(bytes([1, 2, 3, 4, 5]))


@test
def ring_buffer_put_2() -> None:
    """Test putting some data past the end of the buffer."""
    rb = RingBuffer(10)
    rb.put(bytes([1, 2, 3, 4, 5]))
    rb.put(bytes([6, 7, 8, 9, 10, 11, 12]))
    expect(len(rb)).to_equal(10)
    expect(rb.pos).to_equal(2)
    expect(rb.getvalue()).to_equal(bytes([3, 4, 5, 6, 7, 8, 9, 10, 11, 12]))


@test
def ring_buffer_put_too_large() -> None:
    """Test putting data too large for the buffer."""
    rb = RingBuffer(10)
    rb.put(bytes([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]))
    expect(len(rb)).to_equal(10)
    expect(rb.pos).to_equal(2)
    expect(rb.getvalue()).to_equal(bytes([3, 4, 5, 6, 7, 8, 9, 10, 11, 12]))
