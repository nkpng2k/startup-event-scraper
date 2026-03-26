"""Luma event scrapers for luma.com/boston and luma.com/ai."""

import json
from datetime import datetime, timedelta, timezone
from urllib.request import urlopen, Request
from urllib.parse import urlencode

from models import Event

LUMA_BOSTON_URL = "https://luma.com/boston"
LUMA_AI_URL = "https://luma.com/ai"
LUMA_API_URL = "https://api.lu.ma/discover/get-paginated-events"

BOSTON_LAT = 42.35843
BOSTON_LNG = -71.05977
ET_OFFSET = timezone(timedelta(hours=-4))

BOSTON_REGION_STATES = {"Massachusetts", "MA"}
BOSTON_REGION_CITIES = {
    "boston", "cambridge", "somerville", "brookline", "medford",
    "quincy", "newton", "watertown", "waltham", "chelsea",
    "revere", "everett", "malden", "arlington", "belmont",
    "allston", "brighton", "charlestown", "dorchester", "roxbury",
    "jamaica plain", "south boston", "back bay", "fenway",
    "needham", "wellesley", "natick", "framingham", "lexington",
    "concord", "woburn", "burlington", "bedford", "lowell",
    "worcester", "salem", "lynn", "brockton",
}


def _api_get(url: str, params: dict) -> dict:
    full_url = f"{url}?{urlencode(params)}"
    req = Request(full_url, headers={
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    })
    with urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def _fetch_paginated(params: dict, max_pages: int = 10) -> list[dict]:
    all_entries = []
    for _ in range(max_pages):
        data = _api_get(LUMA_API_URL, params)
        all_entries.extend(data.get("entries", []))
        if not data.get("has_more") or not data.get("next_cursor"):
            break
        params["pagination_cursor"] = data["next_cursor"]
    return all_entries


def _format_date(entry: dict) -> str:
    event = entry.get("event", {})
    start = event.get("start_at", "")
    if not start:
        return ""
    try:
        dt_utc = datetime.fromisoformat(start.replace("Z", "+00:00"))
        dt_et = dt_utc.astimezone(ET_OFFSET)
        return dt_et.strftime("%B %d, %Y %I:%M %p")
    except (ValueError, TypeError):
        return start


def _entry_to_event(entry: dict, source: str) -> Event:
    event = entry.get("event", {})
    ticket = entry.get("ticket_info", {})

    name = event.get("name", "Untitled Event")
    date = _format_date(entry)
    reg_link = f"https://lu.ma/{event.get('url', '')}" if event.get("url") else ""
    description = event.get("description_short", "") or ""

    if ticket.get("is_free"):
        cost = "Free"
    elif ticket.get("price"):
        raw = ticket["price"]
        if isinstance(raw, dict) and "cents" in raw:
            cost = f"${raw['cents'] / 100:.2f}"
        elif isinstance(raw, (int, float)):
            cost = f"${raw / 100:.2f}" if raw > 100 else f"${raw}"
        else:
            cost = "Not listed"
    else:
        cost = "Not listed"

    return Event(
        name=name,
        date=date,
        cost=cost,
        description=description,
        registration_link=reg_link,
        source=source,
    )


def _is_within_2_weeks(entry: dict) -> bool:
    event = entry.get("event", {})
    start = event.get("start_at", "")
    if not start:
        return False
    try:
        dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        tomorrow = datetime.now(dt.tzinfo).replace(
            hour=0, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)
        cutoff = tomorrow + timedelta(days=14)
        return tomorrow <= dt <= cutoff
    except (ValueError, TypeError):
        return False


def _is_boston_area(entry: dict) -> bool:
    event = entry.get("event", {})
    geo = event.get("geo_address_info") or {}

    city = (geo.get("city") or "").lower().strip()
    region = (geo.get("region") or "").strip()
    city_state = (geo.get("city_state") or "").lower()

    if city in BOSTON_REGION_CITIES:
        return True
    if region in BOSTON_REGION_STATES:
        return True
    if "massachusetts" in city_state:
        return True
    return False


def _dedup_entries(entries: list[dict]) -> list[dict]:
    seen = set()
    deduped = []
    for e in entries:
        key = (e["event"].get("name", "").strip().lower(), e["event"].get("start_at", "")[:10])
        if key not in seen:
            seen.add(key)
            deduped.append(e)
    return deduped


def scrape_luma_boston() -> list[Event]:
    """Scrape events from luma.com/boston using the Luma public API."""
    print(f"Scraping: {LUMA_BOSTON_URL}")

    entries = _fetch_paginated({"city_slug": "boston", "pagination_limit": "50"})
    print(f"  Retrieved {len(entries)} events from Luma Boston")

    filtered = _dedup_entries([e for e in entries if _is_within_2_weeks(e)])
    filtered.sort(key=lambda e: e["event"].get("start_at", ""))
    print(f"  {len(filtered)} unique events in the next 2 weeks")

    events = [_entry_to_event(e, LUMA_BOSTON_URL) for e in filtered]
    print(f"  Returning {len(events)} events")
    return events


def scrape_luma_ai() -> list[Event]:
    """Scrape AI events near Boston from luma.com/ai using the Luma public API."""
    print(f"Scraping: {LUMA_AI_URL} (filtered to Boston area)")

    params = {
        "slug": "ai",
        "latitude": str(BOSTON_LAT),
        "longitude": str(BOSTON_LNG),
        "pagination_limit": "50",
    }
    entries = _fetch_paginated(params)
    print(f"  Retrieved {len(entries)} AI events near Boston coordinates")

    filtered = _dedup_entries([
        e for e in entries
        if _is_within_2_weeks(e) and _is_boston_area(e)
    ])
    filtered.sort(key=lambda e: e["event"].get("start_at", ""))
    print(f"  {len(filtered)} unique Boston-area AI events in the next 2 weeks")

    events = [_entry_to_event(e, LUMA_AI_URL) for e in filtered]
    print(f"  Returning {len(events)} events")
    return events
