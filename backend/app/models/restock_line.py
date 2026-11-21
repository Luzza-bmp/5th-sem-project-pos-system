
import uuid


from sqlalchemy import (
    String,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    CheckConstraint,
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class RestockLine(Base):
    __tablename__ = "restock_lines"

    __table_args__ = (
        ForeignKeyConstraint(
            ["batch_id", "store_id"],
            ["restock_batches.id", "restock_batches.store_id"],
            name="fk_restock_line_batch_store"
        ),
        ForeignKeyConstraint(
            ["product_id", "store_id"],
            ["products.id", "products.store_id"],
            name="fk_restock_line_product_store"
        ),
        CheckConstraint(
            "suggested_quantity > 0",
            name="ck_restock_line_quantity_positive"
        ),
        CheckConstraint(
    "status IN ('pending', 'approved', 'rejected', 'completed')",
    name="ck_restock_line_status_valid"
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

    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
       
        nullable=False
    )

    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
       
        nullable=True
    )

    ai_product_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    suggested_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending"
    )

    note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
