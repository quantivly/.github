# Claude PR Review - Validation Procedure

This document describes how to test the Claude + GitHub integration end-to-end.

---

## Prerequisites

- [ ] Organization secrets configured:
  - `ANTHROPIC_API_KEY` - Claude API key
  - `LINEAR_API_KEY` - Linear API key
- [ ] Workflow file exists: `.github/workflows/claude-review.yml`
- [ ] Review script exists: `scripts/claude-review.py`
- [ ] Test repository with workflow deployed
- [ ] You are an organization member or collaborator

---

## Test Scenario 1: Basic Review with Issues

### Setup

1. **Create test Linear issue** (if using real Linear):
   ```
   ID: TEST-9999
   Title: Test Claude Review Integration
   Description: This is a test issue for validating Claude review workflow.

   Acceptance Criteria:
   - Code should be secure (no SQL injection)
   - All functions should have proper error handling
   - Tests should cover edge cases
   ```

2. **Create test branch**:
   ```bash
   cd /path/to/test/repo
   git checkout -b user/test-claude-review-9999
   ```

3. **Add test file with issues**:
   ```bash
   # Copy the test-pr-example.py file
   cp tests/test-pr-example.py src/test_file.py
   git add src/test_file.py
   git commit -m "test: Add example code for Claude review testing"
   git push origin user/test-claude-review-9999
   ```

4. **Create pull request**:
   ```bash
   gh pr create \
     --title "TEST-9999 Add example code for testing" \
     --body "This PR tests the Claude review integration with intentionally buggy code."
   ```

### Execution

1. **Trigger Claude review**:
   - Go to PR on GitHub
   - Comment: `@claude`
   - Note the timestamp

2. **Wait for workflow**:
   - Check [Actions tab](https://github.com/org/repo/actions)
   - Verify workflow triggered
   - Monitor logs for errors

3. **Verify review posted**:
   - Check PR comments for Claude review
   - Note the completion time (should be <5 minutes)

### Validation Checklist

**Review Structure**:
- [ ] Review comment appears on PR
- [ ] All required sections present:
  - [ ] Summary
  - [ ] Alignment with Linear Requirements
  - [ ] Critical Issues
  - [ ] Suggestions
  - [ ] Positive Observations
  - [ ] Testing Assessment
  - [ ] Recommendation
- [ ] Review includes metadata footer (triggered by, powered by)

**Issue Detection**:
- [ ] SQL injection flagged as CRITICAL
  - [ ] Location: `test_file.py:24-30` (get_user_by_id function)
  - [ ] Severity: CRITICAL
  - [ ] Explanation includes "parameterized queries"
- [ ] Off-by-one error flagged as HIGH
  - [ ] Location: `test_file.py:48-50` (paginate_items function)
  - [ ] Severity: HIGH
  - [ ] Explains the boundary issue
- [ ] Missing error handling flagged
  - [ ] Location: `test_file.py:60-70` (export_data_to_csv function)
  - [ ] Severity: HIGH or SUGGESTION
- [ ] XSS vulnerability flagged as CRITICAL
  - [ ] Location: `test_file.py:105-107` (process_user_input function)
  - [ ] Severity: CRITICAL
  - [ ] Mentions sanitization/escaping

**Linear Integration**:
- [ ] Review references Linear issue TEST-9999
- [ ] Validates against acceptance criteria
- [ ] Mentions security requirement (SQL injection)
- [ ] Mentions error handling requirement
- [ ] Mentions testing requirement

**Recommendation**:
- [ ] Recommendation is **REQUEST_CHANGES** (due to CRITICAL issues)
- [ ] Justification mentions security vulnerabilities

**Metrics**:
- [ ] Review completed in <5 minutes
- [ ] Token usage logged in workflow output
- [ ] Estimated cost <$1.00
- [ ] No workflow errors

---

## Test Scenario 2: Clean Code Review

### Setup

1. **Create new branch**:
   ```bash
   git checkout -b user/test-claude-clean-code
   ```

2. **Add clean, well-tested code**:
   ```python
   # src/clean_example.py
   """Clean example with proper practices."""
   from __future__ import annotations

   import sqlite3
   from typing import Any


   def get_user_by_id_safe(user_id: int) -> dict[str, Any] | None:
       """
       Fetch user from database by ID (safe version).

       Args:
           user_id: User ID to fetch

       Returns:
           User dictionary or None if not found
       """
       try:
           conn = sqlite3.connect("users.db")
           cursor = conn.cursor()

           # SAFE: Parameterized query
           cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
           result = cursor.fetchone()

           if result:
               return {
                   "id": result[0],
                   "username": result[1],
                   "email": result[2],
               }
           return None
       except sqlite3.Error as e:
           print(f"Database error: {e}")
           return None
       finally:
           conn.close()
   ```

3. **Add tests**:
   ```python
   # tests/test_clean_example.py
   import pytest
   from unittest.mock import Mock, patch
   from src.clean_example import get_user_by_id_safe


   def test_get_user_by_id_safe_success():
       """Test successful user retrieval."""
       with patch("sqlite3.connect") as mock_connect:
           mock_cursor = Mock()
           mock_cursor.fetchone.return_value = (1, "testuser", "test@example.com")
           mock_connect.return_value.cursor.return_value = mock_cursor

           result = get_user_by_id_safe(1)

           assert result == {
               "id": 1,
               "username": "testuser",
               "email": "test@example.com"
           }


   def test_get_user_by_id_safe_not_found():
       """Test user not found."""
       with patch("sqlite3.connect") as mock_connect:
           mock_cursor = Mock()
           mock_cursor.fetchone.return_value = None
           mock_connect.return_value.cursor.return_value = mock_cursor

           result = get_user_by_id_safe(999)

           assert result is None


   def test_get_user_by_id_safe_database_error():
       """Test database error handling."""
       with patch("sqlite3.connect") as mock_connect:
           mock_connect.side_effect = sqlite3.Error("Connection failed")

           result = get_user_by_id_safe(1)

           assert result is None
   ```

4. **Create PR**:
   ```bash
   git add src/clean_example.py tests/test_clean_example.py
   git commit -m "enh: Add safe user lookup with comprehensive tests"
   git push origin user/test-claude-clean-code
   gh pr create --title "Add safe user lookup implementation" \
     --body "Implements parameterized queries and error handling with full test coverage."
   ```

### Execution

1. Comment `@claude` on PR
2. Wait for review

### Validation Checklist

- [ ] Review posted successfully
- [ ] **Critical Issues** section states "No critical issues identified"
- [ ] **Positive Observations** mentions:
  - [ ] Parameterized queries
  - [ ] Proper error handling
  - [ ] Comprehensive test coverage
  - [ ] Good docstrings
- [ ] **Testing Assessment** is positive
- [ ] **Recommendation** is **APPROVE** or **COMMENT**
- [ ] Review acknowledges good practices

---

## Test Scenario 3: Permission Validation

### Setup

1. Get a test GitHub account that is NOT:
   - An organization member
   - A repository collaborator

### Execution

1. Have external user comment `@claude` on a test PR
2. Check workflow execution

### Validation Checklist

- [ ] Workflow runs (triggered by comment)
- [ ] Permission check fails
- [ ] Workflow posts message: "⚠️ Claude reviews are only available to organization members..."
- [ ] Workflow exits gracefully (doesn't post review)
- [ ] No API calls made (no cost incurred)

---

## Test Scenario 4: Re-Review After Fixes

### Setup

1. Use the PR from Scenario 1 (with issues)
2. Fix the issues Claude identified

### Execution

1. **Fix the SQL injection**:
   ```python
   # Change to parameterized query
   query = "SELECT * FROM users WHERE id = ?"
   cursor.execute(query, (user_id,))
   ```

2. **Fix the off-by-one error**:
   ```python
   end = start + page_size  # Remove the -1
   ```

3. **Add error handling**:
   ```python
   try:
       with open(filename, "w") as f:
           # ... existing code
   except IOError as e:
       print(f"Failed to write file: {e}")
       raise
   ```

4. **Fix XSS**:
   ```python
   import html
   return f"<div>User said: {html.escape(user_input)}</div>"
   ```

5. **Commit and push**:
   ```bash
   git add src/test_file.py
   git commit -m "fix: Address Claude review feedback"
   git push origin user/test-claude-review-9999
   ```

6. **Re-request review**:
   - Comment `@claude` on PR again

### Validation Checklist

- [ ] Second review posted
- [ ] Review body includes **Prior reviews** line (e.g., "Re-review #2. X of Y prior findings addressed.")
- [ ] Fixed issues are NOT re-flagged as inline comments
- [ ] New or remaining issues are flagged normally with inline comments
- [ ] Review count is accurate (matches number of previous Claude reviews)
- [ ] **Critical Issues** now shows issues resolved or "No critical issues"
- [ ] **Positive Observations** mentions fixes
- [ ] **Recommendation** changes to **APPROVE** or **COMMENT**
- [ ] Review acknowledges improvements

---

## Test Scenario 5: Large PR Handling

### Setup

1. Create PR with >1000 lines changed
2. Mix of legitimate changes and some issues

### Execution

1. Comment `@claude` on PR
2. Monitor for truncation handling

### Validation Checklist

- [ ] Review completes (doesn't timeout)
- [ ] Review mentions if diff was truncated
- [ ] Key issues still identified despite size
- [ ] Cost remains reasonable (<$2.00)
- [ ] Workflow completes in <10 minutes

---

## Test Scenario 6: No Linear Issue

### Setup

1. Create PR with title NOT containing Linear ID:
   ```
   Fix typo in documentation
   ```

### Execution

1. Comment `@claude` on PR

### Validation Checklist

- [ ] Review posted successfully
- [ ] **Alignment with Linear Requirements** says "No Linear issue to validate against"
- [ ] Review still checks security, logic, quality, etc.
- [ ] No errors in workflow logs
- [ ] Review completes normally

---

## Performance Benchmarks

Track these metrics across all test scenarios:

| Metric | Target | Actual |
|--------|--------|--------|
| Review time | <5 min | _____ |
| Token usage | <200K input | _____ |
| Cost per review | <$1.00 | _____ |
| False positive rate | <5% | _____ |
| False negative rate | <10% | _____ |
| Workflow success rate | >95% | _____ |

---

## Troubleshooting Common Issues

### Workflow Not Triggering

**Symptoms**: No workflow run appears in Actions tab

**Checks**:
- [ ] Comment is exactly `@claude` (case-sensitive, no trailing spaces)
- [ ] PR is open (not draft, not closed)
- [ ] Workflow file exists and is valid YAML
- [ ] You have permissions to trigger workflows

**Solution**: Check workflow syntax, verify permissions

### Review Posting Failed

**Symptoms**: Workflow runs but no review comment appears

**Checks**:
- [ ] Check workflow logs for Python errors
- [ ] Verify GITHUB_TOKEN permissions
- [ ] Check for API rate limiting

**Solution**: Review workflow logs, check API quotas

### Linear Context Missing

**Symptoms**: Review says "No Linear issue" when one exists

**Checks**:
- [ ] PR title format is `AAA-####` (all caps, hyphen, 1-6 digits)
- [ ] Linear issue exists and is accessible
- [ ] LINEAR_API_KEY is valid

**Solution**: Fix PR title format, verify Linear API access

### High Cost Per Review

**Symptoms**: Reviews costing >$1.50 consistently

**Checks**:
- [ ] PR size (lines changed)
- [ ] CLAUDE.md size
- [ ] Token usage in logs

**Solution**: Consider truncation limits, optimize prompt size

---

## Success Criteria

The integration is considered production-ready when:

- [ ] All 6 test scenarios pass
- [ ] Performance benchmarks meet targets
- [ ] No critical security issues in workflow
- [ ] Documentation is complete and clear
- [ ] Team training completed
- [ ] Monitoring and alerting configured
- [ ] Rollback plan documented

---

## Next Steps After Validation

1. **Document results**: Fill in performance benchmarks
2. **Team demo**: Show working integration to developers
3. **Gather feedback**: Survey on usability and quality
4. **Iterate**: Refine prompts based on false positives/negatives
5. **Deploy org-wide**: Roll out to all repositories
6. **Monitor**: Track usage, cost, and satisfaction metrics

---

**Last Updated**: 2026-02-04
