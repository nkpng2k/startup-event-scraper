# Boston Startup Event Scraper

A Python scraper that aggregates upcoming startup and tech events from Boston-area event websites into a single JSON file.

## Sources

- **[StartupBos](https://www.startupbos.org/directory/events)** - Boston startup community events via the Wix Events Calendar widget
- **[Luma Boston](https://luma.com/boston)** - Boston events on Luma
- **[Luma AI](https://luma.com/ai)** - AI-focused events filtered to the Boston area

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:

```bash
playwright install chromium
```

## Usage

```bash
# Scrape all sources
python src/scraper.py

# Scrape a specific source
python src/scraper.py --scrape startupbos
python src/scraper.py --scrape luma-boston
python src/scraper.py --scrape luma-ai

# Print event summary to stdout
python src/scraper.py --print-summary

# Combine flags
python src/scraper.py --scrape luma-ai --print-summary
```

### Options

| Flag | Values | Default | Description |
|------|--------|---------|-------------|
| `--scrape` | `all`, `startupbos`, `luma-boston`, `luma-ai` | `all` | Which site(s) to scrape |
| `--print-summary` | | `false` | Print event details to stdout |

## Output

Events are saved to `events.json`. Each event includes:

```json
{
  "name": "Event Name",
  "date": "April 01, 2026 05:30 PM",
  "cost": "Free",
  "description": "Event description text",
  "registration_link": "https://...",
  "source": "https://luma.com/boston"
}
```

The scraper only returns events occurring within the next 2 weeks and automatically deduplicates events that appear across multiple sources.

A formatted markdown table of upcoming events is published to [`events/EVENTS.md`](events/EVENTS.md) and updated weekly by a GitHub Action.

## Project Structure

```
src/
  scraper.py        # Main entrypoint - aggregates, deduplicates, and outputs events
  models.py         # Shared Event dataclass
  startupbos.py     # StartupBos scraper (uses Playwright for JS rendering)
  luma.py           # Luma Boston and Luma AI scrapers (uses public API)
  generate_table.py # Generates events/EVENTS.md from events.json
events/
  EVENTS.md         # Auto-generated table of upcoming events
```
