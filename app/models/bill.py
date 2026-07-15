from datetime import datetime

from sqlalchemy import DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class BillCache(Base):
    __tablename__ = "bill_cache"

    congress: Mapped[int] = mapped_column(Integer, primary_key=True)
    bill_type: Mapped[str] = mapped_column(String(20), primary_key=True)
    bill_number: Mapped[int] = mapped_column(Integer, primary_key=True)

    title: Mapped[str] = mapped_column(String(1000), default="")
    sponsor: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(255), default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    policy_area: Mapped[str] = mapped_column(String(255), default="")

    subjects_json: Mapped[list] = mapped_column(JSON, default=list)
    committees_json: Mapped[list] = mapped_column(JSON, default=list)
    actions_json: Mapped[list] = mapped_column(JSON, default=list)

    text_version_count: Mapped[int] = mapped_column(Integer, default=0)
    last_fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    beneficiaries = relationship("BillBeneficiary", back_populates="bill", cascade="all, delete-orphan")
    lobbying_matches = relationship("BillLobbyingMatch", back_populates="bill", cascade="all, delete-orphan")
    named_entities = relationship("BillNamedEntity", back_populates="bill", cascade="all, delete-orphan")
    concentration_scores = relationship("ConcentrationScore", back_populates="bill", cascade="all, delete-orphan")
