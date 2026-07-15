from datetime import datetime

from sqlalchemy.orm import Session

from app.models import BillLobbyingMatch, BillNamedEntity, ConcentrationScore


class ConcentrationService:
    # Default thresholds are intentionally simple and easy to retune.
    broad_threshold = 0.33
    moderate_threshold = 0.66

    def compute(self, db: Session, congress: int, bill_type: str, bill_number: int) -> ConcentrationScore:
        entity_count = db.query(BillNamedEntity).filter(
            BillNamedEntity.congress == congress,
            BillNamedEntity.bill_type == bill_type,
            BillNamedEntity.bill_number == bill_number,
            BillNamedEntity.status == "approved",
        ).count()

        match_count = db.query(BillLobbyingMatch).filter(
            BillLobbyingMatch.congress == congress,
            BillLobbyingMatch.bill_type == bill_type,
            BillLobbyingMatch.bill_number == bill_number,
        ).count()

        breadth_ratio = 1.0 / (entity_count + 1)
        score = min(1.0, (entity_count * 0.6) + (match_count * 0.08) + (0.35 * (1 - breadth_ratio)))

        if score < self.broad_threshold:
            label = "broad"
        elif score < self.moderate_threshold:
            label = "moderate"
        else:
            label = "narrow"

        existing = db.query(ConcentrationScore).filter(
            ConcentrationScore.congress == congress,
            ConcentrationScore.bill_type == bill_type,
            ConcentrationScore.bill_number == bill_number,
        ).first()

        if existing is None:
            existing = ConcentrationScore(congress=congress, bill_type=bill_type, bill_number=bill_number)
            db.add(existing)

        existing.score = score
        existing.label = label
        existing.computed_at = datetime.utcnow()
        existing.entity_count = entity_count
        existing.breadth_ratio = breadth_ratio

        db.commit()
        db.refresh(existing)
        return existing
