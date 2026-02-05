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

Quantivly uses automated Claude-powered code reviews for pull requests. This section describes how the integration works and best practices for developers.

### Two Claude Review Systems

Quantivly has two complementary Claude review systems that use the same [review standards](docs/review-standards.md):

#### GitHub Actions (`@claude` comment)
- **Purpose**: Formal PR validation before merge
- **Trigger**: Comment `@claude` on any open PR
- **Posting**: Automatic (posts review directly to PR)
- **Cost**: Organization-paid (~$0.60-0.90 per review)
- **Optimizations**: Prompt caching, retry logic, token metrics
- **Use When**: PR is ready for formal review before requesting human review

#### Local CLI (`review-pr` skill)
- **Purpose**: Interactive development and feature planning
- **Trigger**: Ask Claude to "review PR" in CLI session
- **Posting**: User approval required before posting
- **Cost**: Developer-paid (Claude Pro/Team subscription)
- **Flexibility**: User control, interactive troubleshooting, iterative refinement
- **Use When**: During development for early feedback or exploring design options

**Both systems** reference the same review standards but are optimized for different contexts. Changes to review standards should be reflected in both.

### Overview

**What**: Automated code reviews using Claude (Anthropic's AI) triggered by PR comments

**Why**: Catch security vulnerabilities, logic errors, and code quality issues before human review

**When**: Manually triggered by commenting `@claude` on any open pull request

**Who**: Available to organization members and repository collaborators with write access

### How to Use

1. **Create PR with Linear ID in title**:
   ```
   HUB-1234 Add CSV export feature
   ```

2. **Comment on PR to trigger review** (any comment mentioning `@claude`):
   ```
   @claude
   ```
   ```
   @claude review
   ```
   ```
   Hey @claude, can you review this?
   ```

3. **Optionally include custom instructions** for focused reviews:
   ```
   @claude focus on security and HIPAA compliance
   ```
   ```
   @claude this is a performance-critical path, please check for N+1 queries
   ```
   ```
   @claude please pay attention to the error handling in the retry logic
   ```
   Custom instructions are included in Claude's prompt and prioritized during review.

4. **Wait 2-5 minutes** for review to complete

5. **Address feedback**:
   - Fix **CRITICAL** issues (security, data loss)
   - Fix **HIGH** issues (bugs, logic errors)
   - Consider **Suggestions** (use judgment)

6. **Request human review** after addressing critical feedback

### What Claude Reviews

**Priority order**:
1. **Security** - OWASP Top 10, HIPAA compliance, SQL injection, XSS, credentials
2. **Logic Errors** - Incorrect implementations, edge cases, race conditions
3. **Code Quality** - Readability, complexity, DRY, SOLID, conventions
4. **Testing** - Coverage, edge cases, test quality, framework conventions
5. **Performance** - Algorithmic efficiency, N+1 queries, memory leaks, caching

### Linear Integration

When PR title includes Linear issue ID (format: `AAA-####`), Claude:
- Fetches issue description and acceptance criteria
- Validates PR alignment with requirements
- References specific issue requirements in feedback
- Provides context-aware suggestions

**Note**: GitHub-Linear integration automatically notifies Linear issue when review is posted.

### GitHub MCP Integration (Cross-Repository Context)

Claude can fetch code from related repositories when reviewing PRs. This enables validation that changes work correctly in their consuming context.

**When enabled**, Claude can:
- Read files from other Quantivly repositories (e.g., check how `sre-ui` consumes `sre-core` APIs)
- Search for code patterns across the organization
- Validate that API contracts are maintained across repositories

**Quantivly repository architecture**:

**hub** - Superproject + release management repo that creates manifest images with correct service versions. Contains submodules: sre-core, sre-ui, sre-event-bridge, sre-postgres.

| Repository | Description |
|------------|-------------|
| `sre-core` | Django backend - GraphQL API, business logic |
| `sre-ui` | React + Next.js frontend - consumes sre-core APIs |
| `sre-event-bridge` | WAMP router bridge - notifies backend via REST API |
| `sre-postgres` | PostgreSQL database for hub |

**platform** (quantivly-dockers) - Monorepo containing backbone services with Docker Swarm/Compose orchestration and WAMP for inter-service communication:

| Component | Description |
|-----------|-------------|
| `auto-conf` | Configuration generator - Jinja2 templates for Docker Compose, shell scripts, configs. Two-phase: configure → generate |
| `box` | Data processing engine - DICOM harmonization (GE, Philips, Siemens), RIS integration, job processing |
| `ptbi` | DICOM networking - Python + Java (dcm4che) for SCP/SCU operations |
| `quantivly-sdk` | Foundation library - database utilities, WAMP client, DICOM processing, job framework |

Platform uses Poetry for Python packages, Flyway for DB migrations, and pre-commit hooks (Black, isort, Ruff).

**When to expect cross-repo validation**:
- API endpoint changes in `sre-core` → check `sre-ui` consumers
- Type/interface changes → validate compatibility across repos
- `auto-conf` template changes → verify stack file rendering

**Configuration**: Requires `GITHUB_MCP_TOKEN` organization secret (falls back to `GITHUB_TOKEN` if not set).

### Best Practices

1. **Review BEFORE human review** - Catch issues early, save reviewer time
2. **Address CRITICAL first** - Security and data loss issues must be fixed
3. **Re-review after significant changes** - Comment `@claude` again if substantial fixes made
4. **Don't ignore security findings** - Healthcare data requires extra caution
5. **Use for learning** - Claude explains WHY, not just WHAT

### Tool Allocation

Quantivly uses multiple code quality tools. Here's what each tool owns:

#### Pre-Commit Hooks (Local, Before Push)

Run: `pre-commit run --all-files`

**Responsibilities**:
- **ruff**: Linting, import sorting, basic security patterns (S101-S603)
- **ruff-format** or **black**: Code formatting (PEP 8)
- **mypy**: Type hint completeness and correctness

**When to run**: Before every commit (automatic if configured)

#### Claude Code Review (GitHub Actions, @claude)

Trigger: Comment `@claude` on PR

**Responsibilities**:
- **Security**: OWASP Top 10, SQL injection, XSS, credentials, authentication
- **Logic Errors**: Correctness, edge cases, off-by-one, race conditions
- **Code Quality**: Design patterns, SOLID, maintainability, complexity
- **Testing**: Coverage adequacy, edge case testing, test quality
- **Performance**: N+1 queries, algorithmic efficiency, caching opportunities
- **Linear Alignment**: PR vs. issue requirements validation

**When to run**: After PR creation, before requesting human review

#### CI/CD Pipeline (pytest, coverage)

Run: Automatically on PR push

**Responsibilities**:
- **Unit Tests**: Individual function correctness
- **Integration Tests**: Component interaction
- **Coverage**: Threshold enforcement (80%+ for critical paths)

**Result**: Blocking if tests fail or coverage drops

#### Decision Matrix: When to Use Each

| Scenario | Tool |
|----------|------|
| "I'm about to commit changes" | Pre-commit hooks |
| "I want feedback during feature development" | Local Claude Code CLI (`claude` command) |
| "PR is ready for formal review" | GitHub Actions (`@claude` comment) |
| "I need to verify tests pass" | CI/CD pipeline (automatic) |
| "I want to explore Linear issue context" | Local Claude Code CLI with Linear MCP |

### Implementation Details

**Architecture**: Reusable workflow pattern
- **Central workflow**: `quantivly/.github/.github/workflows/claude-review.yml`
- **Caller workflows**: Minimal files in each repository's `.github/workflows/` directory
- **Secrets**: Automatically inherited from organization secrets using `secrets: inherit`
- **Deployment**: See [Deploying Claude Review](docs/deploying-claude-review.md)

**Workflow**: `.github/workflows/claude-review.yml`
- Triggers on `issue_comment` event with `@claude` pattern (direct) or `workflow_call` (reusable)
- Validates commenter permissions (org member or collaborator)
- Calls Python orchestration script

**Script**: `scripts/claude-review.py`
- Fetches PR context via GitHub API
- Fetches Linear context via GraphQL API (read-only)
- Reads repository CLAUDE.md for guidelines
- Calls Claude API (Sonnet 4.5)
- Posts structured review as PR comment

**Cost**: ~$0.50-$1.00 per review (covered by organization)

**Security**: All API keys stored in organization secrets, passed via environment variables

**Deploying to New Repositories**:

To enable Claude reviews in a repository, add this minimal caller workflow:

```bash
# Copy template to repository
cp ~/quantivly/.github/workflow-templates/claude-review-caller.yml \
   <repo>/.github/workflows/claude-review.yml

# Commit and push
git add .github/workflows/claude-review.yml
git commit -m "enh: Add Claude-powered PR review workflow"
git push origin master
```

See [docs/deploying-claude-review.md](docs/deploying-claude-review.md) for complete deployment guide.

### Local Development with MCP

Developers can optionally use Claude Code CLI with Linear MCP integration for feature implementation:

```bash
# Configure Linear MCP using Claude CLI (recommended)
claude mcp add --transport http linear-server https://mcp.linear.app/mcp

# OR manually add to ~/.config/claude/mcp.json:
# {
#   "mcpServers": {
#     "linear-server": {
#       "url": "https://mcp.linear.app/mcp",
#       "transport": "http",
#       "authorization": {
#         "type": "bearer",
#         "token": "YOUR_LINEAR_API_KEY"
#       }
#     }
#   }
# }

# Use Claude Code with Linear context
cd ~/hub/sre-core
claude
> "Implement feature from HUB-1234"
```

### Troubleshooting

**Review not triggering**:
- Check comment contains `@claude` anywhere in the text
- Verify you're an org member or collaborator
- Check PR is open (not draft or closed)

**Review failed**:
- Check [Actions tab](https://github.com/quantivly/<repo>/actions) for logs
- Common causes: API rate limits, timeouts
- Solution: Wait and retry with `@claude`

**Linear context missing**:
- Verify PR title starts with `AAA-####` format
- Check issue exists and is accessible in Linear
- Review continues without Linear context if not found

### Related Documentation

- [Detailed Integration Guide](docs/claude-integration-guide.md) - Complete usage guide
- [GitHub Actions Docs](https://docs.github.com/en/actions) - Workflow reference
- [Linear API](https://developers.linear.app/) - API documentation

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

**Quantivly Repositories**:
- [hub](https://github.com/quantivly/hub) - Superproject + release management (creates manifest images for sre-* components)
- [sre-core](https://github.com/quantivly/sre-core) - Django backend (GraphQL API, business logic)
- [sre-ui](https://github.com/quantivly/sre-ui) - React + Next.js frontend (consumes sre-core APIs)
- [sre-event-bridge](https://github.com/quantivly/sre-event-bridge) - WAMP router bridge (notifies backend via REST API)
- [sre-postgres](https://github.com/quantivly/sre-postgres) - PostgreSQL database for hub
- [platform (quantivly-dockers)](https://github.com/quantivly/quantivly-dockers) - Backbone services (auto-conf, box, ptbi, quantivly-sdk)

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
