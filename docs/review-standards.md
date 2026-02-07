# Code Review Standards

This document defines the standard review criteria and priorities used by both the automated GitHub Actions Claude review (`@claude` comment) and the local CLI `review-pr` skill. Maintaining consistency between these systems ensures predictable, high-quality code reviews across all contexts.

## Review Priority Order

Reviews should follow this priority order, focusing first on critical issues before style or optimization:

1. **Linear Requirement Validation** - Does the code meet stated requirements?
2. **Security** - Are there vulnerabilities or compliance issues?
3. **Logic Errors** - Is the code correct and bug-free?
4. **Code Quality** - Is it maintainable and well-designed?
5. **Testing** - Is it adequately tested?
6. **Performance** - Is it efficient?

## Triage: What to Check Based on PR Type

Allocate review attention proportionally. Not every checklist item applies to every PR.

| PR Type | Primary Focus | Secondary | Skip |
|---------|--------------|-----------|------|
| New API endpoint | Security, Logic, Testing | Quality | Performance (unless hot path) |
| UI changes | Quality, Testing | Performance | Security (unless auth-related) |
| Config/infra | Security, Correctness | — | Testing, Performance |
| Bug fix | Logic, Testing (regression) | — | Quality, Performance |
| Dependency update | Security (CVEs) | — | Everything else |
| Docs/README only | Correctness of content | — | All code checklists |
| Database migration | Data Consistency, Performance | Security | Quality |

## Severity Definitions

### CRITICAL
**Definition**: Issues that pose immediate security risks, data loss potential, or complete feature breakage.

**Examples**:
- SQL injection vulnerabilities
- Unencrypted PHI in logs or URLs
- Authentication/authorization bypasses
- Data corruption bugs
- Complete feature non-functionality

**Action Required**: Must be fixed before merge. PR should be marked "Request Changes".

### HIGH
**Definition**: Significant bugs, logic errors, or design flaws that will cause problems in production but don't pose immediate security/data risks.

**Examples**:
- Race conditions
- Incorrect business logic
- Missing error handling for critical paths
- N+1 query problems affecting performance
- Edge cases that will cause user-facing errors

**Action Required**: Should be fixed before merge unless there's a strong justification.

### Suggestions
**Definition**: Improvements that would enhance code quality but aren't blockers.

**Examples**:
- Code duplication (refactoring opportunities)
- Minor performance optimizations
- Improved naming or documentation
- Better design patterns
- Test coverage gaps for unlikely edge cases

**Action Required**: Use developer judgment. Good to address but not blocking.

### Severity Decision Heuristic

When the boundary between HIGH and Suggestion is unclear, apply this test:

> **"If this code ships as-is, will it cause a user-visible problem within the first week?"**

| Answer | Severity |
|--------|----------|
| Yes, reliably | HIGH |
| Yes, under specific but realistic conditions | HIGH |
| Possibly, but only under unlikely conditions | Suggestion |
| No, but the code could be better | Suggestion |

**Example**: A missing null check on a field that's always populated by the ORM → **Suggestion** (unlikely to be null). A missing null check on user-submitted API input → **HIGH** (realistic condition).

## Security Review Checklist

### OWASP Top 10
- [ ] **Injection**: SQL, NoSQL, OS command, LDAP injection
- [ ] **Broken Authentication**: Session management, credential storage
- [ ] **Sensitive Data Exposure**: Encryption, PHI handling
- [ ] **XML External Entities (XXE)**: XML parser configuration
- [ ] **Broken Access Control**: Authorization checks, RBAC
- [ ] **Security Misconfiguration**: Default credentials, verbose errors
- [ ] **XSS**: Reflected, stored, DOM-based XSS
- [ ] **Insecure Deserialization**: Pickle, JSON, XML parsing
- [ ] **Components with Known Vulnerabilities**: Dependency versions
- [ ] **Insufficient Logging & Monitoring**: Audit trails, security events

### HIPAA Compliance (Healthcare Specific)
- [ ] **PHI Encryption**: PHI encrypted at rest and in transit
- [ ] **Audit Logging**: All PHI access logged with user ID and timestamp
- [ ] **Access Controls**: Role-based access enforced
- [ ] **Data Minimization**: Queries fetch only necessary PHI
- [ ] **Retention**: Data expiration/anonymization logic
- [ ] **Third-Party**: BAA requirements verified for external APIs
- [ ] **Error Messages**: PHI not exposed in errors or logs

### Common Vulnerabilities
- [ ] **SQL Injection**: Parameterized queries used (not f-strings)
- [ ] **XSS**: User input properly escaped/sanitized
- [ ] **Command Injection**: No shell=True with user input
- [ ] **Path Traversal**: File paths validated
- [ ] **CSRF**: CSRF protection on state-changing operations
- [ ] **Secrets**: No hardcoded credentials or API keys
- [ ] **Dependencies**: No known vulnerabilities in packages

## Logic & Correctness Checklist

### Edge Cases
- [ ] **Null/None**: Null values handled
- [ ] **Empty**: Empty strings, lists, dicts handled
- [ ] **Boundary Values**: Min/max values tested
- [ ] **Concurrent Access**: Race conditions considered
- [ ] **Timeouts**: Network/external service timeouts handled
- [ ] **Large Datasets**: Performance with large inputs

### Error Handling
- [ ] **Exceptions**: Specific exceptions caught (not bare except)
- [ ] **Error Context**: Error messages include useful context
- [ ] **Propagation**: Errors propagated or logged appropriately
- [ ] **User Feedback**: User-facing errors are clear and actionable
- [ ] **Cleanup**: Resources cleaned up on error paths

### Silent Failure Patterns

Pay specific attention to these error-handling anti-patterns:
- Empty `except` or `except Exception: pass` blocks that swallow errors
- Catch blocks that log but silently continue when the caller expects an exception
- Returning default values (None, empty list, 0) on error without logging or raising
- Retry logic that exhausts attempts without surfacing the underlying error
- Broad exception handlers that catch unrelated errors (e.g., `except Exception` when only `ValueError` is expected)

### Data Consistency
- [ ] **Transactions**: Database operations properly transacted
- [ ] **Atomicity**: Related changes are atomic
- [ ] **Idempotency**: Operations can be safely retried
- [ ] **Validation**: Input validation at boundaries

## Code Quality Standards

### Readability
- [ ] **Naming**: Clear, descriptive variable/function names
- [ ] **Length**: Functions are focused and reasonably sized
- [ ] **Complexity**: Cyclomatic complexity is manageable
- [ ] **Comments**: Complex logic has explanatory comments
- [ ] **Documentation**: Public APIs have docstrings/JSDoc

### Design
- [ ] **DRY**: No significant code duplication
- [ ] **SRP**: Single Responsibility Principle followed
- [ ] **Coupling**: Low coupling between modules
- [ ] **Cohesion**: High cohesion within modules
- [ ] **Abstraction**: Appropriate level of abstraction

### Conventions
- [ ] **Style**: Follows repo coding standards (from CLAUDE.md)
- [ ] **Patterns**: Consistent with existing codebase patterns
- [ ] **Formatting**: Pre-commit hooks pass (ruff, black, mypy)
- [ ] **Types**: Type hints present (Python), TypeScript types used

## Testing Standards

### Coverage
- [ ] **New Code**: All new functions/methods have tests
- [ ] **Changed Code**: Existing tests updated for changes
- [ ] **Edge Cases**: Edge cases have dedicated tests
- [ ] **Error Paths**: Error handling paths tested
- [ ] **Integration**: Integration between components tested

### Quality
- [ ] **Assertions**: Tests have meaningful assertions
- [ ] **Isolation**: Tests don't depend on external state
- [ ] **Mocking**: External dependencies properly mocked
- [ ] **Clarity**: Test names clearly describe what's tested
- [ ] **Maintainability**: Tests are easy to understand and update

### Conventions
- [ ] **Framework**: Follows pytest/Jest conventions
- [ ] **Fixtures**: Proper use of test fixtures/factories
- [ ] **Organization**: Tests organized logically
- [ ] **Performance**: Tests run quickly

### Assessment Approach

Evaluate behavioral coverage, not just whether test files exist. Ask: "Would these tests catch a meaningful regression if this code changed?" Focus on:
- Critical paths that could cause data loss or security issues if broken
- Edge cases for boundary conditions (null, empty, overflow)
- Error handling paths — are failure modes tested, not just happy paths?
- Avoid suggesting tests for trivial code unless it contains business logic

## Performance Considerations

### Database
- [ ] **N+1 Queries**: Use select_related/prefetch_related
- [ ] **Indexes**: Queries use appropriate indexes
- [ ] **Query Efficiency**: Queries fetch only needed data
- [ ] **Transactions**: Long transactions avoided
- [ ] **Connection Pooling**: Connections properly managed

### Algorithm
- [ ] **Complexity**: Reasonable time complexity (avoid O(n²) where possible)
- [ ] **Memory**: No memory leaks or unbounded growth
- [ ] **Caching**: Appropriate use of caching
- [ ] **Lazy Loading**: Data loaded only when needed

### Resources
- [ ] **File Handles**: Files properly closed
- [ ] **Network**: Connections properly closed
- [ ] **Memory**: Large objects cleaned up when done
- [ ] **CPU**: No busy-waiting or unnecessary computation

## Output Format for Reviews

The review body should be a concise summary. Code-specific findings (CRITICAL, HIGH, Suggestion) are posted as inline comments on the PR diff — not in the review body.

```markdown
> [1-2 sentences: what the PR does]

**Linear**: [Issue-ID](https://linear.app/quantivly/issue/Issue-ID/) — [Status: ✅ Aligned / ⚠️ Gaps / ❌ Misaligned]

**Re-review**: [If re-review: "Re-review #N. X of Y prior findings addressed. Focusing on new/changed code." Omit on first review.]

**Issues**: 🚨 X · ⚠️ Y · 💡 Z — see inline comments

[If findings were omitted due to comment cap, add a collapsible <details> block listing them with file:line references.]

**Highlights**:
- ✅ [Notable good practice]
- ✅ [Another positive]
```

**Review event** is chosen based on findings:
- `REQUEST_CHANGES`: Has CRITICAL issues
- `COMMENT`: Has HIGH issues or needs clarification
- `APPROVE`: Only suggestions, no blockers

**Inline comments** use severity emoji prefixes and bolded short titles:
- 🚨 for security and data loss issues (must fix)
- ⚠️ for bugs and logic errors (should fix)
- 💡 for improvements (nice to have)

Format: `<emoji> **<Short Title>** → explanation → suggestion/code block`

Each inline comment must include a concrete fix suggestion. When the fix directly replaces the commented line(s), use a GitHub suggestion block (`` ```suggestion ``) so the developer can one-click apply or batch suggestions into a commit. When the fix involves changes elsewhere or structural modifications, use a regular code block with language annotation (e.g., `` ```python ``).

**Suggestion block rules**:
- Use `suggestion` when the fix is a direct replacement of the targeted line(s) and the replacement is complete (no `...` elision)
- Use a regular code block when the fix involves adding code elsewhere, structural changes, or the comment is about the absence of something
- For multi-line suggestions, use `start_line`/`start_side` and `line`/`side` in the review API call
- Each comment body may contain at most one suggestion block
- Suggestion blocks only work on lines that are part of the PR diff

Project-level observations (Linear misalignment, PR scope, architectural direction) belong in the review body, not as inline comments.

## Review Guidelines

### What to Focus On
- **Security first**: Healthcare context means PHI and HIPAA compliance are critical
- **Correctness over style**: Logic errors are more important than formatting
- **Context matters**: Reference Linear requirements and existing patterns
- **Explain WHY**: Don't just flag issues, explain the impact
- **Be specific**: Include file paths and line numbers
- **Be actionable**: Provide concrete fixes, preferably with code examples

### What to Skip
- **Formatting/Linting**: Pre-commit hooks handle this (ruff, black, mypy)
- **Style Preferences**: Unless it violates CLAUDE.md conventions
- **Premature Optimization**: Unless there's a clear performance problem
- **Bikeshedding**: Focus on substance over style

### Common False Positives to Skip
- **Django `Meta` classes** don't need docstrings — they are declarative configuration, not logic
- **`# type: ignore` comments** — verify the suppression context before flagging; these are typically intentional workarounds for mypy limitations
- **Test fixtures appearing as "unused variables"** — pytest injects them via function parameters
- **Django settings files with uppercase naming** — these are constants by design (e.g., `DEBUG`, `ALLOWED_HOSTS`)
- **`noqa` comments** — intentional lint suppressions, not code smells

This list should evolve based on recurring false positives identified in review feedback.

### Edge Cases & Nuance
- **False Positives**: If unsure, mark as "Suggestion" not "CRITICAL"
- **Context Dependent**: Consider repo-specific patterns from CLAUDE.md
- **Tech Stack**: Apply appropriate standards (Django vs React vs Docker)
- **Risk Assessment**: Weigh severity based on healthcare/PHI context

## Tool Allocation

Different tools handle different aspects of code quality:

| Tool | Responsibility | When It Runs |
|------|---------------|--------------|
| **Pre-commit hooks** (ruff, black, mypy) | Formatting, linting, obvious errors, type hints | Before every commit (local) |
| **Claude Code Review** | Security, logic, design, testing, performance, Linear alignment | On `@claude` comment (GitHub Actions) or via CLI |
| **CI/CD Pipeline** (pytest, coverage) | Unit/integration tests, coverage thresholds | Automatic on PR push |

**Claude reviews should NOT flag**:
- Line length violations (ruff handles this)
- Import sorting (ruff handles this)
- Missing type hints (mypy handles this)
- Formatting issues (black handles this)

**Claude reviews SHOULD flag**:
- Security vulnerabilities
- Logic errors and bugs
- Design issues
- Testing gaps
- Performance problems
- Linear requirement misalignment

## Linear Integration

### Issue Format
PR titles must include Linear issue ID in format: `AAA-#### Description`

**Examples**:
- ✅ `HUB-1234 Add CSV export feature`
- ✅ `ENG-5678 Fix race condition in cache sync`
- ❌ `Add CSV export` (no Linear ID)
- ❌ `hub-1234 Add feature` (lowercase not recognized)

### Requirement Validation
When Linear issue is referenced:
1. Fetch issue via Linear tools/API
2. Check description and acceptance criteria
3. Review comments for additional requirements
4. Validate PR aligns with requirements
5. Flag gaps between implementation and requirements

### Issue Quality Feedback
Provide advisory (non-blocking) feedback if Linear issue lacks:
- Clear acceptance criteria
- Technical specifications
- Edge case documentation
- Security requirements
- Performance requirements

## Cross-Repository Context (GitHub MCP)

When GitHub MCP tools are available, Claude can fetch code from related repositories to validate changes:

### When to Use Cross-Repo Context
- **API endpoint changes** in `sre-core` → Check frontend consumers in `sre-ui`
- **Type/interface changes** in `sre-core` → Validate compatibility with `sre-ui` TypeScript types
- **auto-conf template changes** in `platform` → Verify stack file rendering for all products
- **SDK changes** in `platform` → Check consuming services (box, ptbi, etc.)
- **Event bridge changes** → Validate WAMP router integration and REST API consumers

### Quantivly Repository Architecture

Two-layer architecture: **platform** provides the foundational data infrastructure, **hub** provides the user-facing analytics portal on top.

**platform** (`quantivly-dockers` repo) - Core DICOM/RIS data backbone
The foundational layer that ingests, processes, and stores medical imaging data:
| Component | Role | Depends On |
|-----------|------|------------|
| `box` | DICOM harmonization (GE/Philips/Siemens), RIS integration | `quantivly-sdk` |
| `ptbi` | DICOM networking (Python+Java/dcm4che) | `quantivly-sdk` |
| `auto-conf` | Jinja2 stack generator (configures both platform AND hub) | — |
| `quantivly-sdk` | Python SDK for platform services | — |

**hub** (`hub` repo) - Healthcare analytics portal (builds on platform)
User-facing application providing analytics, recommendations, and plugins:
| Repository | Role | Depends On |
|------------|------|------------|
| `sre-core` | Django backend (GraphQL API, plugin system) | `sre-sdk` |
| `sre-ui` | Next.js frontend | `sre-core` GraphQL |
| `sre-event-bridge` | WAMP→REST bridge (connects to platform's WAMP router) | `sre-sdk` |
| `sre-postgres` | PostgreSQL database | — |
| `sre-sdk` | Python SDK for hub services | — |

**How they connect**: In production, hub integrates with platform's backbone (Keycloak auth, WAMP messaging, shared networking). Platform's `auto-conf` generates deployment configs for both: platform services (`modules/quantivly/box/`, etc.) and hub services (`modules/quantivly/sre/`).

### Cross-Repo Validation Examples
| Change In | Validate Against |
|-----------|------------------|
| `sre-core` GraphQL schema | `sre-ui` TypeScript types/queries |
| `sre-sdk` | `sre-core`, `sre-event-bridge` |
| `quantivly-sdk` | `box`, `ptbi`, `healthcheck` |
| `auto-conf` templates | Rendered stack files |

### How to Access Cross-Repo Files

Use `gh api repos/quantivly/<repo>/contents/<path>` to fetch files from other repositories.
Do not use GitHub MCP tools for cross-repo access — they are not configured in the review workflow. The `gh api` command with GET requests is the correct approach.

### Guidelines
- Only access repositories within the `quantivly` organization
- Use cross-repo context when reviewing changes to shared/exported code
- Validate that API contracts are maintained across repositories
- Don't fetch files that are already available in the PR diff — use the local checkout instead

## Healthcare/HIPAA Context

Quantivly builds healthcare analytics software, which means:

### Extra Scrutiny For
- **PHI Handling**: Any code touching patient data
- **Access Controls**: Who can see what data
- **Audit Logging**: All data access must be logged
- **Encryption**: Data at rest and in transit
- **Third-Party**: External service integration requires BAA — if a PR introduces a new third-party API integration (new SDK import, HTTP client call to a non-Quantivly domain), flag as HIGH for BAA review

### Common Patterns

**hub (sre-*) patterns**:
- **Django (sre-core)**: Plugin system, GraphQL API, Celery tasks
- **Next.js (sre-ui)**: Server-side rendering, Keycloak auth
- **Data Flow**: PostgreSQL → Django → GraphQL → Next.js
- **Authentication**: Hybrid Keycloak + Django admin

**platform patterns**:
- **WAMP**: Inter-service communication via Crossbar.io router (pub/sub + RPC)
- **Poetry**: Package management for all Python services
- **Docker Swarm**: Container orchestration with Compose files
- **Flyway**: SQL database migrations with versioned scripts
- **Code Style**: Black (120 line-length), isort, Ruff, pre-commit hooks
- **Testing**: pytest with `--dockers-host` for integration tests

## Framework-Specific Review Patterns

### Django (sre-core)

Watch for these common Django anti-patterns:

| Pattern | Why It Matters | Fix |
|---------|---------------|-----|
| `QuerySet.all()` in views without pagination | Unbounded result sets cause OOM on large tables | Use `Paginator` or limit with `[:N]` |
| Missing `select_related`/`prefetch_related` on FK traversals | N+1 queries — each row triggers a separate DB query | Add to the initial queryset |
| `Model.save()` without `update_fields` | Full row write — overwrites concurrent changes | Pass `update_fields=['field1', 'field2']` |
| Celery tasks without `bind=True` and retry logic | Transient failures silently drop tasks | Add `bind=True`, `autoretry_for`, `max_retries` |
| GraphQL resolvers bypassing Django's permission system | Authorization checks skipped for API queries | Use `@permission_required` or check in resolver |
| Raw SQL without parameterization | SQL injection risk in custom queries | Use `cursor.execute(sql, params)` with `%s` placeholders |
| `except Exception` in view/API handlers | Masks unrelated errors (import, memory) as user errors | Catch specific exceptions (`ValueError`, `ObjectDoesNotExist`) |

### Next.js (sre-ui)

Watch for these common Next.js anti-patterns:

| Pattern | Why It Matters | Fix |
|---------|---------------|-----|
| Client-side fetch when SSR/SSG is appropriate | Unnecessary loading states, worse SEO, slower TTFB | Use `getServerSideProps` or `getStaticProps` |
| Missing `key` props in list rendering | React can't track list items, causes rendering bugs | Add stable, unique `key` from data (not array index) |
| Large library imports without tree-shaking | Bundle size bloat — entire library shipped to client | Use `dynamic(() => import(...))` or named imports |
| Sensitive data in `NEXT_PUBLIC_*` env vars | Client-visible — anyone can read from browser | Use server-only env vars with API routes |
| Missing error boundaries around data components | One failed component crashes the entire page | Wrap data-dependent sections with `ErrorBoundary` |
| Inline styles or `sx` props for reusable patterns | Style duplication, inconsistent theming | Extract to shared styled components or CSS modules |

## Continuous Improvement

This document should evolve based on:
- **Issue Patterns**: Common findings from monthly metrics
- **False Positives**: Reduce noise in reviews
- **Team Feedback**: Developer pain points
- **New Technologies**: As stack evolves

**Review quarterly** and update based on data from `claude-metrics.py` reports.

## Changelog

- **2026-02-07**: Added GitHub suggestion block guidance for inline comments, bolded short titles format, suggestion vs regular code block rules
- **2026-02-07**: Added false-positive exclusion list, BAA guidance for third-party integrations, framework-specific patterns (Django, Next.js), severity decision heuristic, changelog section
- **2026-02-06**: Added few-shot review examples, adaptive comment caps, silent failure patterns, testing assessment approach
- **2026-02-05**: Added PR-type triage matrix, cross-repository validation section
- **2026-02-03**: Separated project-level findings from inline comments, tool allocation table

---

**Last Updated**: 2026-02-07
**Owner**: Engineering Team
**Related**: [Claude Integration Guide](claude-integration-guide.md), [Review Examples](review-examples.md), Repository CLAUDE.md files
