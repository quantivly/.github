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
from pathlib import Path
from typing import Any

import anthropic
from github import Github, GithubException
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Constants
MAX_DIFF_LINES = 2000  # Limit diff size to control token usage
MAX_FILE_CONTENT_LINES = 500  # Limit individual file content
CLAUDE_MODEL = "claude-sonnet-4-5-20250929"
MAX_TOKENS = 8000


def extract_linear_id(pr_title: str) -> str | None:
    """Extract Linear issue ID from PR title (format: AAA-#### ...)."""
    match = re.match(r"^([A-Z]+-\d+)", pr_title)
    return match.group(1) if match else None


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


def convert_mcp_tools_to_anthropic_format(mcp_tools: list[Any]) -> list[dict[str, Any]]:
    """Convert MCP tool definitions to Anthropic API tool format."""
    anthropic_tools = []
    for tool in mcp_tools:
        anthropic_tool = {
            "name": tool.name,
            "description": tool.description or "No description provided",
            "input_schema": tool.inputSchema if hasattr(tool, "inputSchema") else {},
        }
        anthropic_tools.append(anthropic_tool)
    return anthropic_tools


def build_review_prompt(
    pr: Any,
    linear_id: str | None,
    claude_md: str,
    diff: str,
) -> str:
    """Construct comprehensive review prompt with all context."""
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

    # Construct full prompt
    prompt = f"""# Role
You are an expert code reviewer for Quantivly, a healthcare technology company building HIPAA-compliant analytics software.

# PR Context
{pr_section}

{linear_section}

# Repository Guidelines
{claude_md}

# Code Changes
```diff
{diff}
```

# Your Task

Conduct a comprehensive code review with the following priorities:

## 1. Linear Requirement Validation (If Applicable)
If a Linear issue is referenced:
- **Use your Linear tools** to fetch issue details ({linear_id if linear_id else "N/A"})
- Check issue description and acceptance criteria
- Review comments for additional requirements
- Validate PR changes align with stated requirements
- Check for related issues that might provide context

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
{f"[Use Linear tools to fetch {linear_id} and assess alignment]" if linear_id else "[No Linear issue to validate against]"}

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

- **Use Linear tools first** if an issue is referenced - get full context before reviewing code
- Be specific with file paths and line numbers (`file.py:123` or `file.py:123-145`)
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
    return prompt


async def call_claude_with_mcp(
    prompt: str,
    anthropic_key: str,
    linear_api_key: str | None,
) -> str:
    """
    Call Claude API with Linear MCP tools available.

    This function:
    1. Starts the Linear MCP server
    2. Connects as an MCP client
    3. Gets available Linear tools
    4. Calls Claude with tools available
    5. Handles tool_use conversation loop
    6. Returns the final review text
    """
    if not linear_api_key:
        print("⚠️  No LINEAR_API_KEY provided, proceeding without Linear tools")
        # Call Claude without tools
        client = anthropic.Anthropic(api_key=anthropic_key)
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    # Set up MCP server parameters
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-linear"],
        env={"LINEAR_API_KEY": linear_api_key},
    )

    print("🔗 Connecting to Linear MCP server...")

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize MCP connection
                await session.initialize()
                print("✓ Connected to Linear MCP server")

                # Get available tools
                tools_response = await session.list_tools()
                tools = convert_mcp_tools_to_anthropic_format(tools_response.tools)
                print(f"✓ Loaded {len(tools)} Linear tools")

                # Initialize Anthropic client
                client = anthropic.Anthropic(api_key=anthropic_key)

                # Start conversation
                messages = [{"role": "user", "content": prompt}]

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

                    # Log token usage
                    input_tokens = response.usage.input_tokens
                    output_tokens = response.usage.output_tokens
                    print(f"📊 Tokens: {input_tokens} input, {output_tokens} output")

                    # Check if we're done
                    if response.stop_reason == "end_turn":
                        # Extract final review text
                        review_text = ""
                        for block in response.content:
                            if hasattr(block, "text"):
                                review_text += block.text
                        print("✓ Review completed")
                        return review_text

                    # Handle tool use
                    if response.stop_reason == "tool_use":
                        # Add assistant's response to messages
                        messages.append({"role": "assistant", "content": response.content})

                        # Process each tool use
                        tool_results = []
                        for block in response.content:
                            if block.type == "tool_use":
                                print(f"🔧 Executing tool: {block.name}")

                                # Call the tool via MCP
                                try:
                                    result = await session.call_tool(block.name, block.input)
                                    print(f"✓ Tool {block.name} executed successfully")

                                    tool_results.append({
                                        "type": "tool_result",
                                        "tool_use_id": block.id,
                                        "content": result.content,
                                    })
                                except Exception as e:
                                    print(f"⚠️  Tool {block.name} failed: {e}")
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
                    return review_text or "Review completed with unexpected stop reason"

                # Max iterations reached
                print("⚠️  Max iterations reached in conversation loop")
                return "Review incomplete: maximum conversation turns exceeded"

    except Exception as e:
        print(f"❌ MCP integration error: {e}")
        print("⚠️  Falling back to review without Linear tools")

        # Fallback: call Claude without tools
        client = anthropic.Anthropic(api_key=anthropic_key)
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text


def post_review_comment(
    github: Github,
    repo_full_name: str,
    pr_number: int,
    review_text: str,
    commenter: str,
) -> None:
    """Post formatted review comment to PR."""
    repo = github.get_repo(repo_full_name)
    pr = repo.get_pull(pr_number)

    # Format final comment with metadata
    comment_body = f"""## 🤖 Claude Code Review

{review_text}

---
<sub>Triggered by @{commenter} | Powered by Claude Sonnet 4.5 with Linear MCP | [Learn more](https://github.com/quantivly/.github/blob/master/docs/claude-integration-guide.md)</sub>
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
        files = pr.get_files()
        diff_parts = []

        for file in files:
            if file.patch:
                patch = file.patch
                # Truncate very large diffs per file
                if len(patch.split("\n")) > MAX_FILE_CONTENT_LINES:
                    patch = truncate_diff(patch, MAX_FILE_CONTENT_LINES)
                diff_parts.append(f"--- a/{file.filename}\n+++ b/{file.filename}\n{patch}")

        full_diff = "\n\n".join(diff_parts)
        full_diff = truncate_diff(full_diff, MAX_DIFF_LINES)
        print(f"✓ Collected diff ({len(full_diff)} characters)")

        # Build review prompt
        print("📝 Building review prompt...")
        prompt = build_review_prompt(pr, linear_id, claude_md, full_diff)

        # Call Claude API with MCP integration
        review_text = await call_claude_with_mcp(prompt, anthropic_key, linear_key)

        # Post review comment
        post_review_comment(
            github, repo_full_name, args.pr_number, review_text, args.commenter
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
    args = parser.parse_args()

    # Run async main
    return asyncio.run(async_main(args))


if __name__ == "__main__":
    sys.exit(main())
