from sqlalchemy import Float, ForeignKey, ForeignKeyConstraint, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class LobbyingFiling(Base):
    __tablename__ = "lobbying_filing"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    registrant: Mapped[str] = mapped_column(String(255), default="")
    client: Mapped[str] = mapped_column(String(255), default="")
    specific_issues_text: Mapped[str] = mapped_column(Text, default="")
    filing_period: Mapped[str] = mapped_column(String(64), default="")
    amount: Mapped[float] = mapped_column(Float, default=0.0)

    bill_matches = relationship("BillLobbyingMatch", back_populates="filing", cascade="all, delete-orphan")


class BillLobbyingMatch(Base):
    __tablename__ = "bill_lobbying_match"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    congress: Mapped[int] = mapped_column(Integer, index=True)
    bill_type: Mapped[str] = mapped_column(String(20), index=True)
    bill_number: Mapped[int] = mapped_column(Integer, index=True)

    filing_id: Mapped[int] = mapped_column(ForeignKey("lobbying_filing.id", ondelete="CASCADE"), index=True)
    match_method: Mapped[str] = mapped_column(String(32), default="explicit")
    confidence: Mapped[float] = mapped_column(Float, default=0.6)
    rationale: Mapped[str] = mapped_column(Text, default="")

    __table_args__ = (
        ForeignKeyConstraint(
            ["congress", "bill_type", "bill_number"],
            ["bill_cache.congress", "bill_cache.bill_type", "bill_cache.bill_number"],
            ondelete="CASCADE",
        ),
    )

    bill = relationship("BillCache", back_populates="lobbying_matches")
    filing = relationship("LobbyingFiling", back_populates="bill_matches")
