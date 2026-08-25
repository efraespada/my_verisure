# OTP Fail-Closed Closure Implementation Plan

> **For Hermes:** Execute this plan task-by-task using strict RED→GREEN→REFACTOR, then freeze a new staged fingerprint and obtain an independent read-only review before publication.

**Goal:** Complete and verify the My Verisure OTP authentication flow so that device authorization, OTP challenge lifecycle, session persistence, network failures, reauthentication, configuration flow, CLI output, and diagnostics are fail-closed and free of sensitive-data leakage.

**Architecture:** Keep `config_flow.py` and the CLI as thin adapters. Authentication policy and challenge lifecycle remain in application/use-case boundaries; provider transport remains in API adapters; persistence is an injected semantic application port owned by the composition root. Every failure must remain distinguishable until it reaches a safe presentation outcome.

**Tech Stack:** Python 3.11/3.14 test environment, Home Assistant 2026.8.1, pytest/pytest-asyncio, mypy, Bandit, pip-audit, Flake8 critical subset, custom architecture/distribution guards, Git staged-tree fingerprinting, independent read-only review.

---

## Scope and non-negotiable invariants

1. A login result is not an authenticated session until device authorization and OTP verification have completed successfully.
2. A missing, malformed, empty, expired, exhausted, cancelled, or ambiguous OTP challenge stops the flow.
3. A transport timeout, `aiohttp.ClientError`, `OSError`, or cancellation never becomes invalid credentials, OTP required, or success.
4. A verified OTP challenge is single-use. Replay cannot invoke the provider or persistence boundary again.
5. Session persistence is transactional: failed disk persistence cannot leave a new authenticated in-memory session.
6. Config-entry installation and reauthentication updates occur only after verified authentication and successful persistence.
7. No blocking filesystem/network operation runs directly in an async Home Assistant config-flow path.
8. Logs, exceptions, CLI output, diagnostics, fixtures, and evidence contain no real or secret-shaped credential, token, OTP, hash, password, username, phone, UUID, device name, record ID, or raw provider exception. Use `[REDACTED]` or clearly non-sensitive sentinels.
9. No real Verisure credentials or real provider requests are used in tests.
10. No `brand/icon.png` or `brand/icon@2x.png` changes are permitted.
11. No commit or push occurs until the final independent review approves the exact candidate fingerprint.

## Current baseline and evidence

- Repository: `/home/efraespada/my_verisure`
- Remote: `https://github.com/efraespada/my_verisure.git`
- Branch: `fix/otp-flow-hardening`
- HEAD at plan creation: `19a16467384acab6c3601db870bcdb364623c1af`
- Worktree: intended OTP changes are present in both index and worktree; staging must be normalized before final review.
- Previous valid review fingerprint: `TREE=c868554debb9c12de4fe92b3332092655481a802`, `DIFF_SHA=9da9b781f9197f583d0b4e33f69bd81d5a7f81abdf9cde9fa076434d7c074820`; verdict `CHANGES_REQUESTED`.
- Previous review blockers: transport misclassification, post-OTP verified-session fallback, reusable OTP challenge, incomplete redaction, sensitive fixtures, username-derived session path.
- Additional accepted hardening: transactional persistence, invalid JWT fail-closed, strict record-id validation, injected `AuthSessionPersistence`, executor-based phone lookup, CLI selection and sanitization.
- Historical unrelated items remain separate: full Flake8 `W293/E501` debt, Home Assistant-pinned `cryptography==48.0.1` audit findings if reproduced, HACS icon CDN behavior, and the historical SessionDB error.

## Evidence matrix

| Capability | Entry points | Invariants | Primary files | Required evidence | Completion state |
|---|---|---|---|---|---|
| Initial login | `config_flow.async_step_user`, `AuthUseCase.login`, `AuthClient.login` | No persistence before device/OTP confirmation | `config_flow.py`, `auth_client.py`, `auth_repository_impl.py` | Focused login/device/OTP tests; source audit; no early `async_update_credentials` | Must be rechecked after final diff |
| Device authorization | `AuthClient._check_device_authorization`, `_complete_device_authorization` | Connection errors propagate; OTP only on explicit provider challenge | `auth_client.py`, `base_client.py` | timeout, connection, cancellation, provider-response tests | Must be green |
| Phone lookup | `AuthUseCase.get_available_phones`, config-flow executor helper | Missing challenge/error/empty/malformed data never becomes selectable phones | `auth_use_case_impl.py`, `otp_authorization.py`, `config_flow.py` | malformed/empty/error tests; async executor test | Must be green |
| Phone selection and send | `config_flow.async_step_phone_selection`, CLI OTP flow | Explicit valid `record_id`; selected phone required; no hash crosses presentation | `config_flow.py`, `cli/commands/auth.py`, use-case/repository interfaces | invalid selection/missing record-id/selection-order tests | Must be green |
| OTP verification | `AuthUseCase.verify_otp`, `AuthClient.verify_otp` | TTL, max attempts, cancellation, single-use, no fallback | use case, client, repository | expiry/exhaustion/replay/transport tests | Must be green |
| Session persistence | `AuthSessionPersistence`, `SessionManager` | Persist only after success; disk failure rolls back in-memory state | application persistence, session manager | persistence failure/rollback and ordering tests | Must be green |
| Reauthentication | `config_flow.async_step_reauth`, `SessionManager.ensure_authenticated` | Existing entry is unchanged on any failed or incomplete reauth | `config_flow.py`, lifecycle tests | invalid OTP, timeout, cancellation, persistence failure tests | Must be green |
| Sensitive data | logs, headers, exceptions, CLI, fixtures | No raw sensitive material or exception repr | `log_utils.py`, API clients, CLI, tests | sentinel scan and redaction tests | Must be green |
| Architecture | DI composition | semantic persistence injected once; adapters thin | DI module, AuthClient, use case | composition/identity tests, architecture guard | Must be green |
| Publication | staged candidate | exact tree/diff reviewed read-only | Git | all gates, fingerprint, reviewer `APPROVED` | Final stop gate |

## Risk and decision register

| ID | Risk | Decision | Mitigation / evidence | Stop condition |
|---|---|---|---|---|
| R1 | Provider uses ambiguous transport/provider responses | Preserve typed transport errors and reject ambiguous payloads | adapter contract tests; no generic success fallback | Any path maps connection to auth/OTP/success |
| R2 | Persistence fails after remote OTP success | Treat local persistence as part of successful authentication contract; rollback memory and stop | injected persistence + rollback tests | New session remains authenticated after write failure |
| R3 | OTP replay or concurrent verification | Consume challenge immediately after successful provider acceptance, before post-login/persistence/cancellation, and exhaust attempt state | replay test; repository/persistence call count | Second verification reaches provider or persistence |
| R4 | Sensitive data leaks through repr/default serialization | Central recursive redaction for dict/list/dataclass/exception/header aliases | sentinel tests and source scan | Any sentinel appears in emitted output |
| R5 | Async event-loop blocking | Executor for composition and synchronous phone lookup; inspect all config-flow awaits | Home Assistant branch tests; source audit | Sync provider/filesystem call remains in async path |
| R6 | DI graph creates duplicate policies | One composition-owned `AuthSessionPersistence` is injected into AuthClient/use case | composition identity test | AuthClient constructs application persistence internally |
| R7 | Tests become green for the wrong reason | Every new behavior must show RED before implementation | record RED/GREEN commands in final evidence | Test passes before production change or collects zero tests |
| R8 | Review inspects a different candidate | Stage only after all gates; verify exact tree/diff before and after review | `git write-tree`, binary full-index diff SHA, zero unstaged paths | Any fingerprint mismatch |
| R9 | Historical quality debt obscures this block | Separate unrelated Flake8/upstream findings and report honestly | focused critical gates plus full output classification | New OTP-specific failure is misclassified as historical |

## Execution sequence

### Task 0: Normalize and freeze the working scope

**Files:** no production changes; `.hermes/plans/2026-08-24_220140-otp-fail-closed-closure.md` is the only documentation artifact.

1. Read current status, staged/unstaged diff, branch, HEAD, and remote.
2. Confirm brand assets are unchanged.
3. Classify every changed path as OTP scope, supporting architecture, test, translation, or unrelated.
4. Do not reset or discard intended work. Before final staging, `git add -A` only after the complete candidate is ready.

**Verification:** status and changed-path inventory recorded in the final report; no external side effects.

### Task 1: Sensitive fixture and output inventory

**Tests first:** add/extend sentinel tests for `refreshToken`, `otpHash`, `recordId`, UUID/device fields, `Security`/`auth` headers, dataclasses, exception objects, CLI errors, and phone/username output.

**Production changes:**
- Extend `log_utils._REDACT_KEYS_NORM` with normalized snake/camel/provider aliases.
- Convert dataclasses with `asdict()` before redaction.
- Replace raw exception interpolation with fixed sanitized messages.
- Remove phone IDs, UUIDs, usernames, installation identifiers, and phone values from logs/CLI output.

**Verification:** focused redaction and CLI tests; scan changed production/test diff for secret-shaped literals and raw exception formatting.

### Task 2: Transport and cancellation contract

**Tests first:**
- device-authorization connection error does not enter OTP;
- repository login/send/verify propagates `MyVerisureConnectionError`;
- post-OTP connection error is not converted to success/auth failure;
- `CancelledError` propagates and does not become a provider/auth outcome.

**Production changes:**
- Preserve `MyVerisureConnectionError` before generic handlers at every adapter/repository boundary.
- Remove verified-session fallback after post-OTP failure.
- Add explicit `asyncio.CancelledError` branches where a broad handler surrounds transport.
- Keep bounded HTTP timeout and generic connection logging without raw causes.

**Verification:** focused AuthClient/BaseClient/repository matrix and log assertions.

### Task 3: OTP challenge lifecycle and selection

**Tests first:**
- challenge missing, empty, malformed, expired, exhausted;
- missing/invalid/non-positive `record_id` rejected;
- invalid selection cannot call send;
- valid selection must precede send;
- successful verification replay cannot call provider or persistence.

**Production changes:**
- Strictly validate provider phone metadata in `OTPAuthorizationPolicy`.
- Never default `record_id` to UI `phone_id`.
- Consume challenge only after authenticated session persistence succeeds; invalidate expiry and exhaust attempts.
- Preserve fail-closed behavior on persistence failure and cancellation.

**Verification:** use-case, policy, config-flow, reauth, and CLI selection-order tests.

### Task 4: Transactional session persistence

**Tests first:**
- persistence failure raises a sanitized typed/controlled error at the application boundary;
- failed async and sync persistence restore all previous session fields and authentication state;
- config flow does not proceed to installation after persistence failure;
- reauth does not mutate the existing ConfigEntry after persistence failure.

**Production changes:**
- Make session writes fail visibly rather than logging and returning.
- Roll back in-memory credentials/tokens/timestamp/authenticated state on failed writes.
- Ensure `AuthSessionPersistence` persists only successful authenticated results.
- Preserve cancellation rather than catching it as a normal persistence failure.

**Verification:** persistence and lifecycle focused suites plus source audit for unconditional success after failed writes.

### Task 5: Clean Architecture composition and async boundaries

**Tests first:**
- AuthClient receives the exact composition-owned `AuthSessionPersistence` instance;
- AuthUseCase receives the same semantic persistence boundary;
- config-flow phone lookup executes through HA executor;
- no direct application construction of infrastructure/persistence remains.

**Production changes:**
- Inject `AuthSessionPersistence` from `core/dependency_injection/module.py`.
- Keep AuthClient, AuthRepository, AuthUseCase, and config flow contracts compatible without shims.
- Keep all synchronous phone lookup and composition construction off the event loop.

**Verification:** dependency-injection, composition-root, architecture guard, and focused config-flow tests.

### Task 6: Full contract matrix and fixture hygiene

1. Replace credential/token/hash/OTP/identity literals in changed fixtures with `[REDACTED]` or named non-sensitive sentinels; preserve behavioral distinctions without secret-shaped values.
2. Add complete-chain tests where feasible: BaseClient → AuthClient → repository → use case → config flow.
3. Verify initial login, device authorization, phone selection, OTP send/verify, installation, reauth, timeout, connection, cancellation, expiry, max attempts, replay, empty phones, malformed phones, and persistence failure.
4. Run focused suites and require plausible test counts.

### Task 7: Global gates

Run from `/home/efraespada/my_verisure`:

```bash
/tmp/my-verisure-ha-2026.8.1-venv/bin/python -m pytest -c pytest.ini \
  --cov=custom_components/my_verisure --cov-context=test \
  --cov-report=term --cov-report=xml -q
HA_PYTHON=/tmp/my-verisure-ha-2026.8.1-venv/bin/python bash scripts/test-ha-2026.8.sh
/tmp/my-verisure-ha-2026.8.1-venv/bin/python -m mypy --explicit-package-bases --ignore-missing-imports custom_components/my_verisure
python -m compileall -q custom_components/my_verisure cli
python scripts/architecture_guard.py
python scripts/validate_distribution.py
/tmp/my-verisure-ha-2026.8.1-venv/bin/python -m pip check

git diff --check
/tmp/my-verisure-security-venv/bin/python -m bandit -r custom_components/my_verisure -x '*/tests/*' -lll -f txt
/tmp/my-verisure-security-venv/bin/python -m pip_audit -r requirements.txt --strict
```

Run the repository's focused critical Flake8 command for changed production files. Classify historical full-Flake8 W293/E501 and upstream dependency findings separately; do not hide them or attribute them to OTP.

### Task 8: Freeze candidate and independent review

1. `git add -A` only after all intended changes and fixture cleanup are complete.
2. Verify `git diff --cached --check`.
3. Compute:

```bash
GIT_OPTIONAL_LOCKS=0 git write-tree
git diff --cached --binary --full-index | sha256sum
git diff --name-only
```

4. Require zero unstaged and zero untracked source paths.
5. Dispatch a strictly read-only reviewer with the exact tree, diff SHA, serialization command, base SHA, and no-mutation rules.
6. Recompute the exact fingerprint after review. Any mismatch invalidates the verdict.

### Task 9: Closure decision

- If reviewer returns `CHANGES_REQUESTED`: record findings, keep publication blocked, and repeat from Task 1 for the new candidate.
- If reviewer returns `APPROVED`: perform one final status/diff/gate readback. Commit and push only if the user’s publication policy is explicitly active and every gate is green; otherwise leave staged and report the exact approved candidate.
- Never claim provider-real validation without real authorized credentials; this plan uses only deterministic fakes and Home Assistant test environment.

## Acceptance criteria

The work is complete only when all are true:

- [ ] Every invariant above is executable by a test or source-level guard.
- [ ] Full suite passes with plausible count and coverage artifact.
- [ ] Home Assistant 2026.8.1 compatibility suite passes.
- [ ] Mypy, compileall, architecture, distribution, pip check, Bandit, critical Flake8, and diff hygiene pass.
- [ ] Sensitive sentinel scan is clean across logs, exceptions, CLI, diagnostics, fixtures, and reports.
- [ ] No blocking synchronous call remains in async config flow.
- [ ] AuthClient does not construct application persistence internally.
- [ ] Failed persistence cannot produce authenticated success or installation.
- [ ] OTP challenge is single-use and fail-closed on all negative paths.
- [ ] Staged candidate has zero unstaged source changes.
- [ ] Independent read-only review approves the exact final fingerprint.
- [ ] No commit/push happens before the approval gate.

## Stop conditions

Stop and report without publication if:

1. Any OTP-specific test fails.
2. Any sensitive value appears in a log, exception, CLI output, fixture, or generated report.
3. Any transport or cancellation path becomes success/auth/OTP incorrectly.
4. Persistence failure leaves changed authenticated state or reaches installation.
5. Any synchronous network/filesystem call remains in an async config-flow path.
6. The global suite or a required gate is incomplete, zero-test, or suspiciously narrow.
7. The independent reviewer cannot verify the exact fingerprint or returns `CHANGES_REQUESTED`.
8. A tool mutates the candidate during read-only review.

## Evidence ledger to update during execution

| Block | RED evidence | GREEN evidence | Global evidence | Status |
|---|---|---|---|---|
| Transport/cancellation | command + expected failure | focused pass count | full suite pending | in progress |
| OTP lifecycle | command + replay/expiry failure | focused pass count | full suite pending | in progress |
| Persistence | command + rollback failure | focused pass count | full suite pending | in progress |
| Redaction/fixtures | sentinel leak failure | redaction pass count | source scan pending | in progress |
| Composition/async | contract failure | DI/config-flow pass count | architecture/mypy pending | in progress |
| Final gates/review | n/a | all gates | exact fingerprint + reviewer verdict | blocked until complete |

## Execution evidence — 2026-08-24

The implementation phase has been executed through the pre-review gate:

- Focused transport/device/repository matrix: **30 passed**.
- Focused authentication/use-case/repository/session/config-flow matrix: **62 passed**.
- Focused redaction/session matrix: **24 passed**.
- Focused composition/lifecycle matrix: **15 passed**.
- Full repository suite: **558 passed in 5.30s**.
- Coverage: **87%**, **9,872 statements**, `coverage.xml` generated.
- Home Assistant 2026.8.1 compatibility script: **558 passed**.
- Mypy: **216 source files, no issues**.
- Compileall: passed.
- Architecture guard: `ARCHITECTURE_GUARD_OK`.
- Distribution validation: `DISTRIBUTION_VALIDATION_OK`.
- Dependency consistency: `No broken requirements found`.
- Critical Flake8 (`E9,F63,F7,F82`): passed with no output.
- Bandit medium/high: no issues identified.
- pip-audit: no known vulnerabilities found.
- Changed-Python sensitive-constant AST scan: **0 findings**.
- `git diff --check`: passed.

The final independent review and exact candidate fingerprint remain mandatory closure gates. The historical `CHANGES_REQUESTED` verdict is not reused for this candidate.

## Execution evidence — post-review remediation closure — 2026-08-24

The independent review findings were remediated with focused RED→GREEN cycles covering post-OTP transport/error propagation, explicit device-authorization classification, selected-phone/`record_id` binding, persistence rollback and cancellation, OTP hash validation, diagnostics/CLI redaction, fixture PII hygiene, and the missing `installation_not_found` translations.

Current verification was rerun after the final source and fixture edits:

- Focused remediation matrix: **118 passed** before the final fixture-only hygiene pass.
- Final HA/lifecycle/redaction/mapper matrix: **24 passed**.
- Full repository suite with coverage: **578 passed in 5.45s**, **87%**, **10,055 statements**, `coverage.xml` generated.
- Home Assistant 2026.8.1 compatibility suite: **578 passed in 3.54s**.
- Mypy canonical Makefile gate (`--explicit-package-bases --ignore-missing-imports cli custom_components scripts`): **237 source files, no issues**.
- Compileall: passed.
- Architecture guard: `ARCHITECTURE_GUARD_OK`.
- Distribution validation: `DISTRIBUTION_VALIDATION_OK: dist/my_verisure.zip`.
- Dependency consistency: `No broken requirements found`.
- Critical Flake8 (`E9,F63,F7,F82`): passed with no output.
- Bandit medium/high: **0 findings**.
- pip-audit: **No known vulnerabilities found**.
- Changed-Python sensitive-constant AST scan: **0 findings**.
- `git diff --check`: passed.

The candidate must now be staged completely, fingerprinted with the exact tree and binary cached-diff serialization, and independently reviewed read-only. No commit, push, or publication is allowed before a new exact-fingerprint `APPROVED` verdict.

## Execution evidence — current remediation gate — 2026-08-24

The post-review remediation was continued on the same branch and checkout. The rejected fingerprint was not reused.

- New RED→GREEN coverage: malformed OTP challenge, invalid phone binding, post-OTP device-authorization propagation, successful-session persistence, CLI duplicate-write removal, diagnostics installation-ID redaction, runtime translation parity.
- Focused remediation matrix: **122 passed**; the additional invalid-phone-binding regression: **1 passed**.
- Full repository suite with coverage: **585 passed in 5.47s**, **87%**, **10,145 statements**, `coverage.xml` generated and pending cleanup before staging.
- Home Assistant 2026.8.1 compatibility suite: **585 passed in 3.56s**.
- Mypy canonical gate: **237 source files, no issues**.
- Compileall: passed.
- Architecture guard: `ARCHITECTURE_GUARD_OK`.
- Distribution validation: `DISTRIBUTION_VALIDATION_OK: dist/my_verisure.zip`.
- Dependency consistency: `No broken requirements found`.
- Critical Flake8 (`E9,F63,F7,F82`): passed.
- Bandit medium/high: **0 findings**.
- Runtime dependency audit: `pip-audit -r requirements.txt` → **No known vulnerabilities found**.
- Toolchain audit caveat: auditing the full security venv reports vulnerabilities in its own `pip 24.0`/`setuptools 79.0.1`; these are not project runtime dependencies. Auditing `requirements-dev.txt` from that Python 3.11 environment cannot resolve `homeassistant==2026.8.1`, which requires Python >=3.14.2. This remains an environment limitation, not a claim of a green full-development audit.
- Sensitive-constant AST scan: **0 findings**.
- Runtime/config-flow translation error-key parity: **13 keys for en and 13 keys for es**.
- `git diff --check`: passed.
- No commit, push, publication, real credentials, or real provider request performed.

Remaining closure work: remove generated coverage artifacts, verify the real brand-icon paths are unchanged, restage all intended changes, recompute exact tree/diff fingerprints, and obtain a new strictly read-only independent review. Publication remains blocked until that review returns `APPROVED`.

## Execution evidence — remediation after independent review — 2026-08-24

The independent read-only review of `TREE=605791e3e16ee4482d650b2f9d4bbf275761d359` returned `CHANGES_REQUESTED`. Its integrity evidence was valid; that candidate is rejected and its fingerprint is not reused. One reported P0 was an excerpt-rendering artifact: the actual source line is valid `_LOGGER.error(` and compileall had already passed. The actionable P1 findings were remediated with new RED→GREEN cycles:

- `verify_otp()` now requires an active OTP challenge before provider access.
- Post-OTP `OSError`, timeout, and `aiohttp.ClientError` remain transport errors and cannot consume OTP attempts.
- Post-OTP `res=OK` without a non-empty string hash is rejected; the previous hash cannot be reused.
- `_perform_post_otp_login()` no longer mutates local client state before application persistence; committed session state is read from `SessionManager`.
- CLI phone selection and OTP entry use `asyncio.to_thread`, preserving the event loop.
- A call-count regression proves successful device-check login persists exactly once.
- The CLI regression uses deliberately distinct `id=1` and `record_id=70` and asserts that `send_otp(70)` is called.

Current verification after those corrections:

- Full repository suite with coverage: **590 passed in 5.46s**, **87%**, **10,199 statements**, `coverage.xml` generated and pending cleanup.
- Home Assistant 2026.8.1 compatibility suite: **590 passed in 3.48s**.
- Mypy: **237 source files, no issues**.
- Compileall, architecture guard, distribution validation, `pip check`: passed.
- Critical Flake8: passed.
- Bandit medium/high: **0 findings**.
- Runtime `pip-audit -r requirements.txt`: **No known vulnerabilities found**.
- Sensitive AST scan: **0 findings across 33 Python files**.
- `git diff --check` and cached diff check: passed.

A new exact fingerprint and a new independent read-only review are required. No commit, push, or publication is allowed before the new review returns `APPROVED`.

## Execution evidence — current candidate after second review remediation — 2026-08-25

The second independent review of `TREE=48e993d5766ddda19f6833c03b3f7e74fbbd3815` / `DIFF_SHA=2a672bdcb8d97b6a001953580e4b2c6f016d6305b031554cad249a59387e618f` returned `CHANGES_REQUESTED`. That fingerprint is rejected and will not be reused. Its actionable findings were then addressed with additional RED→GREEN cycles:

- Transport/timeout propagation is preserved through AuthClient, repository, and use case for post-OTP paths.
- Fresh post-OTP hashes are taken from the returned `AuthDTO`; no previous client hash/refresh token fallback remains.
- AuthClient uses explicit pending authentication state for an uncommitted transaction and promotes it only after persistence succeeds; committed state remains owned by `SessionManager`.
- Missing OTP TTL is fail-closed in both send and verify paths.
- Direct AuthClient send/verify calls reject missing or malformed challenge data, invalid `record_id` binding, and blank codes before provider access.
- Generic persistence validates a non-empty string hash and synchronous rollback restores the complete prior projection for any `Exception`.
- Runtime/config-flow translation error-key parity: **14 keys for en and 14 keys for es**.

Final verification after these changes:

- Full repository suite with coverage: **607 passed in 5.63s**, **88%**, **10,375 statements**, `coverage.xml` removed after measurement.
- Focused authentication/repository/use-case/CLI matrix: **108 passed**.
- Mypy: **237 source files, no issues**.
- Compileall: passed.
- Architecture/distribution contracts: passed.
- `pip check`: passed.
- Critical Flake8 (`E9,F63,F7,F82`): passed with no output.
- Bandit medium/high: **0 findings**.
- Runtime `pip-audit -r requirements.txt`: **No known vulnerabilities found**.
- Sensitive-constant AST scan: **0 findings**.
- `git diff --check`: passed.

The candidate is now ready for final staging/fingerprinting and a fresh strict read-only review. No commit, push, or publication is allowed before exact-fingerprint `APPROVED`.

## Execution evidence — final remediation after third independent review — 2026-08-25

The independent read-only review of `TREE=e3f9549f6aba712644f552f9b2220311d8d35440` / `DIFF_SHA=add0821abdf6eaaa5c77526293832603214818110593862ee5a744380b15e557` returned `CHANGES_REQUESTED`. Its before/after integrity evidence was unchanged, so the finding set is authoritative for that rejected candidate only. The actionable findings were remediated with RED→GREEN cycles:

- Session persistence now writes a complete temporary file, flushes and fsyncs it, and replaces the committed file atomically with `os.replace`.
- Async persistence snapshots the prior file, shields the worker, waits for a cancelled worker to finish, restores the prior file atomically, and re-raises cancellation.
- Sync persistence and the compatibility writer restore the prior file projection on any exception.
- `AuthClient.login()` and `AuthUseCaseImpl.login()` invalidate stale OTP/pending state before every new authentication attempt.
- `AuthClient` now enforces challenge TTL and one-time consumption independently before `send_otp()`/`verify_otp()` provider access.
- `persist_result()` requires a non-empty string hash independently of the DTO/repository boundary.
- `aiohttp.ClientError` is translated to `MyVerisureConnectionError` in the repository adapter; application use cases no longer import the transport SDK.
- CLI setup and installation-selection failures emit fixed sanitized messages rather than raw exception text.
- Main English/Spanish translations now contain exactly the runtime/config-flow error keyset; synthetic email fixtures were replaced with non-email sentinels.

Final verification after this remediation:

- Full repository suite with coverage: **616 passed in 5.60s**, **88%**, **10,541 statements**.
- Mypy: **237 source files, no issues**.
- Compileall: passed.
- Architecture guard: `ARCHITECTURE_GUARD_OK`.
- Distribution validation: `DISTRIBUTION_VALIDATION_OK: dist/my_verisure.zip`.
- `pip check`: `No broken requirements found.`
- Critical Flake8 (`E9,F63,F7,F82`): passed with no output.
- Bandit medium/high: **0 findings**.
- Runtime `pip-audit -r requirements.txt`: **No known vulnerabilities found**.
- Sensitive-constant AST scan: **0 findings**.
- Runtime/main/config-flow translation keysets: **14 keys aligned for en and es**.
- `git diff --check`: passed.
- `coverage.xml` removed before staging; no commit, push, publication, real credentials, or real provider request performed.

The rejected fingerprint `e3f9549f…` is not reusable. The current state requires a new exact staging fingerprint and a fresh independent read-only review before any publication decision.

## Execution evidence — fourth remediation cycle — 2026-08-25

The post-review hardening continued without reusing any rejected fingerprint:

- Application-owned exception classes were introduced in `core/application/exceptions.py`; `api.exceptions` remains a compatibility export, while the use case imports only application errors.
- HTTP `401` and all other `>=400` responses are rejected before JSON/GraphQL interpretation; transport errors remain typed.
- Async session persistence is serialized per manager; synchronous compatibility persistence is protected by an `RLock`; rollback failures cannot replace the original cancellation.
- CLI command failures use fixed messages; installation identifiers, phone values, OTP codes, serials, device identifiers, and provider exception text are redacted.
- Interactive installation selection, alarm confirmation, and credential collection invoked from async commands run through `asyncio.to_thread`.
- A stale CLI test expectation was updated to assert that the provider exception is not emitted.

Current verification after this cycle:

- Full repository suite with coverage: **620 passed in 5.67s**, **88%**, **10,672 statements**.
- Focused regression matrix: **21 passed**.
- Mypy: **238 source files, no issues**.
- Compileall: passed.
- Architecture guard: `ARCHITECTURE_GUARD_OK`.
- Distribution validation: **2 passed**.
- `pip check`: `No broken requirements found.`
- Critical Flake8 (`E9,F63,F7,F82`): passed with no output.
- Bandit production medium/high: **0 findings**.
- Runtime `pip-audit -r requirements.txt`: **No known vulnerabilities found**.
- Production sensitive-constant AST scan: **0 findings**.

## Execution evidence — fifth remediation cycle — 2026-08-25

The independent review blockers were closed without reusing any rejected fingerprint:

- OTP format is enforced centrally as exactly six ASCII digits and checked in the use case, API client, config flow, and CLI before provider access.
- OTP invalidation is coordinated across application state, repository, and API client on new authentication, send/verify failures, cancellation, persistence failure, and irreversible provider acceptance.
- Post-OTP persistence remains owned only by the application use case; `AuthClient` returns fresh DTO data and does not construct or invoke session persistence.
- Timeout, connection, authorization, authentication, persistence, and cancellation retain typed fail-closed semantics.
- Redaction now recursively handles tuples, sets, dataclasses, exceptions, and unknown objects without `default=str`, preventing DTO `repr` leakage.
- Obsolete persistence-era test attributes and token-shaped fixtures were removed or replaced with explicit sentinels.
- Config-flow fake contracts and the missing `CONF_INSTALLATION_ID` import were corrected.

Final verification on the current checkout:

- Full repository suite with coverage: **634 passed in 5.67s**, **87%**, **10,760 statements**; `coverage.xml` removed after measurement.
- Focused OTP/application/redaction matrix: **128 passed**.
- Mypy with explicit package bases and missing third-party stubs ignored: **217 source files, no issues**.
- Compileall: passed.
- Architecture guard: `ARCHITECTURE_GUARD_OK`.
- Distribution validation: `DISTRIBUTION_VALIDATION_OK: dist/my_verisure.zip`.
- `pip check`: `No broken requirements found.`
- Critical Flake8 (`E9,F63,F7,F82`): passed with no output.
- Bandit production medium/high: **0 findings**.
- Runtime `pip-audit -r requirements.txt`: `No known vulnerabilities found`.
- Config-flow translations: **34 leaves aligned and non-empty**.
- Sensitive-literal scan limited to repository sources: **0 findings**.
- `git diff --check`: passed.

## Execution evidence — sixth remediation cycle — 2026-08-25

The final independent-review blockers were remediated without reusing the rejected candidate:

- Authentication models (`Auth`, `AuthResult`, `OTPData`, `Phone`) now have canonical application-layer ownership under `core/application/models/auth.py`; API model imports remain compatibility exports for adapters/tests only.
- OTP authorization policy no longer imports `PhoneDTO` from the API layer; it operates on the application-owned `Phone` model and the API adapter maps at its boundary.
- Persistence validation failures now raise `MyVerisurePersistenceError`, not raw `ValueError`; the use case preserves the typed boundary.
- Reauthentication credentials remain pending inside the use case until authentication and persistence succeed. `config_flow.py` no longer overwrites the active `SessionManager` before that point.
- `AuthSessionPersistence.persist_result()` accepts explicit pending credentials and updates the session only after validated provider data; regression tests prove old active credentials remain untouched on failure and new credentials are used on success.
- Automatic reauthentication now has a single persistence owner: the injected authentication callback persists the result, while `SessionManager` no longer performs a second update/write.
- Reauthentication persistence failures map to the sanitized `cannot_persist` presentation outcome.
- Authentication repository adapters translate raw `OSError` into sanitized `MyVerisureConnectionError` while preserving `asyncio.CancelledError`.
- The OTP replay decision was corrected in the plan: the challenge is consumed immediately after provider acceptance, before post-login, persistence, or cancellation.
- Translation resources were completed and structurally aligned: base/en/es semantic structures are identical; both config-flow locales contain **34 aligned leaves**.

Final verification on the exact current checkout:

- Full repository suite with coverage: **639 passed in 5.62s**, **87%**, **10,842 statements**; coverage artifact removed after measurement.
- Focused post-review matrix: **47 passed**; persistence-specific matrix: **16 passed**.
- Mypy with explicit package bases and missing third-party stubs ignored: **219 source files, no issues**.
- Compileall: passed.
- Architecture guard: `ARCHITECTURE_GUARD_OK`.
- Distribution validation: `DISTRIBUTION_VALIDATION_OK: dist/my_verisure.zip`.
- `pip check`: `No broken requirements found.`
- Critical Flake8 (`E9,F63,F7,F82`): passed with no output.
- Bandit production medium/high: **0 findings**.
- `pip-audit -r requirements.txt --strict`: `No known vulnerabilities found`.
- Translation structure and Python AST scan: **67 aligned base/en/es leaves**, **34 config-flow leaves**, **238 Python files parsed**, **0 real emails**.
- `git diff --check`: passed.

The security environment itself reports vulnerabilities in its installed `pip`/`setuptools`; that environment finding is kept separate from the green repository requirements audit and is not misrepresented as an application gate.

## Execution evidence — seventh remediation cycle — 2026-08-25

The independent review `deleg_500494b3` identified four additional fail-closed blockers; all were remediated with focused RED→GREEN regressions:

- Reauthentication now snapshots entry data, checks that `async_reload()` returns `True`, restores the previous entry data on `False` or exception, attempts a restoring reload, and returns `cannot_persist` instead of `reauth_successful`. Cancellation restores the entry before propagating.
- Coordinator session files are derived from `entry_id`, never the username. Initial config flows use a temporary `flow_<flow_id>` file only before an entry exists and remove it before creating the entry; reauth uses the stable entry-derived path.
- Retryable provider OTP rejections preserve the active challenge and increment attempts; the challenge is invalidated only when the configured maximum is reached or the condition is terminal.
- OTP metadata rejects conflicting `recordId`/`record_id` aliases instead of silently preferring one.
- `AuthClient.verify_otp()` preserves the challenge for provider `MyVerisureOTPError`; terminal invalidation remains coordinated by the application use case.

Final verification after this remediation:

- Full repository suite with coverage: **642 passed in 5.73s**, **87%**, **10,920 statements**; coverage artifact removed after measurement.
- Focused auth/OTP/reauth matrix: **102 passed**.
- Mypy: **219 source files, no issues**.
- Compileall: passed.
- Architecture guard: `ARCHITECTURE_GUARD_OK`.
- Distribution validation: `DISTRIBUTION_VALIDATION_OK: dist/my_verisure.zip`.
- Critical Flake8: passed with no output.
- Bandit: 0 findings.
- pip-audit: `No known vulnerabilities found`.
- pip check: `No broken requirements found.`
- Translation structure: base/en/es 67 leaves and config flow 34 leaves aligned.
- Python AST/sensitive scan: 238 files parsed, 0 real emails.
- `git diff --check`: passed.

## Execution evidence — eighth remediation cycle — 2026-08-25

The independent review `deleg_387adf19` identified three additional blockers; all were remediated with focused RED→GREEN regressions:

- Reauthentication now snapshots in-memory session state and exact session-file bytes before login. Rollback restores entry data, session memory, session bytes, and a confirmed reload under a shielded task. `CancelledError` is re-raised after rollback attempts and cannot be replaced by a rollback exception; normal rollback failure returns `cannot_persist` and never false success.
- Temporary initial-flow storage now has idempotent asynchronous whole-root cleanup. It runs before `async_create_entry()` and is scheduled on terminal `async_abort()` paths, removing the session JSON and the generated `data/` tree rather than leaving `my_verisure_flow_<flow_id>` artifacts.
- OTP provider failures carry typed `retryable`/`terminal` classification and a provider code. Only explicit invalid-code responses (`invalid code`, `incorrect code`, `wrong code`, or allowlisted provider codes) increment attempts; expired, blocked, malformed, missing, or ambiguous responses invalidate immediately.

Final verification for this remediation cycle:

- Full repository suite: **646 passed in 5.83s**, **87%**, **11,021 statements**.
- Focused reauth/session/file/OTP matrix: **102 passed**.
- Mypy: **219 source files, no issues**.
- Compileall, architecture guard, distribution validation, critical Flake8, Bandit, pip-audit, pip check, translations/AST and sensitive-data checks passed.

## Execution evidence — ninth remediation cycle — 2026-08-25

The independent review `deleg_18a4735c` identified eight blockers; this cycle addressed them with focused regressions:

- Reauthentication hydrates the entry-scoped session before snapshotting. Rollback now verifies complete in-memory state, exact session bytes, entry data, successful reload, and re-read entry identity. An unconfirmed rollback is fail-closed `cannot_persist`; cancellation remains cancellation after protected rollback attempts.
- `SessionManager` credential rollback covers the complete transaction snapshot, including current installation and disk-hydration state.
- `device_identifiers.json` is now stored under each entry's `project_root/data`, preventing cross-entry overwrites and ensuring whole-root cleanup removes it.
- Explicit config-flow abort paths await and verify cleanup of the temporary root and session JSON. External synchronous HA abort hooks schedule the same verification helper without blocking I/O.
- Device authorization aliases (`auth-code`/`authCode`, `auth-type`/`authType`) and OTP direct/nested envelopes reject conflicting ambiguity instead of silently prioritizing one value.
- Provider response messages are stable and redacted; raw provider text cannot reach `MyVerisureOTPError` or upper layers.
- `config_flow.py` now imports canonical application exceptions rather than the API compatibility package.

Verification:

- Full repository suite: **651 passed in 5.78s**, **87%**, **11,109 statements**.
- Focused remediation matrix: **81 passed**.
- Mypy: **219 source files, no issues**.
- Compileall, architecture guard, distribution validation, critical Flake8, Bandit, pip-audit, pip check, translations/AST and sensitive-data checks passed.

## Execution evidence — tenth remediation cycle — 2026-08-25

The independent review `deleg_04073816` rejected the previous candidate. This cycle addressed every reported blocker:

- Corrected invalid annotations in the canonical application model and active API DTO.
- Reauthentication now snapshots original entry data before login; invalid post-OTP sessions use the verified transactional rollback instead of merely showing an error.
- Automatic reauthentication requires `is_session_valid()`, not only credential presence, and restores memory plus exact disk bytes when a successful callback does not establish a valid session.
- Session rollback now recaptures and compares both memory and bytes; failed confirmation triggers fail-closed credential clearing while preserving cancellation propagation.
- Pending authentication fields are cleared on every post-OTP failure or cancellation, and malformed OTP challenges invalidate application state before raising.
- Initial-flow cleanup is awaited and verifies the temporary root, `session.json`, and `device_identifiers.json`; the asynchronous override that only scheduled cleanup was removed.
- Session and device identifier files are both entry-scoped under `<root>/data`.
- Transaction snapshots deep-copy mutable `current_installation` state.
- Login, device-authorization, coordinator, notification, and command-result error channels now use stable messages without raw provider text.
- Added regressions for post-OTP pending-state cleanup, deep-copy snapshots, valid-token automatic reauth, entry-scoped session paths, sanitized failures, and cleanup behavior.

Verification:

- Full repository suite: **652 passed in 5.67s**, **87%**, **11,168 statements**.
- Focused remediation matrix: **120 passed**, plus the new snapshot and pending-state regressions.
- Mypy: **219 source files, no issues**.
- Compileall, architecture guard, distribution validation, critical Flake8, Bandit, pip-audit, pip check, translations/AST and sensitive-data checks passed.

The previous candidate fingerprint is invalidated. A fresh exact fingerprint and independent read-only review are mandatory; no commit, push, or publication is authorized.
