# Deploying Claude PR Review to Organization Repositories

This guide explains how to enable Claude-powered PR reviews in Quantivly repositories using the centralized reusable workflow.

## Overview

The Claude PR review system uses a **reusable workflow** pattern:

- **Central workflow**: Lives in `quantivly/.github/.github/workflows/claude-review.yml`
- **Caller workflows**: Minimal files in each repository's `.github/workflows/` directory
- **Secrets**: Automatically inherited from organization secrets

This maintains a single source of truth while allowing easy deployment to any repository.

## Prerequisites

1. **Organization secrets configured** (already done):
   - `ANTHROPIC_API_KEY` - Claude API access
   - `LINEAR_API_KEY` - Linear issue context
   - `CLAUDE_APP_PRIVATE_KEY` - GitHub App private key for Claude[bot] identity
   - `GITHUB_TOKEN` - Automatically provided by GitHub Actions

2. **Organization variables configured** (already done):
   - `CLAUDE_APP_ID` - GitHub App ID for Claude[bot] identity

3. **GitHub App "Claude" installed** (already done):
   - App provides custom identity so reviews appear as "Claude[bot]" instead of "github-actions[bot]"
   - App needs permissions: Contents (Read), Issues (Write), Pull requests (Write)
   - App must be installed to the organization with access to all repositories

4. **Repository permissions**:
   - Caller must be org member or repo collaborator with write access
   - Workflow must have permissions: `contents: read`, `issues: write`, `pull-requests: write`

5. **`.github` repository access enabled** (needs verification):
   - Navigate to Settings → Actions → General in the `.github` repository
   - Under "Access", ensure "Accessible from repositories in the 'quantivly' organization" is selected

## Deployment Steps

### Step 1: Copy Caller Workflow

Copy the caller workflow template to the target repository:

```bash
# Navigate to target repository
cd ~/quantivly/<repo-name>

# Create workflows directory if it doesn't exist
mkdir -p .github/workflows

# Copy the caller workflow template
cp ~/quantivly/.github/workflow-templates/claude-review-caller.yml \
   .github/workflows/claude-review.yml
```

### Step 2: Commit and Push

```bash
git add .github/workflows/claude-review.yml
git commit -m "enh: Add Claude-powered PR review workflow"
git push origin master
```

### Step 3: Verify Deployment

1. **Create a test PR** in the repository
2. **Comment** `@claude` on the PR
3. **Check Actions tab**: Navigate to `https://github.com/quantivly/<repo>/actions`
4. **Verify workflow runs**: Should see "Claude PR Review" workflow triggered
5. **Confirm review posted**: Check PR for Claude's review comment

## Troubleshooting

### Workflow Not Triggering

**Symptom**: No workflow runs appear after commenting `@claude`

**Potential causes**:
1. Caller workflow not merged to default branch
2. Syntax error in workflow file
3. Repository doesn't have Actions enabled

**Solution**:
```bash
# Check if workflow exists on default branch
git checkout master
git pull origin master
cat .github/workflows/claude-review.yml

# Check for YAML syntax errors
yamllint .github/workflows/claude-review.yml

# Enable Actions if disabled
# Navigate to: Settings → Actions → General → Enable Actions
```

### Permission Denied

**Symptom**: Workflow runs but Claude responds with permission denied message

**Potential causes**:
1. Commenter is not org member or collaborator
2. Commenter has read-only access

**Solution**:
- Verify commenter has write/maintain/admin access to repository
- Add collaborator via Settings → Collaborators

### Reusable Workflow Not Found

**Symptom**: Error: `Workflow file not found: quantivly/.github/.github/workflows/claude-review.yml@master`

**Potential causes**:
1. `.github` repository access not enabled for organization
2. Incorrect path or branch reference
3. Workflow file doesn't exist

**Solution**:
```bash
# Verify workflow exists in .github repo
cd ~/quantivly/.github
ls -la .github/workflows/claude-review.yml

# Enable access in .github repository:
# Settings → Actions → General → Access
# Select "Accessible from repositories in the 'quantivly' organization"
```

### Secrets Not Available

**Symptom**: Workflow fails with API authentication errors

**Potential causes**:
1. Organization secrets not configured
2. `secrets: inherit` not working
3. Secrets have wrong names

**Solution**:
```bash
# Verify organization secrets exist:
# Navigate to: https://github.com/organizations/quantivly/settings/secrets/actions
# Confirm: ANTHROPIC_API_KEY, LINEAR_API_KEY exist

# Alternative: Explicitly pass secrets (not recommended)
# Edit caller workflow to replace "secrets: inherit" with:
secrets:
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  LINEAR_API_KEY: ${{ secrets.LINEAR_API_KEY }}
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Review Fails or Times Out

**Symptom**: Workflow runs but fails with API error

**Potential causes**:
1. Anthropic API rate limits
2. Large PR causing timeout
3. Linear API issues

**Solution**:
- Wait 5-10 minutes and retry with `@claude`
- Check [workflow logs](https://github.com/quantivly/<repo>/actions) for specific error
- Review retries automatically (3 attempts with 30s backoff)

## Rollout Plan

**Phase 1: Testing** (sre-core)
- Deploy to `sre-core` repository
- Test with real PRs
- Verify Linear integration works
- Monitor for errors over 1 week

**Phase 2: Production** (hub, sre-ui)
- Deploy to `hub` and `sre-ui` repositories
- Announce to team in Slack
- Update onboarding documentation

**Phase 3: Rollout** (remaining repos)
- Deploy to `quantivly-dockers`
- Deploy to other active repositories
- Archive inactive repositories first

## Repository Status

| Repository | Status | Notes |
|------------|--------|-------|
| `.github` | ✅ Central workflow | Reusable workflow deployed |
| `sre-core` | ⏳ Phase 1 | Ready for testing |
| `hub` | ⏳ Phase 2 | Awaiting Phase 1 completion |
| `sre-ui` | ⏳ Phase 2 | Awaiting Phase 1 completion |
| `quantivly-dockers` | ⏳ Phase 3 | Awaiting Phase 2 completion |

## Maintenance

### Updating the Review Logic

When making changes to the review workflow:

1. **Edit central workflow** in `quantivly/.github/.github/workflows/claude-review.yml`
2. **Test in `.github` repo** (create PR, comment `@claude`)
3. **Commit and push** changes
4. **Changes propagate automatically** to all repositories using the caller workflow

No changes needed in individual repositories unless:
- Changing trigger conditions
- Modifying concurrency settings
- Adjusting permissions

### Removing Claude Review

To disable Claude review in a repository:

```bash
cd ~/quantivly/<repo-name>
git rm .github/workflows/claude-review.yml
git commit -m "ref: Remove Claude PR review workflow"
git push origin master
```

## Cost Monitoring

Each Claude review costs approximately **$0.60-$0.90** depending on PR size.

**Monitor usage**:
- Check workflow run logs for token metrics
- Review [Actions tab](https://github.com/quantivly/<repo>/actions) for frequency
- Set up billing alerts in GitHub organization settings

**Best practices**:
- Use `@claude` on PRs ready for formal review (not during active development)
- Encourage local `claude` CLI for iterative development
- Address critical feedback before re-reviewing

## Related Documentation

- [Claude Integration Guide](claude-integration-guide.md) - Complete usage guide
- [Review Standards](review-standards.md) - What Claude reviews and how
- [GitHub Actions: Reusing Workflows](https://docs.github.com/en/actions/using-workflows/reusing-workflows) - Official documentation

## Questions?

- **Technical issues**: Check workflow logs in Actions tab
- **Feature requests**: Open issue in `.github` repository
- **Integration questions**: Contact DevOps team
