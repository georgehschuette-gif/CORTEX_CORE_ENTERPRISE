# BUILD.md — Cortex Core Enterprise v3.0.0

A complete, reproducible snapshot of the toolchain required to build, test, and run cortex_core as of release v3.0.0.

## 1. Release identity

- Project: cortex-core
- Version: 3.0.0
- Release date: 2026-09-20
- Test count: 295
- Test pass rate: 100 percent
- Line coverage: 100 percent

The release tag in git is v3.0.0.

## 2. Operating system

Developed and tested on Windows 11 Pro build 26100 or later, and on Linux with Python 3.12.

## 3. Language runtime

- Python: >=3.12,<3.13 (tested: 3.12.0)
- pip: >=23.2 (tested: 23.2.1)
- venv: bundled with Python

Python 3.12 is required because datetime.UTC exists, tomllib is in the standard library, and all dependencies support it.

## 4. Dependencies

Runtime: fastapi, uvicorn, pydantic, pyyaml, python-dotenv, requests, structlog, prometheus_client, PyJWT.

Development and test: pytest, pytest-cov, httpx.

Excluded: torch. The ML model definitions live in python/ and are not imported by the cortex_core runtime.

## 5. Reproducing the build

1. Clone the repo.
2. Checkout the v3.0.0 tag.
3. Create a virtual environment with Python 3.12.
4. Install dependencies with pip install -e . plus pytest, pytest-cov, httpx.
5. Run pytest tests/unit/ -v.
6. Expected: 295 passed.
7. Run pytest tests/unit/ -q and confirm coverage table shows TOTAL 1600 0 100 percent.

## 6. Long-term storage

Container image pushed to multiple registries, signed tarball stored on physical media, paper copy of critical files, IPFS pin, Software Heritage archive.

## 7. Release history

v3.0.0 — 2026-09-20 — First fully-tested release. 295 tests, 100 percent coverage. Seven production bugs fixed.

---

End of BUILD.md