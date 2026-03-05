import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

def uid() -> str:
    return uuid.uuid4().hex

class Batch(Base):
    __tablename__ = "batches"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=uid)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="CREATED", nullable=False)  # CREATED, RUNNING, DONE, ERROR
    total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ok: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    filename_pattern: Mapped[str] = mapped_column(String(300), default="registro_{row_index}", nullable=False)

    # storage paths (relative to storage_root)
    input_excel: Mapped[str] = mapped_column(Text, default="", nullable=False)
    input_template: Mapped[str] = mapped_column(Text, default="", nullable=False)
    output_zip: Mapped[str] = mapped_column(Text, default="", nullable=False)
    errors_csv: Mapped[str] = mapped_column(Text, default="", nullable=False)

    items: Mapped[list["BatchItem"]] = relationship(back_populates="batch", cascade="all, delete-orphan")

class BatchItem(Base):
    __tablename__ = "batch_items"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=uid)
    batch_id: Mapped[str] = mapped_column(String(32), ForeignKey("batches.id"), index=True, nullable=False)

    row_index: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)  # PENDING, OK, ERROR
    error_message: Mapped[str] = mapped_column(Text, default="", nullable=False)
    output_pdf: Mapped[str] = mapped_column(Text, default="", nullable=False)

    batch: Mapped["Batch"] = relationship(back_populates="items")
