# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is the **Quantivly `.github` organization repository** — a special GitHub repository that configures organization-wide settings and displays the public organization profile.

**This repository is PUBLIC.** GitHub requires this for the org profile README to display.

**Purpose**:
- Display organization profile README on https://github.com/quantivly
- Store organization-wide GitHub configuration templates (issues, PRs, discussions)
- Define default community health files for all organization repositories
- Host `assets/` for public URLs (e.g., icons used in CI output)

**Claude review system**: The automated PR review workflow, prompts, standards, and documentation live in the private [`quantivly/ci`](https://github.com/quantivly/ci) repository. This repo only has a thin caller workflow in `.github/workflows/claude-review.yml`.

## Repository Structure

```
.github/
  profile/README.md              # Org profile (PUBLIC, visible on github.com/quantivly)
  assets/icons/linear.png        # Public icon used in review output
  .github/
    workflows/claude-review.yml  # Caller workflow pointing to quantivly/ci
    pull_request_template.md     # Default PR template for org repos
    CODEOWNERS                   # Review gate for profile changes
  CLAUDE.md                      # This file
  .gitignore
```

## Important Gotchas

1. **Immediate Visibility**: Changes to `profile/README.md` appear immediately on https://github.com/quantivly when pushed to `master`. Review carefully before pushing.

2. **Organization-Wide Impact**: Templates and community health files in this repo become defaults for ALL Quantivly repositories. Test thoroughly.

3. **Repository Overrides**: Individual repositories can override these defaults by creating their own `.github/` files. Organization templates are fallbacks.

4. **Image URLs**: Use stable GitHub asset URLs for images in profile README. URLs like `https://github.com/quantivly/.github/assets/...` are permanent.

5. **Public Information Only**: This repository is PUBLIC. Never include:
   - API keys, tokens, passwords
   - Internal infrastructure details
   - Customer information
   - Non-public product features
   - Proprietary CI tooling (that belongs in `quantivly/ci`)

6. **Marketing Coordination**: Profile README changes should be coordinated with marketing team to ensure consistent messaging.

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

### Template Standards

**Issue Templates** (YAML forms, `.yml` extension):
- Require essential fields (component, description)
- Include appropriate labels and helpful placeholders

**Pull Request Templates**:
- Enforce Linear issue reference (AAA-#### format)
- Checklist for tests, docs, breaking changes
- Imperative mood in title

**Community Files**:
- Clear, actionable guidance
- Professional and welcoming tone
- Aligned with Quantivly values and HIPAA compliance

## Git Workflow

### Commit Message Format

```
<type>: <summary>

<optional body>

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**Types**: `doc` (documentation), `enh` (enhancement), `fix` (bug fix)

### PR Title Format

```
DO-#### Summary
```

Use imperative mood. If no Linear issue, use descriptive summary only.

### Branching Strategy

- Main branch: `master`
- Feature branches: `user/description` or `user/linear-id-description`
- Always create PR for profile changes (require review)

## Key Files

- `profile/README.md` - Organization profile page (PUBLIC, visible on github.com/quantivly)
- `assets/icons/linear.png` - Icon used in CI review output (public URL must stay stable)
- `.github/workflows/claude-review.yml` - Caller workflow for reviewing this repo's PRs
- `.github/pull_request_template.md` - Default PR template for all org repos
