from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class USAFactsStat(Base):
    __tablename__ = "usafacts_stat"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    topic: Mapped[str] = mapped_column(String(255), index=True)
    value: Mapped[str] = mapped_column(String(255))
    source_url: Mapped[str] = mapped_column(String(500), default="")
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
