# Review Examples

This document provides concrete examples of complete Claude reviews for reference. These examples illustrate the expected output format, severity calibration, and quality standards.

## Example 1: Review with Findings (COMMENT)

**Scenario**: PR adds a new CSV export endpoint with a SQL injection vulnerability and a missing edge case.

### Review JSON submitted via `gh api`:

```json
{
  "event": "COMMENT",
  "body": "**Summary**: Adds CSV export endpoint for study utilization data with date range filtering.\n\n**Linear**: HUB-1234 - ✅ Aligned (implements export with date filtering as specified)\n\n**Issues**: 0 critical, 1 high, 1 suggestion — see inline comments\n\n**Highlights**:\n- ✅ Good use of streaming response for large datasets\n- ✅ Proper Celery task for async generation\n\n---\n<sub>@reviewer<!-- METRICS --> · [Logs](https://github.com/quantivly/sre-core/actions/runs/12345)</sub>",
  "comments": [
    {
      "path": "apps/export/views.py",
      "line": 47,
      "side": "RIGHT",
      "body": "⚠️ The `start_date` parameter is interpolated directly into the queryset filter via `__range` with an f-string. While Django ORM parameterizes `filter()` calls, this intermediate string formatting defeats that protection.\n\nFix: Pass date objects directly to the filter:\n```python\nStudy.objects.filter(created_at__range=(start_date, end_date))\n```\ninstead of:\n```python\nStudy.objects.filter(created_at__range=f\"({start_date}, {end_date})\")\n```"
    },
    {
      "path": "apps/export/views.py",
      "line": 62,
      "side": "RIGHT",
      "body": "💡 When `queryset` is empty, `csv.writer` still writes the header row but the response Content-Disposition suggests a data file. Consider returning a 204 No Content or including a message row so users understand the export is intentionally empty rather than broken."
    }
  ]
}
```

### Why this is a good review:

- **2 findings, both high-confidence** — not 8 uncertain ones
- **Inline comments reference specific lines** with exact code context
- **Each finding includes a concrete fix** with code example
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
  "body": "**Summary**: Adds role-based dashboard filtering so facility managers only see their assigned facilities.\n\n**Linear**: HUB-5678 - ✅ Aligned (implements all 3 acceptance criteria)\n\n**Issues**: 0 critical, 0 high, 0 suggestions\n\n**Highlights**:\n- ✅ Access control check at both GraphQL resolver and queryset level (defense in depth)\n- ✅ Comprehensive test coverage including cross-facility access denial\n- ✅ Audit logging for filtered access attempts\n\n---\n<sub>@reviewer<!-- METRICS --> · [Logs](https://github.com/quantivly/sre-core/actions/runs/12346)</sub>",
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
  "body": "**Summary**: Adds CSV export endpoint for study utilization data with date range filtering.\n\n**Linear**: HUB-1234 - ✅ Aligned\n\n**Prior reviews**: Re-review #2. 2 of 2 prior findings addressed. Focusing on new/changed code.\n\n**Issues**: 0 critical, 0 high, 0 suggestions\n\n**Highlights**:\n- ✅ SQL parameterization fixed — dates now passed directly to ORM filter\n- ✅ Empty dataset now returns 204 with descriptive message header\n\n---\n<sub>@reviewer<!-- METRICS --> · [Logs](https://github.com/quantivly/sre-core/actions/runs/12347)</sub>",
  "comments": []
}
```

### Why this is a good re-review:

- **Prior reviews line** documents that this is a follow-up and all issues were addressed
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
  "body": "**Summary**: Adds management command to bulk-update patient study assignments.\n\n**Linear**: HUB-9012 - ⚠️ Gaps (issue doesn't mention logging, but HIPAA requires audit trail without PHI exposure)\n\n**Issues**: 1 critical, 0 high, 1 suggestion — see inline comments\n\n**Highlights**:\n- ✅ Proper use of database transaction for atomic bulk update\n- ✅ Dry-run mode for safe testing\n\n---\n<sub>@reviewer<!-- METRICS --> · [Logs](https://github.com/quantivly/sre-core/actions/runs/12348)</sub>",
  "comments": [
    {
      "path": "apps/studies/management/commands/bulk_assign.py",
      "line": 34,
      "side": "RIGHT",
      "body": "🚨 Patient MRN and name are logged in plaintext via `logger.info(f\"Reassigning {patient.name} (MRN: {patient.mrn})\")`. This is a HIPAA violation — PHI must not appear in application logs.\n\nFix: Log the study assignment ID and patient primary key instead:\n```python\nlogger.info(\"Reassigning study %s for patient pk=%s\", assignment.id, patient.pk)\n```\nIf audit trail is needed, use the existing `AuditLog` model which handles PHI encryption."
    },
    {
      "path": "apps/studies/management/commands/bulk_assign.py",
      "line": 58,
      "side": "RIGHT",
      "body": "💡 The `--batch-size` argument defaults to 1000. For facilities with 50k+ studies, this could cause memory pressure. Consider adding a progress bar with `tqdm` and processing in smaller batches (e.g., default 200) to keep memory bounded."
    }
  ]
}
```

### Why this is a good review:

- **REQUEST_CHANGES** because there's a CRITICAL HIPAA violation — this is the correct event for security issues
- **The critical finding is high-confidence** — logging PHI in plaintext is unambiguous
- **Fix suggestion is specific** — shows exact replacement code and references existing AuditLog model
- **The suggestion is separate** — memory concern is 💡 because it's optimization, not a blocker
- **Linear gap noted** — the issue didn't mention logging requirements, flagged as advisory

---

**Last Updated**: 2026-02-06
**Related**: [Review Standards](review-standards.md)
