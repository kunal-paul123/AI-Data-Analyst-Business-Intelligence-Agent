from datetime import date, timedelta

from sqlalchemy import func, select
from backend.database import AsyncSessionLocal
from backend.models import Customer, Order
from backend.tools.helper_fns import revenue_filter

NEW_CUSTOMER_DAYS = 30
INACTIVE_CUSTOMER_DAYS = 90


async def get_customer_metrics():

    """
    Calculate customer-related analytics from the database.

    Returns:
        A dictionary containing:
            - total_customers: Total number of registered customers.
            - new_customers: Number of customers registered in the last 30 days.
            - inactive_customers: Number of customers who have not
                                  placed a qualifying order in the last 90 days.
    """

    today = date.today()
    new_customer = today - timedelta(days=NEW_CUSTOMER_DAYS)
    inactive_customer = today - timedelta(days=INACTIVE_CUSTOMER_DAYS)

    async with AsyncSessionLocal() as db:
        # total customers
        total_customers = await db.scalar(
            select(func.count(Customer.id))
        )

        # new_customers
        new_customers = await db.scalar(
            select(func.count(Customer.id))
            .where(Customer.signup_date >= new_customer)
        )

        # inactive_customers
        recently_active_customers = (
            select(Order.customer_id)
            .where(revenue_filter(), Order.order_date >= inactive_customer)
            .distinct()
        )

        inactive_customers = await db.scalar(
            select(func.count(Customer.id))
            .where(Customer.id.notin_(recently_active_customers))
        )

    return {
        "total_customers": int(total_customers or 0),
        "new_customers": int(new_customers or 0),
        "inactive_customers": int(inactive_customers or 0),

        "new_customer_window_days": NEW_CUSTOMER_DAYS,
        "inactive_customer_window_days": INACTIVE_CUSTOMER_DAYS
    }


