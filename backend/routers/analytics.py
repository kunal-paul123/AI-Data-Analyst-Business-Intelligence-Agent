from typing import List
from fastapi import APIRouter, HTTPException, Query

from backend.schemas import CustomerMetrics, KPISummary, MonthlyRevenue, TopProductItems
from backend.tools.customer_tools import get_customer_metrics
from backend.tools.product_tools import get_top_products
from backend.tools.sales_tools import get_sales_metrics, get_monthly_revenue

router = APIRouter()

# get kpi
@router.get("/kpi", response_model=KPISummary)
async def get_kpis():
    """
    Returns KPIs:
    Total Revenue, Total Orders, Total Customers, and Average Order Value.
    """

    try:
        sales = await get_sales_metrics(period="all_time")
        customers = await get_customer_metrics()

        return KPISummary(
            total_revenue=sales["revenue"],
            total_orders=sales["total_orders"],
            total_customers=customers["total_customers"],
            average_order_value=sales["average_order_value"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"failed to calculate KPIs: {str(e)}")

# get monthly revenue
@router.get("/monthly-revenue", response_model=List[MonthlyRevenue])
async def get_monthly_revenue_endpoint():
    """
    Returns month-by-month revenue for the last 12 months.
    """

    try:
        monthly_revenue = await get_monthly_revenue()

        return monthly_revenue
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"failed to calculate monthly revenue: {str(e)}")

# get top products
@router.get("/top-products", response_model=List[TopProductItems])
async def   get_top_products_endpoint(
    n: int = Query(default=5, ge=1, le=20, description="Number of top products to return"),
    metric: str = Query(default="revenue", pattern="^(revenue|units_sold)$", description="Metric by 'revenue' or 'units_sold'")
):
    """Returns the top products ranked by either revenue or units sold."""

    try:
        return await get_top_products(n=n, metric=metric)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch top products: {str(e)}")

# get customer metrics
@router.get("/customer-metrics", response_model=CustomerMetrics)
async def get_customer_metrics_endpoint():
    """Returns customer retention and acquisition breakdown (total, new, inactive)."""
    try:
        return await get_customer_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch customer metrics: {str(e)}")


