# Task2 Architecture

## Purpose

`Task2` is a human-in-the-loop sentiment annotation system for audio and video files. It supports media import, preprocessing, task assignment, annotation, review, and JSON export. The system is designed to be:

- easy to unit test
- modular and reusable
- strictly layered
- safe for 24-hour unattended operation
- configurable rather than hardcoded

This document is the only source of truth for system structure, dependency rules, state boundaries, and runtime guarantees.

## Top-Level Structure

```text
task2/
├── Agent.md
├── architecture.md
├── config.md
├── runbook.md
├── testing.md
├── api_contract.md
├── media/                     # input samples
├── frontend/
│   ├── src/
│   │   ├── components/ui/     # L0
│   │   ├── foundation/        # L1
│   │   ├── domains/           # L2
│   │   └── pages/             # L3
│   ├── tests/
│   └── depcruise.config.cjs
└── backend/
    ├── src/task2_backend/
    │   ├── common/            # L0
    │   ├── foundation/        # L1
    │   ├── domains/           # L2
    │   └── api/               # L3
    ├── tests/
    └── importlinter.ini
```

## Layer Rules

### Global Rules

- Layer direction is fixed: `L3 -> L2 -> L1 -> L0`.
- A module may import only from its own layer or a lower layer when explicitly allowed below.
- Reverse imports are forbidden.
- Same-layer cross-domain imports are forbidden.
- Shared abstractions must move downward into a lower shared layer; do not bypass boundaries by importing deep internals from another domain.
- Every layer must expose stable public surfaces through index modules or package-level exports. Do not import from arbitrary deep files unless the architecture for that layer explicitly allows it.

### Frontend Layers

#### `frontend-layers`

| Layer | Path | Responsibility | May Import |
|---|---|---|---|
| L3 | `frontend/src/pages` | route-level composition only | same page folder, `domains`, `foundation`, `components/ui` |
| L2 | `frontend/src/domains/<name>` | domain UI, domain hooks, client-side orchestration | same domain, `foundation`, `components/ui` |
| L1 | `frontend/src/foundation` | cross-domain infrastructure and shared app behavior | `components/ui` |
| L0 | `frontend/src/components/ui` | pure atomic UI components | no app-layer imports |

- Pages may not import another page.
- A domain may not import another domain.
- `foundation` may not depend on any domain or page.
- `components/ui` may not depend on application state, routing, or domain types.

### Backend Layers

#### `backend-layers`

| Layer | Path | Responsibility | May Import |
|---|---|---|---|
| L3 | `backend/src/task2_backend/api` | HTTP routes, request mapping, response mapping | `domains`, `foundation`, `common` |
| L2 | `backend/src/task2_backend/domains/<name>` | domain models, repository contracts, services, DTOs | same domain, `foundation`, `common` |
| L1 | `backend/src/task2_backend/foundation` | config loading, db session, media adapters, retry helpers, logging | `common` |
| L0 | `backend/src/task2_backend/common` | pure types, constants, exceptions, value helpers | no higher-layer imports |

- API routes may not contain business rules.
- A backend domain may not import another backend domain.
- `foundation` may not import `domains` or `api`.
- `common` is pure and dependency-minimal.

## Domain Responsibilities

The first version has exactly three domains on both frontend and backend.

### `domain-boundaries`

### `domains/media`

- discover media files from configured input directories
- detect actual media format and metadata
- normalize media to supported working formats
- store source and normalized media references
- emit preprocessing state transitions and failure records

### `domains/annotation`

- create and assign annotation tasks
- manage task locking and autosave behavior
- persist drafts, submissions, and annotation versions
- enforce label schema and annotation validation

### `domains/review_export`

- review submitted annotations
- resolve review state transitions
- export JSON and JSONL output
- record export batches and audit trails

No domain may directly call another domain's internal service, repository, component, or hook. If cross-domain data is needed, expose it through:

- a lower shared abstraction in `foundation` or `common`
- an API boundary
- a dedicated query/use-case module placed in the consuming domain and backed by stable lower-level interfaces

## Frontend Public Surfaces

### `public-surfaces`

- `components/ui` exposes atomic components only through `frontend/src/components/ui/index.ts`.
- `foundation` exposes shared interfaces through `components/`, `hooks/`, `lib/`, `providers/`, and `types/`.
- each domain exposes a single domain index, for example `frontend/src/domains/annotation/index.ts`.
- pages are routed by the app shell and are not reusable imports for other pages.

### Frontend Alias Rules

- `@ui/*` -> `frontend/src/components/ui/*`
- `@foundation/*` -> `frontend/src/foundation/*`
- `@domains/<name>/*` -> `frontend/src/domains/<name>/*`
- `@pages/*` -> `frontend/src/pages/*`

Required rules:

- use aliases instead of long relative upward imports
- do not import `@pages` from non-page code
- do not import `@domains/other-domain/*`

## Backend Public Surfaces

- backend packages use absolute imports rooted at `task2_backend`, for example `task2_backend.domains.annotation.services`.
- no `..` relative imports across packages.
- each domain package may expose:
  - `models.py`
  - `schemas.py`
  - `repository.py`
  - `services.py`
  - optionally `types.py` and `constants.py`
- repository modules may use domain models and lower-layer adapters, but may not import domain services.
- services may depend on repository interfaces, domain schemas, and lower-layer utilities.
- API modules map transport data to domain services and return DTOs. They may not own persistence or retry logic.

## Configuration Model

### `config-sources`

All runtime variability must come from backend configuration. Frontend configuration is presentation-only plus API endpoint selection.

Backend configuration must include at least:

- input media directory
- normalized media output directory
- export directory
- database path
- log directory
- run mode
- retry max attempts
- retry base delay
- retry max delay
- autosave interval seconds
- heartbeat interval seconds
- task lock timeout seconds
- media target audio sample rate
- media target format
- supported export format list

Rules:

- configuration is loaded in `foundation`, validated once, and injected downward
- domains receive typed config values or narrow capability interfaces, not raw environment lookups
- no domain or API code may read environment variables directly

See [config.md](/Users/loumac/Downloads/项目代码/interview-claw/task2/config.md) for the complete runtime key set.

## Failure Model

### `error-classification`

The system must classify failures into stable categories instead of throwing untyped exceptions across boundaries.

Required categories:

- media detection failure
- media normalization failure
- unsupported media format
- transient database lock conflict
- task lock acquisition failure
- annotation validation failure
- export write failure
- configuration validation failure

Rules:

- low-level adapters in `foundation` translate vendor/library exceptions into typed application exceptions
- only `foundation` owns retry orchestration
- domains declare whether an operation is retryable, but do not implement ad-hoc sleep loops
- API routes translate typed failures into transport responses

### `retry-policy`

Retryable operations:

- media probing when file metadata access fails transiently
- media normalization when external tooling returns retryable process failure
- database writes that fail due to temporary lock contention
- export writes when destination is temporarily unavailable

Non-retryable operations:

- invalid config
- unsupported media type
- invalid annotation payload
- domain rule violations

Default retry policy:

- max attempts: `3`
- backoff: exponential
- base delay: `1s`
- max delay: `10s`
- every retry attempt must be logged with operation name, entity id, and attempt number

## Persistence Boundaries

### `task-lifecycle`

The persisted lifecycle is:

`IMPORTED -> PREPROCESSED -> READY -> IN_PROGRESS -> SUBMITTED -> REVIEWED -> EXPORTED`

This exact enum is shared with the frontend. Any frontend mirror type must match it exactly.

Rules:

- all state transitions are written to the database
- import, preprocessing, task allocation, autosave, submission, review, and export are resumable from database state
- no in-memory-only task ownership is allowed
- long-running workers must restore their progress from persisted state after restart

Required persisted entities:

- media file records
- normalized asset records
- annotation task records
- task lock metadata
- annotation drafts
- submitted annotations
- review decisions
- export batches
- audit log events
- background job failure records

## Idempotency And Recovery

### `idempotency-rules`

- repeated directory scans must not create duplicate media tasks for the same source asset
- `media_id` is derived from the source filename stem by default so repeated scans remain stable
- repeated preprocessing must not create conflicting normalized outputs for an unchanged source asset
- repeated submission must follow explicit versioning or replace-last-draft rules; hidden duplicate rows are forbidden
- repeated export of the same reviewed batch must either reuse the existing batch record or create a new versioned batch intentionally

### `24h-operation`

To support 24-hour unattended operation, the implementation must provide:

- structured logs for every state transition and retry event
- durable failure records with retry counts and last failure reason
- task lock expiration and lock recovery
- resumable background jobs
- health metrics for queue depth, task counts by status, and failure counts
- graceful restart behavior based on persisted state

Task lock policy:

- task locks are persisted with owner, acquisition timestamp, and expiry timestamp
- expired `IN_PROGRESS` locks are reclaimable
- heartbeat keeps active locks fresh even when no draft fields changed
- autosave refreshes the active lease when draft content changes
- explicit release moves abandoned in-progress tasks back to `READY`
- abandoned tasks return to `READY` or a recovery queue based on configured timeout policy

### `autosave-lock-timeout`

- autosave interval and task lock timeout are configuration-owned values
- autosave refresh extends the active task lock before expiry
- heartbeat extends active task locks without creating extra draft rows
- release clears lock ownership and returns the task to `READY`
- timeout expiration triggers lock recovery, audit logging, and task requeue or recovery handling

## Testing Strategy

See [testing.md](/Users/loumac/Downloads/项目代码/interview-claw/task2/testing.md) for detailed cases. Mandatory structure rules are:

- L0 and L1 favor pure unit tests
- L2 favors service, repository, and domain-level tests
- L3 favors thin integration tests only
- dependency checks are mandatory CI gates

## Static Dependency Checks

- frontend uses `dependency-cruiser` to enforce:
  - page isolation
  - domain independence
  - no upward imports
  - no cycles
- backend uses `import-linter` to enforce:
  - `api > domains > foundation > common`
  - domain independence
  - forbidden reverse imports

CI is not green unless:

- unit and integration tests pass
- type checks pass
- dependency structure checks pass

## Interview Requirement Coverage

- Clear project structure: fixed top-level layout, layer responsibilities, domain boundaries, and public surfaces.
- Configurable design: all runtime variability is loaded from config and injected downward.
- Exception handling and retries: typed failures plus centralized retry policy in `foundation`.
- Modular and reusable architecture: domains are isolated and shared behavior lives in lower layers.
- 24-hour unattended runtime: state persistence, idempotency, retries, logs, lock recovery, and resumable jobs are all mandatory.
