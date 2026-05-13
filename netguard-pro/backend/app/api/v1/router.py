"""
NetGuard Pro - API v1 Router

Main router that includes all v1 API endpoints.
"""

from fastapi import APIRouter

from app.api.v1 import auth, users, firewall, billing, monitoring

# Create main API router for v1
api_router = APIRouter()

# Include sub-routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(firewall.router, prefix="/firewall", tags=["Firewall"])
api_router.include_router(billing.router, prefix="/billing", tags=["Billing"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["Monitoring"])

# Health and status endpoints are in main.py
