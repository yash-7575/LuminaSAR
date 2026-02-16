"""SAR generation and management routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import time
import traceback

from app.database import get_db
from app.models.customer import Customer
from app.models.transaction import Transaction
from app.models.sar_case import SARCase
from app.models.sar_narrative import SARNarrative
from app.models.audit_trail import AuditTrail
from app.schemas.request import GenerateSARRequest, ApproveSARRequest
from app.schemas.response import (
    GenerateResponse,
    SARResponse,
    AuditTrailResponse,
    AuditStepResponse,
    CaseResponse,
    StatsResponse,
)

router = APIRouter()


@router.post("/generate", response_model=GenerateResponse)
async def generate_sar(request: GenerateSARRequest, db: Session = Depends(get_db)):
    """Generate a SAR narrative for a given case ID."""
    start_time = time.time()

    # Find the case
    case = db.query(SARCase).filter(SARCase.case_id == request.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {request.case_id} not found")

    # Check if narrative already exists
    if not request.force_regenerate:
        existing = (
            db.query(SARNarrative)
            .filter(SARNarrative.case_id == request.case_id)
            .first()
        )
        if existing:
            return GenerateResponse(
                narrative_id=str(existing.narrative_id),
                case_id=str(case.case_id),
                narrative_text=existing.narrative_text,
                risk_score=float(case.risk_score) if case.risk_score else 0.0,
                typologies=case.typologies or [],
                generation_time_seconds=existing.generation_time_seconds or 0,
                audit_steps=db.query(AuditTrail)
                .filter(AuditTrail.narrative_id == existing.narrative_id)
                .count(),
            )

    try:
        # Import workflow
        from app.services.langgraph_workflow import run_sar_workflow

        result = await run_sar_workflow(
            str(case.case_id), str(case.customer_id), db,
            jurisdiction=request.jurisdiction,
        )

        generation_time = int(time.time() - start_time)

        return GenerateResponse(
            narrative_id=result["narrative_id"],
            case_id=str(case.case_id),
            narrative_text=result["narrative"],
            risk_score=result["risk_score"],
            typologies=result["typologies"],
            generation_time_seconds=generation_time,
            audit_steps=result["audit_steps"],
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"SAR generation failed: {str(e)}")


@router.get("/{narrative_id}", response_model=SARResponse)
async def get_narrative(narrative_id: str, db: Session = Depends(get_db)):
    """Get a specific SAR narrative by ID."""
    narrative = (
        db.query(SARNarrative).filter(SARNarrative.narrative_id == narrative_id).first()
    )

    if not narrative:
        raise HTTPException(status_code=404, detail="Narrative not found")

    case = db.query(SARCase).filter(SARCase.case_id == narrative.case_id).first()
    customer = (
        db.query(Customer).filter(Customer.customer_id == case.customer_id).first()
        if case
        else None
    )

    return SARResponse(
        narrative_id=str(narrative.narrative_id),
        case_id=str(narrative.case_id),
        narrative_text=narrative.narrative_text,
        risk_score=float(case.risk_score) if case and case.risk_score else None,
        typologies=case.typologies if case else [],
        generated_at=narrative.generated_at.isoformat()
        if narrative.generated_at
        else None,
        generation_time_seconds=narrative.generation_time_seconds,
        customer_name=customer.name if customer else None,
        customer_account=customer.account_number if customer else None,
        status=case.status if case else None,
    )


@router.get("/{narrative_id}/audit", response_model=AuditTrailResponse)
async def get_audit_trail(narrative_id: str, db: Session = Depends(get_db)):
    """Get the complete audit trail for a SAR narrative."""
    audit_entries = (
        db.query(AuditTrail)
        .filter(AuditTrail.narrative_id == narrative_id)
        .order_by(AuditTrail.logged_at)
        .all()
    )

    if not audit_entries:
        raise HTTPException(status_code=404, detail="Audit trail not found")

    # Verify hash chain integrity
    chain_valid = True
    for i in range(1, len(audit_entries)):
        if audit_entries[i].previous_hash != audit_entries[i - 1].current_hash:
            chain_valid = False
            break

    steps = [
        AuditStepResponse(
            audit_id=str(entry.audit_id),
            step_name=entry.step_name,
            data_sources=entry.data_sources or {},
            reasoning=entry.reasoning or {},
            confidence_scores=entry.confidence_scores or {},
            logged_at=entry.logged_at.isoformat() if entry.logged_at else None,
            previous_hash=entry.previous_hash,
            current_hash=entry.current_hash,
        )
        for entry in audit_entries
    ]

    # Get sentence attribution from the last audit step
    sentence_attribution = {}
    if audit_entries:
        last = audit_entries[-1]
        if last.data_sources and "sentence_attribution" in last.data_sources:
            sentence_attribution = last.data_sources["sentence_attribution"]

    return AuditTrailResponse(
        narrative_id=narrative_id,
        chain_valid=chain_valid,
        steps=steps,
        sentence_attribution=sentence_attribution,
    )


@router.post("/{narrative_id}/approve")
async def approve_sar(
    narrative_id: str, request: ApproveSARRequest, db: Session = Depends(get_db)
):
    """Approve a SAR narrative for filing."""
    narrative = (
        db.query(SARNarrative).filter(SARNarrative.narrative_id == narrative_id).first()
    )

    if not narrative:
        raise HTTPException(status_code=404, detail="Narrative not found")

    case = db.query(SARCase).filter(SARCase.case_id == narrative.case_id).first()
    if case:
        case.status = "approved"
        db.commit()

    return {
        "message": "SAR approved successfully",
        "narrative_id": narrative_id,
        "status": "approved",
        "approved_by": request.analyst_name,
    }


@router.get("/", response_model=List[CaseResponse])
async def get_recent_cases(limit: int = 20, db: Session = Depends(get_db)):
    """Get recent SAR cases."""
    cases = db.query(SARCase).order_by(SARCase.created_at.desc()).limit(limit).all()

    result = []
    for case in cases:
        customer = (
            db.query(Customer).filter(Customer.customer_id == case.customer_id).first()
        )

        has_narrative = (
            db.query(SARNarrative).filter(SARNarrative.case_id == case.case_id).count()
            > 0
        )

        result.append(
            CaseResponse(
                case_id=str(case.case_id),
                customer_name=customer.name if customer else "Unknown",
                customer_account=customer.account_number if customer else "N/A",
                status=case.status or "pending",
                risk_score=float(case.risk_score) if case.risk_score else None,
                typologies=case.typologies or [],
                created_at=case.created_at.isoformat() if case.created_at else None,
                has_narrative=has_narrative,
            )
        )

    return result


@router.get("/stats/overview", response_model=StatsResponse)
async def get_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics."""
    total_sars = db.query(SARNarrative).count()
    pending_cases = db.query(SARCase).filter(SARCase.status == "pending").count()
    total_customers = db.query(Customer).count()

    # Average generation time
    avg_time = db.query(func.avg(SARNarrative.generation_time_seconds)).scalar()
    avg_time = float(avg_time) if avg_time else 0.0

    # High risk cases (score > 7)
    high_risk = db.query(SARCase).filter(SARCase.risk_score > 7).count()

    # Estimated cost savings: ₹5000/SAR manual cost, each SAR saved ~5 hours
    cost_savings = total_sars * 5000 / 100000  # In lakhs

    return StatsResponse(
        total_sars=total_sars,
        pending_cases=pending_cases,
        avg_generation_time=round(avg_time, 1),
        total_customers=total_customers,
        high_risk_cases=high_risk,
        cost_savings_lakhs=round(cost_savings, 1),
    )
