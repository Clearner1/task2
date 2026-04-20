# Task2 Testing Strategy

## Goals

- keep business logic easy to unit test
- prove layer boundaries are enforced
- verify recoverability and idempotency
- block architecture drift in CI

## Frontend Tests

### L0 `components/ui`

- render tests
- interaction tests
- accessibility smoke checks

### L1 `foundation`

- unit tests for shared hooks
- unit tests for API client and utility functions
- provider tests with mocked lower dependencies

### L2 `domains`

- domain hook tests
- thin component tests
- pure data transformation tests
- no tests may import another domain

### L3 `pages`

- route composition tests
- page-level happy path integration tests
- no business-rule assertions that belong in domains

### Frontend Structure Checks

- run `dependency-cruiser`
- fail on upward imports
- fail on page-to-page imports
- fail on cross-domain imports
- fail on circular dependencies

## Backend Tests

### L0 `common`

- pure unit tests for helpers, types, and exception mapping

### L1 `foundation`

- unit tests for config loading
- adapter tests for media probe and normalization wrappers
- retry helper tests
- database session and transaction tests

### L2 `domains`

- service tests using fake repositories
- repository tests using isolated SQLite fixtures
- schema validation tests
- lifecycle state transition tests

### L3 `api`

- request and response contract tests
- transport error mapping tests
- FastAPI `TestClient` tests with mocked domain services where appropriate

### Backend Structure Checks

- run `import-linter`
- fail on reverse imports
- fail on cross-domain imports
- fail when `foundation` or `common` depends upward

## Stability Scenarios

- import the same media twice and confirm idempotent registration
- preprocess the same media again and confirm normalized output paths stay stable
- simulate transient media probe failure and confirm retry behavior
- verify waveform JSON and poster assets are exposed only when generated
- simulate database lock contention and confirm bounded retry
- simulate autosave heartbeat extending a task lock
- simulate stale lock expiry and task recovery
- simulate maintenance loop replaying a persisted retryable failure
- simulate service restart and confirm unfinished work resumes from persisted state
- simulate export rerun and confirm versioned or reused batch semantics

## CI Gates

- frontend unit and integration tests
- backend unit and integration tests
- frontend type check
- backend type check or static analysis
- `dependency-cruiser`
- `import-linter`

CI is failing by default when architecture checks fail, even if functional tests pass.
