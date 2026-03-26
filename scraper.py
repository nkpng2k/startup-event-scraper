"""
Startup event scraper for Boston-area event websites.
Aggregates events from StartupBos, Luma Boston, and Luma AI.
"""

import json
from dataclasses import asdict

from playwright.sync_api import sync_playwright

from models import Event
from startupbos import scrape_startupbos
from luma import scrape_luma_boston, scrape_luma_ai


def deduplicate_events(events: list[Event]) -> list[Event]:
    """Remove duplicate events across all sources by name + date."""
    seen = set()
    unique = []
    for e in events:
        key = (e.name.strip().lower(), e.date[:15] if e.date else "")
        if key not in seen:
            seen.add(key)
            unique.append(e)
    return unique


def main():

    all_events = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        all_events.extend(scrape_startupbos(browser))
        browser.close()

    # Luma scrapers don't need a browser
    all_events.extend(scrape_luma_boston())
    all_events.extend(scrape_luma_ai())

    # Deduplicate across all sources
    all_events = deduplicate_events(all_events)
    all_events.sort(key=lambda e: e.date)

    # Output results
    output = [asdict(e) for e in all_events]
    output_file = "events.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved {len(all_events)} events to {output_file}")

    # Print summary
    for event in all_events:
        print(f"\n{'='*60}")
        print(f"  Name: {event.name}")
        print(f"  Date: {event.date}")
        print(f"  Cost: {event.cost}")
        print(f"  Link: {event.registration_link}")
        print(f"  Source: {event.source}")
        desc = event.description[:120] + "..." if len(event.description) > 120 else event.description
        print(f"  Desc: {desc}")


if __name__ == "__main__":
    main()
