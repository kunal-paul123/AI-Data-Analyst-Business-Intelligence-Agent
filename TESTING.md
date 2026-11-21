# Running the test suite

Run these commands from the repository root (the folder containing `pyproject.toml`).

## Install test dependencies

The project should have `pytest` and `httpx` available. If either is missing:

```powershell
uv add --dev pytest httpx
uv sync
```

## Run API tests (no Gemini calls)

```powershell
uv run pytest tests/test_api.py -v
```

These tests check:

- `GET /api/analytics/kpi` returns HTTP 200 and the KPI fields used by Streamlit.
- `GET /api/analytics/top-products?n=3&metric=revenue` returns no more than three product rows.
- `POST /api/chat` returns HTTP 422 when the required `question` field is missing.

The API tests use the repository's bundled `ecommerce.db` file.

## Run the agent integration tests (real Gemini calls)

The two tests in `test_agent.py` make real Gemini requests and can consume API quota. They are skipped by default so ordinary test runs do not make paid/external API calls.

Configure `GEMINI_API_KEY` in the root `.env`, then enable the live tests in PowerShell:

```powershell
$env:RUN_LIVE_GEMINI_TESTS = "1"
uv run pytest tests/test_agent.py -v
```

The top-product test independently calculates the expected product by querying `products`, `order_items`, and `order` with `sqlite3`, then checks that the AI answer names that product and that the agent called `get_top_products`.

The unsupported-question test asks about Mumbai weather and verifies that the agent responds that the request is outside its e-commerce analytics scope.

## Run everything

```powershell
uv run pytest -v
```

Without `RUN_LIVE_GEMINI_TESTS=1`, the API tests run while the real-Gemini integration tests are skipped.
