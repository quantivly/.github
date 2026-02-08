# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is the **Quantivly `.github` organization repository** - a special GitHub repository that configures organization-wide settings and displays the public organization profile.

**Purpose**:
- Display organization profile README on https://github.com/quantivly
- Store organization-wide GitHub configuration templates (issues, PRs, discussions)
- Define default community health files for all organization repositories

**Current Contents**: Organization profile README in `/profile/README.md`

## Repository Structure

### Special GitHub Directories

GitHub recognizes specific directories in `.github` repositories:

**`/profile/`** (Currently implemented)
- `README.md` - Organization profile displayed on https://github.com/quantivly
- Supports images, links, and standard Markdown
- Public-facing description of Quantivly's mission and products

**`/workflow-templates/`** (Not yet implemented)
- Reusable GitHub Actions workflow templates
- Available to all organization repositories when creating new workflows
- Should include common CI/CD patterns for Quantivly projects

**`/ISSUE_TEMPLATE/`** (Not yet implemented)
- Default issue templates for all organization repositories
- Templates for: bug reports, feature requests, documentation updates
- Can include forms with structured fields

**`/PULL_REQUEST_TEMPLATE/`** (Not yet implemented)
- Default pull request templates
- Should enforce checklist: tests, documentation, Linear issue reference
- Aligns with commit message conventions (imperative mood, Linear prefixes)

**Root-Level Community Health Files** (Not yet implemented)
- `CODE_OF_CONDUCT.md` - Community standards and behavior expectations
- `CONTRIBUTING.md` - How to contribute to Quantivly projects
- `SECURITY.md` - Security policy and vulnerability reporting
- `SUPPORT.md` - Support channels and resources

## Key Commands

### Updating Organization Profile

```bash
# Edit the profile README
vim profile/README.md

# Commit and push changes
git add profile/README.md
git commit -m "doc: Update organization profile with new mission statement"
git push origin master

# Changes appear immediately on https://github.com/quantivly
```

### Adding Issue Templates

```bash
# Create issue templates directory
mkdir -p .github/ISSUE_TEMPLATE

# Create bug report template
cat > .github/ISSUE_TEMPLATE/bug_report.yml <<EOF
name: Bug Report
description: Report a bug or unexpected behavior
labels: ["bug"]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for taking the time to fill out this bug report!

  - type: input
    id: component
    attributes:
      label: Component
      description: Which component/service is affected?
      placeholder: e.g., hub, platform, sre-core
    validations:
      required: true

  - type: textarea
    id: description
    attributes:
      label: Description
      description: What happened?
    validations:
      required: true

  - type: textarea
    id: reproduction
    attributes:
      label: Steps to Reproduce
      placeholder: |
        1. Configure...
        2. Run command...
        3. Observe error...
    validations:
      required: true

  - type: textarea
    id: expected
    attributes:
      label: Expected Behavior
      description: What should have happened?
    validations:
      required: true
EOF

# Commit templates
git add .github/ISSUE_TEMPLATE/
git commit -m "enh: Add organization-wide bug report template"
git push origin master
```

### Adding Pull Request Template

```bash
# Create PR template
cat > .github/pull_request_template.md <<EOF
## Summary
<!-- Brief description of what this PR does -->

## Linear Issue
<!-- Link to Linear issue: HUB-1234, ENG-5678, etc. -->

## Changes
<!-- List of key changes -->
-
-

## Testing
<!-- How was this tested? -->
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Documentation updated

## Checklist
- [ ] PR title follows format: \`AAA-#### Summary\` (imperative mood)
- [ ] Commit messages follow conventions (enh/fix/ref/doc/test)
- [ ] Linear issue linked and updated
- [ ] Breaking changes documented
- [ ] Reviewers assigned

## Additional Context
<!-- Any additional information, screenshots, or context -->
EOF

git add .github/pull_request_template.md
git commit -m "enh: Add organization-wide PR template"
git push origin master
```

### Adding Community Health Files

```bash
# Create security policy
cat > SECURITY.md <<EOF
# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in any Quantivly project, please report it to:

**Email**: security@quantivly.com

**Do not** create public GitHub issues for security vulnerabilities.

## Response Time

- Initial response: Within 24 hours
- Status update: Within 5 business days
- Resolution target: Varies by severity (CRITICAL: 7 days, HIGH: 30 days)

## Disclosure Policy

We follow coordinated disclosure:
1. Issue reported privately
2. Fix developed and tested
3. Security advisory published
4. CVE assigned if applicable

## Supported Versions

See individual repository security policies for version support information.
EOF

git add SECURITY.md
git commit -m "doc: Add organization security policy"
git push origin master
```

## Claude + GitHub Integration

Quantivly uses automated Claude-powered code reviews for pull requests. For complete details, see the linked documentation below.

### Two Claude Review Systems

| | GitHub Actions (`@claude`) | Local CLI (`review-pr` skill) |
|---|---|---|
| **Purpose** | Formal PR validation before merge | Interactive development and feature planning |
| **Trigger** | Comment `@claude` on any open PR | Ask Claude to "review PR" in CLI session |
| **Posting** | Automatic | User approval required |
| **Cost** | Organization-paid (~$0.10-3.00) | Developer-paid (Claude Pro/Team subscription) |
| **Use When** | PR is ready for formal review | During development for early feedback |

**Both systems** reference the same [review standards](docs/review-standards.md). Changes to review standards should be reflected in both.

### Quick Start

1. Create PR with Linear ID in title: `HUB-1234 Add CSV export feature`
2. Comment `@claude` on the PR (optionally add focus: `@claude focus on security`)
3. Wait for review (Haiku: ~1-2 min, Sonnet: ~2-4 min, Opus: ~3-7 min)
4. Fix CRITICAL/HIGH issues, then request human review

See [Integration Guide](docs/claude-integration-guide.md) for complete usage details.

### Architecture

- **Central workflow**: `quantivly/.github/.github/workflows/claude-review.yml`
- **Caller workflows**: Minimal files in each repository's `.github/workflows/` directory (see [template](workflow-templates/claude-review-caller.yml))
- **Secrets**: Inherited from organization secrets via `secrets: inherit`
- **Action**: [`anthropics/claude-code-action`](https://github.com/anthropics/claude-code-action) (SHA-pinned for supply chain security)
- **Identity**: Custom GitHub App "Claude" (posts as "Claude[bot]", falls back to "github-actions[bot]")
- **MCP**: Linear MCP for issue context and requirements validation

See [Deploying Claude Review](docs/deploying-claude-review.md) for setup guide.

### Key Features

- **Formal reviews**: APPROVE/REQUEST_CHANGES/COMMENT review events with inline comments
- **Suggestion blocks**: One-click "Apply suggestion" for direct line replacements
- **Adaptive model selection**: Haiku (docs/config), Sonnet (standard code), Opus (large/security-sensitive PRs)
- **Security escalation**: Small changes to auth-related files automatically escalate to Opus
- **Adaptive comment caps**: Scales with diff size (min 3, max 12 for Sonnet, max 18 for Opus)
- **PR size advisory**: Reviews on 500+ line PRs include advisory about optimal PR size
- **Context-aware re-reviews**: Reads previous findings, skips stale re-reviews on unchanged commits
- **Linear validation**: Fetches issue requirements and validates alignment
- **Custom focus**: `@claude focus on security` prioritizes specific areas
- **Cost alerting**: Reviews exceeding $5 suggest PR size reduction
- **Quality feedback**: 👍/👎 reactions in review footer

### Troubleshooting

**Review not triggering**: Check comment contains `@claude`, verify org membership, check PR is open (not draft/closed).

**Review failed**: Check [Actions tab](https://github.com/quantivly/<repo>/actions) for logs. Common causes: API rate limits, timeouts. Retry with `@claude`.

**Linear context missing**: Verify PR title starts with `AAA-####` format and issue exists in Linear.

**Inline comments appear as file-level**: GitHub's Reviews API returns `line: null` in GET responses even when comments are correctly positioned — always verify in the PR page UI.

### Review Prompt Editing

The `prompt:` field in `claude-review.yml` is the most frequently edited part of this repo:
- Use concrete examples in JSON templates (e.g., `"line": 42`) — LLMs produce better output with realistic examples
- Avoid emphatic/scary constraint language — use factual, concise guidance instead
- Static instructions go first (cacheable), dynamic PR context goes last
- Test on a real PR after pushing (trigger with `@claude`) and verify results in the PR page UI

### Documentation

- [Integration Guide](docs/claude-integration-guide.md) - Complete usage guide for developers
- [Review Standards](docs/review-standards.md) - Severity definitions, checklists, quality criteria, tool allocation
- [Review Examples](docs/review-examples.md) - Concrete examples of well-calibrated reviews
- [Deploying Claude Review](docs/deploying-claude-review.md) - Setup guide for new repositories

## Development Standards

### Profile README Guidelines

**Content Requirements**:
- Mission statement clearly stated
- Brief product description (what Quantivly does)
- Links to key resources (website, social media)
- Professional tone, medical domain context
- High-quality images and branding

**Formatting**:
- Centered alignment for hero section
- Responsive image sizing (use width attributes)
- Consistent branding with quantivly.com
- Working links (test before committing)

**Updates**:
- Review quarterly for accuracy
- Update on major product changes
- Coordinate with marketing team
- Test image links (use stable GitHub URLs)

### Template Standards

**Issue Templates**:
- Use YAML format for structured forms (`.yml` extension)
- Require essential fields (component, description)
- Include appropriate labels
- Provide helpful placeholders and examples
- Consider security context (no passwords/keys in issues)

**Pull Request Templates**:
- Enforce Linear issue reference (AAA-#### format)
- Checklist for tests, docs, breaking changes
- Align with commit message conventions
- Require imperative mood in title
- Include section for testing evidence

**Community Files**:
- Clear, actionable guidance
- Professional and welcoming tone
- Contact information up-to-date
- Aligned with Quantivly values and HIPAA compliance

## Important Gotchas

1. **Immediate Visibility**: Changes to `profile/README.md` appear immediately on https://github.com/quantivly when pushed to `master`. Review carefully before pushing.

2. **Organization-Wide Impact**: Templates and community health files in this repo become defaults for ALL Quantivly repositories. Test thoroughly.

3. **Repository Overrides**: Individual repositories can override these defaults by creating their own `.github/` files. Organization templates are fallbacks.

4. **Image URLs**: Use stable GitHub asset URLs for images in profile README. URLs like `https://github.com/quantivly/.github/assets/...` are permanent.

5. **Template Visibility**: Issue and PR templates only appear in repositories that don't have their own templates. Consider adding to individual repos if customization needed.

6. **Public Information Only**: This repository and profile are PUBLIC. Never include:
   - API keys, tokens, passwords
   - Internal infrastructure details
   - Customer information
   - Non-public product features

7. **Branch Protection**: `master` branch should have protection rules requiring review for profile changes.

8. **Marketing Coordination**: Profile README changes should be coordinated with marketing team to ensure consistent messaging.

## Git Workflow

### Commit Message Format

```
<type>: <summary>

<optional body>

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**Types**: `doc` (documentation), `enh` (enhancement), `fix` (bug fix)

**Examples**:
- `doc: Update organization profile with Q1 2026 mission statement`
- `enh: Add bug report and feature request issue templates`
- `doc: Add SECURITY.md with vulnerability reporting process`

### PR Title Format

```
AAA-#### Summary
```

Use imperative mood. If no Linear issue, use descriptive summary only.

**Examples**:
- `ENG-1234 Add organization-wide PR template`
- `doc: Update profile README with new product offerings`

### Branching Strategy

- Main branch: `master`
- Feature branches: `user/description` or `user/linear-id-description`
- Always create PR for profile changes (require review)

## Common Workflows

### Updating Organization Profile

1. Create feature branch:
   ```bash
   git checkout -b user/update-profile-q1-2026
   ```

2. Edit profile README:
   ```bash
   vim profile/README.md
   ```

3. Preview changes locally (Markdown preview)

4. Commit with descriptive message:
   ```bash
   git add profile/README.md
   git commit -m "doc: Update Q1 2026 organization profile with hub focus"
   ```

5. Push and create PR:
   ```bash
   git push origin user/update-profile-q1-2026
   gh pr create --title "doc: Update Q1 2026 organization profile" --body "Updates profile README to reflect hub as primary product"
   ```

6. Request review from marketing/leadership

7. Merge and verify on https://github.com/quantivly

### Adding Organization-Wide Templates

1. Research template best practices:
   - Review templates from similar organizations
   - Check GitHub documentation for YAML forms
   - Consider Quantivly-specific requirements (Linear, HIPAA)

2. Create templates in appropriate directory:
   ```bash
   mkdir -p .github/ISSUE_TEMPLATE
   vim .github/ISSUE_TEMPLATE/bug_report.yml
   ```

3. Test templates:
   - Push to test branch
   - Create test issue/PR in a sandbox repository
   - Verify fields, labels, and formatting

4. Document template usage:
   - Add comments in template files
   - Update this CLAUDE.md if needed
   - Coordinate with team on rollout

5. Commit and deploy:
   ```bash
   git add .github/ISSUE_TEMPLATE/
   git commit -m "enh: Add organization-wide issue templates"
   git push origin master
   ```

6. Announce to team (Slack/email) about new templates

### Adding Community Health Files

1. Draft content (SECURITY.md, CONTRIBUTING.md, etc.)

2. Review with relevant stakeholders:
   - Legal team for security policy
   - Engineering leadership for contributing guidelines
   - Marketing for tone and messaging

3. Commit to repository:
   ```bash
   git add SECURITY.md
   git commit -m "doc: Add organization security vulnerability reporting policy"
   ```

4. Communicate to team and update documentation

## Recommended Future Additions

### High Priority

**Pull Request Template** (`/PULL_REQUEST_TEMPLATE/pull_request_template.md`)
- Enforce Linear issue reference
- Checklist: tests, docs, breaking changes
- Testing evidence section
- Aligns with existing commit conventions

**Issue Templates** (`/.github/ISSUE_TEMPLATE/`)
- `bug_report.yml` - Structured bug reporting
- `feature_request.yml` - Feature proposals
- `documentation.yml` - Documentation improvements
- Use YAML forms for structured data

**Security Policy** (`/SECURITY.md`)
- Vulnerability reporting process
- Response time commitments
- Supported versions
- Disclosure policy

### Medium Priority

**Contributing Guidelines** (`/CONTRIBUTING.md`)
- How to set up development environment
- Code standards and conventions
- PR submission process
- Testing requirements
- Link to relevant CLAUDE.md files in repos

**Workflow Templates** (`/workflow-templates/`)
- Python CI/CD template (pytest, ruff, mypy)
- Docker build and push template
- Release automation template
- Security scanning template

### Lower Priority

**Code of Conduct** (`/CODE_OF_CONDUCT.md`)
- Community standards
- Reporting process
- Enforcement policy

**Support Resources** (`/SUPPORT.md`)
- Documentation links
- Internal communication channels
- Issue reporting guidelines

**Funding** (`/FUNDING.yml`)
- If applicable for open-source components

## Related Resources

**Quantivly Repositories** (two-layer architecture: platform foundation → hub user portal):

*platform* ([quantivly-dockers](https://github.com/quantivly/quantivly-dockers)) - Core DICOM/RIS data backbone:
- Monorepo containing: `auto-conf`, `box`, `ptbi`, and other infrastructure services
- [quantivly-sdk](https://github.com/quantivly/quantivly-sdk) - Python SDK for platform services

*hub* ([hub](https://github.com/quantivly/hub)) - Healthcare analytics portal (builds on platform):
- Superproject coordinating sre-* components
- [sre-core](https://github.com/quantivly/sre-core) - Django backend (GraphQL, plugins) → uses `sre-sdk`
- [sre-ui](https://github.com/quantivly/sre-ui) - Next.js frontend → consumes `sre-core` APIs
- [sre-event-bridge](https://github.com/quantivly/sre-event-bridge) - WAMP→REST bridge → uses `sre-sdk`
- [sre-sdk](https://github.com/quantivly/sre-sdk) - Python SDK for hub services
- [sre-postgres](https://github.com/quantivly/sre-postgres) - PostgreSQL database

**GitHub Documentation**:
- [Creating a default community health file](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/creating-a-default-community-health-file)
- [About issue and pull request templates](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/about-issue-and-pull-request-templates)
- [Creating workflow templates](https://docs.github.com/en/actions/using-workflows/creating-starter-workflows-for-your-organization)
- [Customizing your organization's profile](https://docs.github.com/en/organizations/collaborating-with-groups-in-organizations/customizing-your-organizations-profile)

## Key Files

- `profile/README.md` - Organization profile page (PUBLIC, visible on github.com/quantivly)
- `.github/ISSUE_TEMPLATE/` - Default issue templates for organization
- `.github/PULL_REQUEST_TEMPLATE/` - Default PR templates
- Root-level `*.md` files - Organization-wide community health files
