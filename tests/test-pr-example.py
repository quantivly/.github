"""
Test PR Example - Code with Intentional Issues

This file demonstrates code that Claude should flag during review.
Use this for end-to-end testing of the Claude PR review workflow.

Intentional issues included:
1. SQL Injection vulnerability (CRITICAL)
2. Off-by-one error (HIGH)
3. Missing error handling (HIGH)
4. Code duplication (SUGGESTION)
5. Missing test coverage (SUGGESTION)
"""

from __future__ import annotations

import sqlite3
from typing import Any


def get_user_by_id(user_id: str) -> dict[str, Any] | None:
    """
    Fetch user from database by ID.

    ISSUE #1: SQL INJECTION VULNERABILITY (CRITICAL)
    - User input directly interpolated into SQL query
    - Should use parameterized queries
    """
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    # CRITICAL: SQL Injection - user_id not sanitized
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)

    result = cursor.fetchone()
    conn.close()

    if result:
        return {
            "id": result[0],
            "username": result[1],
            "email": result[2],
        }
    return None


def paginate_items(items: list[Any], page: int, page_size: int) -> list[Any]:
    """
    Return a page of items from a list.

    ISSUE #2: OFF-BY-ONE ERROR (HIGH)
    - Last item on page will be missing
    - Should use range(start, end) correctly
    """
    start = page * page_size
    # HIGH: Off-by-one - should be start + page_size, not start + page_size - 1
    end = start + page_size - 1  # BUG: Missing last item

    return items[start:end]


def export_data_to_csv(data: list[dict[str, Any]], filename: str) -> None:
    """
    Export data to CSV file.

    ISSUE #3: MISSING ERROR HANDLING (HIGH)
    - No handling for file write errors
    - No validation of data structure
    - Could fail silently
    """
    # HIGH: No error handling, no validation
    with open(filename, "w") as f:
        # Assumes data has consistent keys
        headers = list(data[0].keys())
        f.write(",".join(headers) + "\n")

        for row in data:
            values = [str(row[key]) for key in headers]
            f.write(",".join(values) + "\n")


def calculate_total_price(items: list[dict[str, Any]]) -> float:
    """
    Calculate total price of items with tax.

    ISSUE #4: CODE DUPLICATION (SUGGESTION)
    - Tax calculation duplicated
    - Should extract to separate function
    """
    total = 0.0

    for item in items:
        if item["category"] == "food":
            # Tax calculation duplicated
            subtotal = item["price"] * item["quantity"]
            tax = subtotal * 0.08
            total += subtotal + tax
        elif item["category"] == "electronics":
            # Same tax calculation duplicated
            subtotal = item["price"] * item["quantity"]
            tax = subtotal * 0.08
            total += subtotal + tax
        else:
            total += item["price"] * item["quantity"]

    return total


def process_user_input(user_input: str) -> str:
    """
    Process user input and return sanitized result.

    ISSUE #5: XSS VULNERABILITY (CRITICAL)
    - User input returned without sanitization
    - Could be used for XSS attacks if rendered in HTML
    """
    # CRITICAL: No sanitization - XSS vulnerability
    return f"<div>User said: {user_input}</div>"


# ISSUE #6: MISSING TEST COVERAGE (SUGGESTION)
# None of these functions have tests
# Tests should cover:
# - Normal cases
# - Edge cases (empty input, None, boundary values)
# - Error cases
# - Security issues (injection attempts)
