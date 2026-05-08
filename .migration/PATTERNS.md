# Tryke migration PATTERNS — repo-specific playbook

Concrete adaptations learned for **homeassistant-core** specifically. Not a copy of the Tryke cheat sheet; it's the conventions we've settled on for this codebase.

---

## Tryke binary management

- Source at `~/src/tryke` (separate clone). Branch `main` = upstream.
- Install pattern: `uv pip install --reinstall --no-deps ~/src/tryke` (verified working — see [memory: tryke whole-suite hang]).
- Run via `.venv/bin/tryke ...` directly (not `uv run tryke`). Reason: `.python-version` says 3.14.4, the venv has 3.14.2; `uv run` errors trying to download a 3.14.4 interpreter, but the venv-internal binary works fine.
- Version sanity-check: `~/$(.venv/bin/tryke --version)` should match the source's `Cargo.toml` package version. Binary is ~12.9 MB stripped.

### When tryke needs upstream changes

1. Branch `~/src/tryke` (e.g. `feat/tryke-<feature>`).
2. Commit + push.
3. Open a **draft** PR to `thejchap/tryke`.
4. `uv pip install --reinstall --no-deps ~/src/tryke` to use the branch.
5. Note the PR URL in `CURRENT.md`.

PR #66 (stderr drain fix) is precedent — see [memory: tryke whole-suite hang].

## HA-specific pytest infrastructure (what we're replacing)

- **`tests/conftest.py`** (2,216 LOC, 92 fixtures) — root config. Most migration risk is here.
  - Line 159: `pytest_addoption()` — `--dburl`, `--drop-existing-db`.
  - Line 165: `pytest_configure()` — registers `no_fail_on_log_exception` marker; overrides `SnapshotSession.finish` (xdist syrupy workaround at line 176).
  - Line 190: `pytest_runtest_setup()` — installs `pytest_socket` blocker, swaps `SocketBlockedError` → `HASocketBlockedError`, monkeypatches `freezegun` with `HAFakeDatetime` and sqlite3/MySQLdb converters.
  - Line 256: `caplog_fixture(caplog)` — sets log level to DEBUG.
  - Line 263–350: autouse fixtures — `garbage_collection`, `expected_lingering_tasks`, `expected_lingering_timers`.
  - Line 625: `async def hass(...)` — core HomeAssistant fixture.
  - Lines 760-1016: auth/HTTP/MQTT fixtures.
- **`tests/common.py`** (2,027 LOC) — utility classes: `MockConfigEntry`, `MockUser`, `async_test_home_assistant`, `async_fire_*`, registry mocks. Imported broadly. Stays as-is.
- **`tests/syrupy.py`** — `HomeAssistantSnapshotExtension` with HA-type serializers. In-test object, not a hook → expected to keep working under tryke unchanged. Verify the xdist `override_syrupy_finish` workaround still applies.
- **`tests/patch_json.py`, `patch_recorder.py`, `patch_time.py`** — early import-time patches loaded before HA imports. Need to run before tryke spawns workers.
- **Component-specific conftest hooks:**
  - `tests/components/recorder/conftest.py:pytest_configure` registers `skip_on_db_engine` marker; `skip_by_db_engine` fixture introspects `request.node` → needs `markers.py` shim.
  - `tests/components/tts/conftest.py:pytest_runtest_makereport` — adds report metadata.
- **Custom marker `freeze_time`** — `@pytest.mark.freeze_time(...)` (~435 sites) — codemod target for `Depends(freezer)`.

## Pytest plugins → Tryke equivalents

| pytest plugin | usage | tryke replacement |
|---|---|---|
| pytest-asyncio | `asyncio_mode=auto` | built-in (`@test` + `async def`) |
| pytest-xdist | parallelism | `[tool.tryke]` defaults to parallel; `-j N` flag |
| pytest-cov | coverage | `coverage run -m tryke test ...` in CI (no per-test shim) |
| pytest-timeout | per-test timeout | `hass_tryke.timeout` Depends-based shim |
| pytest-aiohttp | aiohttp_client/server fixtures | `hass_tryke.aiohttp` shim port |
| pytest-socket | network blocking | `hass_tryke.socket_guard` re-implements with `HASocketBlockedError` |
| pytest-freezer | `@pytest.mark.freeze_time` | `hass_tryke.freezer` Depends-based shim wrapping `freezegun` |
| pytest-unordered | `unordered(...)` | `hass_tryke.matchers.to_equal_unordered` |
| pytest-picked | `--picked` | tryke `--changed` (built-in) |
| pytest-sugar | output format | `tryke test --reporter sugar` (built-in) |
| pytest-github-actions-annotate | CI failure annotations | drop; tryke's `junit` reporter is enough |
| syrupy | snapshot fixture | keep — runs inside test bodies, not pytest hook |
| respx | async HTTP mocking | keep — library, not plugin |
| requests-mock | sync HTTP mocking | keep — library, not plugin |
| freezegun | direct time mocking | keep — library, used by `hass_tryke.freezer` |

## Shim layout — actual

Implementation diverged from the original plan: rather than a `tests/hass_tryke/` package, everything lives in **`tests/hass_fixtures.py`** as a single module (proven on the prior branch, 686+ LOC). Conversion sites:

```python
from tests.hass_fixtures import hass, caplog, freezer, tmp_path, capfd, \
    aiohttp_client, hass_client, hass_client_no_auth, hass_ws_client, \
    hass_admin_user, hass_owner_user, hass_read_only_user, hass_access_token, \
    aioclient_mock, current_request, current_request_with_host, \
    enable_bluetooth, mock_bluetooth_adapters, mock_bleak_scanner_start, \
    mock_network, disable_block_async_io, \
    area_registry, category_registry, device_registry, entity_registry, \
    floor_registry, issue_registry, label_registry, \
    hass_storage, hass_unloaded
```

Plus:
- `LogCapture`, `CapFd`, `Captured` classes for type annotations
- `ClientSessionGenerator` type alias

Not in shim (rare enough to use inline patterns):
- `monkeypatch` — most ports inline `with patch(...)` or `with patch.dict(...)`
- `expect_warns` — never needed in this slice
- `to_equal_unordered` — never needed
- `marker_check` — recorder-only; still pending
- `timeout` — relying on tryke's own timeouts

If a real need surfaces, add it directly to `tests/hass_fixtures.py` and document here.

## Conversion patterns

### Per-integration `_fixtures.py` (proven on 359 integrations)

When porting `tests/components/<int>/test_config_flow.py`:
- Move every `@pytest.fixture` from that integration's `conftest.py` into `_fixtures.py` next to the test file.
- Convert `@pytest.fixture` → `@fixture` with explicit `Depends()` wiring.
- The `conftest.py` is deleted only after **every** test in the directory is ported (not just `test_config_flow.py`).

### Display names (cheap, always do)

Lift the test docstring (or function name reword) into `@test("<sentence>")`. Label `expect()` calls with `expect(value, "<noun>")`. Free metadata at parse time.

### Soft assertions

Tryke is soft by default. Only use `.fatal()` when a later assertion *dereferences* what an earlier one checked (e.g. status 200 then read body). Don't sprinkle `.fatal()` to "match pytest".

### `pytest.raises(match=...)` regex

Pass through unchanged. `to_raise(MyError, match=r"...same regex...")`.

### Async tests

Built-in. `@test` + `async def`. No marker.

### `@pytest.mark.parametrize(...)` → `@test.cases(...)`

Labels must be string literals. Case kwargs must match function signature exactly. No indirect parametrization.

**Form:** `@test.cases(test.case("label", **kwargs), ...)` — and `@test.cases` *replaces* `@test`; do NOT stack both. The positional shorthand `@test.cases(("a", val), ...)` only takes ONE positional list — not multiple tuples — so always use `test.case(...)` for each row.

```python
# Wrong — TypeError: test.cases() positional form takes exactly one list argument
@test.cases(
    ("case_a", val1, val2),
    ("case_b", val3, val4),
)
@test
async def my_test(...): ...

# Correct
@test.cases(
    test.case("case_a", val1=val1, val2=val2),
    test.case("case_b", val1=val3, val2=val4),
)
async def my_test(*, val1, val2, ...): ...
```

### Local fixture overrides in pytest test files

Pytest tests sometimes redefine a fixture at module scope to override the `conftest.py` version (eg. `fritzbox`'s test_config_flow defines its own `fritz` that also patches `async_setup_entry`). Under tryke port: stash the **test-file-local** version in `_fixtures.py` and import it from the test module — that is what the test author intended.

### `bool(value)` for truthy-checks

`assert not result["errors"]` → `expect(bool(result["errors"])).to_be(False)` (not `expect(result["errors"]).to_be({})` — the original may have produced `None` or `{}`).

### `with describe(...)` blocks

Use sparingly. They prepend a `group::` to test IDs which then need normalization in Phase 3 / 4 diffs. Default: don't group; tests already live in module files.

### Tryke fixture-injection quirk: module-local anchor fixture

**Discovered porting `here_travel_time` and `homeassistant_connect_zbt2` (skipped-three batch).**

A test signature like
```python
@test
async def my_test(
    hass: HomeAssistant = Depends(hass_fixture),
    setup_addons: AsyncMock = Depends(setup_addons),  # imported from ._fixtures
    ...
) -> None: ...
```
*sometimes* fails to resolve `hass` — it stays as the `_Depends(...)` sentinel and the test body crashes accessing methods on it. The workaround that abode/yardian/skipped-three settled on:

```python
# in test file, NOT _fixtures.py — must be defined in the test module:
@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
    # bundle any cross-module dependencies here so tests don't have to
) -> HomeAssistant:
    return hass

@test
async def my_test(
    hass: HomeAssistant = Depends(_trigger_executor),
    ...
) -> None: ...
```

**Why:** an extra Depends-hop through a *module-local* fixture seems to force tryke to fully resolve before the test runs. Likely a tryke 0.0.27 bug; if it ever gets fixed upstream, this pattern can be deleted.

**How to apply:** if a port hits "received `_Depends(...)` but expected `HomeAssistant`" or similar, add `_trigger_executor` to the test module and re-route every test's `hass` Depends through it.

### Module-level `_trigger_executor` is autouse — keep it minimal

Tryke fixtures defined in a test module run **automatically for every test in that module** (per the docs: "module-level fixtures cover all tests in the file"). That means `_trigger_executor` itself is autouse — and crucially, anything `_trigger_executor` `Depends()` on transitively also runs autouse for every test.

**Rule:** Only put fixtures into `_trigger_executor` that you want active for *all* tests in the file. Common safe choices: `mock_network`, fixtures every test needs.

**Counter-example (caused namecheapdns to fail until fixed):** if 4 of 5 tests need `mock_setup_entry` and 1 test wants the real `async_setup_entry` to run (so it can hit `aioclient_mock`), do **not** stuff `mock_setup_entry` into `_trigger_executor`. Each test should depend on its mocks individually via `Depends(mock_setup_entry)`. The trigger fixture is just the resolution anchor.

```python
# Good — trigger primes only what every test needs:
@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    pass

@test
async def test_a(
    _t: None = Depends(_trigger_executor),
    setup: AsyncMock = Depends(mock_setup_entry),  # only here, not autouse
    hass: HomeAssistant = Depends(hass_fixture),
): ...

@test
async def test_b_with_real_setup(
    _t: None = Depends(_trigger_executor),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),  # different mock
    hass: HomeAssistant = Depends(hass_fixture),
): ...   # mock_setup_entry NOT applied here
```

### `@test.skip` stubbing as a discovery scaffold

When porting an integration whose test relies on a fixture not yet in the shim
(eg. `mqtt_mock`, `recorder_mock`, `OAuth2 application credentials`,
`syrupy snapshot`, `supervisor_client` beyond the homeassistant_connect_zbt2
slice, indirect parametrize), generate a stub file with:

```python
"""Tryke skip-stubs for <int> config flow tests."""
from tryke import test

@test.skip("requires <fixture-name> (not in tryke shim)")
async def <test-fn-name>() -> None:
    """Stub for test_<test-fn-name> (port deferred)."""
```

**Why:** keeps `tryke test` discovery counts honest (test still appears in the
output as `skipped` rather than disappearing). Stubs are easy to reverse-port
once a missing shim lands. Strip the `test_` prefix when renaming so tryke
doesn't double-count.

### Patch-target verification when porting

Some legacy tests `with patch("pyfoo.bar.Baz", ...)` instead of
`patch("homeassistant.components.X.config_flow.Baz", ...)`. The HA test
runner used to be lax about which name actually got intercepted. Under tryke
+ no aggressive socket blocker, the unpatched real call goes through to the
network and fails. **Symptom:** test assertion expects `cannot_connect` but
received `invalid_auth` (real HTTP 401). **Fix options:** (1) port the test
but skip it with a one-line reason; (2) update the patch target to the
import-site (`homeassistant.components.<int>.config_flow.<Class>`).
Precedent: prosegur — two tests skipped after diagnosis.

### Translation injection for entity_id slugs and exception messages

The tryke test environment doesn't compile integration translations
(`translations/<lang>.json` is absent in dev tree, only `strings.json`
exists). Without those compiled files, `_async_get_component_strings`
returns nothing, which means:

- Entities with `_attr_has_entity_name=True` and `translation_key="..."`
  get an entity_id slug that falls back to just the device name (e.g.
  `button.lunar_ddeeff` instead of `button.lunar_ddeeff_tare`).
- `HomeAssistantError(translation_key="api_error", ...)` returns the
  literal "api_error" instead of the translated message with placeholders.

Tests that assert on those slugs/messages need a translation injection.
The reliable pattern (4 patches) — used in actron_air's test_climate /
test_switch and acaia/altruist/abode/aemet/airzone_cloud test ports:

```python
_FAKE_TRANSLATIONS = {
    # Entity name slugs — picked up by EntityPlatform
    "component.actron_air.entity.switch.away_mode.name": "Away mode",
    # Sensor entity_component (device_class) — picked up by sensor platform
    "component.sensor.entity_component.humidity.name": "Humidity",
    # Exception messages — picked up by HomeAssistantError.__str__
    "component.actron_air.exceptions.api_error.message":
        "Failed to communicate: {error}",
}

async def _fake_get_translations(hass, language, category, integrations=None, config_flow=None):
    return _FAKE_TRANSLATIONS

def _fake_get_cached_translations(hass, language, category, integration=None):
    return _FAKE_TRANSLATIONS

def _fake_get_exception_message(translation_domain, translation_key, translation_placeholders=None):
    key = f"component.{translation_domain}.exceptions.{translation_key}.message"
    msg = _FAKE_TRANSLATIONS.get(key, translation_key)
    if translation_placeholders:
        try:
            msg = msg.format(**translation_placeholders)
        except KeyError:
            pass
    return msg

with (
    patch("homeassistant.helpers.entity_platform.translation.async_get_translations", side_effect=_fake_get_translations),
    patch("homeassistant.helpers.translation.async_get_cached_translations", side_effect=_fake_get_cached_translations),
    patch("homeassistant.helpers.translation.async_get_exception_message", side_effect=_fake_get_exception_message),
    # Must seed the function cache too — homeassistant/exceptions.py caches
    # the resolved async_get_exception_message on first __str__ call.
    patch.dict(
        "homeassistant.exceptions._function_cache",
        {"async_get_exception_message": _fake_get_exception_message},
        clear=False,
    ),
):
    await setup_integration(...)
```

**Materializing the translated message**: HomeAssistantError caches its
`__str__` result. When `expect_raises_async` later calls `str(raised)`
*after* the patch context exits, the patches are gone and the message
resolves to the bare `translation_key`. Workaround — capture inside the
patch context:

```python
raised: HomeAssistantError | None = None
with _patch_translations():
    try:
        await hass.services.async_call(...)
    except HomeAssistantError as err:
        err._message = str(err)  # noqa: SLF001 — freeze translated message
        raised = err
expect("Test error" in str(raised)).to_be(True)
```

### Tryke 0.0.27 missing matcher: `to_not_be`

`expect(x).to_not_be(None)` doesn't exist (tryke 0.0.27). Rewrite as `expect(x is not None).to_be(True)`. Likely a candidate for an upstream tryke PR. **Why:** chaining `.not_` on `to_be` works for most matchers but `to_not_be` was missing; just use the bool form for now.

### `freeze_time` codemod

```python
# pytest:
@pytest.mark.freeze_time("2024-01-01")
def test_foo(): ...

# tryke:
@test
def foo(_freeze: Annotated[FreezeTime, Depends(freeze_time("2024-01-01"))]): ...
```

`hass_tryke.freezer.freeze_time(spec)` is a fixture factory that yields a freezegun-frozen context.

## Don'ts (from prompt + experience)

- No `cast()`, `# type: ignore`, `getattr`, or `Any` on `Depends()`. Fix the fixture's return type.
- Don't translate `pytest.raises(match=r"...")` regex — copy it.
- Don't keep `conftest.py` "just in case" — delete after re-homing.
- Don't edit the baseline file in Phase 3 to make a missing test go away.
- Don't mass-`.fatal()` to make Phase-4 numbers match — diagnose each case.

## Discovery / Phase-3 tripwires

When `tryke test --collect-only` is missing a test:

1. Dynamic imports — `grep -R 'importlib.import_module' tests/<path>` and replace with static.
2. Fixture still in `conftest.py`.
3. `@test.cases` label not a string literal, or kwargs mismatch.
4. Plain `def test_foo` not decorated with `@test`.
5. Test nested inside `if`/`for`/`while` body — flatten.

## CI commands (Phase 5)

```bash
.venv/bin/tryke test --reporter junit > junit.xml
coverage run -m tryke test ...
coverage xml
```
