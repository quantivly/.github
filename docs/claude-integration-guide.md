# Claude + GitHub Integration Guide

**Version**: 1.0
**Last Updated**: 2026-02-07

---

## Overview

Quantivly uses Claude (Anthropic's AI) to provide automated, high-quality code reviews for all pull requests. Claude analyzes your code for security vulnerabilities, logic errors, code quality issues, test coverage gaps, and performance problems — all before human review.

**Key Features**:
- ⚡ **Fast reviews** - 1-7 minutes depending on model tier (shown in progress comment)
- 🔒 **Security-focused** - OWASP Top 10, HIPAA compliance, injection attacks
- 📋 **Linear integration** - Validates alignment with issue requirements
- 🎯 **Multi-focus analysis** - Security, logic, quality, testing, performance
- 🤖 **Consistent standards** - Follows repository CLAUDE.md conventions
- 💬 **Inline comments** - Comments attached directly to specific lines in the diff
- ✅ **Formal reviews** - Proper GitHub review events (APPROVE/REQUEST_CHANGES)
- 🔄 **Context-aware re-reviews** - Remembers previous findings, focuses on new/changed code

---

## Quick Start

### 1. Create Your Pull Request

```bash
# Create feature branch with Linear issue ID
git checkout -b user/hub-1234-add-export-feature

# Make your changes, write tests
# ...

# Push and create PR with Linear ID in title
git push origin user/hub-1234-add-export-feature
gh pr create --title "HUB-1234 Add CSV export feature" \
  --body "Implements CSV export as specified in HUB-1234"
```

### 2. Request Claude Review

Go to your PR on GitHub and comment:

```
@claude
```

or

```
@claude review
```

That's it! Claude will:
1. Analyze your code changes
2. Fetch Linear issue context
3. Check against repository conventions
4. Post a structured review (duration varies by model tier — shown in progress comment)

### 3. Address Feedback

Claude posts a **formal GitHub review** (not just a comment), which means:

- **Review event**: Appears as APPROVE, REQUEST_CHANGES, or COMMENT in the PR's review section
- **Inline comments**: Specific feedback attached directly to lines in the diff
- **Identity**: Posted as "Claude[bot]" (distinct from other GitHub Actions)

**Review Structure**:

1. **Inline Comments** - Attached to specific lines in your code
   - 🚨 Critical - Security vulnerabilities, data loss risks
   - ⚠️ High - Logic errors, broken functionality
   - 💡 Suggestion - Nice-to-have improvements

2. **Summary Section** - High-level assessment including:
   - Overview of the PR
   - Alignment with Linear requirements
   - Issues summary (counts by severity)
   - Positive observations
   - Testing assessment

**Priority for Addressing Feedback**:
1. Fix all **CRITICAL** issues (security vulnerabilities, data loss risks)
2. Fix **HIGH** severity issues (logic errors, broken functionality)
3. Consider **SUGGESTION** items (use your judgment)
4. Re-request review if you made significant changes

---

## When to Use Local Claude Code CLI vs GitHub Actions

### Use Local Claude Code CLI During Development

**Command**: `claude` in terminal

**Best for**:
- Planning feature implementation (brainstorming, architecture)
- Real-time iteration with Linear context (fetch issue details, comments)
- Exploring codebase patterns before writing code
- Quick security checks on sensitive changes
- Interactive debugging and problem-solving

**Setup Required**:
- Linear MCP configured in `~/.config/claude/mcp.json`
- Anthropic API key configured

**Cost**: Paid by individual developer (via Claude Pro/Team subscription)

### Use GitHub Actions @claude During PR Review

**Trigger**: Comment `@claude` on PR

**Best for**:
- Formal validation before human review
- Security audit before merge
- Comprehensive multi-dimensional review
- Linear requirement alignment verification
- Team-wide standardized feedback

**Setup Required**: None (automatic for organization members)

**Cost**: Paid by organization (~$0.10-3.00 per review depending on PR complexity — model is selected automatically)

### Recommended Workflow

1. **Implementation Phase**: Use local CLI for guidance and iteration
2. **PR Creation**: Push code to GitHub
3. **Self-Review**: Comment `@claude` to get automated feedback
4. **Address Issues**: Fix CRITICAL and HIGH severity findings
5. **Human Review**: Request review from team members

---

## What Claude Reviews

### 1. Security (Highest Priority)

Claude checks for:
- **OWASP Top 10** vulnerabilities
- **SQL injection** in database queries
- **XSS (Cross-Site Scripting)** in user input handling
- **Command injection** in shell commands
- **Credential leaks** and hardcoded secrets
- **Authentication/authorization** flaws
- **HIPAA compliance** considerations (PHI handling, audit logs, access controls)
- **Dependency vulnerabilities** (known CVEs)

**Example Critical Finding** (inline comment on PR diff):
```
🚨 **SQL injection in export query**

User input is directly interpolated into the SQL query via f-string.
An attacker could extract the entire database.

```suggestion
cursor.execute('SELECT * FROM studies WHERE date >= %s', (start_date,))
```
```

### 2. Logic Errors and Bugs

Claude identifies:
- **Incorrect implementations** vs. Linear requirements
- **Edge cases** not handled (null, empty arrays, boundary values)
- **Off-by-one errors** in loops and array access
- **Race conditions** in concurrent code
- **Error handling** gaps
- **Data consistency** issues

**Example Finding** (inline comment on PR diff):
```
⚠️ **Off-by-one error in pagination**

`range(0, total_pages)` excludes the last page — users will never see
the final page of results.

```suggestion
for page in range(0, total_pages + 1):
```
```

### 3. Code Quality and Maintainability

Claude evaluates:
- **Readability** - Clear naming, appropriate abstractions
- **Complexity** - Functions should be focused and simple
- **DRY principle** - Avoid code duplication
- **SOLID principles** - Good object-oriented design
- **Documentation** - Docstrings and comments where needed
- **Conventions** - Following repository CLAUDE.md standards

### 4. Testing Completeness

Claude assesses:
- **Test coverage** for new/changed code
- **Edge case testing** - Null, empty, boundary conditions
- **Integration tests** - How components work together
- **Test quality** - Proper assertions, appropriate mocking
- **Framework conventions** - pytest/Jest best practices

**Example Suggestion** (inline comment on PR diff):
```
💡 **Missing edge case test for empty dataset**

The test suite only covers the happy path with valid data. Consider
adding a test for `export_to_csv([])` to verify the empty dataset
behavior (should return 204 No Content or an empty CSV with headers).
```

### 5. Performance

Claude looks for:
- **Algorithmic efficiency** - O(n²) vs. O(n) algorithms
- **Database N+1 queries** - Django ORM gotchas
- **Memory leaks** - Unclosed resources
- **Caching opportunities** - Repeated expensive operations
- **Unnecessary computations** - Can it be optimized?

---

## Linear Integration

### How It Works

When your PR title includes a Linear issue ID (format: `AAA-####`), Claude has **dynamic access to Linear** via the Model Context Protocol (MCP):

1. **During the review, Claude can**:
   - Fetch issue description and acceptance criteria
   - Check labels, project, and state
   - Read recent comments and discussion
   - Explore related issues if needed
   - Query Linear dynamically as questions arise

2. **Validates alignment**:
   - Does PR implement what the issue describes?
   - Are acceptance criteria met?
   - Are there missing requirements?

3. **Provides context-aware feedback**:
   - References specific requirements from Linear
   - Identifies gaps between code and specs
   - Suggests improvements based on issue discussion

**MCP Architecture**: Unlike traditional integrations that pre-fetch data, Claude has **live Linear tools** available during the review. This means Claude can explore Linear as needed, checking related issues or comments on-demand rather than being limited to static context.

**Benefits**:
- More thorough requirement validation (Claude can dig deeper if needed)
- Consistent with local development (same MCP tools as Claude Code CLI)
- Future-proof (easy to add more tool access)

**Example PR Title**:
```
HUB-1234 Add CSV export with pagination
```

Claude will fetch `HUB-1234` from Linear and validate that your code:
- Implements CSV export
- Includes pagination
- Meets any acceptance criteria in the issue

**No Linear Issue?**

If your PR doesn't reference a Linear issue (or the ID isn't found), Claude still reviews your code — just without requirement validation.

---

## Best Practices

### 1. Review BEFORE Human Review

**Workflow**:
```
Write code → Run tests locally → Create PR → @claude → Fix issues → Request human review
```

**Why**: Catch issues early, save reviewer time, faster feedback loop.

### 2. Address CRITICAL Issues First

**Priority Order**:
1. **CRITICAL** - Security vulnerabilities, data loss (must fix)
2. **HIGH** - Broken functionality, logic errors (must fix)
3. **Suggestions** - Improvements (consider, use judgment)

Don't request human review until **CRITICAL** and **HIGH** issues are resolved.

### 3. Use Claude for Learning

Claude explains **WHY** something is an issue, not just **WHAT**. Read the explanations to improve your code skills.

### 4. Re-Review After Significant Changes

If you make substantial changes (not just minor tweaks), comment `@claude` again to verify fixes. Re-reviews are context-aware: Claude reads its previous review findings and focuses on new or changed code rather than repeating the same feedback. Fixed issues are acknowledged in the summary rather than re-flagged.

If no code has changed since the last review, `@claude` will skip the re-review to save cost. To bypass this check (e.g., after updating review prompts or Linear requirements), use `@claude force`.

### 5. Don't Ignore Security Findings

Security issues are **always** worth fixing, even if they seem unlikely. Healthcare data requires extra caution.

### 6. Combine with Pre-Commit Hooks

Claude doesn't check formatting/linting (your pre-commit hooks do that). Make sure pre-commit passes **before** creating PR:

```bash
pre-commit run --all-files
```

---

## Common Questions

### Q: How long does a review take?

**A**: Depends on the auto-selected model tier:
- **Haiku** (docs/config PRs): ~1-2 minutes
- **Sonnet** (standard code PRs): ~2-4 minutes
- **Opus** (large/security-sensitive PRs): ~3-7 minutes

The progress comment shows which model is being used and the expected duration.

---

### Q: What if Claude gets something wrong?

**A**: Claude is very good but not perfect. If you disagree with a finding:
1. Verify Claude understood the context correctly
2. Check if there's missing context in the PR/Linear issue
3. Use your judgment — Claude provides recommendations, not mandates
4. If it's clearly wrong, ignore it (but consider if there's a communication gap)

---

### Q: Can I trigger reviews automatically?

**A**: No, reviews are manual (via `@claude` comment). This gives you control over when reviews happen and reduces API costs.

---

### Q: Does this replace human review?

**A**: **No!** Claude reviews are a **first pass** to catch common issues. Human review is still required for:
- Architectural decisions
- Business logic validation
- User experience considerations
- Judgment calls on trade-offs

---

### Q: What does a review cost?

**A**: Varies by PR complexity: ~$0.10-0.15 for docs/config (Haiku), ~$0.60-0.90 for standard code (Sonnet), ~$2-3 for large or security-sensitive PRs (Opus). Model selection is automatic. Quantivly covers the cost.

---

### Q: Can external contributors use this?

**A**: No, only Quantivly organization members and repository collaborators with write access can trigger reviews.

---

### Q: What if the workflow fails?

**A**: Check the [workflow logs](https://github.com/quantivly/<repo>/actions) for details. Common causes:
- API rate limits (wait and retry)
- Invalid PR state (check PR is open)
- Network timeouts (retry)

You can always re-trigger by commenting `@claude` again.

---

### Q: Does Claude remember previous reviews?

**A**: Yes. When you trigger `@claude` on a PR that already has Claude reviews, it reads the latest review summary and inline findings. Re-reviews focus on:
- New code not previously reviewed
- Code changed since the last review
- Prior findings addressed incorrectly or incompletely

Fixed issues are acknowledged in the summary but not re-flagged as inline comments. The review body includes a "Prior reviews" line showing the review count and how many prior findings were addressed.

If no code has changed since the last review, `@claude` will skip to avoid redundant reviews. Use `@claude force` to bypass this check when you need a fresh review on unchanged code (e.g., testing updated review prompts, getting a second opinion, or validating after Linear requirements change).

---

### Q: How does this affect Linear?

**A**: Claude's review comment is automatically linked to your Linear issue via the GitHub-Linear integration. You'll see a notification in Linear pointing to the review.

Claude **reads** Linear issues (descriptions, comments) but **does not post** to Linear. All communication happens in GitHub.

---

## Example Workflow

Here's a complete example of the recommended workflow:

```bash
# 1. Start feature from Linear issue
git checkout -b user/hub-1234-add-export

# 2. Implement feature
vim src/export.py
vim tests/test_export.py

# 3. Run tests locally
pytest tests/test_export.py
pre-commit run --all-files

# 4. Create PR with Linear ID in title
git add .
git commit -m "enh: Add CSV export with streaming support"
git push origin user/hub-1234-add-export

gh pr create \
  --title "HUB-1234 Add CSV export with streaming support" \
  --body "Implements CSV export as specified in HUB-1234. Uses streaming to handle large datasets without memory issues."

# 5. Request Claude review (on GitHub PR page)
# Comment: @claude

# 6. Wait for review (progress comment shows model tier and expected time)

# 7. Fix any CRITICAL/HIGH issues
vim src/export.py
git add .
git commit -m "fix: Add input validation to prevent injection"
git push origin user/hub-1234-add-export

# 8. Optional: Re-review if changes were substantial
# Comment: @claude

# 9. Request human review
gh pr edit --add-reviewer @teammate
# Comment: "Claude review passed, ready for review"

# 10. Merge after approval
gh pr merge --squash
```

---

## Troubleshooting

### Review Not Triggering

**Symptom**: No response after commenting `@claude`

**Checks**:
- [ ] Comment is exactly `@claude` or `@claude review` (case-sensitive)
- [ ] You are an organization member or collaborator
- [ ] PR is in `open` state (not draft, not closed)
- [ ] Workflow file exists in `.github/workflows/claude-review.yml`

**Fix**: Check [Actions tab](https://github.com/quantivly/<repo>/actions) for workflow runs. If none, verify workflow file exists.

---

### Review Failed with Error

**Symptom**: Error message posted to PR

**Checks**:
- [ ] Check workflow logs for detailed error
- [ ] Verify API keys are configured (organization secrets)
- [ ] Check for API rate limits

**Fix**: Most errors are transient. Wait 5 minutes and comment `@claude` again.

---

### Review Quality Issues

**Symptom**: Review misses issues or has false positives

**Possible Causes**:
- Missing context in PR description
- Linear issue lacks acceptance criteria
- CLAUDE.md is outdated
- Very large diff (truncated for token limits)

**Fix**:
1. Add more context to PR description
2. Update Linear issue with clear requirements
3. Keep PRs focused and reasonably sized (<500 lines changed)
4. Provide context in code comments where logic is complex

---

### Linear Context Missing

**Symptom**: Review says "No Linear issue to validate against"

**Checks**:
- [ ] PR title starts with Linear ID (e.g., `HUB-1234 ...`)
- [ ] Format is exactly `AAA-####` (all caps, hyphen, 1-6 digits)
- [ ] Issue exists and is accessible in Linear

**Fix**: Edit PR title to include valid Linear ID, then re-trigger review.

---

## Advanced Usage

### Force Re-Review

By default, `@claude` skips the review if no code has changed since the last review. Use `@claude force` to bypass this staleness check.

**Syntax**:
- `@claude force` — full re-review with no custom focus
- `@claude force focus on security` — re-review with custom instructions
- `@claude force, check auth` — comma separator also works

**When to use**:
- Testing updated review prompts or standards
- Getting a second opinion after discussion
- Re-validating after Linear requirements change
- Reviewing after dependency updates (no code diff but different behavior)

---

### Local Development with Claude Code CLI

For implementing features locally (not PR review), install Claude Code CLI with Linear MCP integration:

```bash
# Install Claude Code CLI
npm install -g @anthropic/claude-code

# Configure Linear MCP server using Claude CLI (easiest method)
claude mcp add --transport http linear-server https://mcp.linear.app/mcp

# The above command will prompt for your Linear API key and configure everything automatically.
# Alternatively, you can manually edit ~/.config/claude/mcp.json if needed.

# Start Claude Code in your project
cd ~/hub/sre-core
claude

# Now you can ask Claude to implement features from Linear
> "Implement the feature described in HUB-1234"
```

This gives you Linear context while writing code, not just during PR review.

---

## Related Documentation

- [Quantivly Git Workflow](../../CLAUDE.md#git-workflow)
- [Linear Issue Management](https://linear.app/quantivly/settings/integrations)
- [GitHub Actions Workflows](https://docs.github.com/en/actions)
- [Anthropic Claude API](https://docs.anthropic.com/en/api)

---

## Feedback and Support

**Found a bug?** Open an issue in [quantivly/.github](https://github.com/quantivly/.github/issues)

**Have suggestions?** Message in `#engineering` Slack channel

**Need help?** Ask in `#claude-reviews` Slack channel (or `#engineering` if channel doesn't exist yet)

---

**Last Updated**: 2026-02-07
**Maintained by**: Engineering Team
