"""Analytics dashboard endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..services import analytics as analytics_service

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/overview", response_model=schemas.AnalyticsOverview)
def analytics_overview(db: Session = Depends(get_db)):
    return analytics_service.overview(db)
