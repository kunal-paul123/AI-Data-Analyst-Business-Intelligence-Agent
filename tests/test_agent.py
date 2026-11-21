"""Live integration checks for the Gemini analytics agent.

These tests intentionally call the real Gemini model and consume API quota.
They are skipped by default. Enable them explicitly with
RUN_LIVE_GEMINI_TESTS=1 after configuring GEMINI_API_KEY in .env or the shell.

The expected top product is computed independently with sqlite3 rather than
being taken from the AI agent's own tool result.
"""

from __future__ import annotations

import asyncio
import os
import sqlite3
from pathlib import Path

import pytest

from backend.agent.agent import run_agent
from backend.config import settings
from backend.database import engine
from backend.tools.helper_fns import REVENUE_STATUSES


LIVE_GEMINI_TESTS_ENABLED = (
    os.getenv("RUN_LIVE_GEMINI_TESTS") == "1"
    and bool(settings.GEMINI_API_KEY)
    and settings.GEMINI_API_KEY != "pytest-placeholder-key"
)

pytestmark = pytest.mark.skipif(
    not LIVE_GEMINI_TESTS_ENABLED,
    reason=(
        "Live Gemini tests are opt-in. Set GEMINI_API_KEY and "
        "RUN_LIVE_GEMINI_TESTS=1 to run them."
    ),
)


def _sqlite_database_path() -> Path:
    """Resolve the SQLite file used by the application's SQLAlchemy engine."""
    database_name = engine.url.database
    if not database_name:
        pytest.fail("The application database URL does not identify a SQLite file.")

    database_path = Path(database_name)
    if not database_path.is_absolute():
        database_path = Path.cwd() / database_path

    if not database_path.is_file():
        pytest.fail(
            f"SQLite database not found at {database_path}. "
            "Run the project's seed script or restore the bundled database."
        )

    return database_path


def _independently_query_top_product_by_revenue() -> str:
    """Return the top product using a direct SQL query independent of the agent."""
    database_path = _sqlite_database_path()
    placeholders = ", ".join("?" for _ in REVENUE_STATUSES)

    query = f"""
        SELECT p.name
        FROM products AS p
        JOIN order_items AS oi ON oi.product_id = p.id
        JOIN "order" AS o ON o.id = oi.order_id
        WHERE LOWER(o.status) IN ({placeholders})
        GROUP BY p.id, p.name
        ORDER BY SUM(oi.subtotal) DESC, p.id ASC
        LIMIT 1
    """

    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            query,
            tuple(str(status).lower() for status in REVENUE_STATUSES),
        ).fetchone()

    if row is None:
        pytest.fail(
            "No qualifying order items were found. The agent test needs a seeded database."
        )

    return str(row[0])


def _ask_agent(question: str) -> dict:
    """Run the asynchronous Gemini agent from this synchronous pytest test."""
    return asyncio.run(run_agent(question))


def test_top_product_question() -> None:
    """The AI answer should name the top-revenue product from an independent SQL query."""
    expected_product = _independently_query_top_product_by_revenue()

    result = _ask_agent("What is the top product by revenue?")
    answer = result.get("answer", "")

    assert isinstance(answer, str)
    assert expected_product.casefold() in answer.casefold(), (
        f"Expected the AI answer to include {expected_product!r}; got: {answer!r}"
    )

    # # Confirm the agent actually used the top-products analytics tool.
    # tools_used = result.get("tools_used", [])
    # assert any(
    #     call.get("tool_name") == "get_top_products"
    #     for call in tools_used
    #     if isinstance(call, dict)
    # ), f"Expected get_top_products to be called; tools_used={tools_used!r}"


def test_unsupported_question_handled() -> None:
    """The agent should decline a question outside its e-commerce analytics scope."""
    result = _ask_agent("What is the weather in Mumbai?")
    answer = result.get("answer", "")

    assert isinstance(answer, str)
    normalized_answer = answer.casefold()
    assert (
        "cannot" in normalized_answer
        or "can't" in normalized_answer
        or "not supported" in normalized_answer
        or "outside the scope" in normalized_answer
        or "only support" in normalized_answer
    ), f"Expected a clear unsupported-request response; got: {answer!r}"


