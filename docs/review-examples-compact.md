# Review Examples (Compact)

Condensed version of [review-examples.md](review-examples.md) for the CI review workflow. Contains the 3 most instructive examples plus all anti-examples.

## Example 1: Finding with Suggestion Block (COMMENT)

**Scenario**: PR adds a new CSV export endpoint with a SQL injection vulnerability and a missing edge case.

```json
{
  "event": "COMMENT",
  "body": "## 📋 Summary\n\n> Adds CSV export endpoint for study utilization data with date range filtering.\n\n**Linear**: [HUB-1234](https://linear.app/quantivly/issue/HUB-1234/) — ✅ Aligned (implements export with date filtering as specified)\n\n**Highlights**:\n- ✅ Good use of streaming response for large datasets\n- ✅ Proper Celery task for async generation\n\n**Issues**: 🚨 0 · ⚠️ 1 · 💡 1 — see inline comments\n\n---\n<sub>@reviewer<!-- METRICS --> · [Logs](https://github.com/quantivly/sre-core/actions/runs/12345) · 👍 👎</sub>",
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

**Why good**: 2 high-confidence findings. Suggestion block for direct replacement (one-click apply). Regular text for behavioral advice. Accurate severity calibration. Concise summary.

---

## Example 2: Critical Security Finding (REQUEST_CHANGES)

**Scenario**: PR introduces a management command that logs PHI in plaintext.

```json
{
  "event": "REQUEST_CHANGES",
  "body": "## 📋 Summary\n\n> Adds management command to bulk-update patient study assignments.\n\n**Linear**: [HUB-9012](https://linear.app/quantivly/issue/HUB-9012/) — ⚠️ Gaps (issue doesn't mention logging, but HIPAA requires audit trail without PHI exposure)\n\n**Highlights**:\n- ✅ Proper use of database transaction for atomic bulk update\n- ✅ Dry-run mode for safe testing\n\n**Issues**: 🚨 1 · ⚠️ 0 · 💡 1 — see inline comments\n\n---\n<sub>@reviewer<!-- METRICS --> · [Logs](https://github.com/quantivly/sre-core/actions/runs/12348) · 👍 👎</sub>",
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

**Why good**: REQUEST_CHANGES for HIPAA violation. Multi-line suggestion block (start_line/line). References existing AuditLog model. Separate severity for security vs optimization.

---

## Example 3: Mixed Suggestion and Fallback Formats (COMMENT)

**Scenario**: PR adds a paginated API endpoint. One finding has a direct line replacement (suggestion block), and the other requires adding code elsewhere (regular code block).

```json
{
  "event": "COMMENT",
  "body": "## 📋 Summary\n\n> Adds paginated list endpoint for facility equipment inventory.\n\n**Linear**: [HUB-4567](https://linear.app/quantivly/issue/HUB-4567/) — ✅ Aligned\n\n**Highlights**:\n- ✅ Proper use of DjangoFilterBackend for query parameters\n- ✅ Serializer validates equipment status transitions\n\n**Issues**: 🚨 0 · ⚠️ 1 · 💡 1 — see inline comments\n\n---\n<sub>@reviewer<!-- METRICS --> · [Logs](https://github.com/quantivly/sre-core/actions/runs/12352) · 👍 👎</sub>",
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

**Why good**: Suggestion block for direct replacement. Regular code block for cross-line fix. Explicit annotation explaining why each format was chosen.

---

## Example 4: CI Failing — REQUEST_CHANGES with No Code Findings

**Scenario**: PR has clean code but the Docker build CI check has been failing for 2 days. No code-level issues found.

```json
{
  "event": "REQUEST_CHANGES",
  "body": "## 📋 Summary\n\n> Updates Dockerfile base image and adds health check endpoint.\n\n**Linear**: [SRE-5678](https://linear.app/quantivly/issue/SRE-5678/) — ✅ Aligned\n\n**CI**: ❌ 1 check failing:\n- `Docker Build`: failure (2d ago)\n\nCI checks must pass before this PR can be approved. Please investigate the Docker build failure and push a fix.\n\n**Highlights**:\n- ✅ Proper multi-stage build reduces image size\n- ✅ Health check uses lightweight endpoint\n\n**Issues**: 🚨 0 · ⚠️ 0 · 💡 0\n\n---\n<sub>@reviewer<!-- METRICS --> · [Logs](https://github.com/quantivly/sre-core/actions/runs/12355) · 👍 👎</sub>",
  "comments": []
}
```

**Why good**: REQUEST_CHANGES despite no code findings — CI failure is a merge blocker. CI details in body (not inline). Empty comments array since this is a project-level concern. Still includes highlights for the code that was reviewed.

---

## Anti-Examples: What Bad Reviews Look Like

### Anti-Example A: Flagging Formatting Issues (ruff's Job)

```json
{
  "comments": [
    {"path": "apps/export/views.py", "line": 3, "side": "RIGHT", "body": "💡 Imports should be sorted alphabetically."},
    {"path": "apps/export/views.py", "line": 45, "side": "RIGHT", "body": "💡 This line exceeds 120 characters."}
  ]
}
```

**Why wrong**: Import sorting and line length are ruff/black's responsibility. Wastes developer attention on auto-fixable issues.

### Anti-Example B: Re-Flagging Unchanged Code on Re-Review

```json
{
  "event": "COMMENT",
  "comments": [
    {"path": "apps/export/views.py", "line": 62, "side": "RIGHT", "body": "⚠️ When `queryset` is empty, consider returning a 204 No Content."}
  ]
}
```

**Why wrong**: Same finding from prior review on unchanged code. Developer already has this feedback visible in the PR conversation.

### Anti-Example C: Vague Finding Without Concrete Fix

```json
{
  "comments": [
    {"path": "apps/auth/middleware.py", "line": 28, "side": "RIGHT", "body": "⚠️ This could be a security issue. Consider reviewing the authentication logic."}
  ]
}
```

**Why wrong**: No specific vulnerability identified. "Consider reviewing" is not actionable. No code fix provided.

### Anti-Example D: Misusing Suggestion Block for Non-Replacement Fix

```json
{
  "comments": [
    {"path": "apps/export/views.py", "line": 45, "side": "RIGHT", "body": "⚠️ **Missing CSV import**\n\n```suggestion\nimport csv\n```"}
  ]
}
```

**Why wrong**: Line 45 contains business logic — the suggestion would replace it with `import csv`. Suggestion blocks replace the targeted line(s) exactly. Use a regular code block and explain where the fix belongs.

---

**Last Updated**: 2026-02-08
**Related**: [Full Review Examples](review-examples.md), [Review Standards](review-standards.md)
