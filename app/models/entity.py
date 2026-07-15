from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, ForeignKeyConstraint, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class NamedEntity(Base):
    __tablename__ = "named_entity"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    entity_type: Mapped[str] = mapped_column(String(64), default="organization")
    source: Mapped[str] = mapped_column(String(64), default="ai")

    bill_links = relationship("BillNamedEntity", back_populates="entity", cascade="all, delete-orphan")


class BillNamedEntity(Base):
    __tablename__ = "bill_named_entity"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    congress: Mapped[int] = mapped_column(Integer, index=True)
    bill_type: Mapped[str] = mapped_column(String(20), index=True)
    bill_number: Mapped[int] = mapped_column(Integer, index=True)

    entity_id: Mapped[int] = mapped_column(ForeignKey("named_entity.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    source: Mapped[str] = mapped_column(String(64), default="ai")
    evidence_text: Mapped[str] = mapped_column(Text, default="")
    reviewed_by: Mapped[str] = mapped_column(String(255), default="")
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["congress", "bill_type", "bill_number"],
            ["bill_cache.congress", "bill_cache.bill_type", "bill_cache.bill_number"],
            ondelete="CASCADE",
        ),
    )

    bill = relationship("BillCache", back_populates="named_entities")
    entity = relationship("NamedEntity", back_populates="bill_links")


class ConcentrationScore(Base):
    __tablename__ = "concentration_score"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    congress: Mapped[int] = mapped_column(Integer, index=True)
    bill_type: Mapped[str] = mapped_column(String(20), index=True)
    bill_number: Mapped[int] = mapped_column(Integer, index=True)

    score: Mapped[float] = mapped_column(Float, default=0.0)
    label: Mapped[str] = mapped_column(String(20), default="broad")
    computed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    entity_count: Mapped[int] = mapped_column(Integer, default=0)
    breadth_ratio: Mapped[float] = mapped_column(Float, default=0.0)

    __table_args__ = (
        ForeignKeyConstraint(
            ["congress", "bill_type", "bill_number"],
            ["bill_cache.congress", "bill_cache.bill_type", "bill_cache.bill_number"],
            ondelete="CASCADE",
        ),
    )

    bill = relationship("BillCache", back_populates="concentration_scores")
