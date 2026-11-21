from decimal import Decimal
import uuid


from sqlalchemy import (
    String,
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


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        ForeignKeyConstraint(
            ["invoice_id", "store_id"],
            ["invoices.id", "invoices.store_id"],
            name="fk_payment_invoice_store"
        ),
        CheckConstraint(
            "amount >= 0",
            name="ck_payment_amount_nonnegative"
        ),
        CheckConstraint(
    "status IN ('pending', 'successful', 'failed', 'refunded')",
    name="ck_payment_status_valid"
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

    provider_ref: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    payment_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending"
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    verified_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
