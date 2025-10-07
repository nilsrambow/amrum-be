from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.alert_service import AlertService
from app.services.booking_status_service import BookingStatusService
from app.auth_dependencies import get_current_admin

router = APIRouter()


@router.get("/alerts/pending-emails")
def get_pending_emails(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get all pending email alerts calculated on the fly."""
    alert_service = AlertService(db)
    return alert_service.get_pending_emails()


@router.get("/alerts/outstanding-guest-actions")
def get_outstanding_guest_actions(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get all outstanding guest actions that need attention."""
    alert_service = AlertService(db)
    return alert_service.get_outstanding_guest_actions()


@router.post("/alerts/update-booking-statuses")
def update_booking_statuses(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Manually update all booking statuses (for testing)."""
    status_service = BookingStatusService(db)
    updated_count = status_service.update_all_booking_statuses()
    return {
        "message": f"Updated {updated_count} booking statuses",
        "updated_count": updated_count
    } 