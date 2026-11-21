from backend.models import Order, OrderItem, Product
from sqlalchemy import select, func, join, desc
from backend.database import AsyncSessionLocal
from backend.tools.helper_fns import date_range, revenue_filter, date_conditions


async def get_top_products(n: int = 5, metric: str = "revenue"):

    """
    Retrieve the top-selling products based on revenue or units sold.

    Args:
        n: Number of top products to retrieve. Defaults to 10.
        metric: Ranking criteria. Supported values:
                'revenue' - Rank products by total revenue.
                'units' - Rank products by total units sold.

    Returns:
        A list of dictionaries containing:
            - product_id: Unique product ID.
            - product_name: Name of the product.
            - category: Product category.
            - revenue: Total revenue generated.
            - units_sold: Total quantity sold.
    """

    if n < 1:
        raise ValueError("n must be at least 1")

    metric = metric.lower()

    if metric not in ("revenue", "units_sold"):
        raise ValueError(
            "metric must be 'revenue' or 'units_sold'."
        )
    
    revenue_expr = func.sum(OrderItem.subtotal)
    units_expr = func.sum(OrderItem.quantity)

    sort_expression = (
        revenue_expr if metric == "revenue" else units_expr
    )

    async with AsyncSessionLocal() as db:
        query = (
            select(
                Product.id.label("product_id"),
                Product.name,
                Product.category,

                func.coalesce(revenue_expr, 0).label("revenue"),
                func.coalesce(units_expr, 0).label("units_sold")
            )
            .join(
                OrderItem,
                OrderItem.product_id == Product.id
            )
            .join(
                Order,
                Order.id == OrderItem.order_id
            )
            .where(revenue_filter())
            .group_by(
                Product.id,
                Product.name,
                Product.category
            )
            .order_by(desc(sort_expression))
            .limit(n)
        )

        result = await db.execute(query)
        rows = result.all()

    return [
        {
            "product_id": row.product_id,
            "name": row.name,
            "category": row.category,
            "revenue": round(float(row.revenue or 0), 2),
            "units_sold": int(row.units_sold or 0)
        }
        for row in rows
    ]



