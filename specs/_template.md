# Capability specification

- Status: Draft
- Date: YYYY-MM-DD
- Catalog capability ID: stable-capability-id
- Last verified: not applicable until evidence is recorded
- Owners: My Verisure maintainers
- Scope: one independently reviewable capability
- Required review gates: behavior, architecture, testing, documentation, security/operations
- Open decisions blocking readiness: list unresolved decisions explicitly

## 1. Executive summary

State the outcome, default and principal correctness rule.

## 2. Problem, current behavior and evidence

Separate observed behavior, intentional contract, known debt, unknown historical
rationale and proposed improvements. Link inspected sources and dated evidence.

## 3. Actors, surfaces and terminology

Define users, Home Assistant, Verisure, adapters and shared product terms.

## 4. Goals, non-goals and fixed invariants

Give requirements stable IDs. Distinguish product invariants from session-specific
limits on authorized live testing.

## 5. Current versus intended journey

Show dependent transitions in a diagram and adjacent textual equivalent.

## 6. Functional behavior and state model

Specify normal, alternative, duplicate, stale, concurrent, canceled and partial paths.

## 7. User-facing configuration

Document types, defaults, bounds, invalid combinations, precedence, persistence,
migration and one meaningful alternative.

## 8. Clean Architecture design

Name actual files, use cases, semantic ports, adapters, composition and prohibited
dependencies. Specify executable architecture checks.

## 9. UI/UX and content contract

Provide concrete pending, action-required, error, partial and completed views,
including localization, accessibility and mobile behavior.

## 10. Failure, recovery and cleanup

Explain impact, retained facts, retry policy, human action and owned cleanup.

## 11. Security, permissions and privacy

Define trusted inputs, authorization, secret storage, logging and replay boundaries.

## 12. Observability and operations

Define safe evidence, timing boundaries, rate limits and notification budget.

## 13. Compatibility, migration, rollout and rollback

Preserve existing entity IDs, device settings and account isolation.

## 14. Testing strategy and numeric budget

Derive distinct-case minima from risks. State measured coverage separately from
enforced thresholds. Use deterministic clocks, fakes and synthetic fixtures.

## 15. Documentation and discoverability

List exact existing or proposed file paths, intended changes and navigation.

## 16. Acceptance scenarios

Write observable Given/When/Then scenarios for every normative requirement.

## 17. Requirements traceability

Map each requirement to its owner, test/evidence and documentation.

## 18. Implementation or maintenance sequence

Order contracts, policy, adapters, presentation, migration, documentation and evidence.
For a baseline, describe future maintenance rather than claiming new implementation.

## 19. Definition of Done

- [ ] Requirements, acceptance and traceability agree.
- [ ] Architecture, tests, configuration, migration and documentation are verified.
- [ ] Partial success, retry, privacy, cancellation and cleanup are covered.
- [ ] Live evidence and its limits are stated accurately.
- [ ] Catalog and Markdown inventory agree; unresolved decisions remain visible.

## 20. References and decisions

Link primary sources, related SDDs and dated decisions. Separate follow-up work.
