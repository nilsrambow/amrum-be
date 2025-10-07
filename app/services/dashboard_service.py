"""
Dashboard statistics service for providing summary data.
"""
import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract

from app.models import Booking, Payment
from app.schemas import DashboardStatsResponse


class DashboardService:
    """Service for calculating dashboard statistics."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_dashboard_stats(self, year: int = None) -> DashboardStatsResponse:
        """
        Get dashboard statistics for a specific year.
        
        Args:
            year: The year to get statistics for. Defaults to current year.
            
        Returns:
            DashboardStatsResponse with aggregated statistics
        """
        if year is None:
            year = datetime.date.today().year
        
        # Calculate date range for the year
        year_start = datetime.date(year, 1, 1)
        year_end = datetime.date(year, 12, 31)
        
        # Total bookings: count bookings where check_in is in the specified year
        total_bookings = self.db.query(Booking).filter(
            and_(
                Booking.check_in >= year_start,
                Booking.check_in <= year_end,
                Booking.confirmed == True
            )
        ).count()
        
        # Total occupied nights: sum of (check_out - check_in) for bookings in the year
        occupied_nights_result = self.db.query(
            func.sum(Booking.check_out - Booking.check_in)
        ).filter(
            and_(
                Booking.check_in >= year_start,
                Booking.check_in <= year_end,
                Booking.confirmed == True
            )
        ).scalar()
        
        total_occupied_nights = int(occupied_nights_result.days) if occupied_nights_result else 0
        
        # Total invoice amount: sum of payments made in the specified year
        # Note: This uses payment_date for the year calculation as per requirements
        total_invoice_amount_result = self.db.query(
            func.sum(Payment.amount)
        ).join(Booking).filter(
            and_(
                Payment.payment_date >= year_start,
                Payment.payment_date <= year_end,
                Booking.confirmed == True
            )
        ).scalar()
        
        total_invoice_amount = float(total_invoice_amount_result) if total_invoice_amount_result else 0.0
        
        return DashboardStatsResponse(
            total_bookings=total_bookings,
            total_invoice_amount=total_invoice_amount,
            total_occupied_nights=total_occupied_nights,
            year=year
        )
    
    def get_yearly_comparison(self, current_year: int = None) -> Dict[str, Any]:
        """
        Get comparison data between current year and previous year.
        
        Args:
            current_year: The year to compare. Defaults to current year.
            
        Returns:
            Dictionary with current and previous year statistics
        """
        if current_year is None:
            current_year = datetime.date.today().year
        
        previous_year = current_year - 1
        
        current_stats = self.get_dashboard_stats(current_year)
        previous_stats = self.get_dashboard_stats(previous_year)
        
        return {
            "current_year": {
                "year": current_stats.year,
                "total_bookings": current_stats.total_bookings,
                "total_invoice_amount": current_stats.total_invoice_amount,
                "total_occupied_nights": current_stats.total_occupied_nights
            },
            "previous_year": {
                "year": previous_stats.year,
                "total_bookings": previous_stats.total_bookings,
                "total_invoice_amount": previous_stats.total_invoice_amount,
                "total_occupied_nights": previous_stats.total_occupied_nights
            },
            "comparison": {
                "bookings_change": current_stats.total_bookings - previous_stats.total_bookings,
                "invoice_amount_change": current_stats.total_invoice_amount - previous_stats.total_invoice_amount,
                "occupied_nights_change": current_stats.total_occupied_nights - previous_stats.total_occupied_nights
            }
        }


