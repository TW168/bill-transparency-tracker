from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.models import (
    BeneficiaryRule,
    BillBeneficiary,
    BillNamedEntity,
    BillLobbyingMatch,
    LobbyingFiling,
    NamedEntity,
)
from app.services.ai_client import AIClient
from app.services.lda_client import LDAClient


class BeneficiaryEngine:
    def __init__(self) -> None:
        self.lda_client = LDAClient()
        self.ai_client = AIClient()

    async def run_layer_a(
        self,
        db: Session,
        congress: int,
        bill_type: str,
        bill_number: int,
        policy_area: str,
        subjects: list[str],
        committees: list[str],
    ) -> list[BillBeneficiary]:
        db.query(BillBeneficiary).filter(
            BillBeneficiary.congress == congress,
            BillBeneficiary.bill_type == bill_type,
            BillBeneficiary.bill_number == bill_number,
        ).delete()

        rules = db.query(BeneficiaryRule).all()
        created: list[BillBeneficiary] = []
        searchable = {
            "policy_area": [policy_area],
            "subject": subjects,
            "committee": committees,
        }

        for rule in rules:
            values = searchable.get(rule.match_field, [])
            if any(rule.match_value.lower() in (v or "").lower() for v in values):
                record = BillBeneficiary(
                    congress=congress,
                    bill_type=bill_type,
                    bill_number=bill_number,
                    group_id=rule.group_id,
                    rule_id=rule.id,
                    confidence=0.7,
                    evidence=f"Rule matched on {rule.match_field}: {rule.match_value}",
                )
                db.add(record)
                created.append(record)

        db.commit()
        return created

    async def run_layer_b(
        self,
        db: Session,
        congress: int,
        bill_type: str,
        bill_number: int,
        bill_title: str,
        bill_summary: str,
    ) -> None:
        bill_label = f"{bill_type.upper()} {bill_number}"
        filings = await self.lda_client.search_filings_for_bill(bill_label)

        existing_match_ids = {
            m.filing_id
            for m in db.query(BillLobbyingMatch).filter(
                BillLobbyingMatch.congress == congress,
                BillLobbyingMatch.bill_type == bill_type,
                BillLobbyingMatch.bill_number == bill_number,
            )
        }

        explicit_found = False
        for item in filings:
            filing = db.query(LobbyingFiling).filter(LobbyingFiling.external_id == item["external_id"]).first()
            if filing is None:
                filing = LobbyingFiling(**item)
                db.add(filing)
                db.flush()

            issues_text = (item.get("specific_issues_text") or "").lower()
            if bill_label.lower() in issues_text or str(bill_number) in issues_text:
                explicit_found = True
                if filing.id not in existing_match_ids:
                    db.add(
                        BillLobbyingMatch(
                            congress=congress,
                            bill_type=bill_type,
                            bill_number=bill_number,
                            filing_id=filing.id,
                            match_method="explicit",
                            confidence=0.85,
                            rationale=f"specific_issues contains {bill_label}",
                        )
                    )

        if not explicit_found:
            suggestions = await self.ai_client.suggest_entities(bill_title, bill_summary, filings)
            for suggestion in suggestions:
                entity = db.query(NamedEntity).filter(NamedEntity.name == suggestion["name"]).first()
                if entity is None:
                    entity = NamedEntity(
                        name=suggestion["name"],
                        entity_type=suggestion.get("entity_type", "organization"),
                        source=suggestion.get("source", "ai"),
                    )
                    db.add(entity)
                    db.flush()

                exists = db.query(BillNamedEntity).filter(
                    BillNamedEntity.congress == congress,
                    BillNamedEntity.bill_type == bill_type,
                    BillNamedEntity.bill_number == bill_number,
                    BillNamedEntity.entity_id == entity.id,
                ).first()
                if exists is None:
                    db.add(
                        BillNamedEntity(
                            congress=congress,
                            bill_type=bill_type,
                            bill_number=bill_number,
                            entity_id=entity.id,
                            status="pending",
                            source="ai",
                            evidence_text=suggestion.get("evidence", "AI-suggested beneficiary"),
                            reviewed_by="",
                            reviewed_at=None,
                        )
                    )

        db.commit()

    def review_entity(self, db: Session, row_id: int, decision: str, reviewer: str) -> BillNamedEntity | None:
        row = db.query(BillNamedEntity).filter(BillNamedEntity.id == row_id).first()
        if row is None:
            return None
        row.status = decision
        row.reviewed_by = reviewer
        row.reviewed_at = datetime.utcnow()
        db.commit()
        db.refresh(row)
        return row
