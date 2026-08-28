"""API routes - HTTP input/output only, never core decisions."""

from fastapi import APIRouter, HTTPException, status

from backend.services.case_loader import store
from backend.workflow.engine import run_workflow
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel
from backend.domain.enums import DisputeAction
from backend.services.packet_generator import generate_dispute_packet_pdf


router = APIRouter()
_workflow_results: dict[str, dict] = {}
_approved_cases : dict[str , dict] = {} # In memory approval store

@router.get("/health")
async def health_check():
    """Verify the API is running."""
    return {"status": "healthy", "service": "DisputeGuard"}


@router.get("/cases")
async def list_cases():
    """Return summary data for all available synthetic dispute cases."""
    cases = store.get_all_disputes()
    return {
        "cases": [
            {
                "id": case.id,
                "merchant_name": case.merchant_name,
                "amount": case.amount,
                "currency": case.currency,
                "reason": case.reason,
                "status": case.status,
                "respond_by": case.respond_by,
                "risk_level": case.risk_level,
            }
            for case in cases
        ]
    }


@router.get("/cases/{case_id}")
async def get_case(case_id: str):
    """Return one synthetic dispute with its evidence and fixture metadata."""
    case = store.get_dispute(case_id)
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {case_id} not found",
        )

    return {
        "case": case,
        "evidence_documents": store.get_documents_for_dispute(case_id),
        "metadata": store.get_case_metadata(case_id),
    }


@router.post("/cases/{case_id}/run")
async def run_case(case_id: str):
    """Run extraction and deterministic validation for one case."""
    case = store.get_dispute(case_id)
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case {case_id} not found")
    result = run_workflow(case, store.get_documents_for_dispute(case_id))
    _workflow_results[case_id] = result
    return result


@router.get("/cases/{case_id}/decision")
async def get_decision(case_id: str):
    """Return the most recent workflow result for a case."""
    if store.get_dispute(case_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case {case_id} not found")
    result = _workflow_results.get(case_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case has not been run yet")
    return {"decision": result["decision"], "issues": result["issues"], "missing_evidence": result["missing_evidence"]}


@router.get("/cases/{case_id}/evidence")
async def get_evidence(case_id: str):
    """Return extracted claims when available, otherwise source documents."""
    if store.get_dispute(case_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case {case_id} not found")
    result = _workflow_results.get(case_id)
    if result is None:
        return {"claims": [], "documents": store.get_documents_for_dispute(case_id)}
    return {"claims": result["claims"], "documents": store.get_documents_for_dispute(case_id)}


class ApprovalRequest(BaseModel):
    approved_by: str = "Merchant Reviewer"
    narrative: str | None = None
    notes: str | None = None
# ── Add Approval Route ───────────────────────────────────────────────────────
@router.post("/cases/{case_id}/approve")
async def approve_case(case_id: str, request: ApprovalRequest = ApprovalRequest()):
    """
    Explicit human reviewer approval for a CONTEST recommendation.
    Rejects cases that do not have a CONTEST action recommendation.
    """
    case = store.get_dispute(case_id)
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case {case_id} not found")
    result = _workflow_results.get(case_id)
    if result is None:
        # Run workflow if not yet executed
        result = run_workflow(case, store.get_documents_for_dispute(case_id))
        _workflow_results[case_id] = result
    decision = result["decision"]
    if decision.action != DisputeAction.CONTEST:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve case with action '{decision.action.value}'. Only 'contest' cases can be approved for representment.",
        )
    approval_record = {
        "dispute_id": case_id,
        "approved_by": request.approved_by,
        "approved_at": datetime.now(timezone.utc).strftime("%d-%b-%Y %H:%M UTC"),
        "narrative": request.narrative,
        "notes": request.notes,
    }
    _approved_cases[case_id] = approval_record
    return {"status": "approved", "approval": approval_record}
@router.get("/cases/{case_id}/approval")
async def get_approval(case_id: str):
    """Check approval status of a case."""
    approval = _approved_cases.get(case_id)
    return {"is_approved": approval is not None, "approval": approval}
# ── Add Packet Download Route ────────────────────────────────────────────────
@router.get("/cases/{case_id}/packet")
async def download_packet(case_id: str):
    """
    Generate and download a submission-ready PDF packet for an approved CONTEST case.
    Rejects unapproved cases.
    """
    case = store.get_dispute(case_id)
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case {case_id} not found")
    result = _workflow_results.get(case_id)
    if result is None or result["decision"].action != DisputeAction.CONTEST:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Packet generation requires a completed CONTEST decision.",
        )
    approval = _approved_cases.get(case_id)
    if approval is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Human reviewer approval is required before downloading the evidence packet.",
        )
    pdf_bytes = generate_dispute_packet_pdf(
        dispute=case,
        decision=result["decision"],
        documents=store.get_documents_for_dispute(case_id),
        claims=result["claims"],
        approval_info=approval,
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="DisputeGuard_Packet_{case_id}.pdf"'
        },
    )
