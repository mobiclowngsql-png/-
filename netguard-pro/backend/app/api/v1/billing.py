"""NetGuard Pro - Billing Management Endpoints."""
from fastapi import APIRouter
router = APIRouter()

@router.get("/accounts")
async def list_accounts():
    return {"accounts": []}
