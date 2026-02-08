# Review Examples

This document provides concrete examples of complete Claude reviews for reference. These examples illustrate the expected output format, severity calibration, and quality standards.

## Example 1: Review with Findings (COMMENT)

**Scenario**: PR adds a new CSV export endpoint with a SQL injection vulnerability and a missing edge case.

### Review JSON submitted via `gh api`:

```json
{
  "event": "COMMENT",
  "body": "## 📋 Summary\n\n> Adds CSV export endpoint for study utilization data with date range filtering.\n\n<img src=\"https://raw.githubusercontent.com/quantivly/.github/master/assets/icons/linear.png\" alt=\"Linear\" height=\"18\"> [HUB-1234](https://linear.app/quantivly/issue/HUB-1234/) — ✅ Aligned (implements export with date filtering as specified)\n\n**Highlights**:\n- ✅ Good use of streaming response for large datasets\n- ✅ Proper Celery task for async generation\n\n🚨 0 · ⚠️ 1 · 💡 1 — see inline comments\n\n---\n<sub>@reviewer<!-- METRICS --> · [Logs](https://github.com/quantivly/sre-core/actions/runs/12345) · 👍 👎</sub>",
  "comments": [
    {
      "path": "apps/export/views.py",
      "line": 47,
      "side": "RIGHT",
      "body": "⚠️ **Unprotected date interpolation**\n\nThe `start_date` parameter is interpolated directly into the queryset filter via `__range` with an f-string. While Django ORM parameterizes `filter()` calls, this intermediate string formatting defeats that protection.\n\n```suggestion\nStudy.objects.filter(created_at__range=(start_date, end_date))\n```"
    },
    {
      "path": "apps/export/views.py",
      "line": 62,
      "side": "RIGHT",
      "body": "💡 **Empty dataset returns data file**\n\nWhen `queryset` is empty, `csv.writer` still writes the header row but the response Content-Disposition suggests a data file. Consider returning a 204 No Content or including a message row so users understand the export is intentionally empty rather than broken."
    }
  ]
}
```

### Why this is a good review:

- **2 findings, both high-confidence** — not 8 uncertain ones
- **Inline comments reference specific lines** with exact code context
- **Suggestion block for direct replacement** — the ⚠️ finding uses `` ```suggestion `` because the fix directly replaces line 47, enabling one-click apply
- **Regular text for behavioral advice** — the 💡 finding has no code block because it's about adding a check, not replacing the current line
- **Bolded short titles** — each comment starts with `**Short Title**` for quick scanning
- **Severity calibration is accurate** — SQL concern is ⚠️ (not 🚨 because Django ORM provides some protection), empty result is 💡
- **Summary is concise** — 4 lines plus highlights
- **Project-level observation** (Linear alignment) is in the body, not an inline comment

---

## Example 2: Clean Review (APPROVE)

**Scenario**: PR implements a well-tested feature that aligns with requirements and has no significant issues.

### Review JSON submitted via `gh api`:

```json
{
  "event": "APPROVE",
  "body": "## 📋 Summary\n\n> Adds role-based dashboard filtering so facility managers only see their assigned facilities.\n\n<img src=\"https://raw.githubusercontent.com/quantivly/.github/master/assets/icons/linear.png\" alt=\"Linear\" height=\"18\"> [HUB-5678](https://linear.app/quantivly/issue/HUB-5678/) — ✅ Aligned (implements all 3 acceptance criteria)\n\n**Highlights**:\n- ✅ Access control check at both GraphQL resolver and queryset level (defense in depth)\n- ✅ Comprehensive test coverage including cross-facility access denial\n- ✅ Audit logging for filtered access attempts\n\n🚨 0 · ⚠️ 0 · 💡 0\n\n---\n<sub>@reviewer<!-- METRICS --> · [Logs](https://github.com/quantivly/sre-core/actions/runs/12346) · 👍 👎</sub>",
  "comments": []
}
```

### Why this is a good review:

- **Empty comments array** — no findings means no inline comments, not forced suggestions
- **APPROVE event** — matches the assessment (no blockers)
- **Highlights call out specific good practices** — not generic praise like "looks good"
- **Linear validation is specific** — references the 3 acceptance criteria, not just "aligned"

---

## Example 3: Re-review After Fixes (APPROVE)

**Scenario**: Second review after the developer addressed the findings from Example 1.

### Review JSON submitted via `gh api`:

```json
{
  "event": "APPROVE",
  "body": "## 📋 Summary\n\n> Adds CSV export endpoint for study utilization data with date range filtering.\n\n<img src=\"https://raw.githubusercontent.com/quantivly/.github/master/assets/icons/linear.png\" alt=\"Linear\" height=\"18\"> [HUB-1234](https://linear.app/quantivly/issue/HUB-1234/) — ✅ Aligned\n\n🔄 **Re-review #2** — 2 of 2 prior findings addressed. Focusing on new/changed code.\n\n**Highlights**:\n- ✅ SQL parameterization fixed — dates now passed directly to ORM filter\n- ✅ Empty dataset now returns 204 with descriptive message header\n\n🚨 0 · ⚠️ 0 · 💡 0\n\n---\n<sub>@reviewer<!-- METRICS --> · [Logs](https://github.com/quantivly/sre-core/actions/runs/12347) · 👍 👎</sub>",
  "comments": []
}
```

### Why this is a good re-review:

- **Re-review line** documents that this is a follow-up and all issues were addressed
- **No re-flagging** of previously reported issues that were fixed
- **Highlights specifically acknowledge the fixes** rather than repeating original findings
- **APPROVE** because all prior issues are resolved and no new issues found

---

## Example 4: Critical Security Finding (REQUEST_CHANGES)

**Scenario**: PR introduces a management command that logs PHI in plaintext.

### Review JSON submitted via `gh api`:

```json
{
  "event": "REQUEST_CHANGES",
  "body": "## 📋 Summary\n\n> Adds management command to bulk-update patient study assignments.\n\n<img src=\"https://raw.githubusercontent.com/quantivly/.github/master/assets/icons/linear.png\" alt=\"Linear\" height=\"18\"> [HUB-9012](https://linear.app/quantivly/issue/HUB-9012/) — ⚠️ Gaps (issue doesn't mention logging, but HIPAA requires audit trail without PHI exposure)\n\n**Highlights**:\n- ✅ Proper use of database transaction for atomic bulk update\n- ✅ Dry-run mode for safe testing\n\n🚨 1 · ⚠️ 0 · 💡 1 — see inline comments\n\n---\n<sub>@reviewer<!-- METRICS --> · [Logs](https://github.com/quantivly/sre-core/actions/runs/12348) · 👍 👎</sub>",
  "comments": [
    {
      "path": "apps/studies/management/commands/bulk_assign.py",
      "start_line": 33,
      "line": 34,
      "start_side": "RIGHT",
      "side": "RIGHT",
      "body": "🚨 **PHI in application logs**\n\nPatient MRN and name are logged in plaintext via `logger.info(f\"Reassigning {patient.name} (MRN: {patient.mrn})\")`. This is a HIPAA violation — PHI must not appear in application logs.\n\nIf an audit trail is needed, use the existing `AuditLog` model which handles PHI encryption.\n\n```suggestion\nlogger.info(\"Reassigning study %s for patient pk=%s\", assignment.id, patient.pk)\n```"
    },
    {
      "path": "apps/studies/management/commands/bulk_assign.py",
      "line": 58,
      "side": "RIGHT",
      "body": "💡 **Large batch size default**\n\nThe `--batch-size` argument defaults to 1000. For facilities with 50k+ studies, this could cause memory pressure. Consider adding a progress bar with `tqdm` and processing in smaller batches (e.g., default 200) to keep memory bounded."
    }
  ]
}
```

### Why this is a good review:

- **REQUEST_CHANGES** because there's a CRITICAL HIPAA violation — this is the correct event for security issues
- **The critical finding is high-confidence** — logging PHI in plaintext is unambiguous
- **Multi-line suggestion block** — uses `start_line: 33` and `line: 34` to replace both logging lines with the safe version, enabling one-click apply
- **Fix suggestion is specific** — shows exact replacement code and references existing AuditLog model
- **The suggestion is separate** — memory concern is 💡 because it's optimization, not a blocker
- **Linear gap noted** — the issue didn't mention logging requirements, flagged as advisory

---

## Example 5: Docs/Config Review with Haiku (APPROVE)

**Scenario**: PR updates README and adds a YAML configuration file. Haiku is auto-selected because all files are docs/config.

### Review JSON submitted via `gh api`:

```json
{
  "event": "APPROVE",
  "body": "## 📋 Summary\n\n> Updates project README with new deployment instructions and adds Helm chart values template.\n\n<img src=\"https://raw.githubusercontent.com/quantivly/.github/master/assets/icons/linear.png\" alt=\"Linear\" height=\"18\"> [OPS-456](https://linear.app/quantivly/issue/OPS-456/) — ✅ Aligned (adds deployment docs as requested)\n\n**Highlights**:\n- ✅ Clear step-by-step deployment instructions with prerequisites\n- ✅ Helm values template includes sensible defaults with comments\n\n🚨 0 · ⚠️ 0 · 💡 1 — see inline comments\n\n---\n<sub>@reviewer<!-- METRICS --> · [Logs](https://github.com/quantivly/sre-core/actions/runs/12349) · 👍 👎</sub>",
  "comments": [
    {
      "path": "docs/deployment.md",
      "line": 28,
      "side": "RIGHT",
      "body": "💡 The example `POSTGRES_PASSWORD=changeme` could be mistaken for a real credential and accidentally committed as-is. Consider using a clearly placeholder value like `<your-password-here>` or referencing a secrets manager instead."
    }
  ]
}
```

### Why this is a good docs/config review:

- **Appropriate depth for non-code PR** — one lightweight suggestion, not over-analyzed
- **APPROVE despite having a suggestion** — docs PRs don't need to block on minor feedback
- **Finding is practical** — placeholder credentials in docs is a real problem worth flagging
- **No code-quality comments** — no linting, formatting, or complexity feedback on documentation

---

## Example 6: Large PR with Opus and Comment Cap (COMMENT)

**Scenario**: A 700-line PR refactoring the authentication middleware. Opus is selected due to security paths and size. Comment cap is 12 but there are 15 findings — the review triages to show only the most critical ones inline.

### Review JSON submitted via `gh api`:

```json
{
  "event": "COMMENT",
  "body": "## 📋 Summary\n\n> Refactors authentication middleware to support multi-tenant Keycloak realms with per-facility token validation.\n\n<img src=\"https://raw.githubusercontent.com/quantivly/.github/master/assets/icons/linear.png\" alt=\"Linear\" height=\"18\"> [HUB-2345](https://linear.app/quantivly/issue/HUB-2345/) — ✅ Aligned (implements all 4 acceptance criteria for multi-tenant auth)\n\n**Highlights**:\n- ✅ Token validation uses RS256 with JWKS endpoint (not shared secrets)\n- ✅ Per-facility realm isolation prevents cross-tenant data access\n- ✅ Comprehensive test suite with 12 test cases covering happy path and error scenarios\n\n🚨 0 · ⚠️ 3 · 💡 2 — see inline comments\n\n<details>\n<summary>📋 3 additional findings omitted (comment cap)</summary>\n\n- `middleware/keycloak.py:142` — Consider caching realm discovery documents to reduce auth latency\n- `middleware/keycloak.py:198` — The `max_retries=5` constant could be extracted to settings for configurability\n- `tests/test_auth.py:67` — Missing test for expired token with valid realm but revoked permissions\n\n</details>\n\n---\n<sub>@reviewer<!-- METRICS --> · [Logs](https://github.com/quantivly/sre-core/actions/runs/12350) · 👍 👎</sub>",
  "comments": [
    {
      "path": "middleware/keycloak.py",
      "line": 67,
      "side": "RIGHT",
      "body": "⚠️ **Missing audience claim validation**\n\nThe `audience` claim is not validated during token verification. An attacker with a valid token from a different Keycloak client could access this service's endpoints.\n\n```suggestion\ndecoded = jwt.decode(\n    token, key,\n    algorithms=['RS256'],\n    audience=settings.KEYCLOAK_CLIENT_ID,\n)\n```"
    },
    {
      "path": "middleware/keycloak.py",
      "line": 89,
      "side": "RIGHT",
      "body": "⚠️ **Missing HTTP timeout**\n\n`requests.get(jwks_url)` has no timeout. If the Keycloak server is slow or unreachable, this blocks the request thread indefinitely.\n\n```suggestion\nresponse = requests.get(jwks_url, timeout=5)\n```"
    },
    {
      "path": "middleware/keycloak.py",
      "start_line": 112,
      "line": 114,
      "start_side": "RIGHT",
      "side": "RIGHT",
      "body": "⚠️ **Overly broad exception handler**\n\nThe `except Exception` block catches all errors during token decode (including `ImportError`, `MemoryError`) and returns 401. This masks unrelated failures as authentication errors.\n\n```suggestion\nexcept (jwt.ExpiredSignatureError, jwt.InvalidTokenError, jwt.DecodeError) as e:\n    logger.warning('Token validation failed: %s', e)\n    return JsonResponse({'error': 'Invalid token'}, status=401)\n```"
    },
    {
      "path": "middleware/keycloak.py",
      "line": 156,
      "side": "RIGHT",
      "body": "💡 **Per-request DB query for realm mapping**\n\nThe realm-to-facility mapping is loaded from the database on every request. For high-traffic endpoints, this adds a query per request. Consider using Django's `cache_page` or a TTL-based in-memory cache with a 5-minute expiry."
    },
    {
      "path": "tests/test_auth.py",
      "line": 34,
      "side": "RIGHT",
      "body": "💡 **Test algorithm mismatch**\n\nThe test JWT is constructed with `HS256` algorithm, but production uses `RS256`. This means the test doesn't exercise the JWKS key retrieval path. Consider using `PyJWT`'s `jwt.encode()` with an RSA test key to match production behavior."
    }
  ]
}
```

### Why this is a good large PR review:

- **Suggestion blocks for direct replacements** — all 3 ⚠️ findings use `` ```suggestion `` because each fix directly replaces the commented line(s); the multi-line exception handler uses `start_line`/`line` to span 3 lines
- **Regular text for behavioral advice** — 💡 findings have no code block because they suggest architectural changes, not line replacements
- **Prioritized findings** — the 3 inline ⚠️ findings are highest impact (security, reliability, error masking); lower-priority items are in the body
- **Comment cap explained** — collapsible `<details>` block lists 3 additional suggestions that didn't fit, with file:line references
- **Linear validation is thorough** — references 4 acceptance criteria
- **Highlights are specific** — RS256, per-facility isolation, test count — not generic praise

---

## Example 7: Review with Custom Instructions (COMMENT)

**Scenario**: Developer commented `@claude focus on N+1 queries and database performance`. The custom instructions are incorporated into the review focus.

### Review JSON submitted via `gh api`:

```json
{
  "event": "COMMENT",
  "body": "## 📋 Summary\n\n> Adds facility dashboard endpoint aggregating study counts, equipment utilization, and alert summaries.\n\n<img src=\"https://raw.githubusercontent.com/quantivly/.github/master/assets/icons/linear.png\" alt=\"Linear\" height=\"18\"> [HUB-3456](https://linear.app/quantivly/issue/HUB-3456/) — ✅ Aligned\n\n**Custom focus**: N+1 queries and database performance (as requested)\n\n**Highlights**:\n- ✅ Good use of `annotate()` for study count aggregation (avoids per-facility query)\n- ✅ Dashboard response is paginated (won't unboundedly grow)\n\n🚨 0 · ⚠️ 2 · 💡 1 — see inline comments\n\n---\n<sub>@reviewer<!-- METRICS --> · [Logs](https://github.com/quantivly/sre-core/actions/runs/12351) · 👍 👎</sub>",
  "comments": [
    {
      "path": "apps/dashboard/resolvers.py",
      "line": 45,
      "side": "RIGHT",
      "body": "⚠️ N+1 query: `facility.equipment_set.all()` inside the list comprehension executes a separate query for each facility. With 50 facilities, this is 50 additional queries.\n\nFix: Add `prefetch_related` to the initial queryset:\n```python\nfacilities = Facility.objects.filter(\n    organization=org\n).prefetch_related('equipment_set').annotate(\n    study_count=Count('studies')\n)\n```"
    },
    {
      "path": "apps/dashboard/resolvers.py",
      "line": 72,
      "side": "RIGHT",
      "body": "⚠️ `Alert.objects.filter(facility=facility, resolved=False).count()` inside the loop creates another N+1 pattern. This can be aggregated in one query.\n\nFix: Use a subquery annotation:\n```python\nfrom django.db.models import Subquery, OuterRef\n\nopen_alerts = Alert.objects.filter(\n    facility=OuterRef('pk'), resolved=False\n).values('facility').annotate(c=Count('*')).values('c')\n\nfacilities = facilities.annotate(open_alert_count=Subquery(open_alerts))\n```"
    },
    {
      "path": "apps/dashboard/resolvers.py",
      "line": 88,
      "side": "RIGHT",
      "body": "💡 The `last_activity` field calls `studies.order_by('-created_at').first()` per facility. Since you're already querying facilities, consider adding `.annotate(last_activity=Max('studies__created_at'))` to get this in the same query."
    }
  ]
}
```

### Why this is a good custom-instruction review:

- **Custom focus is acknowledged** — the body includes a "Custom focus" line showing what was requested
- **Findings align with focus** — all 3 findings are database performance issues, matching the developer's request
- **Standard review isn't abandoned** — security and logic checks still ran (just no findings in those areas)
- **All findings are N+1 or query optimization** — demonstrating the custom focus was effective

---

## Example 8: Mixed Suggestion and Fallback Formats (COMMENT)

**Scenario**: PR adds a paginated API endpoint. One finding has a direct line replacement (suggestion block), and the other requires adding code at a different location (regular code block). This demonstrates how to choose the right format per finding.

### Review JSON submitted via `gh api`:

```json
{
  "event": "COMMENT",
  "body": "## 📋 Summary\n\n> Adds paginated list endpoint for facility equipment inventory.\n\n<img src=\"https://raw.githubusercontent.com/quantivly/.github/master/assets/icons/linear.png\" alt=\"Linear\" height=\"18\"> [HUB-4567](https://linear.app/quantivly/issue/HUB-4567/) — ✅ Aligned\n\n**Highlights**:\n- ✅ Proper use of DjangoFilterBackend for query parameters\n- ✅ Serializer validates equipment status transitions\n\n🚨 0 · ⚠️ 1 · 💡 1 — see inline comments\n\n---\n<sub>@reviewer<!-- METRICS --> · [Logs](https://github.com/quantivly/sre-core/actions/runs/12352) · 👍 👎</sub>",
  "comments": [
    {
      "path": "apps/equipment/views.py",
      "line": 38,
      "side": "RIGHT",
      "body": "⚠️ **Unbounded queryset**\n\nThe `get_queryset` method returns `Equipment.objects.all()` without pagination defaults. If the frontend omits the `page` query parameter, Django REST Framework returns all rows in a single response.\n\n```suggestion\n    return Equipment.objects.all().order_by('id')[:100]\n```"
    },
    {
      "path": "apps/equipment/views.py",
      "line": 25,
      "side": "RIGHT",
      "body": "⚠️ **Missing `select_related` for FK traversal**\n\nThe serializer accesses `equipment.facility.name` (line 52), but the queryset doesn't prefetch the facility relation. This creates an N+1 query — one additional query per equipment item.\n\nFix: Add `select_related` to the queryset in `get_queryset`:\n```python\nreturn Equipment.objects.select_related('facility').all()\n```\n\n(Not using a suggestion block because the fix applies to `get_queryset` at line 38, not to the viewset class definition at line 25 where the issue manifests.)"
    }
  ]
}
```

### Why this is a good mixed-format review:

- **Suggestion block for direct replacement** — the first finding replaces line 38 exactly, so `` ```suggestion `` enables one-click apply
- **Regular code block for cross-line fix** — the second finding is attached to line 25 (where the FK is declared in the serializer) but the fix belongs at line 38 (`get_queryset`), so a regular code block is correct
- **Explicit annotation** — the second comment explains *why* it doesn't use a suggestion block, helping calibrate expectations

---

## Anti-Examples: What Bad Reviews Look Like

These examples show common failure modes to avoid.

### Anti-Example A: Flagging Formatting Issues (ruff's Job)

**What went wrong**: The review flags import sorting and line length — issues that pre-commit hooks (ruff, black) already handle.

```json
{
  "comments": [
    {
      "path": "apps/export/views.py",
      "line": 3,
      "side": "RIGHT",
      "body": "💡 Imports should be sorted alphabetically. `from datetime import date` should come before `from django.http import JsonResponse`."
    },
    {
      "path": "apps/export/views.py",
      "line": 45,
      "side": "RIGHT",
      "body": "💡 This line exceeds 120 characters. Consider breaking it into multiple lines for readability."
    }
  ]
}
```

**Why this is wrong**:
- Import sorting is ruff/isort's responsibility — Claude should never flag this
- Line length violations are caught by black/ruff formatters
- These comments waste developer attention on issues that would be caught automatically
- The review missed actual logic issues because it focused on trivial style problems

---

### Anti-Example B: Re-Flagging Unchanged Code on Re-Review

**What went wrong**: On a re-review, the reviewer flagged the same issues from the previous review on code that hasn't changed, creating duplicate noise.

```json
{
  "event": "COMMENT",
  "body": "**Summary**: Re-reviewing CSV export endpoint.\n\n**Prior reviews**: Re-review #2.\n\n**Issues**: 0 critical, 1 high, 0 suggestions",
  "comments": [
    {
      "path": "apps/export/views.py",
      "line": 62,
      "side": "RIGHT",
      "body": "⚠️ When `queryset` is empty, `csv.writer` still writes the header row but the response Content-Disposition suggests a data file. Consider returning a 204 No Content."
    }
  ]
}
```

**Why this is wrong**:
- This exact finding was already in the previous review (Example 1, second comment)
- The code at line 62 hasn't changed since the last review — the diff shows no modifications
- The developer already has this feedback visible in the PR conversation
- Re-flagging creates the impression that the review didn't read its own prior context
- Correct behavior: acknowledge in the body ("1 prior suggestion on empty dataset handling remains open") without a new inline comment

---

### Anti-Example C: Vague Finding Without Concrete Fix

**What went wrong**: The finding identifies a potential issue category but doesn't explain the specific problem or provide a fix.

```json
{
  "comments": [
    {
      "path": "apps/auth/middleware.py",
      "line": 28,
      "side": "RIGHT",
      "body": "⚠️ This could be a security issue. Consider reviewing the authentication logic for potential vulnerabilities."
    }
  ]
}
```

**Why this is wrong**:
- "Could be a security issue" doesn't explain what the issue actually is
- "Consider reviewing" is not actionable — the developer already submitted this for review
- No code fix is provided — the developer doesn't know what to change
- If the reviewer can't articulate the specific vulnerability, it shouldn't be an inline comment
- Correct behavior: either explain the specific issue with a fix (e.g., "missing CSRF token validation — add `@csrf_protect` decorator") or omit it entirely

---

### Anti-Example D: Misusing Suggestion Block for Non-Replacement Fix

**What went wrong**: The suggestion block replaces the targeted line with code that belongs elsewhere, destroying the original line's content.

```json
{
  "comments": [
    {
      "path": "apps/export/views.py",
      "line": 45,
      "side": "RIGHT",
      "body": "⚠️ **Missing CSV import**\n\nThe `csv` module is used at line 52 but never imported.\n\n```suggestion\nimport csv\n```"
    }
  ]
}
```

**Why this is wrong**:
- Line 45 contains `queryset = Study.objects.filter(...)` — the suggestion block would *replace* that line with `import csv`, destroying the filter logic
- Suggestion blocks replace the targeted line(s) exactly — they are not "insert at" directives
- The fix (adding an import) belongs at the top of the file, not at line 45
- Correct behavior: use a regular code block and explain where the fix should go: "Add `import csv` at the top of the file with the other imports"

---

**Last Updated**: 2026-02-08
**Related**: [Review Standards](review-standards.md)
