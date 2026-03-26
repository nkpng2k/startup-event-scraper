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
python scraper.py

# Scrape a specific source
python scraper.py --scrape startupbos
python scraper.py --scrape luma-boston
python scraper.py --scrape luma-ai

# Print event summary to stdout
python scraper.py --print-summary

# Combine flags
python scraper.py --scrape luma-ai --print-summary
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

## Project Structure

```
scraper.py      # Main entrypoint - aggregates, deduplicates, and outputs events
models.py       # Shared Event dataclass
startupbos.py   # StartupBos scraper (uses Playwright for JS rendering)
luma.py         # Luma Boston and Luma AI scrapers (uses public API)
```
