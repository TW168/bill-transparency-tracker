from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models import BeneficiaryGroup, BeneficiaryRule, BillNamedEntity
from app.services.beneficiary_engine import BeneficiaryEngine
from app.templating import templates

router = APIRouter(prefix="/admin", tags=["admin"])
security = HTTPBasic()


def require_admin(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    settings = get_settings()
    valid_user = secrets.compare_digest(credentials.username, settings.admin_username)
    valid_pass = secrets.compare_digest(credentials.password, settings.admin_password)
    if not (valid_user and valid_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@router.get("/rules", response_class=HTMLResponse)
async def admin_rules(
    request: Request,
    admin_user: str = Depends(require_admin),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    del admin_user
    groups = db.query(BeneficiaryGroup).order_by(BeneficiaryGroup.name.asc()).all()
    rules = db.query(BeneficiaryRule).order_by(BeneficiaryRule.id.desc()).all()
    return templates.TemplateResponse(
        request,
        "admin_rules.html",
        {"request": request, "groups": groups, "rules": rules},
    )


@router.post("/rules", response_class=HTMLResponse)
async def save_rule(
    request: Request,
    action: str = Form(...),
    group_name: str = Form(default=""),
    group_description: str = Form(default=""),
    group_id: int = Form(default=0),
    match_field: str = Form(default=""),
    match_value: str = Form(default=""),
    admin_user: str = Depends(require_admin),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    del admin_user

    if action == "create_group" and group_name.strip():
        exists = db.query(BeneficiaryGroup).filter(BeneficiaryGroup.name == group_name.strip()).first()
        if exists is None:
            db.add(BeneficiaryGroup(name=group_name.strip(), description=group_description.strip()))
            db.commit()

    if action == "create_rule" and group_id and match_field and match_value:
        db.add(
            BeneficiaryRule(
                group_id=group_id,
                match_field=match_field.strip(),
                match_value=match_value.strip(),
            )
        )
        db.commit()

    groups = db.query(BeneficiaryGroup).order_by(BeneficiaryGroup.name.asc()).all()
    rules = db.query(BeneficiaryRule).order_by(BeneficiaryRule.id.desc()).all()
    return templates.TemplateResponse(
        request,
        "admin_rules.html",
        {
            "request": request,
            "groups": groups,
            "rules": rules,
            "flash_message": "Saved",
        },
    )


@router.get("/entity-review", response_class=HTMLResponse)
async def entity_review(
    request: Request,
    admin_user: str = Depends(require_admin),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    del admin_user
    pending = db.query(BillNamedEntity).filter(BillNamedEntity.status == "pending").order_by(BillNamedEntity.id.asc()).all()
    return templates.TemplateResponse(request, "admin_entity_review.html", {"request": request, "pending": pending})


@router.post("/entity-review/{row_id}/approve", response_class=HTMLResponse)
async def approve_entity(
    request: Request,
    row_id: int,
    admin_user: str = Depends(require_admin),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    row = BeneficiaryEngine().review_entity(db, row_id=row_id, decision="approved", reviewer=admin_user)
    if row is None:
        raise HTTPException(status_code=404, detail="Row not found")
    return templates.TemplateResponse(
        request,
        "partials/entity_review_result.html",
        {"request": request, "row": row, "decision": "approved"},
    )


@router.post("/entity-review/{row_id}/reject", response_class=HTMLResponse)
async def reject_entity(
    request: Request,
    row_id: int,
    admin_user: str = Depends(require_admin),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    row = BeneficiaryEngine().review_entity(db, row_id=row_id, decision="rejected", reviewer=admin_user)
    if row is None:
        raise HTTPException(status_code=404, detail="Row not found")
    return templates.TemplateResponse(
        request,
        "partials/entity_review_result.html",
        {"request": request, "row": row, "decision": "rejected"},
    )
