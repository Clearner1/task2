# Task2 Agent Index

`Task2` is an independent sentiment annotation subsystem for audio and video media. This file is the retrieval index and governance entrypoint for every future implementation change.

## How To Use This File

1. Read [architecture.md](/Users/loumac/Downloads/项目代码/interview-claw/task2/architecture.md) before creating files, modules, routes, schemas, or tests.
2. Use the navigation table below to jump to the correct source of truth.
3. If a change modifies layers, imports, config boundaries, retry behavior, runtime state, or testing rules, update the referenced document in the same change.

## Hard Rules

- Dependency direction is strictly one-way: `L3 -> L2 -> L1 -> L0`.
- Reverse imports are forbidden.
- Same-layer cross-domain imports are forbidden.
- Shared behavior must be pushed down into `foundation` or `common`; do not import internals from another domain.
- Page and API layers are orchestration-only. Business logic belongs in domain services, repositories, hooks, and pure functions.
- Configuration is the only source for runtime variability. Do not hardcode paths, retry counts, timeouts, media parameters, or export locations inside business code.
- Long-running behavior must be recoverable from persisted state. Runtime-critical state cannot live only in memory.

## Navigation

| Topic | Document | Use When |
|---|---|---|
| System layers, boundaries, imports, state model | [architecture.md](/Users/loumac/Downloads/项目代码/interview-claw/task2/architecture.md) | You need to know where code belongs and what it may import |
| Runtime configuration sources and keys | [config.md](/Users/loumac/Downloads/项目代码/interview-claw/task2/config.md) | You need to add or consume config |
| Operational flow, long-run stability, retries, recovery | [runbook.md](/Users/loumac/Downloads/项目代码/interview-claw/task2/runbook.md) | You need to reason about 24h unattended operation |
| Unit, integration, structure, and stability tests | [testing.md](/Users/loumac/Downloads/项目代码/interview-claw/task2/testing.md) | You need to add tests or CI checks |
| HTTP contracts and JSON export shapes | [api_contract.md](/Users/loumac/Downloads/项目代码/interview-claw/task2/api_contract.md) | You need request, response, or export schema details |

## Entry Points By Role

- Frontend implementation: start with `architecture.md` sections `Frontend Layers`, `Frontend Public Surfaces`, and `Static Dependency Checks`.
- Backend implementation: start with `architecture.md` sections `Backend Layers`, `Domain Responsibilities`, `Failure Model`, and `Persistence Boundaries`.
- Testing work: start with `testing.md`, then confirm layer restrictions in `architecture.md`.
- Runtime and operations work: start with `runbook.md`, then check configuration keys in `config.md`.
- API and export work: start with `api_contract.md`, then validate placement and imports in `architecture.md`.

## Retrieval Keywords

- `frontend-layers`
- `backend-layers`
- `domain-boundaries`
- `public-surfaces`
- `task-lifecycle`
- `config-sources`
- `retry-policy`
- `error-classification`
- `autosave-lock-timeout`
- `24h-operation`
- `idempotency-rules`
- `dependency-cruiser`
- `import-linter`
- `export-json-contract`

## Change Policy

- Any new domain must follow the same four-layer layout and may not directly depend on existing domain internals.
- Any change to directory layout, package aliases, import boundaries, runtime states, or retry behavior must update [architecture.md](/Users/loumac/Downloads/项目代码/interview-claw/task2/architecture.md).
- Any new runtime key must update [config.md](/Users/loumac/Downloads/项目代码/interview-claw/task2/config.md).
- Any new endpoint or exported field must update [api_contract.md](/Users/loumac/Downloads/项目代码/interview-claw/task2/api_contract.md).
- Any new test type or CI gate must update [testing.md](/Users/loumac/Downloads/项目代码/interview-claw/task2/testing.md).
- Dependency rules must stay enforceable by `dependency-cruiser` on the frontend and `import-linter` on the backend.

## Interview Requirement Mapping

- Clear project structure: defined in [architecture.md](/Users/loumac/Downloads/项目代码/interview-claw/task2/architecture.md).
- Configurable design: defined in [config.md](/Users/loumac/Downloads/项目代码/interview-claw/task2/config.md).
- Exception handling and retries: defined in [architecture.md](/Users/loumac/Downloads/项目代码/interview-claw/task2/architecture.md) and [runbook.md](/Users/loumac/Downloads/项目代码/interview-claw/task2/runbook.md).
- Modular and extensible design: defined in [architecture.md](/Users/loumac/Downloads/项目代码/interview-claw/task2/architecture.md).
- 24-hour unattended operation: defined in [runbook.md](/Users/loumac/Downloads/项目代码/interview-claw/task2/runbook.md).
