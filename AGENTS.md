**Mission**
- Build reliable, evolvable software with clear boundaries, pragmatic engineering, and operational excellence.
- Favor modular monoliths that can scale to services when necessary.
- Keep business logic independent from frameworks and infrastructure.

**Core Principles**
- Boundary clarity over cleverness: define domain borders first, tech choices second.
- Hexagonal/Clean architecture: ports as contracts, adapters for I/O.
- Business logic framework-agnostic: frameworks stay at the edges.
- Explicit contracts and validation: schemas at boundaries, typed DTOs, uniform errors.
- Testability as a design goal: pure domain first, compose I/O later.
- Evolution-first: small steps, reversible decisions, record ADRs.
- Operational parity: logs/metrics/traces are first-class.
- Quality through simplicity: smallest sufficient solution, avoid incidental complexity.

**Architecture**
- Layers
  - Domain: entities, value objects, domain services, domain events.
  - Application: use cases, orchestration, policies, transactions, authorization.
  - Ports: interfaces for persistence, messaging, external services.
  - Adapters: HTTP, DB, MQ, cache, scheduler, CLI.
  - Infra: configuration, DI, logging/metrics/tracing, migrations, outbox.
- Interaction
  - External sync: HTTP/REST with versioning.
  - Internal sync: HTTP/gRPC.
  - Async: event bus (Kafka/RabbitMQ); outbox for consistency.
- Data
  - One schema per bounded context; share instances, not tables.
  - Repositories + Unit of Work; DB constraints for invariants.

**Project Structure (generic)**
- `src/domain`: entities, value objects, policies, domain events
- `src/app`: use cases, DTOs, authorization, transactions
- `src/ports`: repository and gateway interfaces
- `src/adapters`: `http/`, `db/`, `mq/`, `cache/`, `scheduler/`
- `src/infra`: config, DI, logging, metrics, tracing, migrations, outbox
- `src/shared`: cross-cutting utils (Result/Either, ids, clock, validation)
- `tests`: unit, contract, integration, e2e
- `docs`: ADRs, C4 diagrams, runbooks
- `scripts`: tooling, CI helpers

**API Contracts**
- REST naming: plural nouns; idempotency for PUT/DELETE; POST supports `Idempotency-Key`.
- Versioning: `/v1` or Accept header.
- Error envelope: `{ code, message, details, correlationId }`; stable error codes.
- Pagination: page/size or cursor with `nextCursor`.
- Boundary validation: runtime schema validation and static typing.

**Asynchrony & Consistency**
- Domain events: past tense names (e.g., `UserRegistered`).
- Event schemas versioned and non-breaking; outbox + dedupe keys; idempotent consumers.
- Saga/process orchestration for long-lived workflows with compensations.

**Data & Transactions**
- Repositories own aggregate persistence; Application begins/commits transactions.
- Prefer DB constraints for uniqueness and referential integrity.
- Soft delete and audit fields are explicit; reconcile read-after-write with replicas.

**Coding Standards (language-agnostic)**
- Small functions, single level of abstraction per function.
- Names: use-case verbs (`CreateOrder`), domain nouns (`Policy`, `Aggregate`).
- No variable declared first inside `if`/`try` if it will be used outside; declare outside, assign inside.
- Explicit dependencies: constructor injection; avoid service locators and globals.
- Pure functions for business logic; side-effects live in adapters.
- Structured logs (JSON) with correlation/trace ids.
- No swallowed errors; domain errors are modeled, technical errors are observable.

**Python Standards**
- First declaration must include a type annotation (PEP 526).
- A variable must keep a single type for its lifetime, None allowed as the only extra value via `Optional[T]`.
- Disallow other `Union` forms for variables (use `Optional[T]` only).
- Do not first declare a variable inside `if`/`try` that is later used outside; declare outside, assign inside.
- Prefer small functions + early returns to reduce wide-scoped variables.
- Suggested tooling
  - mypy strict mode with `no_implicit_optional = True`
  - pyright strict (optional)
  - ruff for linting
- Patterns
  - Late init: `x: T; x = compute()`
  - Optional: `res: Optional[T] = None; res = load()`
  - Try paths: `cfg: Config; try: cfg = load() except: cfg = default()`

**TypeScript Standards**
- Compiler: `"strict": true`, `noUncheckedIndexedAccess: true`, no implicit any.
- Result/Either for domain errors; avoid bare throws except unrecoverable.
- Runtime validation in adapters (e.g., zod) to produce DTOs.
- `kebab-case` files, `PascalCase` types/classes, `camelCase` variables.
- Dependency injection via lightweight container or factories; no global singletons.

**JavaScript Standards**
- No semicolons
  - Style: rely on Automatic Semicolon Insertion (ASI); do not end statements with `;`.
  - Enforcement: Prettier `{ "semi": false }` and ESLint rules `"semi": ["error", "never"]`, `"no-extra-semi": "error"`.
  - ASI safety: when a new line starts with `(`, `[`, `` ` ``, `/`, `+`, or `-`, insert a leading semicolon to avoid unintended concatenation, e.g. `;(() => {})()` and `;[1,2].forEach(...)`.
- Modules and syntax
  - Prefer ESM (`import`/`export`); in Node, set `"type": "module"` or use `.mjs`.
  - Keep identifiers and APIs in English; follow the same architectural boundaries as TypeScript (domain/app/ports/adapters/infra).
- Tooling
  - Use ESLint with `eslint:recommended` plus rules that mirror the TypeScript section where applicable; format with Prettier (`semi: false`).
  - Optional: adopt StandardJS conventions while keeping project-specific rules from this AGENTS.md.

**Go Standards**
- Encapsulation via `internal/`
  - Place any package not intended for public use under `internal/`. Only code within the same module can import it.
  - Expose the smallest possible API; avoid `pkg/` unless you intentionally publish stable packages. Prefer keeping everything in `internal/` and wiring from `cmd/`.
  - Suggested modular monolith layout:
    - `cmd/api/main.go` (composition root; wires dependencies)
    - `internal/<context>/{domain,app,ports,adapters,infra}`
    - `internal/platform/{config,db,http,mq,cache,logging,metrics}`
    - `pkg/` (optional; only for stable public packages)
- Layering and dependencies
  - `domain` is pure Go (no HTTP/DB). `app` orchestrates use cases and transactions. `ports` define interfaces consumed by `app`. `adapters` implement ports. `infra` holds technical setup.
  - Main functions in `cmd/` assemble concrete adapters and pass them into `app` constructors.
- Interfaces and DI
  - Define interfaces in the consumer package (usually `app`); avoid creating interfaces for every struct. Accept concrete types until an abstraction is needed.
  - Prefer constructor injection; no global singletons. Optional: use `google/wire` for wiring, but keep graphs small.
- Errors
  - Return errors, don’t panic (except truly unrecoverable init). Wrap with `%w` (`fmt.Errorf("...: %w", err)`), use `errors.Is/As`.
  - Model domain errors as values; map to transport errors at adapters.
- Concurrency and context
  - Always accept `context.Context` as the first parameter for I/O-bound functions; don’t store contexts in structs.
  - Use `errgroup` for concurrent workflows; ensure cancellation; avoid goroutine leaks; set deadlines/timeouts at boundaries.
- Logging and observability
  - Use structured logging (e.g., `log/slog` in Go 1.21+); include correlation/trace IDs.
  - Expose RED/USE metrics; instrument critical paths; propagate trace context.
- Testing
  - Prefer table-driven tests; include `-race` in CI. Separate slow/integration tests with build tags (e.g., `//go:build integration`).
  - Mock at port boundaries (handwritten fakes or `mockgen`); avoid mocking concrete types.
- Style and linting
  - Package names: short, no stutter (e.g., `user`, not `userpkg`).
  - Run `go vet`, `staticcheck`, `golangci-lint` (e.g., `errcheck`, `revive`, `gofumpt`, `gocritic`). Enforce `go fmt`/`gofumpt`.
- Versioning and modules
  - Target a recent Go version (e.g., 1.21/1.22). Use `go.work` for multi-module repos when needed.
  - Keep `CGO_ENABLED=0` where possible for simpler builds.
- Control-flow rule alignment
  - If a value computed in an `if` block is needed after the block, declare the variable before the block (e.g., `var u *User; if cond { u = ... } use(u)`).

**Error Handling**
- Map domain errors to explicit, typed results.
- Map technical errors to structured logs and correct HTTP status codes.
- Never swallow exceptions; add context and rethrow or convert to error results.
- Idempotency: accept keys where duplication is plausible.

**Testing Strategy**
- Pyramid: many domain unit tests; contract tests for ports; integration tests for adapters; critical e2e smoke.
- Given-When-Then naming; deterministic tests; factories/mothers for data.
- Coverage targets: domain 90%+, adapters based on criticality.
- Add performance assertions for hot paths where feasible.

**Observability**
- Logs: JSON, consistent fields (timestamp, level, service, correlationId, trace/span).
- Metrics: RED/USE models; SLIs for latency, error rate, saturation.
- Tracing: OpenTelemetry; propagate context across services.
- Audit logs for sensitive business actions.

**Security Baseline**
- Secrets out of repo; per-env separation; rotation policy.
- Validate input, encode output; CSRF/CORS/headers (CSP).
- Authorization in the Application layer; least privilege for DB/cloud roles.
- Dependency scanning and scheduled upgrades.

**CI/CD & Workflow**
- Trunk-based with short-lived PRs; mandatory lint + tests on PR.
- Conventional Commits; auto-generated changelog.
- SemVer; main merges build artifacts and images; tag to release.
- Quality gates: coverage thresholds, API breaking-change checks, bundle/image size limits.

**Documentation**
- ADRs for key decisions (context, options, decision, consequences).
- C4 diagrams (Context, Container, Component).
- Onboarding: `make dev` or `npm run dev`; `make test` runs all tests.
- Per-module README describing purpose, dependencies, and invariants.

**Agent Operating Guide**
- Goals
  - Act as a senior software engineer and architect.
  - Deliver minimal, correct, and maintainable changes aligned with this AGENTS.md.
- Behavior
  - Be concise, direct, and friendly. Focus on actionable steps.
  - Prefer plans for multi-step or ambiguous work; keep them short and outcome-driven.
  - Explain what you’re about to do before running commands.
- Scoping and Edits
  - Respect boundaries in this file. Do the smallest change that solves the problem.
  - Do not refactor unrelated code or rename files unless required to complete the task.
  - Follow existing code style; if absent, apply standards in this AGENTS.md.
- Working With Files
  - Use `apply_patch` to add or modify files.
  - When touching files, ensure changes adhere to the rules under “Python Standards” and “Coding Standards”.
  - Update or add minimal docs/tests as needed to keep the repo healthy.
- Validation
  - Prefer running the narrowest relevant tests first, then broaden if needed.
  - If the repo has linters/type-checkers, run them; otherwise suggest a focused set to add.
  - Confirm behavior by describing how to reproduce and what changed.
- Communication
  - Use short preambles before grouped commands.
  - Summarize progress in a sentence or two for longer tasks.
  - Avoid excessive verbosity; include only necessary context.
- Safety and Constraints
  - Avoid destructive actions unless explicitly requested; always back up or explain impact.
  - Keep secrets out of code and logs. Scrub sensitive data in examples.
  - If sandboxed or read-only, propose alternatives or ask for permission to write.
- Decision-Making
  - Default to modular monolith; propose service extraction only when justified by operational pain (scalability, independence, different lifecycles).
  - Prefer composition over inheritance; dependency injection over global state.
  - Model errors and states explicitly; avoid Boolean parameters where enums fit better.
- What to Avoid
  - Gold-plating, speculative abstractions, and unnecessary generalization.
  - Large, multi-purpose PRs; prefer incremental, reviewable changes.
  - Hidden coupling between modules; leaking framework types into domain.
- When In Doubt
  - Ask clarifying questions with suggested options.
  - Offer a minimal viable path and a safe extension path.

**PR Checklist**
- Architecture: respects boundaries; business logic is framework-free.
- Contracts: inputs/outputs validated; error envelope consistent and typed.
- Data: invariants enforced; migrations safe and reversible.
- Code: follows language standards here; no first-time declarations inside `if/try` that are used outside.
- Python: first declarations annotated; single type plus Optional only.
- Tests: unit + relevant contract/integration; deterministic; coverage adequate.
- Observability: logs with correlationId; metrics/traces for critical paths.
- Security: secrets safe; inputs validated; authorization enforced.
- Docs: ADR or README updated if behavior or decisions changed.
- CI: passes lint, type checks, tests; no unintended breaking changes.

**User Preferences**
- Language: default to Traditional Chinese (繁體中文) with Taiwan usage for all user-facing communication. Keep code identifiers, APIs, and commit messages in English unless the user explicitly requests zh-TW.
- Bilingual clarity: when introducing domain/tech terms, include the English term on first mention in parentheses; avoid over-translating established terms (API, HTTP, commit, PR).
- Ask before switching: if the conversation starts in another language or the audience changes (e.g., external docs), confirm language choice with the user.
- Regional conventions: timezone `Asia/Taipei`; dates `YYYY-MM-DD HH:mm:ss`; currency `NTD` (新台幣); metric units; thousands separator with commas in numeric examples.
- Documentation stance: this AGENTS.md and general repo docs can remain in English for broader collaboration; add zh-TW summaries on request.
