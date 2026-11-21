from decimal import Decimal
import uuid


from sqlalchemy import (
    Integer,
    Numeric,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    CheckConstraint,
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class Item(Base):
    __tablename__ = "items"

    
    __table_args__ = (
        ForeignKeyConstraint(
            ["invoice_id", "store_id"],
            ["invoices.id", "invoices.store_id"],
            name="fk_item_invoice_store"
        ),
        ForeignKeyConstraint(
            ["product_id", "store_id"],
            ["products.id", "products.store_id"],
            name="fk_item_product_store"
        ),
        CheckConstraint(
            "qty > 0",
            name="ck_item_quantity_positive"
        ),
        CheckConstraint(
            "unit_price >= 0",
            name="ck_item_unit_price_nonnegative"
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

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False
    )

    qty: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
