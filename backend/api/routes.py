"""API routes - HTTP input/output only, never core decisions."""

from fastapi import APIRouter, HTTPException, status

from backend.services.case_loader import store
from backend.workflow.engine import run_workflow

router = APIRouter()
_workflow_results: dict[str, dict] = {}


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
