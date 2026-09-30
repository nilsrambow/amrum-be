import logging

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.api.routes.guest_booking_router import guest_privacy_headers
from app.logging_filters import MaskGuestTokenFilter, mask_guest_token
from app.schemas import GuestBookingResponse

TOKEN = "3oENxdpUEPm_AnXSbv3ts6ta_ZHBswiOHaHAFIjQvjE"


def test_mask_guest_token_in_paths():
    assert mask_guest_token(f"/guest/booking/{TOKEN}") == "/guest/booking/***"
    assert mask_guest_token(f"/guest/booking/{TOKEN}/readings") == "/guest/booking/***/readings"
    assert mask_guest_token(f"GET /guest/booking/{TOKEN}?x=1 HTTP/1.1") == "GET /guest/booking/***?x=1 HTTP/1.1"
    # other paths stay untouched
    assert mask_guest_token("/bookings/12") == "/bookings/12"


def test_filter_masks_uvicorn_access_record():
    # uvicorn logs: '%s - "%s %s HTTP/%s" %d' with client, method, path, http version, status
    record = logging.LogRecord(
        "uvicorn.access", logging.INFO, __file__, 1,
        '%s - "%s %s HTTP/%s" %d',
        ("172.18.0.1:34384", "GET", f"/guest/booking/{TOKEN}", "1.1", 200), None,
    )
    assert MaskGuestTokenFilter().filter(record) is True
    assert TOKEN not in record.getMessage()
    assert '"GET /guest/booking/*** HTTP/1.1" 200' in record.getMessage()


def test_guest_privacy_headers():
    app = FastAPI()

    @app.get("/x", dependencies=[Depends(guest_privacy_headers)])
    def x():
        return {"ok": True}

    response = TestClient(app).get("/x")
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-robots-tag"] == "noindex, nofollow"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_guest_response_has_no_email_or_surname():
    fields = GuestBookingResponse.model_fields
    assert "guest_first_name" in fields
    assert "guest_email" not in fields
    assert "guest_name" not in fields
