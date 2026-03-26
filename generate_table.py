"""Generate a markdown table from events.json and write it to EVENTS.md."""

import json
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

    lines = [
        "# Upcoming Boston Startup Events",
        "",
        f"*{len(events)} events scraped from [StartupBos](https://www.startupbos.org/directory/events), "
        "[Luma Boston](https://luma.com/boston), and [Luma AI](https://luma.com/ai).*",
        "",
        "| Date | Event | Cost | Source |",
        "|------|-------|------|--------|",
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
        lines.append(f"| {e['date']} | {event_col} | {e['cost']} | {source} |")

    output = Path("EVENTS.md")
    output.write_text("\n".join(lines) + "\n")
    print(f"Generated EVENTS.md with {len(events)} events")


if __name__ == "__main__":
    generate_table()
