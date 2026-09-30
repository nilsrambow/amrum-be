import datetime

from app.services import waste_service
from app.services.waste_service import Pickup, parse_calendar, pickup_window, pickups_for_stay

D = datetime.date

ICS = """BEGIN:VCALENDAR
BEGIN:VEVENT
DTSTART;VALUE=DATE:20260107
SUMMARY:gelbe Tonne
END:VEVENT
BEGIN:VEVENT
DTSTART;VALUE=DATE:20260112
SUMMARY:graue Tonne 4-wö.
END:VEVENT
BEGIN:VEVENT
DTSTART;VALUE=DATE:20260121
SUMMARY:grüne Tonne 4-wö.
END:VEVENT
BEGIN:VEVENT
DTSTART;VALUE=DATE:20260122
SUMMARY:Sperrmüll
END:VEVENT
END:VCALENDAR
"""


def test_parse_calendar_maps_bins_and_skips_unknown():
    assert parse_calendar(ICS) == (
        Pickup(D(2026, 1, 7), "plastik"),
        Pickup(D(2026, 1, 12), "restmuell"),
        Pickup(D(2026, 1, 21), "papier"),
    )


def test_parse_calendar_handles_folded_lines():
    folded = "BEGIN:VEVENT\r\nDTSTART;VALUE=DATE:20260107\r\nSUMMARY:gelbe\r\n  Tonne\r\nEND:VEVENT\r\n"
    assert parse_calendar(folded) == (Pickup(D(2026, 1, 7), "plastik"),)


def test_window_next_guest_arrives_right_away():
    # same-day and next-day turnover: only the day after departure
    assert pickup_window(D(2026, 7, 1), D(2026, 7, 8), D(2026, 7, 8)) == (D(2026, 7, 2), D(2026, 7, 9))
    assert pickup_window(D(2026, 7, 1), D(2026, 7, 8), D(2026, 7, 9)) == (D(2026, 7, 2), D(2026, 7, 9))


def test_window_house_stays_empty():
    assert pickup_window(D(2026, 7, 1), D(2026, 7, 8), None) == (D(2026, 7, 2), D(2026, 7, 13))
    # next arrival far away is capped at 5 days
    assert pickup_window(D(2026, 7, 1), D(2026, 7, 8), D(2026, 8, 1)) == (D(2026, 7, 2), D(2026, 7, 13))


def test_window_ends_at_next_arrival_if_sooner_than_five_days():
    assert pickup_window(D(2026, 7, 1), D(2026, 7, 8), D(2026, 7, 11)) == (D(2026, 7, 2), D(2026, 7, 11))


def test_pickups_for_stay_filters_by_window():
    pickups = parse_calendar(ICS)
    # window 2026-01-02 .. 2026-01-13 (empty house afterwards)
    result = pickups_for_stay(D(2026, 1, 1), D(2026, 1, 8), None, pickups)
    assert result == [Pickup(D(2026, 1, 7), "plastik"), Pickup(D(2026, 1, 12), "restmuell")]
    # next guest arrives right away: window ends 2026-01-09
    result = pickups_for_stay(D(2026, 1, 1), D(2026, 1, 8), D(2026, 1, 8), pickups)
    assert result == [Pickup(D(2026, 1, 7), "plastik")]


def test_pickups_for_stay_without_calendar_coverage_is_none():
    pickups = parse_calendar(ICS)
    assert pickups_for_stay(D(2027, 3, 1), D(2027, 3, 8), None, pickups) is None
    assert pickups_for_stay(D(2026, 12, 28), D(2027, 1, 3), None, pickups) is None
    assert pickups_for_stay(D(2026, 3, 1), D(2026, 3, 8), None, ()) is None


def test_shipped_calendar_is_readable():
    pickups = waste_service.load_pickups()
    assert len(pickups) == 52
    assert {p.bin_type for p in pickups} == {"plastik", "restmuell", "papier"}
