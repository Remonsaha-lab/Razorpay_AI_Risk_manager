"""API routes — HTTP input/output only, never core decisions."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Verify the API is running."""
    return {"status": "healthy", "service": "DisputeGuard"}


@router.get("/cases")
async def list_cases():
    """Return available synthetic dispute cases."""
    # Placeholder — will load from data/fixtures/ in Step 5
    return {
        "cases": [
            {
                "id": "DSP-2026-001",
                "amount_inr": 18400,
                "reason": "Merchandise/services not received",
                "status": "pending_review",
            }
        ]
    }


@router.get("/cases/{case_id}")
async def get_case(case_id: str):
    """Return a single dispute case by ID."""
    # Placeholder — will load full case from fixtures
    if case_id == "DSP-2026-001":
        return {
            "id": "DSP-2026-001",
            "amount_inr": 18400,
            "reason": "Merchandise/services not received",
            "respond_by": "2026-09-04T18:00:00+05:30",
            "status": "pending_review",
        }
    return {"error": f"Case {case_id} not found"}
