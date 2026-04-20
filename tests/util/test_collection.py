"""Test collection utils."""

from tryke import expect, test

from homeassistant.util.collection import chunked_or_all as _chunked_or_all


@test
def chunked_or_all() -> None:
    """Test chunked_or_all can iterate chunk sizes larger than the passed in collection."""
    all_items: list[int] = []
    incoming = (1, 2, 3, 4)
    for chunk in _chunked_or_all(incoming, 2):
        expect(len(chunk)).to_equal(2)
        all_items.extend(chunk)
    expect(all_items).to_equal([1, 2, 3, 4])

    all_items = []
    incoming = (1, 2, 3, 4)
    for chunk in _chunked_or_all(incoming, 5):
        expect(len(chunk)).to_equal(4)
        # Verify the chunk is the same object as the incoming
        # collection since we want to avoid copying the collection
        # if we don't need to
        expect(chunk is incoming).to_be(True)
        all_items.extend(chunk)
    expect(all_items).to_equal([1, 2, 3, 4])
