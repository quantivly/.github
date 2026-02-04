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
.github/workflows/claude-review.yml    # Workflow (triggers on @claude)
scripts/claude-review.py               # Orchestration (MCP-based)
CLAUDE.md                              # Repository guidelines (Claude reads this)
```

**Note**: Uses **MCP (Model Context Protocol)** for Linear integration. Claude can dynamically explore Linear during review instead of relying on pre-fetched context.

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

**Update prompts** (scripts/claude-review.py):
- Line ~260: System prompt with review guidelines
- Adjust based on false positives/negatives

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

| Reviews/Month | Cost |
|---------------|------|
| 10            | ~$7  |
| 25            | ~$17 |
| 40            | ~$27 |
| 100           | ~$68 |

**Per review**: ~$0.50-$1.00 (varies by PR size)

---

## Architecture (MCP-Based)

```
@claude comment → GitHub Actions → Python Script → Start Linear MCP Server
                      ↓                   ↓                ↓
                  Validate          Fetch PR Context   Connect as MCP Client
                  Permission        Build Prompt       Get Linear Tools
                                        ↓                ↓
                                    Claude API with Tools
                                        ↓
                                    [Tool Use Loop]
                                    Claude ↔ MCP Server
                                        ↓
                                    Final Review
                                        ↓
                                    Post to PR
```

**MCP Advantage**: Claude can dynamically query Linear during review (fetch issues, check comments, explore related tickets) instead of being limited to pre-fetched data.

---

## Key Design Decisions

- **Manual trigger** - Gives control, reduces cost
- **MCP-based Linear** - Dynamic tool access, consistency with local development
- **Read-only Linear** - GitHub integration handles notifications
- **Token limits** - Truncate at 2000 lines to control cost
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

**Version**: 1.0 | **Last Updated**: 2026-02-04
