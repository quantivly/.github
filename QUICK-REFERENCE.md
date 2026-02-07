# Claude PR Review - Quick Reference Card

## For Developers

### How to Use

1. **Create PR** with Linear ID in title: `HUB-1234 Add feature`
2. **Comment** `@claude` on the PR
3. **Wait** 2-5 minutes for review
4. **Fix** CRITICAL and HIGH issues
5. **Request** human review

### Review Structure

- **Summary** - High-level assessment
- **Alignment** - How well it meets Linear requirements
- **Critical Issues** - Must fix (CRITICAL, HIGH)
- **Suggestions** - Nice to have
- **Positive Observations** - What you did well
- **Testing** - Coverage assessment
- **Recommendation** - APPROVE / REQUEST_CHANGES / COMMENT

### Severity Levels

- **CRITICAL** - Security vulnerabilities, data loss (must fix immediately)
- **HIGH** - Logic errors, broken functionality (must fix before merge)
- **SUGGESTION** - Improvements, nice-to-have (use judgment)

### What Claude Checks

1. **Security** - SQL injection, XSS, credentials, HIPAA
2. **Logic** - Edge cases, off-by-one, race conditions
3. **Quality** - Readability, DRY, SOLID, complexity
4. **Testing** - Coverage, edge cases, test quality
5. **Performance** - N+1 queries, memory leaks, caching

### Best Practices

✅ **DO**:
- Use on complex PRs
- Address CRITICAL issues first
- Re-review after major changes
- Learn from explanations

❌ **DON'T**:
- Skip security findings
- Ignore CRITICAL issues
- Request human review with unresolved CRITICAL issues

### Troubleshooting

**Review not starting?**
- Check comment is exactly `@claude` or `@claude review`
- Verify you're an org member/collaborator

**Review failed?**
- Wait 5 minutes and try again
- Check [Actions tab](https://github.com/quantivly/<repo>/actions) for logs

**Linear context missing?**
- Ensure PR title starts with `AAA-####`

**Need help?**
- Read: [Full Guide](docs/claude-integration-guide.md)
- Ask: #engineering Slack channel

---

## For Maintainers

### Files to Know

```
.github/workflows/claude-review.yml    # Central reusable workflow (triggers on @claude)
docs/review-standards.md               # Review criteria (Claude reads this during review)
docs/review-examples.md                # Calibration examples (Claude reads this during review)
CLAUDE.md                              # Repository-specific guidelines (Claude reads this)
```

**Architecture**: Uses [`anthropics/claude-code-action`](https://github.com/anthropics/claude-code-action) (GitHub Action) with **Linear MCP** for dynamic issue context. Claude can explore Linear during review (fetch issues, check comments, explore related tickets) instead of relying on pre-fetched data.

### Secrets Required

```
ANTHROPIC_API_KEY    # Claude API key (org-level)
LINEAR_API_KEY       # Linear read access (org-level)
GITHUB_TOKEN         # Auto-provided by GitHub
```

### Monitoring

**Check monthly**:
- Cost: `gh api /orgs/quantivly/actions/billing/usage` (if available)
- Usage: Check Actions tab for workflow runs
- Errors: Monitor workflow failure rate

**Budget**: Alert at $50/month, investigate at >$100

### Common Maintenance

**Update review prompt** (`.github/workflows/claude-review.yml`):
- The `prompt:` field in the workflow contains review instructions
- Adjust based on false positives/negatives
- Test on a real PR after changes (trigger with `@claude`)

**Update review standards** (`docs/review-standards.md`, `docs/review-examples.md`):
- Add severity calibration examples
- Update false-positive exclusion list
- Add framework-specific patterns

**Update guidelines** (CLAUDE.md):
- Add repository-specific patterns
- Document security rules
- Include framework best practices

**Rotate keys** (quarterly):
- Generate new API keys
- Update organization secrets
- Test in sandbox first

### Rollback

```bash
# Disable workflow quickly
mv .github/workflows/claude-review.yml .github/workflows/claude-review.yml.disabled
git commit -m "chore: Disable Claude reviews"
git push
```

---

## Cost Tracking

| Model Tier | Per Review | Use Case |
|------------|-----------|----------|
| Haiku 4.5  | ~$0.10    | Docs/config PRs |
| Sonnet 4.5 | ~$0.50-1.00 | Standard code PRs |
| Opus 4.6   | ~$2.00-3.00 | Security-sensitive / large PRs |

**Per review**: ~$0.10-$3.00 (varies by model tier and PR size)

---

## Architecture

```
@claude comment → GitHub Actions workflow
                      ↓
                  Validate permissions
                      ↓
                  Assess PR complexity → Select model (Haiku / Sonnet / Opus)
                      ↓
                  anthropics/claude-code-action
                      ↓
                  Claude reads: review-standards.md, review-examples.md, CLAUDE.md
                      ↓
                  Claude analyzes diff, fetches Linear context via MCP
                      ↓
                  Single gh api call → PR review with inline comments
                      ↓
                  Metrics extraction → Update review footer
```

**Key features**: Adaptive model selection (Haiku for docs, Sonnet default, Opus for security/large PRs), PHI detection in diffs, staleness guard for re-reviews, single-submission pattern (no comment spam).

---

## Key Design Decisions

- **Manual trigger** - Gives control, reduces cost
- **Adaptive model selection** - Haiku for docs ($0.10), Sonnet for code ($0.50), Opus for security/large PRs ($2-3)
- **MCP-based Linear** - Dynamic tool access, consistency with local development
- **Read-only Linear** - GitHub integration handles notifications
- **Single submission** - All findings in one API call (no comment spam)
- **Staleness guard** - Skips review on unchanged commits after 2 prior reviews
- **Graceful fallback** - Review continues if MCP unavailable

---

## Support

**Documentation**: [docs/claude-integration-guide.md](docs/claude-integration-guide.md)
**Testing**: [tests/validation-procedure.md](tests/validation-procedure.md)
**Deployment**: [NEXT-STEPS.md](NEXT-STEPS.md)
**Summary**: [README-CLAUDE-INTEGRATION.md](README-CLAUDE-INTEGRATION.md)

**Slack**: #engineering
**Issues**: [quantivly/.github](https://github.com/quantivly/.github/issues)

---

**Version**: 2.0 | **Last Updated**: 2026-02-07
