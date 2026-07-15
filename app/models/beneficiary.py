from sqlalchemy import Float, ForeignKey, ForeignKeyConstraint, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class BeneficiaryGroup(Base):
    __tablename__ = "beneficiary_group"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")

    rules = relationship("BeneficiaryRule", back_populates="group", cascade="all, delete-orphan")


class BeneficiaryRule(Base):
    __tablename__ = "beneficiary_rule"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("beneficiary_group.id", ondelete="CASCADE"), index=True)
    match_field: Mapped[str] = mapped_column(String(50))
    match_value: Mapped[str] = mapped_column(String(255), index=True)

    group = relationship("BeneficiaryGroup", back_populates="rules")


class BillBeneficiary(Base):
    __tablename__ = "bill_beneficiary"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    congress: Mapped[int] = mapped_column(Integer, index=True)
    bill_type: Mapped[str] = mapped_column(String(20), index=True)
    bill_number: Mapped[int] = mapped_column(Integer, index=True)

    group_id: Mapped[int] = mapped_column(ForeignKey("beneficiary_group.id", ondelete="CASCADE"))
    rule_id: Mapped[int] = mapped_column(ForeignKey("beneficiary_rule.id", ondelete="SET NULL"), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.7)
    evidence: Mapped[str] = mapped_column(Text, default="")

    __table_args__ = (
        ForeignKeyConstraint(
            ["congress", "bill_type", "bill_number"],
            ["bill_cache.congress", "bill_cache.bill_type", "bill_cache.bill_number"],
            ondelete="CASCADE",
        ),
    )

    bill = relationship("BillCache", back_populates="beneficiaries")
    group = relationship("BeneficiaryGroup")
    rule = relationship("BeneficiaryRule")
