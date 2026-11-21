from decimal import Decimal
import uuid

from sqlalchemy import (
    String,
    Text,
    Integer,
    Numeric,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    __table_args__ = (
        UniqueConstraint(
            "store_id",
            "sku",
            name="uq_product_store_sku"
        ),
        UniqueConstraint(
            "id",
            "store_id",
            name="uq_product_id_store"
        ),
        CheckConstraint(
            "price >= 0",
            name="ck_product_price_nonnegative"
        ),
        CheckConstraint(
            "cost_price IS NULL OR cost_price >= 0",
            name="ck_product_cost_nonnegative"
        ),
        CheckConstraint(
            "stock >= 0",
            name="ck_product_stock_nonnegative"
        ),
    )


    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stores.id"),
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    cost_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True
    )

    stock: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    deleted_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
