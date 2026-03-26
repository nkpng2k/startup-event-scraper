"""
Startup event scraper for Boston-area event websites.
Aggregates events from StartupBos, Luma Boston, and Luma AI.
"""

import argparse
import json
from dataclasses import asdict
from datetime import datetime

from playwright.sync_api import sync_playwright

from models import Event
from startupbos import scrape_startupbos
from luma import scrape_luma_boston, scrape_luma_ai

SCRAPE_CHOICES = ["all", "startupbos", "luma-boston", "luma-ai"]


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


def parse_args():
    parser = argparse.ArgumentParser(
        description="Scrape Boston-area startup events."
    )
    parser.add_argument(
        "--scrape",
        choices=SCRAPE_CHOICES,
        default="all",
        help="Which site to scrape (default: all)",
    )
    parser.add_argument(
        "--print-summary",
        action="store_true",
        default=False,
        help="Print a summary of scraped events to stdout",
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        default=False,
        help="Generate events/EVENTS.md table from scraped data",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    all_events = []
    sources = SCRAPE_CHOICES[1:] if args.scrape == "all" else [args.scrape]

    if "startupbos" in sources:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            all_events.extend(scrape_startupbos(browser))
            browser.close()

    if "luma-boston" in sources:
        all_events.extend(scrape_luma_boston())

    if "luma-ai" in sources:
        all_events.extend(scrape_luma_ai())

    # Deduplicate across all sources
    all_events = deduplicate_events(all_events)
    def parse_date(date_str):
        for fmt in ("%B %d, %Y %I:%M %p", "%B %d, %Y (All Day)", "%B %d, %Y"):
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return datetime.max

    all_events.sort(key=lambda e: parse_date(e.date))

    # Output results
    output = [asdict(e) for e in all_events]
    output_file = "events.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved {len(all_events)} events to {output_file}")

    if args.generate:
        from generate_table import generate_table
        generate_table()

    if args.print_summary:
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
