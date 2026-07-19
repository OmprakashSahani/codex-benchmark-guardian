# Codex Benchmark Guardian Repository Guide

## Architecture

- `src/codex_benchmark_guardian/` contains the Python benchmark, regression, readiness, reporting, and gate logic. This Python engine is the source of truth.
- `api/` exposes the Python engine through FastAPI.
- `app/`, `components/`, and `lib/` contain the Next.js dashboard. It renders engine results and must not duplicate benchmark business logic.
- `app.py` is the supported Streamlit interface.
- `benchmarks/` contains the protected benchmark harness; `tests/` covers the Python engine and interfaces; `examples/` contains sample evidence and configuration.
- The protected GitHub evaluator makes the final PR readiness decision.

## Repair Boundaries

Prefer minimal root-cause fixes. Codex may investigate, edit, test, benchmark, review the diff, and prepare a patch. It may not declare its patch Ready or merge automatically. Only protected benchmark evidence may return a PR to Ready, and human review is required before merge.

Never lower thresholds to make a repair pass, alter metric directions to hide a regression, weaken, skip, replace, or bypass the protected harness or evaluator, or delete or skip tests to obtain Ready.

## Required Checks

Run `make lint`, `make format-check`, `make test`, `npm run lint`, `npm run typecheck`, and `npm run build`. Performance repairs must also run the relevant benchmark or PR gate.
