"""NetGuard Pro - Firewall Management Endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.rbac import PermissionChecker, ResourceType, Action
router = APIRouter()

@router.get("/rules")
async def list_firewall_rules(_ : bool = Depends(PermissionChecker(ResourceType.FIREWALL_RULE, Action.READ))):
    return {"rules": []}
