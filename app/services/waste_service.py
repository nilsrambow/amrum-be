"""Waste collection dates for the house (AWNF, Nebel ohne Süddorf und Steenodde).

The dates come from an ICS export of the AWNF widget that is stored in
data/abfuhrtermine_nebel.ics. AWNF publishes a new calendar every year, replace
the file then (a calendar year that is not covered simply yields no dates).
"""
import datetime
import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import List, NamedTuple, Optional, Tuple

logger = logging.getLogger(__name__)

CALENDAR_PATH = Path(__file__).resolve().parents[2] / "data" / "abfuhrtermine_nebel.ics"

# Days after check-out that still count when the house stays empty
MAX_DAYS_EMPTY = 5

# Summary keyword in the calendar -> bin type used in the API
BIN_KEYWORDS = (
    ("gelb", "plastik"),
    ("grau", "restmuell"),
    ("grün", "papier"),
)


class Pickup(NamedTuple):
    date: datetime.date
    bin_type: str


def _unfold(text: str) -> List[str]:
    """Undo ICS line folding (continuation lines start with a space or tab)."""
    lines: List[str] = []
    for line in text.splitlines():
        if line[:1] in (" ", "\t") and lines:
            lines[-1] += line[1:]
        else:
            lines.append(line)
    return lines


def parse_calendar(text: str) -> Tuple[Pickup, ...]:
    pickups: List[Pickup] = []
    start: Optional[datetime.date] = None
    summary = ""
    for line in _unfold(text):
        if line == "BEGIN:VEVENT":
            start, summary = None, ""
        elif line.startswith("DTSTART"):
            match = re.search(r":(\d{8})", line)
            if match:
                start = datetime.datetime.strptime(match.group(1), "%Y%m%d").date()
        elif line.startswith("SUMMARY:"):
            summary = line[len("SUMMARY:"):].casefold()
        elif line == "END:VEVENT" and start:
            bin_type = next((b for keyword, b in BIN_KEYWORDS if keyword in summary), None)
            if bin_type:
                pickups.append(Pickup(start, bin_type))
            else:
                logger.warning("Unknown waste calendar entry on %s: %r", start, summary)
    return tuple(sorted(pickups))


@lru_cache(maxsize=4)
def load_pickups(path: Path = CALENDAR_PATH) -> Tuple[Pickup, ...]:
    try:
        return parse_calendar(path.read_text(encoding="utf-8"))
    except OSError as e:
        logger.error("Waste calendar %s could not be read: %s", path, e)
        return ()


def pickup_window(
    check_in: datetime.date,
    check_out: datetime.date,
    next_check_in: Optional[datetime.date],
) -> Tuple[datetime.date, datetime.date]:
    """Days for which the guest has to put out bins (first and last collection day).

    Starts the day after arrival. Ends the day after departure when the next guest
    arrives right away, otherwise when the next guest arrives (or after
    MAX_DAYS_EMPTY days if nobody is booked).
    """
    one_day = datetime.timedelta(days=1)
    start = check_in + one_day
    latest = check_out + datetime.timedelta(days=MAX_DAYS_EMPTY)
    if next_check_in is None:
        end = latest
    elif next_check_in <= check_out + one_day:
        end = check_out + one_day
    else:
        end = min(latest, next_check_in)
    return start, end


def pickups_for_stay(
    check_in: datetime.date,
    check_out: datetime.date,
    next_check_in: Optional[datetime.date] = None,
    pickups: Optional[Tuple[Pickup, ...]] = None,
) -> Optional[List[Pickup]]:
    """Collections the guest has to care about, or None if the calendar does not cover the stay."""
    pickups = load_pickups() if pickups is None else pickups
    start, end = pickup_window(check_in, check_out, next_check_in)

    covered_years = {p.date.year for p in pickups}
    if not {start.year, end.year} <= covered_years:
        return None
    return [p for p in pickups if start <= p.date <= end]
