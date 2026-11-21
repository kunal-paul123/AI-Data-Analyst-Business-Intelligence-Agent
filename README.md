# AI Data Analyst & Business Intelligence Agent

This project is an AI Data Analyst & Business Intelligence Agent for an e-commerce/retail company. It allows business users to explore customer, order, product and sales data using natural language instead of SQL or manual reports. An LLM interprets the user's question and selects from a controlled set of tools. These tools compute results directly from the dataset, and the LLM only summarizes the verified output, so every number in a response comes from real data.

## Features

- **Business KPI dashboard:** total revenue, order count, registered customers, and average order value (AOV).
- **Sales trends:** monthly revenue for the last 12 calendar months.
- **Product performance:** top products ranked by revenue or units sold.
- **Customer metrics:** total customers, recently registered customers, and inactive customers.
- **Natural-language analytics:** ask questions about sales, orders, products, customers, and revenue without writing SQL.
- **Chart generation:** the agent can generate bar and line charts from retrieved analytics data. Generated chart images can be displayed and downloaded in the chat.
- **API documentation:** FastAPI exposes interactive Swagger documentation.
- **Synthetic demo data:** a Faker-based script can create reproducible e-commerce data for local development.

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | Streamlit, Pandas, Plotly |
| Backend  | FastAPI, Pydantic |
| LLM | Gemini model `gemini-3.5-flash-lite` |
| Agent tools | Gemini function calling with registered Python functions |
| Database | SQLite |
| ORM / Database access | SQLAlchemy 2.x async ORM, `aiosqlite` |
| Agent-generated charts | Matplotlib |
| Dashboard charts | Plotly |
| Configuration | `pydantic-settings`, `.env` file |
| Dependency management | `uv`, `pyproject.toml`, `uv.lock` |
| Tests | Pytest (included as a development dependency) |

## Architecture and AI Agent Approach

The application has two main interfaces:

1. **Dashboard:** Streamlit calls the FastAPI analytics endpoints to load KPI cards, the monthly revenue chart, and the top-products chart.
2. **Conversational analyst:** Streamlit sends a user's question to `POST /api/chat`. The backend passes the question and registered tool definitions to llm.

The agent uses a tool-calling loop:

1. Llm receives the user's question, the system instructions, and the available analytics tools.
2. Llm chooses the relevant tool or tools and supplies their arguments.
3. The backend executes the selected Python functions. These functions query SQLite through asynchronous SQLAlchemy sessions.
4. The results are returned to llm as function responses.
5. llm uses those results to write the final business explanation. If a chart is requested, the agent first retrieves the required data and then calls the chart-generation tool.

The agent loop is bounded to a maximum of five tool-calling steps. The system prompt instructs the model to ground numerical statements in tool results and not invent metrics.

### Available analytics tools

- `get_sales_metrics`: revenue, order count, and average order value for a supported period or custom date range.
- `get_monthly_revenue`: monthly revenue for the latest 12 calendar months.
- `get_top_products`: top products by revenue or units sold.
- `get_customer_metrics`: total, new, and inactive customer metrics.
- `generate_chart`: creates a bar or line chart from analytics data.

The agent does **not** generate arbitrary SQL from the user's prompt. It calls the predefined Python tools listed above.

## Database and Sample Data

The application uses the database file `ecommerce.db` at the project root. SQLAlchemy models represent customers, products, orders, and order items. The database connection uses the async SQLite driver (`sqlite+aiosqlite`).

TA seed script is also provided at `data/seed_data.py`. It generates e-commerce data using Faker with a fixed random seed:

- 500 customers
- 50 products across Electronics, Clothing, Books, Home & Kitchen, and Sports
- 2,000 orders spread over approximately the previous 12 months

The seed script creates the database tables and checks whether customer records already exist before inserting data. If the database is already populated, it stops to avoid duplicate records.

To initialise a fresh/empty database, run the seed command from the repository root:

```bash
uv run python data/seed_data.py
```

Do not run this against an existing database expecting it to reset the data; the script intentionally avoids reseeding a populated database. Back up the database before replacing or deleting it.

## Project Structure

```text
AI-Data-Analyst-Business-Intelligence-Agent/
├── backend/
│   ├── agent/
│   │   ├── agent.py          # Gemini client and bounded function-calling loop
│   │   └── prompts.py        # Agent system instructions
│   ├── routers/
│   │   ├── analytics.py     # Dashboard analytics endpoints
│   │   └── chat.py          # Conversational agent endpoint
│   ├── tools/
│   │   ├── customer_tools.py
│   │   ├── helper_fns.py    # Date-range, revenue-filter, and formatting helpers
│   │   ├── product_tools.py
│   │   └── sales_tools.py   # Sales metrics and chart generation
│   ├── config.py            # Environment-based settings
│   ├── database.py          # Async SQLite engine and session factory
│   ├── main.py              # FastAPI application and route registration
│   ├── models.py            # SQLAlchemy models
│   └── schemas.py           # Pydantic request/response schemas
├── data/
│   └── seed_data.py         # e-commerce data generator
├── frontend/
│   └── app.py               # Frontend dashboard and chat UI
├── tests/                   # Test directory
├── src/                     # Python package scaffold
├── charts/                  # Generated chart images (created at runtime)
├── ecommerce.db             # demo database
├── .python-version          # Python version selection for uv
├── pyproject.toml           # Project metadata and dependencies
├── uv.lock                  # Locked dependency versions
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.12 or newer
- [`uv`](https://docs.astral.sh/uv/) for Python environment and dependency management
- A Google Gemini API key from [Google AI Studio](https://aistudio.google.com/)

### 1. Clone the repository

```bash
git clone https://github.com/kunal-paul123/AI-Data-Analyst-Business-Intelligence-Agent.git
cd AI-Data-Analyst-Business-Intelligence-Agent
```

### 2. Install dependencies

Run this from the repository root:

```bash
uv sync
```

`uv` uses `pyproject.toml` and `uv.lock` to create the project virtual environment and install the declared dependencies.

### 3. Configure environment variables

Create a file named `.env` in the repository root and add:

```env
GEMINI_API_KEY=your_google_gemini_api_key
BACKEND_URL=http://localhost:8000
```

Run this command from the project root so SQLite creates/opens `ecommerce.db` in the expected location.

### 4. Start the FastAPI backend

Open a terminal at the repository root and run:

```bash
uv run fastapi dev backend/main.py
```

The backend runs at `http://localhost:8000` by default.

- Health check: <http://localhost:8000/>
- Interactive API docs: <http://localhost:8000/docs>

### 5. Start the frontend

Open a **second terminal**, also at the repository root, and run:

```bash
uv run streamlit run frontend/app.py
```

Streamlit normally opens at <http://localhost:8501>. Keep the FastAPI backend running while using the dashboard; the frontend sends requests to `http://localhost:8000`.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Backend health check |
| `GET` | `/api/analytics/kpi` | Overall revenue, order, customer, and AOV metrics |
| `GET` | `/api/analytics/monthly-revenue` | Monthly revenue for the last 12 calendar months |
| `GET` | `/api/analytics/top-products?n=5&metric=revenue` | Top products; `n` is 1–20 and `metric` is `revenue` or `units_sold` |
| `GET` | `/api/analytics/customer-metrics` | Total, new, and inactive customer metrics |
| `POST` | `/api/chat` | Send a natural-language business question to the AI agent |

Example chat request:

```json
{
  "question": "What were the top 5 products by revenue?"
}
```

Example chart request to the agent:

```json
{
  "question": "Show monthly revenue as a bar chart"
}
```

## Testing

Pytest is included in the project dependencies, and a `tests/` directory is present. Run the test command from the project root:

```bash
uv run pytest -v
```

**Test coverage note:** the checked-in `tests/test_api.py` currently appears to be empty. Treat the test suite as incomplete until meaningful unit and API tests are added and the command above completes with collected tests. Recommended coverage includes date-range helpers, revenue calculations, product rankings, customer metrics, API validation/error responses, and the agent tool-execution loop. Gemini network calls should be mocked in automated tests so the core tests do not depend on API availability or quota.

## Known Limitations and Notes

- **Gemini dependency:** chat and agent-driven chart generation require a valid Gemini API key and network access. Model availability, quota, and provider rate limits can affect responses.
- **Local development configuration:** the Streamlit frontend currently points to `http://localhost:8000`; update `API_BASE_URL` in `frontend/app.py` when running the backend elsewhere.
- **Local SQLite storage:** the database path is relative to the working directory. Run commands from the repository root to use the expected `ecommerce.db` file.
- **Synthetic data:** the included data is generated for demonstration and testing, not representative of a real company's transactions.
- **Revenue status definition:** the current `REVENUE_STATUSES` helper includes `completed`, `returned`, and `cancelled` orders in the qualifying revenue set. Review this definition in `backend/tools/helper_fns.py` before interpreting the KPIs as completed/recognised revenue.
- **Customer segmentation:** the current customer metrics report total customers, customers registered in the last 30 days, and customers without a qualifying order in the last 90 days. They do not currently calculate a repeat-customer metric.
- **No authentication or user roles:** the local app is intended as a demonstration project and should not be exposed publicly without adding authentication, authorisation, and deployment safeguards.
- **Test coverage:** automated test coverage is not yet demonstrated by the checked-in test file; expand and run the suite before production use.
- **Chart output:** generated chart images are written to a local `charts/` directory and served by the FastAPI application. This is designed for a single local development environment, not shared multi-instance deployment.

## Security

- Store the Gemini API key in `.env` and never commit secrets.
- Do not put private customer or business data into a demo instance without reviewing the data flow and the external LLM provider's terms and privacy requirements.
- Do not expose the development server directly to the public internet. Add authentication, access controls, appropriate logging, and production server configuration before deployment.

  
