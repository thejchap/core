"""Debug snapshot."""
from syrupy.assertion import SnapshotAssertion
from tryke import Depends, expect, fixture, test
from tests.hass_tryke_helpers import snapshot as snapshot_fixture


@test
async def unknown_llm_api(snapshot: SnapshotAssertion = Depends(snapshot_fixture)) -> None:
    import sys
    ext = snapshot.extension
    loc = snapshot._extension.test_location
    print("LOC path:", loc.filepath, file=sys.stderr)
    print("LOC name:", loc.snapshot_name, file=sys.stderr)
    print("EXT snapshot_location:", ext.get_location(test_location=loc, index=0) if hasattr(ext,'get_location') else 'n/a', file=sys.stderr)
    print("EXT _dirname:", ext._dirname if hasattr(ext,'_dirname') else 'n/a', file=sys.stderr)
    expect(1).to_equal(99)
