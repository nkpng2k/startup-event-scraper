"""StartupBos event scraper using the Wix Events Calendar widget API."""

import json
import re
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from playwright.sync_api import Page, Browser

from models import Event

STARTUPBOS_URL = "https://www.startupbos.org/directory/events"
EVENTS_CALENDAR_APP_ID = "133bb11e-b3db-7e3b-49bc-8aa16af72cac"
EVENTS_CALENDAR_COMP_ID = "comp-k7v0es90"


def _get_instance_token(browser: Browser) -> str:
    """Load the StartupBos page and capture the Events Calendar instance token
    from the Wix access-tokens API response."""
    tokens = {}

    def on_response(response):
        if "access-tokens" in response.url:
            try:
                tokens["data"] = response.json()
            except Exception:
                pass

    page = browser.new_page()
    page.on("response", on_response)
    page.goto(STARTUPBOS_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(8000)
    page.close()

    apps = tokens.get("data", {}).get("apps", {})
    return apps.get(EVENTS_CALENDAR_APP_ID, {}).get("instance", "")


def _fetch_calendar_data(browser: Browser, instance_token: str) -> list[dict]:
    """Load the Events Calendar widget and capture the data API response."""
    widget_url = (
        f"https://plugin.eventscalendar.co/widget.html"
        f"?instance={instance_token}"
        f"&compId={EVENTS_CALENDAR_COMP_ID}"
        f"&viewMode=site"
    )

    calendar_data = {}

    def on_response(response):
        if "inffuse.eventscalendar.co" in response.url and "/data" in response.url:
            try:
                calendar_data["full"] = response.json()
            except Exception:
                pass

    page = browser.new_page()
    page.on("response", on_response)
    page.goto(widget_url, wait_until="domcontentloaded", timeout=20000)
    page.wait_for_timeout(8000)
    page.close()

    if "full" not in calendar_data:
        return []
    return calendar_data["full"].get("project", {}).get("data", {}).get("events", [])


def _scrape_luma_cost(page: Page, url: str) -> str:
    """Follow a Luma registration link to extract cost info."""
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(4000)
        html = page.content()
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator="\n", strip=True)

        ld_json = soup.find("script", type="application/ld+json")
        if ld_json and ld_json.string:
            try:
                data = json.loads(ld_json.string)
                if isinstance(data, list):
                    data = data[0]
                if "offers" in data:
                    offers = data["offers"]
                    if isinstance(offers, list):
                        prices = [o.get("price", "") for o in offers]
                        return ", ".join(
                            f"${p}" if p and p != "0" else "Free" for p in prices
                        )
                    elif isinstance(offers, dict):
                        price = offers.get("price", "")
                        return f"${price}" if price and price != "0" else "Free"
            except (json.JSONDecodeError, KeyError):
                pass

        if "free" in text.lower():
            return "Free"
        price_match = re.search(r"\$[\d,.]+", text)
        if price_match:
            return price_match.group()

        return "Not listed"
    except Exception as e:
        print(f"  Warning: Could not fetch Luma details from {url}: {e}")
        return "Not listed"


def _format_time(raw_event: dict) -> str:
    date_str = raw_event.get("startDate", "")
    if not date_str:
        return ""

    hour = raw_event.get("startHour", 0)
    minute = raw_event.get("startMinutes", 0)

    if raw_event.get("allday"):
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.strftime("%B %d, %Y") + " (All Day)"
        except ValueError:
            return date_str

    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        dt = dt.replace(hour=hour, minute=minute)
        return dt.strftime("%B %d, %Y %I:%M %p")
    except ValueError:
        return date_str


def _get_link(raw_event: dict) -> str:
    links = raw_event.get("links", {})
    if isinstance(links, list):
        if links:
            return links[0].get("url", "")
    elif isinstance(links, dict):
        first = links.get("0", {})
        if isinstance(first, dict):
            return first.get("url", "")
    return ""


def scrape_startupbos(browser: Browser) -> list[Event]:
    """Scrape events from startupbos.org using the Events Calendar API."""
    print(f"Scraping: {STARTUPBOS_URL}")

    print("  Getting calendar instance token...")
    instance_token = _get_instance_token(browser)
    if not instance_token:
        print("  Error: Could not get Events Calendar instance token")
        return []

    print("  Fetching calendar data...")
    raw_events = _fetch_calendar_data(browser, instance_token)
    print(f"  Retrieved {len(raw_events)} total events from calendar")

    tomorrow = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    cutoff = tomorrow + timedelta(days=14)
    tomorrow_ms = tomorrow.timestamp() * 1000
    cutoff_ms = cutoff.timestamp() * 1000

    future_raw = [
        e for e in raw_events
        if tomorrow_ms <= e.get("start", 0) <= cutoff_ms
    ]
    future_raw.sort(key=lambda e: e.get("start", 0))

    seen = set()
    deduped = []
    for e in future_raw:
        key = (e.get("title", "").strip().lower(), e.get("startDate", ""))
        if key not in seen:
            seen.add(key)
            deduped.append(e)
    future_raw = deduped
    print(f"  {len(future_raw)} unique events in the next 2 weeks")

    events = []
    detail_page = browser.new_page()

    for raw in future_raw:
        title = raw.get("title", "Untitled Event")
        date = _format_time(raw)
        description = raw.get("description", "")
        reg_link = _get_link(raw)
        cost = "Not listed"

        if reg_link and "luma.com" in reg_link:
            print(f"  Fetching cost from {reg_link}...")
            cost = _scrape_luma_cost(detail_page, reg_link)

        events.append(
            Event(
                name=title,
                date=date,
                cost=cost,
                description=description,
                registration_link=reg_link,
                source=STARTUPBOS_URL,
            )
        )

    detail_page.close()
    print(f"  Returning {len(events)} events")
    return events
