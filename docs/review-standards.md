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

Reviews should follow this structure for consistency:

```markdown
## Summary
[2-3 sentence overview of PR and overall assessment]

## Alignment with Linear Requirements
[Requirement validation if Linear issue referenced]
[Linear issue quality feedback if applicable - ADVISORY ONLY]

## Critical Issues (Must Fix Before Merge)
[List ONLY if found, with specific locations and fixes]
1. **[Category]**: [Description]
   - **Location**: `file.py:123-145`
   - **Finding**: [What is wrong]
   - **Risk**: [Why this matters]
   - **Fix**: [Concrete recommendation with code example]
   - **Severity**: CRITICAL | HIGH

[If none: "No critical issues identified"]

## Suggestions (Should Consider)
[Non-blocking improvements]
1. **[Category]**: [Description]
   - **Location**: `file.py:456`
   - **Current**: [What exists]
   - **Suggested**: [Alternative approach]
   - **Benefit**: [Why this helps]

[If none: "No significant suggestions"]

## Positive Observations
[2-3 good patterns or practices observed]
- [Specific positive finding with location]

## Testing Assessment
- **Coverage**: [Assessment of test completeness]
- **Edge Cases**: [Which edge cases are/aren't tested]
- **Quality**: [Test quality observations]

## Recommendation
**[APPROVE | REQUEST_CHANGES | COMMENT]**

[1-2 sentence justification]
```

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

**hub** (superproject + release management)
- Creates manifest images with correct service versions
- Orchestrates releases across sre-* components
- Contains submodules: sre-core, sre-ui, sre-event-bridge, sre-postgres

**sre-*** (hub components)
| Repository | Description |
|------------|-------------|
| `sre-core` | Django backend - GraphQL API, business logic |
| `sre-ui` | React + Next.js frontend - consumes sre-core APIs |
| `sre-event-bridge` | WAMP router bridge - notifies backend via REST API |
| `sre-postgres` | PostgreSQL database for hub |

**platform** (quantivly-dockers - backbone services)
| Component | Description |
|-----------|-------------|
| `auto-conf` | Stack file templates and rendering logic for all products |
| `box` | Main data processing engine (DICOM harmonization, RIS) |
| `ptbi` | DICOM networking (SCP/SCU operations) |
| `quantivly-sdk` | Foundation library for all Python services |

### Cross-Repo Validation Examples
| Change In | Validate Against |
|-----------|------------------|
| `sre-core` GraphQL schema | `sre-ui` TypeScript types and queries |
| `sre-core` API endpoints | `sre-ui` API client calls |
| `platform/auto-conf` templates | Rendered stack files for hub, other products |
| `platform/quantivly-sdk` | Services using SDK (box, ptbi) |

### Available GitHub MCP Tools
- `github_get_file_contents` - Read specific files from any Quantivly repo
- `github_search_code` - Search for code patterns across organization repos
- `github_get_commit` - Get commit details for context
- `github_list_commits` - List recent commits in a repository

### Guidelines
- Only access repositories within the `quantivly` organization
- Use cross-repo context when reviewing changes to shared/exported code
- Validate that API contracts are maintained across repositories
- Don't use GitHub tools for files already in the PR diff

## Healthcare/HIPAA Context

Quantivly builds healthcare analytics software, which means:

### Extra Scrutiny For
- **PHI Handling**: Any code touching patient data
- **Access Controls**: Who can see what data
- **Audit Logging**: All data access must be logged
- **Encryption**: Data at rest and in transit
- **Third-Party**: External service integration requires BAA

### Common Patterns
- **Django**: Plugin system, GraphQL API, Celery tasks
- **Next.js**: Server-side rendering, Keycloak auth
- **Data Flow**: PostgreSQL → Django → GraphQL → Next.js
- **Authentication**: Hybrid Keycloak + Django admin

## Continuous Improvement

This document should evolve based on:
- **Issue Patterns**: Common findings from monthly metrics
- **False Positives**: Reduce noise in reviews
- **Team Feedback**: Developer pain points
- **New Technologies**: As stack evolves

**Review quarterly** and update based on data from `claude-metrics.py` reports.

---

**Last Updated**: 2026-02-05
**Owner**: Engineering Team
**Related**: [Claude Integration Guide](claude-integration-guide.md), Repository CLAUDE.md files
