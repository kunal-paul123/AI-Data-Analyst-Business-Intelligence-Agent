from backend.models import Order
from sqlalchemy import select, func
from backend.database import AsyncSessionLocal
from backend.tools.helper_fns import date_range, format_inr, revenue_filter, date_conditions
from datetime import date, datetime
from pathlib import Path
from backend.config import settings

output_path = Path("charts")

async def get_sales_metrics(
    period: str = "last_30_days",
    start: date | str | None = None,
    end: date | str | None = None
):

    """
    Calculate sales metrics for a given period or custom date range.

    Args:
        period: Predefined period such as 'last_7_days',
                'last_30_days', 'this_month', or 'all_time'.
        start: Custom start date in DD-MM-YYYY or YYYY-MM-DD format.
        end: Custom end date in DD-MM-YYYY or YYYY-MM-DD format.

    Returns:
        A dictionary containing:
            - total_revenue: Total revenue generated.
            - order_count: Total number of orders.
            - avg_order_value: Average value per order.
    """

    start_date, end_date, period_name = date_range(period, start, end)

    conditions = [
        revenue_filter(),
        *date_conditions(start_date, end_date)
    ]

    async with AsyncSessionLocal() as db:

        result = await db.execute(
            select(
            func.coalesce(func.sum(Order.total_amount), 0),
            func.count(Order.id)
            ).where(*conditions)
        )

        revenue, order_count = result.one()

    revenue = float(revenue)
    order_count = int(order_count)

    aov = (revenue / order_count) if order_count > 0 else 0.0

    return {
        "period": period_name,
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
        "revenue": round(revenue, 2),
        "total_orders": order_count,
        "average_order_value": round(aov, 2)
    }

async def get_monthly_revenue():

    """
    Calculate month-by-month revenue for the last 12 calendar months.

    Returns:
        A list of dictionaries containing:
            - month: Month in YYYY-MM format.
            - revenue: Total revenue generated during that month.
    """

    today = date.today()

    months = []

    for i in range(11, -1,-1):
        month_index = today.year * 12 + today.month - 1 - i
        year, month_zero = divmod(month_index, 12)

        months.append(f"{year:04d}-{month_zero + 1:02d}")

    revenue_map = {month: 0.0 for month in months}

    first_month = date.fromisoformat(months[0] + "-01")

    async with AsyncSessionLocal() as db:
        query = select(
            Order.order_date,
            Order.total_amount,
        ).where(
            revenue_filter(),
            Order.order_date >= first_month,
            Order.order_date <= today
        )

        result = await db.execute(query)

    for order_date, total_amount in result.all():
        if isinstance(order_date, datetime):
            order_date = order_date.date()

        month_key = order_date.strftime("%Y-%m")

        if month_key in revenue_map:
            revenue_map[month_key] += float(total_amount)

    return [
        {
            "month": month,
            "revenue": round(revenue_map[month], 2)
        }
        for month in months
    ]

async def generate_chart(
    chart_type: str,
    data: list[dict],
):
    """
    Generate a chart based on the provided data and chart type.

    Args:
        chart_type: Type of chart to generate (e.g., 'bar', 'line', 'pie').
        data: List of dictionaries containing the data for the chart.
        output_dir: Directory where the generated chart will be saved.
    """

    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker

    if not data:
        raise ValueError("Cannot generate a chart from empty data")

    chart_type = chart_type.lower()

    if chart_type not in ("bar", "line"):
        raise ValueError(f"Unsupported chart type: {chart_type}, chart type must be in bar or line chart")

    first_row = data[0]

    label_key = next(
        (
            key for key in (
                "name",
                "month",
                "product_name",
                "category",
                "customer_name",
            )
            if key in first_row
        ), 
        None
    )

    value_key = next(
        (
            key for key in (
                "revenue",
                "total_spent",
                "units_sold",
                "orders_count"
            )
            if key in first_row
        ),
        None
    )

    if label_key is None or value_key is None:
        raise ValueError(
            "Data must contain a label column and a numeric column."
        )

    labels = [str(row[label_key]) for row in data]
    values = [float(row[value_key]) for row in data]

    fig, ax = plt.subplots(figsize=(11, 5.5))

    # bar chart
    if chart_type == "bar":
        ax.bar(labels, values, color="#38bdf8")
        ax.set_xlabel(label_key.replace("_", " ").title())
        ax.set_ylabel(value_key.replace("_", " ").title())
        ax.ticklabel_format(style="plain", axis="y")
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: format_inr(x)))
        
    # line chart
    elif chart_type == "line":
        ax.plot(labels, values, marker="o", linewidth=2.5, color="#38bdf8")
        ax.set_xlabel(label_key.replace("_", " ").title())
        ax.set_ylabel(value_key.replace("_", " ").title())
        ax.ticklabel_format(style="plain", axis="y")
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: format_inr(x)))

    output_path.mkdir(parents=True, exist_ok=True)

    filename = f"chart_{chart_type}_{label_key}.png"
    filepath = f"charts/{filename}"
    fig.savefig(filepath, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return {
        "status": "success",
        "chart_path": filepath,
        "chart_url": f"{settings.BACKEND_URL}/{filepath}"
    }



