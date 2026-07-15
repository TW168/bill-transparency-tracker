from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import BillCache, BillNamedEntity, ConcentrationScore
from app.services.beneficiary_engine import BeneficiaryEngine
from app.services.concentration_service import ConcentrationService
from app.services.congress_client import CongressClient


class AnalysisService:
    def __init__(self) -> None:
        self.congress_client = CongressClient()
        self.beneficiary_engine = BeneficiaryEngine()
        self.concentration_service = ConcentrationService()

    async def get_or_build_bill_analysis(
        self, db: Session, congress: int, bill_type: str, bill_number: int
    ) -> dict[str, object]:
        bill = db.query(BillCache).filter(
            BillCache.congress == congress,
            BillCache.bill_type == bill_type,
            BillCache.bill_number == bill_number,
        ).first()

        details = await self.congress_client.get_bill(congress, bill_type, bill_number)
        if bill is None:
            bill = BillCache(congress=congress, bill_type=bill_type, bill_number=bill_number)
            db.add(bill)

        bill.title = str(details.get("title", ""))
        bill.sponsor = str(details.get("sponsor", ""))
        bill.status = str(details.get("status", ""))
        bill.summary = str(details.get("summary", ""))
        bill.policy_area = str(details.get("policy_area", ""))
        bill.subjects_json = list(details.get("subjects", []))
        bill.committees_json = list(details.get("committees", []))
        bill.actions_json = list(details.get("actions", []))
        bill.text_version_count = int(details.get("text_version_count", 0))
        bill.last_fetched_at = datetime.now(timezone.utc).replace(tzinfo=None)

        db.commit()

        await self.beneficiary_engine.run_layer_a(
            db=db,
            congress=congress,
            bill_type=bill_type,
            bill_number=bill_number,
            policy_area=bill.policy_area,
            subjects=bill.subjects_json,
            committees=bill.committees_json,
        )

        await self.beneficiary_engine.run_layer_b(
            db=db,
            congress=congress,
            bill_type=bill_type,
            bill_number=bill_number,
            bill_title=bill.title,
            bill_summary=bill.summary,
        )

        concentration = self.concentration_service.compute(db, congress, bill_type, bill_number)

        confirmed_entities = db.query(BillNamedEntity).filter(
            BillNamedEntity.congress == congress,
            BillNamedEntity.bill_type == bill_type,
            BillNamedEntity.bill_number == bill_number,
            BillNamedEntity.status == "approved",
        ).all()

        pending_entities = db.query(BillNamedEntity).filter(
            BillNamedEntity.congress == congress,
            BillNamedEntity.bill_type == bill_type,
            BillNamedEntity.bill_number == bill_number,
            BillNamedEntity.status == "pending",
        ).all()

        return {
            "bill": bill,
            "concentration": concentration,
            "confirmed_entities": confirmed_entities,
            "pending_entities": pending_entities,
        }

    def get_cached_recent_bills(self, db: Session, limit: int = 6) -> list[BillCache]:
        return db.query(BillCache).order_by(BillCache.last_fetched_at.desc()).limit(limit).all()

    def score_for_bill(self, db: Session, congress: int, bill_type: str, bill_number: int) -> ConcentrationScore | None:
        return db.query(ConcentrationScore).filter(
            ConcentrationScore.congress == congress,
            ConcentrationScore.bill_type == bill_type,
            ConcentrationScore.bill_number == bill_number,
        ).first()
