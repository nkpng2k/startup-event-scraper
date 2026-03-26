"""Generate a markdown table from events.json and write it to events/EVENTS.md."""

import json
import re
from datetime import datetime
from pathlib import Path


def generate_table():
    events_file = Path("events.json")
    if not events_file.exists():
        print("events.json not found")
        return

    events = json.loads(events_file.read_text())
    if not events:
        print("No events found")
        return

    def parse_date(date_str):
        for fmt in ("%B %d, %Y %I:%M %p", "%B %d, %Y (All Day)", "%B %d, %Y"):
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return datetime.max

    events.sort(key=lambda e: parse_date(e.get("date", "")))

    def truncate_desc(desc):
        if not desc or len(desc) <= 100:
            return desc
        match = re.search(r'[.!?]', desc[100:])
        if match:
            return desc[:100 + match.end()]
        return desc[:100] + "..."

    lines = [
        "# Upcoming Boston Startup Events",
        "",
        f"*{len(events)} events scraped from [StartupBos](https://www.startupbos.org/directory/events), "
        "[Luma Boston](https://luma.com/boston), and [Luma AI](https://luma.com/ai).*",
        "",
        "| Date | Event | Cost | Description | Source |",
        "|------|-------|------|-------------|--------|",
    ]

    for e in events:
        name = e["name"].replace("|", "\\|")
        link = e.get("registration_link", "")
        event_col = f"[{name}]({link})" if link else name
        source_url = e.get("source", "")
        if "startupbos" in source_url:
            source = "StartupBos"
        elif "luma.com/ai" in source_url:
            source = "Luma AI"
        elif "luma.com/boston" in source_url:
            source = "Luma Boston"
        else:
            source = source_url
        desc = truncate_desc(e.get("description", "")).replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {e['date']} | {event_col} | {e['cost']} | {desc} | {source} |")

    output = Path("events/EVENTS.md")
    output.parent.mkdir(exist_ok=True)
    output.write_text("\n".join(lines) + "\n")
    print(f"Generated events/EVENTS.md with {len(events)} events")


if __name__ == "__main__":
    generate_table()
