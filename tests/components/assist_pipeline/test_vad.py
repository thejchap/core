"""Tests for voice command segmenter."""

import itertools as it

from tryke import expect, test

from homeassistant.components.assist_pipeline.vad import (
    AudioBuffer,
    VoiceCommandSegmenter,
    chunk_samples,
)

_ONE_SECOND = 1.0


@test
def silence() -> None:
    """Test that 3 seconds of silence does not trigger a voice command."""
    segmenter = VoiceCommandSegmenter()

    # True return value indicates voice command has not finished
    expect(segmenter.process(_ONE_SECOND * 3, 0.0)).to_be_truthy()
    expect(segmenter.in_command).to_be_falsy()


@test
def speech() -> None:
    """Test that silence + speech + silence triggers a voice command."""

    segmenter = VoiceCommandSegmenter()

    # silence
    expect(segmenter.process(_ONE_SECOND, 0.0)).to_be_truthy()

    # "speech"
    expect(segmenter.process(_ONE_SECOND, 1.0)).to_be_truthy()
    expect(segmenter.in_command).to_be_truthy()

    # silence
    # False return value indicates voice command is finished
    expect(segmenter.process(_ONE_SECOND, 0.0)).to_be_falsy()
    expect(segmenter.in_command).to_be_falsy()


@test
def audio_buffer() -> None:
    """Test audio buffer wrapping."""

    samples_per_chunk = 160  # 10 ms
    bytes_per_chunk = samples_per_chunk * 2
    leftover_buffer = AudioBuffer(bytes_per_chunk)

    # Partially fill audio buffer
    half_chunk = bytes(it.islice(it.cycle(range(256)), bytes_per_chunk // 2))
    chunks = list(chunk_samples(half_chunk, bytes_per_chunk, leftover_buffer))

    expect(chunks).to_be_falsy()
    expect(leftover_buffer.bytes()).to_equal(half_chunk)

    # Fill and wrap with 1/4 chunk left over
    three_quarters_chunk = bytes(
        it.islice(it.cycle(range(256)), int(0.75 * bytes_per_chunk))
    )
    chunks = list(chunk_samples(three_quarters_chunk, bytes_per_chunk, leftover_buffer))

    expect(len(chunks)).to_equal(1)
    expect(leftover_buffer.bytes()).to_equal(
        three_quarters_chunk[len(three_quarters_chunk) - (bytes_per_chunk // 4) :]
    )
    expect(chunks[0]).to_equal(
        half_chunk + three_quarters_chunk[: bytes_per_chunk // 2]
    )

    # Run 2 chunks through
    leftover_buffer.clear()
    expect(len(leftover_buffer)).to_equal(0)

    two_chunks = bytes(it.islice(it.cycle(range(256)), bytes_per_chunk * 2))
    chunks = list(chunk_samples(two_chunks, bytes_per_chunk, leftover_buffer))

    expect(len(chunks)).to_equal(2)
    expect(len(leftover_buffer)).to_equal(0)
    expect(chunks[0]).to_equal(two_chunks[:bytes_per_chunk])
    expect(chunks[1]).to_equal(two_chunks[bytes_per_chunk:])


@test
def partial_chunk() -> None:
    """Test that chunk_samples returns when given a partial chunk."""
    bytes_per_chunk = 5
    samples = bytes([1, 2, 3])
    leftover_chunk_buffer = AudioBuffer(bytes_per_chunk)
    chunks = list(chunk_samples(samples, bytes_per_chunk, leftover_chunk_buffer))

    expect(len(chunks)).to_equal(0)
    expect(leftover_chunk_buffer.bytes()).to_equal(samples)


@test
def chunk_samples_leftover() -> None:
    """Test that chunk_samples property keeps left over bytes across calls."""
    bytes_per_chunk = 5
    samples = bytes([1, 2, 3, 4, 5, 6])
    leftover_chunk_buffer = AudioBuffer(bytes_per_chunk)
    chunks = list(chunk_samples(samples, bytes_per_chunk, leftover_chunk_buffer))

    expect(len(chunks)).to_equal(1)
    expect(leftover_chunk_buffer.bytes()).to_equal(bytes([6]))

    # Add some more to the chunk
    chunks = list(chunk_samples(samples, bytes_per_chunk, leftover_chunk_buffer))

    expect(len(chunks)).to_equal(1)
    expect(leftover_chunk_buffer.bytes()).to_equal(bytes([5, 6]))


@test
def silence_seconds() -> None:
    """Test end of voice command silence seconds."""

    segmenter = VoiceCommandSegmenter(silence_seconds=1.0)

    # silence
    expect(segmenter.process(_ONE_SECOND, 0.0)).to_be_truthy()
    expect(segmenter.in_command).to_be_falsy()

    # "speech"
    expect(segmenter.process(_ONE_SECOND, 1.0)).to_be_truthy()
    expect(segmenter.in_command).to_be_truthy()

    # not enough silence to end
    expect(segmenter.process(_ONE_SECOND * 0.5, 0.0)).to_be_truthy()
    expect(segmenter.in_command).to_be_truthy()

    # exactly enough silence now
    expect(segmenter.process(_ONE_SECOND * 0.5, 0.0)).to_be_falsy()
    expect(segmenter.in_command).to_be_falsy()


@test
def silence_reset() -> None:
    """Test that speech resets end of voice command detection."""

    segmenter = VoiceCommandSegmenter(silence_seconds=1.0, reset_seconds=0.5)

    # silence
    expect(segmenter.process(_ONE_SECOND, 0.0)).to_be_truthy()
    expect(segmenter.in_command).to_be_falsy()

    # "speech"
    expect(segmenter.process(_ONE_SECOND, 1.0)).to_be_truthy()
    expect(segmenter.in_command).to_be_truthy()

    # not enough silence to end
    expect(segmenter.process(_ONE_SECOND * 0.5, 0.0)).to_be_truthy()
    expect(segmenter.in_command).to_be_truthy()

    # speech should reset silence detection
    expect(segmenter.process(_ONE_SECOND * 0.5, 1.0)).to_be_truthy()
    expect(segmenter.in_command).to_be_truthy()

    # not enough silence to end
    expect(segmenter.process(_ONE_SECOND * 0.5, 0.0)).to_be_truthy()
    expect(segmenter.in_command).to_be_truthy()

    # exactly enough silence now
    expect(segmenter.process(_ONE_SECOND * 0.5, 0.0)).to_be_falsy()
    expect(segmenter.in_command).to_be_falsy()


@test
def speech_reset() -> None:
    """Test that silence resets start of voice command detection."""

    segmenter = VoiceCommandSegmenter(
        silence_seconds=1.0, reset_seconds=0.5, speech_seconds=1.0
    )

    # silence
    expect(segmenter.process(_ONE_SECOND, 0.0)).to_be_truthy()
    expect(segmenter.in_command).to_be_falsy()

    # not enough speech to start voice command
    expect(segmenter.process(_ONE_SECOND * 0.5, 1.0)).to_be_truthy()
    expect(segmenter.in_command).to_be_falsy()

    # silence should reset speech detection
    expect(segmenter.process(_ONE_SECOND, 0.0)).to_be_truthy()
    expect(segmenter.in_command).to_be_falsy()

    # not enough speech to start voice command
    expect(segmenter.process(_ONE_SECOND * 0.5, 1.0)).to_be_truthy()
    expect(segmenter.in_command).to_be_falsy()

    # exactly enough speech now
    expect(segmenter.process(_ONE_SECOND * 0.5, 1.0)).to_be_truthy()
    expect(segmenter.in_command).to_be_truthy()


@test
def timeout() -> None:
    """Test that voice command detection times out."""

    segmenter = VoiceCommandSegmenter(timeout_seconds=1.0)

    # not enough to time out
    expect(segmenter.timed_out).to_be_falsy()
    expect(segmenter.process(_ONE_SECOND * 0.5, 0.0)).to_be_truthy()
    expect(segmenter.timed_out).to_be_falsy()

    # enough to time out
    expect(segmenter.process(_ONE_SECOND * 0.5, 1.0)).to_be_falsy()
    expect(segmenter.timed_out).to_be_truthy()

    # flag resets with more audio
    expect(segmenter.process(_ONE_SECOND * 0.5, 1.0)).to_be_truthy()
    expect(segmenter.timed_out).to_be_falsy()

    expect(segmenter.process(_ONE_SECOND * 0.5, 0.0)).to_be_falsy()
    expect(segmenter.timed_out).to_be_truthy()


@test
def command_seconds() -> None:
    """Test minimum number of seconds for voice command."""

    segmenter = VoiceCommandSegmenter(
        command_seconds=3, speech_seconds=1, silence_seconds=1, reset_seconds=1
    )

    expect(segmenter.process(_ONE_SECOND, 1.0)).to_be_truthy()

    # Silence counts towards total command length
    expect(segmenter.process(_ONE_SECOND * 0.5, 0.0)).to_be_truthy()

    # Enough to finish command now
    expect(segmenter.process(_ONE_SECOND, 1.0)).to_be_truthy()
    expect(segmenter.process(_ONE_SECOND * 0.5, 0.0)).to_be_truthy()

    # Silence to finish
    expect(segmenter.process(_ONE_SECOND * 0.5, 0.0)).to_be_falsy()


@test
def speech_thresholds() -> None:
    """Test before/in command speech thresholds."""

    segmenter = VoiceCommandSegmenter(
        before_command_speech_threshold=0.2,
        in_command_speech_threshold=0.5,
        command_seconds=2,
        speech_seconds=1,
        silence_seconds=1,
    )

    # Not high enough probability to trigger command
    expect(segmenter.process(_ONE_SECOND, 0.1)).to_be_truthy()
    expect(segmenter.in_command).to_be_falsy()

    # Triggers command
    expect(segmenter.process(_ONE_SECOND, 0.3)).to_be_truthy()
    expect(segmenter.in_command).to_be_truthy()

    # Now that same probability is considered silence.
    # Finishes command.
    expect(segmenter.process(_ONE_SECOND, 0.3)).to_be_falsy()
