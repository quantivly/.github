#!/usr/bin/env python3
"""
Claude PR Review Orchestration Script (MCP-Based)

This script coordinates Claude-powered code reviews for GitHub PRs using
the Model Context Protocol (MCP) for Linear integration:

1. Fetches PR context (files, diffs, metadata)
2. Connects to Linear MCP server for dynamic Linear access
3. Reads repository-specific CLAUDE.md guidelines
4. Calls Claude API with Linear tools available
5. Handles tool_use conversation loop (Claude can query Linear)
6. Posts structured review comment to PR

Environment variables required:
- ANTHROPIC_API_KEY: Claude API key
- LINEAR_API_KEY: Linear API key (used by MCP server)
- GITHUB_TOKEN: GitHub API token
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, AsyncGenerator

if TYPE_CHECKING:
    from collections.abc import Callable

import anthropic
from github import Github, GithubException
from mcp import ClientSession
try:
    # Try new import path (mcp >= 1.1.0)
    from mcp.client.streamable_http import streamablehttp_client
except ImportError:
    # Fall back to older import path if it exists
    try:
        from mcp.client.sse import sse_client as streamablehttp_client
    except ImportError:
        # If neither exists, we'll handle this gracefully later
        streamablehttp_client = None

# Constants
MAX_DIFF_LINES = 2000  # Limit diff size to control token usage
MAX_FILE_CONTENT_LINES = 500  # Limit individual file content
MAX_INSTRUCTION_LENGTH = 2000  # Limit reviewer instructions to prevent prompt injection
CLAUDE_MODEL = "claude-sonnet-4-5-20250929"
MAX_TOKENS = 5000

# MCP Server Configuration
LINEAR_MCP_URL = "https://mcp.linear.app/mcp"
GITHUB_MCP_URL = "https://api.githubcopilot.com/mcp/"
GITHUB_TOOL_PREFIX = "github_"  # Namespace to distinguish from Linear tools

# GitHub MCP tools to expose (whitelist for security and token efficiency)
# Only include tools needed for cross-repository code context
GITHUB_ESSENTIAL_TOOLS = {
    "get_file_contents",  # Read files from related repos
    "search_code",  # Search for code patterns across repos
    "get_commit",  # Get commit details
    "list_commits",  # List commits for context
}


def extract_linear_id(pr_title: str) -> str | None:
    """Extract Linear issue ID from PR title (format: AAA-#### ...)."""
    match = re.match(r"^([A-Z]+-\d+)", pr_title)
    return match.group(1) if match else None


def extract_reviewer_instructions(comment_body: str) -> str:
    """
    Extract custom reviewer instructions from the @claude comment.

    Handles various comment formats:
    - "@claude" -> returns ""
    - "@claude review" -> returns ""
    - "@claude focus on security" -> returns "focus on security"
    - "@claude, please check for N+1 queries" -> returns "please check for N+1 queries"
    - "Hey @claude can you look at the error handling?" -> returns "can you look at the error handling?"

    Security:
    - Truncates to MAX_INSTRUCTION_LENGTH to prevent prompt stuffing
    - Does not execute or eval content (just string inclusion in prompt)

    Args:
        comment_body: The full comment body from GitHub

    Returns:
        Extracted instructions (may be empty string if only "@claude" or similar)
    """
    if not comment_body:
        return ""

    # Find @claude mention and extract everything after it
    # Case-insensitive match for @claude
    match = re.search(r"@claude\b[,:]?\s*(.*)", comment_body, re.IGNORECASE | re.DOTALL)

    if not match:
        return ""

    instructions = match.group(1).strip()

    # Filter out generic trigger words that aren't real instructions
    generic_triggers = {
        "",
        "review",
        "please review",
        "review this",
        "please review this",
        "review this pr",
        "please review this pr",
        "check this",
        "please check this",
    }

    if instructions.lower() in generic_triggers:
        return ""

    # Truncate to prevent prompt stuffing
    if len(instructions) > MAX_INSTRUCTION_LENGTH:
        instructions = instructions[:MAX_INSTRUCTION_LENGTH] + "... (truncated)"

    return instructions


def read_claude_md(repo_path: Path) -> str:
    """Read repository-specific CLAUDE.md guidelines."""
    claude_md_path = repo_path / "CLAUDE.md"
    if claude_md_path.exists():
        print(f"✓ Found CLAUDE.md at {claude_md_path}")
        return claude_md_path.read_text()
    print("⚠️  No CLAUDE.md found, using generic guidelines")
    return "No repository-specific guidelines provided."


def truncate_diff(diff: str, max_lines: int) -> str:
    """Truncate diff to max lines while preserving structure."""
    lines = diff.split("\n")
    if len(lines) <= max_lines:
        return diff

    truncated = lines[:max_lines]
    remaining = len(lines) - max_lines
    truncated.append(f"\n... ({remaining} more lines truncated)")
    return "\n".join(truncated)


def convert_mcp_tools_to_anthropic_format(
    mcp_tools: list[Any],
    prefix: str = "",
    filter_set: set[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Convert MCP tool definitions to Anthropic API tool format.

    Args:
        mcp_tools: List of MCP tool objects from list_tools()
        prefix: Optional prefix to add to tool names (e.g., "github_")
        filter_set: Optional set of tool names to include (whitelist)

    Returns:
        List of tool definitions in Anthropic API format
    """
    anthropic_tools = []
    for tool in mcp_tools:
        # Skip tools not in whitelist (if specified)
        if filter_set and tool.name not in filter_set:
            continue

        # Apply prefix for namespacing
        tool_name = f"{prefix}{tool.name}" if prefix else tool.name

        anthropic_tool = {
            "name": tool_name,
            "description": tool.description or "No description provided",
            "input_schema": tool.inputSchema if hasattr(tool, "inputSchema") else {},
        }
        anthropic_tools.append(anthropic_tool)
    return anthropic_tools


def strip_tool_simulation_markup(text: str) -> str:
    """
    Remove Claude's simulated tool usage markup from review text.

    When Linear tools are unavailable but Claude is still instructed to use them,
    it may simulate tool usage with XML-like tags. This function removes those tags
    to ensure clean markdown output.

    Examples of patterns removed:
    - <tool_name attr="value">content</tool_name>
    - <linear_fetch_issue ...>...</linear_fetch_issue>
    - Self-closing tags: <tag attr="value" />
    """
    # Remove XML-like tool tags (both paired and self-closing)
    # Pattern matches: <tag ...>content</tag> or <tag ... />
    cleaned = re.sub(
        r'<\w+[^>]*>.*?</\w+>',  # Paired tags with content
        '',
        text,
        flags=re.DOTALL
    )
    cleaned = re.sub(
        r'<\w+[^>]*/>\s*',  # Self-closing tags
        '',
        cleaned
    )

    # Clean up excessive whitespace left behind
    cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)

    return cleaned.strip()


def detect_tech_stack(files: list[Any]) -> str:
    """
    Detect primary tech stack from changed files.

    Returns one of: 'django', 'react', 'docker', 'mixed'
    """
    py_count = 0
    ts_count = 0
    docker_count = 0

    for file in files:
        filename = file.filename.lower()

        if filename.endswith('.py'):
            py_count += 1
        elif filename.endswith(('.ts', '.tsx', '.jsx', '.js')):
            ts_count += 1
        elif 'dockerfile' in filename or filename == 'docker-compose.yml':
            docker_count += 1

    # Determine primary stack
    total = py_count + ts_count + docker_count
    if total == 0:
        return 'mixed'

    # Calculate percentages
    py_pct = py_count / total if total > 0 else 0
    ts_pct = ts_count / total if total > 0 else 0
    docker_pct = docker_count / total if total > 0 else 0

    # Dominant stack if >50%
    if py_pct > 0.5:
        return 'django'
    elif ts_pct > 0.5:
        return 'react'
    elif docker_pct > 0.5:
        return 'docker'
    else:
        return 'mixed'


def get_tech_stack_guidelines(tech_stack: str) -> str:
    """
    Return tech-stack-specific security and best practice guidelines.

    These guidelines are added to static_content (cacheable) to provide
    specialized review focus based on the primary tech stack.
    """
    guidelines = {
        'django': """
## Django-Specific Security & Best Practices

**Priority Checks**:
1. **ORM Injection**: Check for `.raw()`, `.extra()`, or string interpolation in queries
   - Bad: `User.objects.raw(f"SELECT * FROM users WHERE id = {user_id}")`
   - Good: `User.objects.raw("SELECT * FROM users WHERE id = %s", [user_id])`

2. **GraphQL Security**: Validate query complexity limits and authentication on resolvers
   - Ensure all resolvers have proper authentication decorators
   - Check for N+1 query issues (use `.select_related()` / `.prefetch_related()`)

3. **Celery Tasks**: Check for task injection and proper error handling
   - Validate task arguments are sanitized
   - Ensure retry logic and failure handling

4. **Django Admin**: Verify CSRF protection and permission checks
   - Custom admin actions should check permissions
   - Sensitive operations require confirmation

5. **File Uploads**: Check for file type validation and size limits
   - Validate file extensions and MIME types
   - Check for virus scanning integration hooks

6. **Plugin System**: Verify plugin sandboxing and input validation
   - Plugins should not access database directly (use APIs)
   - Plugin inputs must be validated and sanitized

7. **Migrations**: Check for safe migrations (no blocking operations)
   - Avoid adding columns without defaults on large tables
   - Check for index creation (use CONCURRENTLY in production)
""",
        'react': """
## React/Next.js-Specific Security & Best Practices

**Priority Checks**:
1. **XSS Prevention**: Check for dangerous patterns
   - Bad: Direct DOM manipulation with user input
   - Good: Use React's automatic escaping

2. **API Routes**: Validate authentication and CORS configuration
   - Check for auth middleware on protected routes
   - Verify CORS settings don't allow arbitrary origins

3. **State Management**: Check for sensitive data exposure
   - Bad: PHI or credentials in localStorage/sessionStorage
   - Good: Sensitive data in memory only or secure httpOnly cookies

4. **Component Security**: Verify prop validation and TypeScript types
   - Check for proper TypeScript types (avoid `any`)
   - Validate props with PropTypes or TypeScript

5. **SSR Security**: Check for server-side data leakage
   - Verify sensitive data isn't serialized to client
   - Check `getServerSideProps` doesn't expose credentials

6. **Third-Party Libraries**: Flag dependencies with known vulnerabilities
   - Large bundle sizes (>100KB for single dependency)
   - Outdated packages with security advisories

7. **Performance**: Check for common React anti-patterns
   - Missing dependency arrays in useEffect
   - Unnecessary re-renders (missing memo/useMemo)
   - N+1 API calls (use batching or caching)
""",
        'docker': """
## Docker/Infrastructure-Specific Security & Best Practices

**Priority Checks**:
1. **Base Images**: Verify official, minimal base images
   - Good: `python:3.11-alpine`, `node:20-alpine`, `nginx:alpine`
   - Bad: `latest` tag, unofficial images, large base images

2. **Secrets Management**: Check for hardcoded credentials
   - Bad: `ENV DATABASE_PASSWORD=secret123`
   - Good: Use Docker secrets or environment variables at runtime

3. **User Permissions**: Verify containers run as non-root
   - Check for `USER` directive (not root)
   - Verify processes don't require root privileges

4. **Network Isolation**: Check for proper network segmentation
   - Verify services use specific networks (not default bridge)
   - Check for unnecessary exposed ports

5. **Volume Mounts**: Check for minimal, read-only mounts where possible
   - Sensitive directories should be read-only
   - Avoid mounting entire host filesystem

6. **Image Optimization**: Check for layer optimization
   - Combine RUN commands to reduce layers
   - Use .dockerignore to exclude unnecessary files
   - Multi-stage builds for smaller production images

7. **Health Checks**: Verify HEALTHCHECK directives
   - All services should have health checks
   - Health checks should validate actual functionality
""",
        'mixed': """
## Multi-Technology Stack

This PR touches multiple technologies. Focus on:
1. **Cross-cutting concerns**: Authentication, authorization, data flow
2. **API boundaries**: Validate contracts between frontend/backend
3. **Integration security**: Check for consistent security across layers
4. **Data consistency**: Ensure data models align across stack
"""
    }

    return guidelines.get(tech_stack, '')


def build_review_prompt(
    pr: Any,
    files: list[Any],
    linear_id: str | None,
    claude_md: str,
    diff: str,
    has_linear_tools: bool = False,
    has_github_tools: bool = False,
    reviewer_instructions: str = "",
) -> tuple[str, str]:
    """
    Construct comprehensive review prompt with static and dynamic content.

    Args:
        pr: PyGithub PullRequest object
        files: List of changed files
        linear_id: Linear issue ID extracted from PR title (or None)
        claude_md: Contents of repository CLAUDE.md
        diff: PR diff content
        has_linear_tools: Whether Linear MCP tools are available
        has_github_tools: Whether GitHub MCP tools are available for cross-repo context
        reviewer_instructions: Custom instructions from @claude comment

    Returns:
        Tuple of (static_content, dynamic_content) for prompt caching optimization.
        Static content includes role, guidelines, CLAUDE.md, and tech-specific guidelines (cacheable).
        Dynamic content includes PR context and diff (not cacheable).
    """
    # Detect tech stack for specialized guidance
    tech_stack = detect_tech_stack(files)
    tech_guidelines = get_tech_stack_guidelines(tech_stack)

    print(f"🔧 Detected tech stack: {tech_stack}")
    if tech_guidelines:
        print(f"✓ Added {tech_stack}-specific review guidelines")

    # Read shared review standards
    standards_path = Path(__file__).parent.parent / "docs" / "review-standards.md"
    review_standards = ""
    if standards_path.exists():
        review_standards = standards_path.read_text()
        print("✓ Loaded shared review standards")

    # Build conditional Linear instructions based on tool availability
    if has_linear_tools and linear_id:
        linear_instructions = """If a Linear issue is referenced:
- **Use your Linear tools** to fetch issue details
- Check issue description and acceptance criteria
- Review comments for additional requirements
- Validate PR changes align with stated requirements
- Check for related issues that might provide context

### Linear Issue Quality Assessment (Advisory)
When you fetch a Linear issue, also assess its quality and provide **advisory feedback** (not blocking):

**Check for**:
- Clear, measurable acceptance criteria
- Technical specifications (API contracts, data models, error handling)
- Edge cases documented
- Security/compliance requirements mentioned
- Performance requirements specified

**If issue quality is poor**, include this in your "Alignment with Linear Requirements" section:
```
⚠️ **Linear Issue Quality**: This issue could be improved with:
- Specific acceptance criteria (e.g., "handles 10K records", "loads in <2s")
- Edge case documentation (empty states, error scenarios)
- Security requirements (authentication, data validation)

This is advisory only - the review proceeds based on what IS documented.
```

**Note**: This helps improve issue quality over time for better requirement validation in future PRs."""
        linear_usage_guideline = "- **Use Linear tools first** if an issue is referenced - get full context before reviewing code\n"
    else:
        linear_instructions = """Linear tools are not available for this review.

**IMPORTANT**: Do NOT simulate tool usage or include tool markup (like `<tool_name>...</tool_name>`) in your response.

Review based on:
- PR description and code changes
- Repository guidelines (CLAUDE.md)
- General best practices

If a Linear issue is mentioned in the PR title, note its ID but proceed without fetching details."""
        linear_usage_guideline = ""

    # Build conditional GitHub instructions for cross-repository context
    if has_github_tools:
        github_instructions = """
## Cross-Repository Context (GitHub MCP)

You have GitHub MCP tools (prefixed with `github_`) for fetching code from Quantivly repositories:
- `github_get_file_contents` - Read specific files from any Quantivly repo
- `github_search_code` - Search for code patterns across organization repos
- `github_get_commit` - Get commit details for context
- `github_list_commits` - List recent commits in a repository

**When to use cross-repo context**:
1. **`sre-core` GraphQL changes** → Check `sre-ui` queries and TypeScript types
2. **`sre-sdk` changes** → Check consumers: `sre-core`, `sre-event-bridge`
3. **`quantivly-sdk` changes** → Check consumers: `box`, `ptbi`, `healthcheck`
4. **`auto-conf` template changes** → Verify stack file rendering

**Quantivly repository architecture** (two ecosystems with separate SDKs):

*hub* (healthcare analytics product - superproject):
- `sre-core` - Django backend (GraphQL, plugins) — depends on `sre-sdk`
- `sre-ui` - Next.js frontend — consumes `sre-core` GraphQL
- `sre-event-bridge` - WAMP→REST bridge — depends on `sre-sdk`
- `sre-sdk` - Python SDK for hub services

*platform* (quantivly-dockers - DICOM/RIS backbone):
- `auto-conf` - Jinja2 stack generator (also generates hub deployment in `modules/quantivly/sre/`)
- `box` - DICOM harmonization (GE/Philips/Siemens), RIS — depends on `quantivly-sdk`
- `ptbi` - DICOM networking (Python+Java/dcm4che) — depends on `quantivly-sdk`
- `quantivly-sdk` - Python SDK for platform services

**Guidelines**:
- Only access repositories within the `quantivly` organization
- Use cross-repo context when reviewing changes to shared/exported code
- Validate that API contracts are maintained across repositories
- Don't use GitHub tools for files already in the PR diff
"""
        github_usage_guideline = "- **Use GitHub tools** for cross-repo validation when reviewing shared components or APIs\n"
    else:
        github_instructions = ""
        github_usage_guideline = ""

    # Build static content (cacheable - doesn't change between reviews)
    static_content = f"""# Role
You are an expert code reviewer for Quantivly, a healthcare technology company building HIPAA-compliant analytics software.

# Review Standards
These are the organization-wide code review standards. Follow these for consistency across all reviews.

{review_standards}

# Repository Guidelines
{claude_md}

{tech_guidelines}

# Your Task

Conduct a comprehensive code review with the following priorities:

## Review Approach: Exhaustive First Pass

**Goal**: Provide complete, thorough feedback in this FIRST review to minimize developer round-trips.

**Be Exhaustive**:
- Check **EVERY file** for issues (don't skip similar patterns)
- List **ALL edge cases**, not just representative examples
- Flag **ALL instances** of a pattern violation (not just the first occurrence)
- Identify **EVERY untested code path**
- Validate **EVERY acceptance criterion** from Linear (if applicable)
- Provide **specific, actionable fixes** with code examples where helpful

**Why This Matters**: Developers will address all issues at once rather than iteratively. A thorough first pass saves 10-15 minutes per PR and reduces frustration.

## 1. Linear Requirement Validation (If Applicable)
{linear_instructions}
{github_instructions}
## 2. Security Analysis (CRITICAL)
- OWASP Top 10 vulnerabilities
- HIPAA compliance considerations (PHI handling, access controls, audit logging)
- SQL injection, XSS, command injection
- Credential leaks and secrets exposure
- Dependency vulnerabilities
- Authentication and authorization flaws
- Input validation and sanitization

## 3. Logic Errors and Bugs
- Incorrect implementations vs. requirements
- Edge cases not handled (null, empty, boundary values)
- Race conditions and concurrency issues
- Off-by-one errors
- Error propagation and handling
- Data consistency issues

## 4. Code Quality and Maintainability
- Readability and clarity
- Function complexity (cyclomatic complexity)
- Code duplication (DRY principle)
- Naming conventions
- SOLID principles adherence
- Design pattern appropriateness
- Documentation and comments

## 5. Testing Completeness
- Test coverage for new/changed code
- Edge cases tested
- Integration test gaps
- Test quality (assertions, mocking)
- Pytest/Jest conventions followed
- Test maintainability

## 6. Performance
- Algorithmic efficiency (O(n) complexity)
- Database query optimization (N+1 queries)
- Memory usage patterns
- Caching opportunities
- Unnecessary computations
- Resource cleanup (connections, file handles)

# Output Format

Provide your review in this exact structure:

## Summary
[2-3 sentence overview of the PR and overall assessment]

## Alignment with Linear Requirements
[If Linear issue referenced, use tools to fetch and assess alignment]
[If no Linear issue, state: "No Linear issue to validate against"]

## Critical Issues (Must Fix Before Merge)
[List ONLY if found. Each issue must include:]
1. **[Category]**: [Specific description]
   - **Location**: `file.py:123-145`
   - **Finding**: [What is wrong]
   - **Risk**: [Why this matters]
   - **Fix**: [Concrete recommendation]
   - **Severity**: CRITICAL | HIGH

[If none found, state: "No critical issues identified"]

## Suggestions (Should Consider)
[List improvements that would enhance code quality but aren't blockers]
1. **[Category]**: [Description]
   - **Location**: `file.py:456`
   - **Current**: [What exists]
   - **Suggested**: [Alternative approach]
   - **Benefit**: [Why this helps]

[If none, state: "No significant suggestions"]

## Positive Observations
[List 2-3 good patterns or practices observed]
- [Specific positive finding with location]

## Testing Assessment
- **Coverage**: [Assessment of test completeness]
- **Edge Cases**: [Which edge cases are/aren't tested]
- **Quality**: [Test quality observations]

## Recommendation
**[APPROVE | REQUEST_CHANGES | COMMENT]**

[1-2 sentence justification]

# Guidelines

{linear_usage_guideline}{github_usage_guideline}- Be specific with file paths and line numbers (`file.py:123` or `file.py:123-145`)
- Prioritize security and correctness over style
- Reference Linear requirements explicitly when applicable
- Explain WHY something is an issue, not just WHAT
- Provide actionable, concrete recommendations
- Acknowledge good patterns and practices
- Consider healthcare/HIPAA context (PHI, security, audit trails)
- Respect existing code conventions from CLAUDE.md
- Don't flag formatting/linting (pre-commit hooks handle this)
- Focus on logic and design, not style
- Be thorough but concise
- Use severity labels appropriately (CRITICAL = security/data loss, HIGH = bugs/logic errors)
"""

    # Build PR metadata section
    pr_section = f"""**Repository**: {pr.base.repo.full_name}
**PR**: #{pr.number} - {pr.title}
**Author**: @{pr.user.login}
**Branch**: {pr.head.ref} → {pr.base.ref}
**Files Changed**: {pr.changed_files}
**Additions**: +{pr.additions} | **Deletions**: -{pr.deletions}
"""

    # Build Linear requirement note
    linear_section = ""
    if linear_id:
        linear_section = f"""
# Linear Issue Reference

The PR references Linear issue **{linear_id}**.

**You have access to Linear tools** - use them to fetch issue details, related issues, comments, and any other context needed to validate this PR against requirements.

Suggested approach:
1. Use Linear tools to fetch issue {linear_id} details
2. Check issue description and acceptance criteria
3. Review recent comments for additional context
4. Validate PR changes align with requirements
"""
    else:
        linear_section = """
# Linear Issue Reference

No Linear issue ID found in PR title. Proceeding with code review without requirement validation.
"""

    # Build reviewer instructions section if provided
    instructions_section = ""
    if reviewer_instructions:
        instructions_section = f"""
# Reviewer Instructions

The reviewer who triggered this review provided the following specific instructions:

> {reviewer_instructions}

**Please prioritize these instructions** in addition to the standard review criteria above.
"""

    # Build dynamic content (not cacheable - changes for each PR)
    dynamic_content = f"""# PR Context
{pr_section}

{linear_section}
{instructions_section}
# Code Changes
```diff
{diff}
```

Please conduct your review according to the guidelines and priorities above.
"""

    return static_content, dynamic_content


@asynccontextmanager
async def multi_mcp_sessions(
    linear_api_key: str | None,
    github_mcp_token: str | None,
) -> AsyncGenerator[tuple[list[dict[str, Any]], dict[str, tuple[ClientSession, str]]], None]:
    """
    Connect to multiple MCP servers and yield combined tools with routing info.

    This context manager handles connections to both Linear and GitHub MCP servers,
    combining their tools into a single list while maintaining routing information
    for tool execution.

    Args:
        linear_api_key: Linear API key for Linear MCP server (optional)
        github_mcp_token: GitHub token for GitHub MCP server (optional)

    Yields:
        Tuple of (all_tools, tool_router) where:
        - all_tools: Combined list of tools in Anthropic format
        - tool_router: Dict mapping tool_name -> (session, original_name)
    """
    all_tools: list[dict[str, Any]] = []
    tool_router: dict[str, tuple[ClientSession, str]] = {}

    # Track MCP server stats
    linear_tool_count = 0
    github_tool_count = 0

    # Check if HTTP client is available
    if streamablehttp_client is None:
        print("⚠️  MCP HTTP client not available in installed mcp package")
        yield all_tools, tool_router
        return

    # Use a list to track sessions so we can clean them up
    sessions_to_close: list[tuple[Any, ClientSession]] = []

    try:
        # Connect to Linear MCP if API key provided
        if linear_api_key:
            try:
                print(f"🔗 Connecting to Linear MCP server at {LINEAR_MCP_URL}...")
                linear_ctx = await streamablehttp_client(
                    LINEAR_MCP_URL,
                    headers={"Authorization": f"Bearer {linear_api_key}"},
                ).__aenter__()

                linear_session = ClientSession(linear_ctx[0], linear_ctx[1])
                await linear_session.__aenter__()
                sessions_to_close.append((linear_ctx, linear_session))

                await linear_session.initialize()
                linear_tools_response = await linear_session.list_tools()

                # Convert and add Linear tools (no prefix - existing behavior)
                linear_tools = convert_mcp_tools_to_anthropic_format(
                    linear_tools_response.tools
                )
                for tool in linear_tools:
                    all_tools.append(tool)
                    tool_router[tool["name"]] = (linear_session, tool["name"])
                    linear_tool_count += 1

                print(f"✓ Linear MCP: {linear_tool_count} tools")
            except (asyncio.TimeoutError, ConnectionError, OSError) as e:
                print(f"⚠️  Linear MCP connection failed: {e}")
            except Exception as e:
                print(f"⚠️  Linear MCP error: {e}")

        # Connect to GitHub MCP if token provided
        if github_mcp_token:
            try:
                print(f"🔗 Connecting to GitHub MCP server at {GITHUB_MCP_URL}...")
                github_ctx = await streamablehttp_client(
                    GITHUB_MCP_URL,
                    headers={"Authorization": f"Bearer {github_mcp_token}"},
                ).__aenter__()

                github_session = ClientSession(github_ctx[0], github_ctx[1])
                await github_session.__aenter__()
                sessions_to_close.append((github_ctx, github_session))

                await github_session.initialize()
                github_tools_response = await github_session.list_tools()

                # Convert and add GitHub tools (with prefix and filter)
                github_tools = convert_mcp_tools_to_anthropic_format(
                    github_tools_response.tools,
                    prefix=GITHUB_TOOL_PREFIX,
                    filter_set=GITHUB_ESSENTIAL_TOOLS,
                )
                for tool in github_tools:
                    all_tools.append(tool)
                    # Strip prefix to get original name for MCP call
                    original_name = tool["name"][len(GITHUB_TOOL_PREFIX):]
                    tool_router[tool["name"]] = (github_session, original_name)
                    github_tool_count += 1

                print(f"✓ GitHub MCP: {github_tool_count} tools (filtered from {len(github_tools_response.tools)})")
            except (asyncio.TimeoutError, ConnectionError, OSError) as e:
                print(f"⚠️  GitHub MCP connection failed: {e}")
            except Exception as e:
                print(f"⚠️  GitHub MCP error: {e}")

        yield all_tools, tool_router

    finally:
        # Clean up sessions in reverse order
        for ctx, session in reversed(sessions_to_close):
            try:
                await session.__aexit__(None, None, None)
            except Exception:
                pass
            try:
                await ctx.__aexit__(None, None, None)
            except Exception:
                pass


async def call_claude_with_mcp(
    static_content: str,
    dynamic_content: str,
    anthropic_key: str,
    linear_api_key: str | None,
    github_mcp_token: str | None = None,
) -> tuple[str, Any, bool, bool, int, dict[str, Any] | None]:
    """
    Call Claude API with MCP tools (Linear and GitHub) available and prompt caching.

    This function:
    1. Connects to Linear MCP server (for issue context)
    2. Connects to GitHub MCP server (for cross-repo code context)
    3. Gets available tools from both servers
    4. Calls Claude with tools available and prompt caching enabled
    5. Handles tool_use conversation loop with routing
    6. Returns the final review text and response object for metrics

    Prompt caching optimization:
    - Static content (role, guidelines, CLAUDE.md) is cached (5min TTL)
    - Reduces cost by 35% and latency by 85% for cached content
    - Cache automatically refreshes on each use (free)

    Args:
        static_content: Cacheable prompt content (role, guidelines)
        dynamic_content: PR-specific content (not cached)
        anthropic_key: Anthropic API key
        linear_api_key: Linear API key for Linear MCP server (optional)
        github_mcp_token: GitHub token for GitHub MCP server (optional)

    Returns:
        Tuple of (review_text, final_response, had_linear_context, had_github_context,
                  tool_call_count, linear_issue_data)
            - review_text: The generated review content
            - final_response: The Anthropic API response object (for metrics)
            - had_linear_context: Whether Linear tools were available
            - had_github_context: Whether GitHub tools were available
            - tool_call_count: Number of tool calls made during review
            - linear_issue_data: Linear issue details if fetched (dict with id, title, state)
    """
    # Prepare content blocks with caching
    initial_content = [
        {
            "type": "text",
            "text": static_content,
            "cache_control": {"type": "ephemeral"},  # Cache static instructions
        },
        {
            "type": "text",
            "text": dynamic_content,  # Dynamic PR context - not cached
        },
    ]

    # Check if we have any MCP credentials
    if not linear_api_key and not github_mcp_token:
        print("⚠️  No MCP credentials provided, proceeding without tools")
        # Call Claude without tools
        client = anthropic.Anthropic(api_key=anthropic_key)
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": initial_content}],
        )

        # Log cache metrics if available
        if hasattr(message.usage, "cache_creation_input_tokens"):
            print(f"💾 Cache created: {message.usage.cache_creation_input_tokens} tokens")
        if hasattr(message.usage, "cache_read_input_tokens"):
            print(f"⚡ Cache hit: {message.usage.cache_read_input_tokens} tokens")

        review_text = strip_tool_simulation_markup(message.content[0].text)
        return review_text, message, False, False, 0, None

    try:
        # Connect to MCP servers using multi-session context manager
        async with multi_mcp_sessions(linear_api_key, github_mcp_token) as (tools, tool_router):
            # Track which MCP servers were connected
            had_linear = any(not name.startswith(GITHUB_TOOL_PREFIX) for name in tool_router)
            had_github = any(name.startswith(GITHUB_TOOL_PREFIX) for name in tool_router)

            if not tools:
                print("⚠️  No MCP tools available, proceeding without tools")
                client = anthropic.Anthropic(api_key=anthropic_key)
                message = client.messages.create(
                    model=CLAUDE_MODEL,
                    max_tokens=MAX_TOKENS,
                    messages=[{"role": "user", "content": initial_content}],
                )
                review_text = strip_tool_simulation_markup(message.content[0].text)
                return review_text, message, False, False, 0, None

            print(f"✓ Total MCP tools available: {len(tools)}")

            # Initialize Anthropic client
            client = anthropic.Anthropic(api_key=anthropic_key)

            # Start conversation with cached content
            messages = [{"role": "user", "content": initial_content}]

            # Track tool usage and Linear issue data for metrics
            tool_call_count = 0
            linear_issue_data: dict[str, Any] | None = None

            # Conversation loop to handle tool use
            iteration = 0
            max_iterations = 10  # Prevent infinite loops

            while iteration < max_iterations:
                iteration += 1
                print(f"⏳ Claude API call (iteration {iteration})...")

                response = client.messages.create(
                    model=CLAUDE_MODEL,
                    max_tokens=MAX_TOKENS,
                    tools=tools,
                    messages=messages,
                )

                # Log token usage including cache metrics
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens
                print(f"📊 Tokens: {input_tokens} input, {output_tokens} output")

                # Log cache performance
                if hasattr(response.usage, "cache_creation_input_tokens"):
                    cache_created = response.usage.cache_creation_input_tokens
                    if cache_created > 0:
                        print(f"💾 Cache created: {cache_created} tokens")
                if hasattr(response.usage, "cache_read_input_tokens"):
                    cache_hit = response.usage.cache_read_input_tokens
                    if cache_hit > 0:
                        print(f"⚡ Cache hit: {cache_hit} tokens (saved ~85% latency)")

                # Check if we're done
                if response.stop_reason == "end_turn":
                    # Extract final review text
                    review_text = ""
                    for block in response.content:
                        if hasattr(block, "text"):
                            review_text += block.text
                    review_text = strip_tool_simulation_markup(review_text)
                    print("✓ Review completed")
                    print(f"📊 Total tool calls: {tool_call_count}")
                    return review_text, response, had_linear, had_github, tool_call_count, linear_issue_data

                # Handle tool use
                if response.stop_reason == "tool_use":
                    # Add assistant's response to messages
                    messages.append({"role": "assistant", "content": response.content})

                    # Process each tool use
                    tool_results = []
                    for block in response.content:
                        if block.type == "tool_use":
                            tool_name = block.name
                            print(f"🔧 Executing tool: {tool_name}")
                            tool_call_count += 1  # Track tool usage

                            # Route tool call to appropriate MCP session
                            if tool_name not in tool_router:
                                print(f"⚠️  Unknown tool: {tool_name}")
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": f"Unknown tool: {tool_name}",
                                    "is_error": True,
                                })
                                continue

                            session, original_name = tool_router[tool_name]

                            # Call the tool via MCP
                            try:
                                result = await session.call_tool(original_name, block.input)
                                print(f"✓ Tool {tool_name} executed successfully")

                                # Capture Linear issue data if this is get_issue
                                if original_name == "get_issue" and linear_issue_data is None:
                                    try:
                                        # Parse the result to extract issue details
                                        issue_content = result.content[0].text if result.content else "{}"
                                        issue_json = json.loads(issue_content)
                                        linear_issue_data = {
                                            "id": issue_json.get("identifier", ""),
                                            "title": issue_json.get("title", ""),
                                            "state": issue_json.get("state", {}).get("name", ""),
                                            "description": (issue_json.get("description", "") or "")[:200],
                                        }
                                        print(f"📋 Captured Linear issue: {linear_issue_data['id']} - {linear_issue_data['title']}")
                                    except (json.JSONDecodeError, KeyError, IndexError, AttributeError) as e:
                                        print(f"⚠️  Could not parse Linear issue data: {e}")

                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": result.content,
                                })
                            except (asyncio.TimeoutError, OSError, RuntimeError) as e:
                                # MCP tool execution failures (connection, timeout, runtime errors)
                                print(f"⚠️  Tool {tool_name} failed: {e}")
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": f"Error executing tool: {str(e)}",
                                    "is_error": True,
                                })

                    # Add tool results to conversation
                    messages.append({"role": "user", "content": tool_results})
                    continue

                # Unknown stop reason
                print(f"⚠️  Unexpected stop reason: {response.stop_reason}")
                # Extract whatever text we have
                review_text = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        review_text += block.text
                review_text = strip_tool_simulation_markup(review_text or "Review completed with unexpected stop reason")
                return (
                    review_text,
                    response,
                    had_linear,
                    had_github,
                    tool_call_count,
                    linear_issue_data,
                )

            # Max iterations reached
            print("⚠️  Max iterations reached in conversation loop")
            return "Review incomplete: maximum conversation turns exceeded", response, had_linear, had_github, tool_call_count, linear_issue_data

    except (asyncio.TimeoutError, ConnectionError, FileNotFoundError, OSError) as e:
        # MCP connection failures (timeout, server not found, connection issues)
        print(f"❌ MCP integration error: {e}")
        print("⚠️  Falling back to review without MCP tools")

        # Fallback: call Claude without tools but still use caching
        client = anthropic.Anthropic(api_key=anthropic_key)
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": initial_content}],
        )

        # Log cache metrics
        if hasattr(message.usage, "cache_read_input_tokens"):
            cache_hit = message.usage.cache_read_input_tokens
            if cache_hit > 0:
                print(f"⚡ Cache hit: {cache_hit} tokens")

        review_text = strip_tool_simulation_markup(message.content[0].text)
        return review_text, message, False, False, 0, None  # No MCP context (fallback)


def log_token_metrics(response: Any, pr_number: int, tool_call_count: int = 0) -> float:
    """
    Log detailed token usage for cost analysis and budget tracking.

    Pricing (Claude Sonnet 4.5):
    - Input: $3.00/M tokens
    - Output: $15.00/M tokens
    - Cached input: $0.30/M tokens (90% cheaper)

    Returns:
        Total review cost in dollars
    """
    usage = response.usage
    input_tokens = usage.input_tokens
    output_tokens = usage.output_tokens

    # Calculate costs
    input_cost = (input_tokens / 1_000_000) * 3.00
    output_cost = (output_tokens / 1_000_000) * 15.00

    # Check for cache metrics
    cache_created = getattr(usage, "cache_creation_input_tokens", 0)
    cache_hit = getattr(usage, "cache_read_input_tokens", 0)
    cache_savings = 0.0

    if cache_hit > 0:
        # Cached tokens cost $0.30/M instead of $3.00/M (90% cheaper)
        cache_savings = (cache_hit / 1_000_000) * (3.00 - 0.30)

    total_cost = input_cost + output_cost - cache_savings

    # Log to console
    print(f"\n📊 Token Usage Summary:")
    print(f"  Input: {input_tokens:,} tokens (${input_cost:.4f})")
    print(f"  Output: {output_tokens:,} tokens (${output_cost:.4f})")
    if cache_created > 0:
        print(f"  Cache created: {cache_created:,} tokens")
    if cache_hit > 0:
        print(f"  Cache hit: {cache_hit:,} tokens (saved ${cache_savings:.4f})")
    print(f"  Total cost: ${total_cost:.4f}")

    # Add to GitHub Actions summary if available
    summary_file = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_file:
        try:
            with open(summary_file, "a") as f:
                f.write(f"\n### 📊 Token Metrics (PR #{pr_number})\n\n")
                f.write(f"| Metric | Value | Cost |\n")
                f.write(f"|--------|-------|------|\n")
                f.write(f"| Input tokens | {input_tokens:,} | ${input_cost:.4f} |\n")
                f.write(f"| Output tokens | {output_tokens:,} | ${output_cost:.4f} |\n")
                if cache_created > 0:
                    f.write(f"| Cache created | {cache_created:,} | - |\n")
                if cache_hit > 0:
                    f.write(
                        f"| Cache hit | {cache_hit:,} | -${cache_savings:.4f} (saved) |\n"
                    )
                f.write(f"| **Total** | **{input_tokens + output_tokens:,}** | **${total_cost:.4f}** |\n")

                # Add tool usage if applicable
                if tool_call_count > 0:
                    f.write(f"| Linear queries | {tool_call_count} | - |\n")
                f.write("\n")

                # Budget alert and performance notes
                if total_cost > 0.10:
                    f.write(
                        f"⚠️ **Cost Alert**: Review exceeded $0.10 budget (${total_cost:.4f})\n\n"
                    )
                elif cache_hit > 0:
                    cache_pct = int((cache_savings / (input_cost + cache_savings)) * 100) if (input_cost + cache_savings) > 0 else 0
                    f.write(
                        f"⚡ **Cache Performance**: Saved ${cache_savings:.4f} ({cache_pct}% cost reduction)\n\n"
                    )
        except Exception as e:
            print(f"⚠️  Failed to write metrics to GitHub summary: {e}")

    return total_cost


def post_review_comment(
    github: Github,
    repo_full_name: str,
    pr_number: int,
    review_text: str,
    commenter: str,
    had_linear_context: bool = True,
    had_github_context: bool = False,
    tool_call_count: int = 0,
    linear_issue_data: dict[str, Any] | None = None,
    review_cost: float = 0.0,
) -> None:
    """Post formatted review comment to PR with MCP context status and metrics."""
    repo = github.get_repo(repo_full_name)
    pr = repo.get_pull(pr_number)

    # Format final comment with metadata
    comment_body = f"""## 🤖 Claude Code Review

{review_text}

---
"""

    # Add Linear context warning if not available (keep the warning, just remove the section)
    if not had_linear_context:
        comment_body += """⚠️ **Linear Context**: Unable to fetch Linear issue context. Review performed without requirement validation.

**Possible reasons**:
- PR title doesn't include Linear ID (format: `AAA-#### Description`)
- Linear MCP server unavailable
- Issue doesn't exist or is inaccessible

**Recommendation**: Verify PR title format and ensure Linear issue is linked.

---
"""

    # Build minimalist footer with MCP context info, tool usage, and cost
    footer_parts = [f"Triggered by @{commenter}", "Powered by Claude Sonnet 4.5"]

    # Add Linear issue link if available
    if linear_issue_data:
        issue_id = linear_issue_data.get('id', '')
        issue_url = f"https://linear.app/quantivly/issue/{issue_id.lower()}"
        query_text = f"{tool_call_count} {'query' if tool_call_count == 1 else 'queries'}" if tool_call_count > 0 else "validated"
        footer_parts.append(f"Reviewed [{issue_id}]({issue_url}) ({query_text})")
    elif tool_call_count > 0:
        footer_parts.append(f"Validated using {tool_call_count} {'query' if tool_call_count == 1 else 'queries'}")

    # Indicate GitHub cross-repo context was available
    if had_github_context:
        footer_parts.append("Cross-repo context enabled")

    # Add cost if available
    if review_cost > 0:
        footer_parts.append(f"Cost: ${review_cost:.2f}")

    footer_parts.append("[Learn more](https://github.com/quantivly/.github/blob/master/docs/claude-integration-guide.md)")

    comment_body += f"""<sub>{' | '.join(footer_parts)}</sub>
"""

    try:
        pr.create_issue_comment(comment_body)
        print(f"✓ Posted review comment to PR #{pr_number}")
    except GithubException as e:
        print(f"❌ Failed to post comment: {e}")
        raise


async def async_main(args: argparse.Namespace) -> int:
    """Main async orchestration function."""
    # Get environment variables
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    linear_key = os.getenv("LINEAR_API_KEY", "")
    github_token = os.getenv("GITHUB_TOKEN")
    # GitHub MCP token for cross-repository context (optional)
    # Falls back to GITHUB_TOKEN if GITHUB_MCP_TOKEN not set
    github_mcp_token = os.getenv("GITHUB_MCP_TOKEN") or github_token

    if not anthropic_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return 1

    if not github_token:
        print("❌ GITHUB_TOKEN not set")
        return 1

    repo_full_name = f"{args.repo_owner}/{args.repo_name}"
    print(f"🔍 Reviewing PR #{args.pr_number} in {repo_full_name}")

    try:
        # Initialize GitHub client
        github = Github(github_token)
        repo = github.get_repo(repo_full_name)
        pr = repo.get_pull(args.pr_number)

        print(f"✓ PR Title: {pr.title}")
        print(f"✓ Author: @{pr.user.login}")
        print(f"✓ Files changed: {pr.changed_files}")

        # Extract Linear issue ID
        linear_id = extract_linear_id(pr.title)
        if linear_id:
            print(f"📋 Linear issue: {linear_id}")
        else:
            print("⚠️  No Linear issue ID in PR title")

        # Read repository CLAUDE.md
        repo_path = Path.cwd()
        claude_md = read_claude_md(repo_path)

        # Fetch PR diff
        print("📥 Fetching PR diff...")
        files_paginated = pr.get_files()  # PyGithub PaginatedList - iteration auto-paginates

        # Convert to list for tech stack detection (need to iterate twice)
        files = list(files_paginated)
        diff_parts = []

        for file in files:  # Iterating handles pagination automatically (all pages fetched)
            if file.patch:
                patch = file.patch
                # Truncate very large diffs per file
                if len(patch.split("\n")) > MAX_FILE_CONTENT_LINES:
                    patch = truncate_diff(patch, MAX_FILE_CONTENT_LINES)
                diff_parts.append(f"--- a/{file.filename}\n+++ b/{file.filename}\n{patch}")

        full_diff = "\n\n".join(diff_parts)
        full_diff = truncate_diff(full_diff, MAX_DIFF_LINES)
        print(f"✓ Collected diff ({len(full_diff)} characters)")

        # Determine if MCP tools will be available
        # (using hosted HTTP MCP servers - no npx needed)
        has_linear_tools = bool(linear_key)
        has_github_tools = bool(github_mcp_token)

        if has_linear_tools:
            print("✓ Linear API key found, Linear MCP tools will be available")
        else:
            print("⚠️  No LINEAR_API_KEY, Linear MCP will not be available")

        if has_github_tools:
            print("✓ GitHub MCP token found, cross-repo context will be available")
        else:
            print("⚠️  No GITHUB_MCP_TOKEN, cross-repo context will not be available")

        # Extract reviewer instructions from comment body
        reviewer_instructions = extract_reviewer_instructions(args.comment_body)
        if reviewer_instructions:
            print(f"📋 Reviewer instructions: {reviewer_instructions[:100]}{'...' if len(reviewer_instructions) > 100 else ''}")

        # Build review prompt with caching optimization
        print("📝 Building review prompt...")
        static_content, dynamic_content = build_review_prompt(
            pr, files, linear_id, claude_md, full_diff,
            has_linear_tools=has_linear_tools,
            has_github_tools=has_github_tools,
            reviewer_instructions=reviewer_instructions,
        )

        # Call Claude API with MCP integration and prompt caching
        (
            review_text,
            final_response,
            had_linear_context,
            had_github_context,
            tool_call_count,
            linear_issue_data,
        ) = await call_claude_with_mcp(
            static_content, dynamic_content, anthropic_key, linear_key, github_mcp_token
        )

        # Log token usage and cost metrics
        review_cost = log_token_metrics(final_response, args.pr_number, tool_call_count)

        # Post review comment with MCP context status and metrics
        post_review_comment(
            github, repo_full_name, args.pr_number, review_text, args.commenter,
            had_linear_context, had_github_context, tool_call_count, linear_issue_data, review_cost
        )

        print("✅ Review completed successfully")
        return 0

    except Exception as e:
        print(f"❌ Review failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


def main() -> int:
    """Entry point - parse args and run async main."""
    parser = argparse.ArgumentParser(description="Claude PR Review with MCP")
    parser.add_argument("--pr-number", type=int, required=True)
    parser.add_argument("--repo-owner", required=True)
    parser.add_argument("--repo-name", required=True)
    parser.add_argument("--comment-id", required=True)
    parser.add_argument("--commenter", required=True)
    parser.add_argument(
        "--comment-body",
        default="",
        help="Full comment body for extracting reviewer instructions",
    )
    args = parser.parse_args()

    # Run async main
    return asyncio.run(async_main(args))


if __name__ == "__main__":
    sys.exit(main())
