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
 - High modularity and single source of truth: cohesive modules with minimal public surfaces; one behavior is controlled by one setting.

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
- No magic strings or numbers: extract to named constants/enums/config; colocate with domain or configuration.

**Visibility & API Surface**
- Default non-public: keep functions, methods, and modules non-public unless exposure is required by a stable contract. Design a minimal surface area per bounded context.
- Public-by-need: promote visibility only when a consumer requires it and the API is intended to be stable; document invariants and versioning strategy.
- Language specifics
  - Python: prefix non-public functions/methods/modules with a single underscore `_name`. Use `__all__` in `__init__.py` to whitelist exports. Avoid `from module import *`. Use `__name` double underscore only for name-mangling cases, not as access control.
  - TypeScript/JavaScript: do not export by default. Export only what is part of the public contract from `index.ts`. Use `private` (TS) or `#field` (JS) for class internals. Control package exposure via `package.json#exports` and forbid deep imports with ESLint `no-restricted-imports`.
  - Go: keep identifiers unexported (lowercase) unless they’re part of the public API; reinforce with `internal/` directories as documented.
  - Java: prefer package-private or `private/protected`; make classes/methods `public` only when necessary. In JPMS, export only required packages in `module-info.java`.
  - C#/.NET: use `internal` by default for library code; `public` only for external consumers. Use `InternalsVisibleTo` for tests if needed.
  - Rust: items are private by default; use `pub(crate)` to limit to crate; carefully curate `pub` surface and avoid blanket re-exports.
  - Kotlin/Swift: Kotlin prefer `internal` (module-scoped) or `private`; Swift default `internal`, use `public/open` only for library boundaries; narrow with `fileprivate` where useful.
  - PHP/Ruby: use `private/protected` where possible; for PHP libraries, mark non-public with `@internal` and keep them out of Composer exports; Ruby keep internals undocumented and under non-public namespaces.

**Python Standards**
- First declaration must include a type annotation (PEP 526).
- Prefer Python 3.10+ built-in typing syntax over `typing.*`
  - Use union `T | None` instead of `Optional[T]`; avoid `Union[...]` except for `T | None` in variable declarations.
  - Use built-in generics: `list[str]`, `dict[str, int]`, `set[Foo]`, `tuple[int, ...]` instead of `List/Dict/Set/Tuple`.
  - Keep `typing` for advanced constructs only: `TypedDict`, `Protocol`, `Literal`, `Final`, `ClassVar`, `overload`, `Self` (3.11+), `NotRequired/Required`.
  - For 3.10/3.11 projects, add `from __future__ import annotations` at module top to avoid forward-ref ordering issues.
- A variable must keep a single type for its lifetime; `None` is the only additional allowed value (i.e., `T | None`).
- Disallow other unions for variables (no `A | B` unless `B` is `None`).
- Do not first declare a variable inside `if`/`try` that is later used outside; declare outside, assign inside.
- Prefer small functions + early returns to reduce wide-scoped variables.
- Suggested tooling
  - mypy strict mode with `no_implicit_optional = True`
  - pyright strict (optional)
  - ruff for linting
- Patterns
  - Late init: `x: T; x = compute()`
  - Optional: `res: T | None = None; res = load()`
  - Try paths: `cfg: Config; try: cfg = load() except: cfg = default()`

**TypeScript Standards**
- Compiler: `"strict": true`, `noUncheckedIndexedAccess: true`, no implicit any.
- Result/Either for domain errors; avoid bare throws except unrecoverable.
- Runtime validation in adapters (e.g., zod) to produce DTOs.
- `kebab-case` files, `PascalCase` types/classes, `camelCase` variables.
- Dependency injection via lightweight container or factories; no global singletons.
- No semicolons
  - Style: rely on ASI; do not end statements with `;`.
  - Enforcement: Prettier `{ "semi": false }` and ESLint `"semi": ["error", "never"]`, `"no-extra-semi": "error"`.
  - ASI safety: when a line starts with `(`, `[`, `` ` ``, `/`, `+`, or `-`, add a leading semicolon, e.g. `;(() => {})()` and `;[1,2].forEach(...)`.

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

**Encapsulation Across Languages (Internal-like)**
- Principle
  - Treat anything under an `internal`/`_internal`-like path as non-public, unstable API. Only expose stable contracts through ports/adapters or top-level package/module exports.
  - Enforce boundaries at the package/module level; tests may access internals with explicit allowances, but product code must not.
- Monorepo/workspaces
  - Split features into packages/modules. Mark non-publishable ones as private. Expose only via package entry points and exports maps. Avoid deep imports and cross-context internal access.
- TypeScript/JavaScript
  - Directory: `src/internal/` for non-public code; never re-export internals from `src/index.ts`.
  - Control exposure with `package.json#exports` and `typesVersions`; block deep imports. ESLint `no-restricted-imports` to forbid `internal/` from outside.
  - In monorepos, create separate packages per bounded context; only depend on other packages’ public entry points.
- Python
  - Use `_internal/` or `internal/` subpackages; gate exposure with `__all__` and avoid importing internals across bounded contexts.
  - Packaging: keep internals under the top-level package (e.g., `myapp/_internal/...`) and do not document them; wheel/sdist includes but docs mark as non-API.
  - Enforce via ruff + custom pre-commit: disallow `from X._internal import ...` in non-test code across contexts.
- Java
  - Place non-public APIs under packages named `...internal...`. With JPMS, only `exports` public packages in `module-info.java`.
  - Prefer package-private visibility by default; only `public` what must be consumed externally.
- C#/.NET
  - Use the `internal` modifier for non-public API; expose to tests with `[assembly: InternalsVisibleTo("<TestAssembly>")]`.
  - Keep internals in separate projects when feasible; only reference public contracts between projects.
- Rust
  - Use `pub(crate)` and private modules; group internals under `crate::internal` and avoid re-exporting them from `lib.rs`.
  - In workspaces, keep crates’ public API minimal; share via dedicated `shared` crates rather than reaching into internals.
- Kotlin / Swift
  - Kotlin `internal` is module-scoped—split Gradle modules to bound visibility. Swift: prefer `internal`/`fileprivate` and separate SwiftPM targets to enforce boundaries.
- PHP / Ruby
  - PHP: annotate non-public with `@internal` (honored by Psalm/PhpStan); keep internal code outside Composer exports for libraries.
  - Ruby: keep internal modules/classes undocumented; use `private`/`module_function`; avoid exposing under gem’s public namespace.

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

**Research & Writing**
- Scope
  - Perform research, organize information, and produce writing deliverables (essays, reports, whitepapers, academic-style papers) in addition to coding tasks.
  - Synthesize user-provided materials and local repo content; when network is restricted, ask for sources or constraints and proceed with structured assumptions.
- Outcomes (choose based on request)
  - Executive summary (5–7 bullets), outline, annotated bibliography, claim–evidence–source matrix, literature review, report/paper draft, slide notes.
  - Revision artifacts: tracked changes summary, versioned drafts, open questions list, risks/limitations section.
- Workflow
  - Clarify: audience, purpose, scope/length, deadline, desired structure (e.g., IMRaD, problem–solution, argumentative), tone, citation style (APA/MLA/Chicago/IEEE), and language (default zh-TW for user-facing).
  - Collect: request provided sources; enumerate constraints. Capture metadata (title, author, date, link/DOI, access date) for every source.
  - Extract: build a claim–evidence–source table; record exact quotes with page/section; note contradictions and gaps.
  - Synthesize: cluster themes, resolve conflicts, decide narrative; propose an outline with headings and key points per section.
  - Draft: write topic-sentence-first paragraphs, add transitions, keep one idea per paragraph, avoid redundancy; include figures/tables descriptions if needed.
  - Review: check completeness, accuracy, coherence, tone, and consistency with citation style; run a quick terminology and numbers/units pass (metric, thousands separator, date/timezone per preferences).
  - Iterate: summarize deltas, ask focused questions, and refine.
- Writing Standards
  - Tone: default clear, concise, and neutral; switch to academic/professional/marketing/plain-language on request.
  - zh-TW usage: write in Traditional Chinese for user-facing content; include English term on first mention; keep identifiers/APIs/commit messages in English.
  - Structure: headings are descriptive; paragraphs start with a topic sentence; avoid overly long sentences; prefer active voice.
  - Formatting in this CLI: avoid heavy formatting; short bullet lists are preferred; provide plain-text references.
  - Figures/Tables: if not rendering, describe content and purpose; include alt-text-like descriptions.
- Citation & Evidence Policy
  - Distinguish facts from opinions; qualify uncertain claims; avoid unverifiable statements.
  - Cite every non-trivial claim; include source metadata (author, year, title, link/DOI if available, access date). When links are not available, include bibliographic details only.
  - Do not fabricate sources. If a required source is unavailable, state the gap and propose alternatives.
- Common Output Templates
  - Executive Summary: purpose, key findings, implications, 1–2 recommendations, next steps.
  - Report (professional): title, summary, background, methodology, findings, discussion, recommendations, risks/limitations, appendix, references.
  - Academic-style (IMRaD): abstract, introduction, methods, results, discussion, conclusion, references.
  - Literature Review Matrix: topic/theme, representative works, key claims, evidence quality, relevance, notes.
- Writing Task Checklist
  - Goal defined (audience, purpose, length, tone, structure, citation style, language)
  - Sources collected and logged; claim–evidence–source table built
  - Outline agreed; draft produced; references included and formatted
  - Consistency checks (terms, numbers/units, dates/timezone, zh-TW style)
  - Limitations and open questions documented; next steps proposed

**Writing Guidelines**
- Language & Typography (zh-TW)
  - Default zh-TW for user-facing text; include the English term on first mention; keep code identifiers/APIs in English.
  - Dates `YYYY-MM-DD HH:mm:ss` (`Asia/Taipei`); numbers use commas as thousands separator; prefer metric units; write number + space + unit (e.g., `10 km`, `3.5 ms`), percent without space (`12%`).
  - Use concise punctuation; avoid duplicated exclamation/question marks; keep ASCII punctuation for code/paths/URLs.
- Tone & Voice
  - Default neutral, clear, professional; switch to academic/marketing/plain-language on request.
  - Prefer active voice; avoid filler and weasel words (e.g., "just", "very", "some", "various").
  - Keep sentences ~12–22 words; one idea per sentence; vary rhythm without run-ons.
- Structure & Readability
  - Headings are descriptive; keep depth at two levels when possible.
  - Paragraphs start with a topic sentence; maintain logical transitions; avoid nested lists beyond one level (in this CLI, prefer flat lists).
  - Lists: 4–6 items, parallel grammar, no trailing punctuation unless full sentences.
- Evidence & Citations
  - Choose one style per document (APA/MLA/Chicago/IEEE) during clarification and apply consistently.
  - In-text examples: APA `(Author, Year)`; IEEE `[1]`. Include page/section for direct quotes.
  - References include author, year, title, source, link/DOI (if available), and access date. Do not fabricate sources.
- Quotations & Paraphrasing
  - Quote verbatim only when necessary; otherwise paraphrase faithfully and cite.
  - For quotes ≥ 10 words, mark clearly and add page/section; avoid overuse of block quotes.
- Data & Figures
  - State source and date with each key number; define sample, scope, and assumptions.
  - Keep units consistent; round sensibly and note precision; avoid mixing timezones.
  - Describe figures/tables in text with a one-line purpose and key takeaway when rendering is unavailable.
- Anti-hallucination & Assumptions
  - Never invent facts or citations; if a claim lacks a source, mark as assumption or request references.
  - When offline/restricted, base writing on provided sources; otherwise provide placeholders like "[citation needed]" and list gaps.
- Editing Passes
  - Content pass (structure/coverage) → line edit (clarity/style) → copy edit (typos/format).
  - Deliver a short revision log summarizing what changed and why; list open questions.
- Consistency Checklist
  - Audience, purpose, tone, length confirmed; key terms defined consistently (include English on first mention).
  - Numbers/units/dates consistent; citations complete and uniform; no unsupported claims.
  - Paragraphs with topic sentences; headings reflect content; bullets parallel and concise.

**PR Checklist**
- Architecture: respects boundaries; business logic is framework-free.
- Contracts: inputs/outputs validated; error envelope consistent and typed.
- Data: invariants enforced; migrations safe and reversible.
- Code: follows language standards here; no first-time declarations inside `if/try` that are used outside.
- Visibility: default non-public; only expose what’s required; Python internals use underscore prefix and `__all__`.
- Constants: no magic strings/numbers; use named constants/enums/config.
- Python: first declarations annotated; single type plus Optional only.
- Tests: unit + relevant contract/integration; deterministic; coverage adequate.
- Observability: logs with correlationId; metrics/traces for critical paths.
- Security: secrets safe; inputs validated; authorization enforced.
- Docs: ADR or README updated if behavior or decisions changed.
- CI: passes lint, type checks, tests; no unintended breaking changes.
- Commits: follow Conventional Commits (type(scope)!: subject), clear body/footers.
 - Modularity/Config: cohesive modules, minimal public surfaces; one behavior -> one config; validated with clear precedence.

**Constants & Magic Values**
- Ban magic values: do not inline unexplained strings/numbers/regex flags/units. Name them and centralize appropriately.
- Placement
  - Domain invariants (limits, statuses): colocate as constants/enums in the domain package/module.
  - Cross-cutting knobs (timeouts, retries, buffer sizes): put in configuration with sane defaults and env overrides.
  - Protocol keys (headers, claim names, JSON field names): define once in shared constants; avoid retyping literals.
- Language guidance
  - TypeScript/JavaScript: `export const` for constants; prefer `as const` literal objects and string literal unions over numeric enums. Keep header names, event types, and error codes centralized.
  - Python: module-level `UPPER_SNAKE` constants; use `enum.Enum`/`StrEnum` (3.11+) or `Literal` for finite sets; mark constants `Final` when applicable.
  - Go: `const` and typed aliases; group with `iota` when meaningful; expose through small helper packages; avoid stray string keys.
  - Java/C#: `public static final`/`static readonly` in dedicated classes; use real enums for discrete sets.
  - SQL/config: keep environment-specific values out of code; inject via config with validation.
- Exceptions
  - Obvious mathematical literals (`0`, `1`, `-1`) may be inline when idiomatic and self-evident; otherwise, prefer a named constant or inline comment explaining the value.

**Modularity & Configuration**
- High cohesion, low coupling
  - Group related responsibilities into modules with clear boundaries and minimal public API.
  - Avoid cross-module reach-ins and deep imports; communicate via ports/interfaces.
- Single source of truth (SSOT) for settings
  - A single behavior must be governed by a single configuration variable. Avoid multiple flags/vars toggling the same behavior.
  - Centralize configuration in one place per service/app with a typed schema, defaults, and validation.
  - Establish a clear precedence order (env vars > config file > defaults) and document it.
  - Centralize feature flags in one module/service; avoid scattered ad-hoc booleans.
- Immutability and injection
  - Load and validate configuration once at startup and inject as immutable dependencies.
  - If live reload is required, isolate update paths, ensure atomic swaps, and surface versioning/monotonicity.
- Language guidance
  - TypeScript/JavaScript: define `Config` types/interfaces; load/validate once (e.g., zod); export a single `config` object.
  - Python: use dataclasses or pydantic for config; one loader validates and returns a single config object.
  - Go: define a `Config` struct; load once (env/file/flags), validate, and pass through constructors.
  - Java/C#: one configuration root type bound via framework; avoid scattered static fields.

**Engineering Excellence**
- Engineering mindset
  - Problem-first: define success metrics before choosing solutions.
  - Trade-offs: record options and consequences via ADRs.
  - Small steps: incremental, reversible changes with feature flags when needed.
  - Observability by design: decide logs/metrics/traces at design time.
- Code quality
  - Readability first: straight-line logic, single abstraction level, one responsibility per file.
  - Clear boundaries: domain and I/O are separate; schemas and error models at edges.
  - Consistency: follow this AGENTS.md (JS/TS no semicolons; Python 3.10+ typing; Go `internal/`).
  - Tests: unit (many), contract (ports), integration (adapters), e2e (smoke); factories/mothers for data.
- Reliability & operations
  - Timeouts/retries/circuit-breaking/bulkheads; assume remote calls fail.
  - Safe deploys: blue/green or canary; two-phase data migrations; backups.
  - Runbooks: 5-minute actionable guides; blameless postmortems after incidents.
- Performance & scalability
  - Data-centric: indexes, avoid N+1, batch/stream, caching with clear invalidation.
  - Backpressure: queues, rate limits, and leak-free concurrency.
  - Cost awareness: monitor per-request cost and cold starts.
  - Memory efficiency (when equally performant): prefer the most memory-compact representation that satisfies correctness and clarity.
- Memory-efficient representation (language guidance)
  - General: choose the smallest data type that covers the valid range; avoid oversized containers; minimize unnecessary allocations and copies. Do this only when it doesn’t reduce clarity or harm performance.
  - Go: pick `uint8/uint16/int32` etc. when ranges are known; prefer `[]byte` over `string` for binary; pass slices and avoid copying; preallocate with `make(len, cap)`; avoid `interface{}` boxing; consider `time.Duration` (`int64`) for time.
  - Python: prefer `bytes/bytearray/memoryview` for binary; use `tuple` for small immutable sequences; use generators/iterators to avoid large intermediates; consider `__slots__` for high-count lightweight classes; for numeric arrays use `array('b','H','I',...)` or `numpy` dtypes when appropriate.
  - TypeScript/JavaScript: numbers are IEEE-754 doubles—use `BigInt` only when needed; for binary data use `Uint8Array`/typed arrays; avoid large intermediate arrays (prefer streaming/iterators) and object churn on hot paths.
  - Java/C#: use primitives (`int`, `short`, `byte`, `double`) instead of boxed types; prefer arrays for dense data; in C# consider `Span<T>/Memory<T>` and `struct`/`readonly struct` for value types.
  - Rust: choose the smallest integer types; borrow (`&str`, `&[u8]`) instead of owning (`String`, `Vec<u8>`) where lifetime allows; use `Option<NonZero*>` niche optimization; box large enum variants; use `#[repr(u8)]` for small enums when FFI/size matters.
  - Persistence/API alignment: keep DB columns and wire formats consistent with chosen sizes; avoid surprises from overflow/truncation and cross-language mismatches.
- Security & privacy
  - Least privilege for DB/cloud; network segmentation.
  - Secrets management, rotation, and log scrubbing.
  - Validate input/encode output; secure headers/CSP; sensitive-data handling and compliance.
- Collaboration & process
  - Clear PRs: why, how to verify, risks, rollback.
  - Code review: boundaries, error handling, tests, observability, compatibility.
  - Estimation and risk: spikes for uncertainty; list known unknowns and blockers.
  - Dependency hygiene: upgrades, SBOM, supply-chain scanning; reproducible builds.
- Red flags
  - Hidden coupling and deep imports; relying on luck (no timeouts/monitoring).
  - Mega PRs and mass renames without necessity.
  - Tests that overfit implementations and mask poor design.
- Daily habits
  - Add minimal tests and observability with each change.
  - Read ADRs/AGENTS.md/README before modifying; keep consistent.
  - Conventional commits with clear subjects.
  - Rehearse rollback paths (data/deploy/flags).

**Commit Conventions**
- Standard: Conventional Commits v1.0.0 for readable history, changelogs, and automation.
- Format: `type(scope)!: subject`
  - `type`: one of `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
  - `scope`: optional, lower-kebab. Prefer architectural or feature scopes:
    - Layers/contexts: `domain`, `app`, `ports`, `adapters`, `infra`, `platform`.
    - Subsystems: `http`, `db`, `mq`, `cache`, `scheduler`, `logging`, `metrics`, `tracing`.
    - Languages: `py`, `ts`, `js`, `go` (when the change is language-specific).
    - Feature modules: e.g., `user`, `order`, `payment`.
  - `!`: use when introducing a breaking change.
  - `subject`: imperative, concise, lowercase, no trailing period, ≤ 72 chars.
- Body (optional but recommended)
  - Explain the what and why, not restating the diff; wrap at ~72 chars.
  - Use bullets (`- `) for lists; include benchmarks or evidence for `perf`.
- Footers
  - Breaking changes: `BREAKING CHANGE: describe the impact and migration path`.
  - Issue refs: `Closes #123` `Refs #456` (comma-separated for multiples).
- Examples
  - `feat(app-user): register user with email verification`
  - `fix(adapters-db): map unique violation to conflict error`
  - `docs: add AGENTS.md user preferences (zh-TW)`
  - `refactor(domain): extract pricing policy from aggregate`
  - `perf(app): cache product list query`
  - `test(ports): add contract tests for MessageBus`
  - `ci: run mypy/ruff and go vet in pipeline`
  - `build(go): enable -race for tests`
  - `chore(deps): bump zod to 3.22.4`
  - `revert: revert "feat(app-user): register user with email verification"`
- Monorepo/workspaces guidance
  - Prefer one logical change per package/context per commit. Avoid cross-cutting mega-commits.
  - If a single commit spans contexts, pick the most representative scope or split into multiple commits.
- Merge strategy
  - Prefer small, atomic commits during development. Squash-merge PRs using a Conventional Commit title if the internal history is noisy.
- Language preference for commits
  - Per User Preferences, commit messages are in English by default. If a repo is exclusively zh-TW audience, you may write the body in zh-TW but keep `type`/`scope` and subject keywords in English for tooling compatibility.

**User Preferences**
- Language: default to Traditional Chinese (繁體中文) with Taiwan usage for all user-facing communication. Keep code identifiers, APIs, and commit messages in English unless the user explicitly requests zh-TW.
- Bilingual clarity: when introducing domain/tech terms, include the English term on first mention in parentheses; avoid over-translating established terms (API, HTTP, commit, PR).
- Ask before switching: if the conversation starts in another language or the audience changes (e.g., external docs), confirm language choice with the user.
- Regional conventions: timezone `Asia/Taipei`; dates `YYYY-MM-DD HH:mm:ss`; currency `NTD` (新台幣); metric units; thousands separator with commas in numeric examples.
- Documentation stance: this AGENTS.md and general repo docs can remain in English for broader collaboration; add zh-TW summaries on request.
