"""
Dashboard router for providing summary statistics and analytics.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.dashboard_service import DashboardService
from app.schemas import DashboardStatsResponse
from app.auth_dependencies import get_current_admin

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    year: Optional[int] = Query(None, description="Year to get statistics for. Defaults to current year."),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Get dashboard statistics for a specific year.
    
    - **year**: The year to get statistics for. If not provided, defaults to current year.
    
    Returns:
    - **total_bookings**: Number of confirmed bookings with check-in in the specified year
    - **total_invoice_amount**: Total amount of payments made in the specified year
    - **total_occupied_nights**: Total number of occupied nights for bookings in the specified year
    - **year**: The year the statistics are for
    
    Business Rules:
    - A booking is counted for the year if its check-in date is in that year
    - Invoice amounts are counted for the year based on payment date
    - New Year's Eve is considered part of the old year
    """
    dashboard_service = DashboardService(db)
    return dashboard_service.get_dashboard_stats(year)


@router.get("/stats/comparison")
async def get_yearly_comparison(
    current_year: Optional[int] = Query(None, description="Year to compare. Defaults to current year."),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Get comparison data between current year and previous year.
    
    - **current_year**: The year to compare. If not provided, defaults to current year.
    
    Returns:
    - **current_year**: Statistics for the specified year
    - **previous_year**: Statistics for the previous year
    - **comparison**: Changes between current and previous year
    """
    dashboard_service = DashboardService(db)
    return dashboard_service.get_yearly_comparison(current_year)


