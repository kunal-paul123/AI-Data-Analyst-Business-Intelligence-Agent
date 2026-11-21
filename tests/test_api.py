"""API contract tests for the FastAPI application.

These tests use the repository's bundled SQLite database. They do not call
Gemini and therefore do not require a working Gemini API key.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Provide one TestClient for the API tests in this module."""
    with TestClient(app) as test_client:
        yield test_client


def test_kpi_endpoint_returns_200(client: TestClient) -> None:
    """The dashboard KPI endpoint should return its expected metrics."""
    response = client.get("/api/analytics/kpi")

    assert response.status_code == 200

    payload = response.json()
    assert isinstance(payload, dict)
    assert {
        "total_revenue",
        "total_orders",
        "total_customers",
        "average_order_value",
    }.issubset(payload.keys())


def test_top_products_respects_n_param(client: TestClient) -> None:
    """The top-products endpoint should return no more than the requested n."""
    requested_count = 3
    response = client.get(
        "/api/analytics/top-products",
        params={"n": requested_count, "metric": "revenue"},
    )

    assert response.status_code == 200

    products = response.json()
    # The Streamlit dashboard consumes this endpoint as a list of rows.
    assert isinstance(products, list)
    assert len(products) <= requested_count

    for product in products:
        assert "name" in product
        assert "revenue" in product

    # A smaller n must also produce a smaller-or-equal result set.
    one_product_response = client.get(
        "/api/analytics/top-products",
        params={"n": 1, "metric": "revenue"},
    )
    assert one_product_response.status_code == 200
    assert isinstance(one_product_response.json(), list)
    assert len(one_product_response.json()) <= 1


def test_chat_with_invalid_input_returns_422(client: TestClient) -> None:
    """Chat requests must contain the required `question` field."""
    # `query` is intentionally incorrect: ChatRequest expects `question`.
    response = client.post(
        "/api/chat",
        json={"query": "Show me the top-selling products"},
    )

    assert response.status_code == 422
    assert isinstance(response.json(), dict)


