"""
Test for dashboard service functionality.
"""
import pytest
from datetime import date, datetime
from sqlalchemy.orm import Session

from app.services.dashboard_service import DashboardService
from app.schemas import DashboardStatsResponse
from app.models import Booking, Guest, Payment


def test_dashboard_stats_empty_year(db: Session):
    """Test dashboard stats for a year with no data."""
    dashboard_service = DashboardService(db)
    stats = dashboard_service.get_dashboard_stats(2020)
    
    assert stats.total_bookings == 0
    assert stats.total_invoice_amount == 0.0
    assert stats.total_occupied_nights == 0
    assert stats.year == 2020


def test_dashboard_stats_with_data(db: Session):
    """Test dashboard stats with sample data."""
    # Create a test guest
    guest = Guest(
        first_name="Test",
        last_name="Guest",
        email="test@example.com",
        hashed_password="hashed_password"
    )
    db.add(guest)
    db.commit()
    
    # Create a booking in 2024
    booking = Booking(
        guest_id=guest.id,
        check_in=date(2024, 6, 1),
        check_out=date(2024, 6, 15),
        confirmed=True
    )
    db.add(booking)
    db.commit()
    
    # Create a payment in 2024
    payment = Payment(
        booking_id=booking.id,
        amount=1000.0,
        payment_date=date(2024, 7, 1)
    )
    db.add(payment)
    db.commit()
    
    dashboard_service = DashboardService(db)
    stats = dashboard_service.get_dashboard_stats(2024)
    
    assert stats.total_bookings == 1
    assert stats.total_invoice_amount == 1000.0
    assert stats.total_occupied_nights == 14  # 15 - 1 = 14 nights
    assert stats.year == 2024


def test_dashboard_stats_year_parameter(db: Session):
    """Test that year parameter works correctly."""
    dashboard_service = DashboardService(db)
    
    # Test with explicit year
    stats_2023 = dashboard_service.get_dashboard_stats(2023)
    assert stats_2023.year == 2023
    
    # Test with None (should default to current year)
    current_year = date.today().year
    stats_default = dashboard_service.get_dashboard_stats(None)
    assert stats_default.year == current_year


