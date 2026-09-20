# EVOLUTION.md — Cortex Core Enterprise

A plan for how the codebase moves from v3.0.0 (2026) toward a system that is still coherent, verifiable, and runnable in 2050.

## 0. Guiding principles

1. The journal is the source of truth.
2. Canonical bytes are permanent.
3. Version everything that can change.
4. Tests are the specification.
5. No magic.

## 1. From v3.0.0 to v4.0.0

Goals: multi-node operation with real Raft consensus, storage abstraction, signature algorithm agility, timestamp format normalized to Unix epoch milliseconds, branch coverage enforced.

Work items: replace datetime.utcnow() with timezone-aware or integer timestamps; introduce a JournalStorage interface with FileStorage, S3Storage, HttpStorage implementations; replace the stubbed DistributedCoordinator with a real Raft implementation; add signature algorithm dispatch based on the schema field; enforce branch coverage in pytest-cov configuration.

Breaking change policy: v4.0.0 is a major bump because the event envelope changes and the timestamp format changes. Old readers reject v4 events. New readers accept both v3 and v4 events. Existing v3 journals are preserved byte-for-byte in journal/historical/ and read-only.

## 2. From v4.0.0 to v5.0.0

Goals: cryptographic agility fully deployed, pluggable fold versions, cross-journal references, snapshot checkpoints.

Work items: fold dispatches on foldVersion to support v1, v2, v3 simultaneously; events gain optional references field for cross-journal anchoring; define checkpoint format with signed state snapshots.

## 3. Beyond v5.0.0

Long-term principles: never delete history, never change canonical bytes, never require a specific OS, never require a specific programming language.

The 2050 test:
1. Cold-start test — reconstruct runtime from tarball in under one hour.
2. Journal verification test — all signatures and hashes validate.
3. Cross-version test — 2050 fold reads 2026 events and produces consistent state.
4. Independence test — journal verifiable without the private key.

## 4. Concrete near-term actions

1. Commit and tag v3.0.0.
2. Generate requirements.lock.
3. Write BUILD.md and EVOLUTION.md.
4. Add .github/workflows/test.yml enforcing 100 percent coverage.
5. Build a Docker image.
6. Write SECURITY.md.
7. Publish the genesis hash.
8. Archive to Software Heritage and IPFS.

## 5. Timeline

- 2026 — v3.0.0 frozen, docs written, Docker image published.
- 2027 — v4.0.0 multi-node.
- 2028 — v4.x hardening.
- 2029 — v5.0.0 cross-journal and snapshots.
- 2030+ — deployments in production.
- 2040+ — archive refresh.
- 2050+ — the system runs. Journals verify. History is intact.

---

End of EVOLUTION.md