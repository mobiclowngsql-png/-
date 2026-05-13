"""NetGuard Pro - User Management Endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
router = APIRouter()

@router.get("/")
async def list_users():
    return {"users": []}
