from __future__ import annotations

from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Float, ForeignKey, Date
from backend.database import Base

class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    city: Mapped[str | None] = mapped_column(String(50), nullable=True)
    signup_date: Mapped[datetime] = mapped_column(Date, nullable=False)

    orders: Mapped[list[Order]] = relationship(
        back_populates = "customer",
        cascade = "all, delete-orphan"
    ) 

class Product(Base):
    """Represents the products table."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    stock: Mapped[int] = mapped_column(Integer, default=100)

    order_items: Mapped[list[OrderItem]] = relationship(
        back_populates="product",
    )

class Order(Base):
    __tablename__ = "order"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    order_date: Mapped[Date] = mapped_column(Date, nullable=False)  
    status: Mapped[str] = mapped_column(String, default="completed")
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)

    customer: Mapped[Customer] = relationship(
        back_populates = "orders",
    )   

    items: Mapped[list[OrderItem]] = relationship(
        back_populates = "order",
        cascade = "all, delete-orphan"     
    )

class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("order.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)

    order: Mapped[Order] = relationship(
        back_populates = "items"
    )

    product: Mapped[Product] = relationship(
        back_populates = "order_items"
    )


