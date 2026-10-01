import logging
from datetime import date, timedelta

from app.models import Booking
from app.services.communication_service import CommunicationService
from app.services.kurkarten_service import KurkartenService
from app.services.token_service import TokenService


def test_pre_arrival_email_contains_magic_link(db_session, test_guest, caplog, monkeypatch):
    monkeypatch.setenv("SEND_REAL_EMAILS", "false")
    booking = Booking(
        guest_id=test_guest.id,
        check_in=date.today() + timedelta(days=3),
        check_out=date.today() + timedelta(days=10),
        confirmed=True,
        kurtaxe_amount=0,
    )
    db_session.add(booking)
    db_session.commit()
    token = TokenService(db_session).generate_token(booking.id)
    communication_service = CommunicationService(
        {"sender": "test@example.com"}, base_url="https://example.test"
    )
    service = KurkartenService(db_session, communication_service)

    with caplog.at_level(logging.INFO):
        assert service.send_pre_arrival_email(booking.id) is True

    assert communication_service.generate_magic_link(token) in caplog.text
