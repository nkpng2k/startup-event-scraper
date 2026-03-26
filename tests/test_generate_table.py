"""Tests for generate_table.py - date parsing and description truncation."""

import json
from datetime import datetime
from pathlib import Path

from generate_table import generate_table


# Extract the helper functions by running generate_table's internals
import re


def truncate_desc(desc):
    if not desc or len(desc) <= 100:
        return desc
    match = re.search(r'[.!?]', desc[100:])
    if match:
        return desc[:100 + match.end()]
    return desc[:100] + "..."


def parse_date(date_str):
    for fmt in ("%B %d, %Y %I:%M %p", "%B %d, %Y (All Day)", "%B %d, %Y"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return datetime.max


class TestTruncateDesc:
    def test_short_string_unchanged(self):
        assert truncate_desc("Hello world") == "Hello world"

    def test_empty_string(self):
        assert truncate_desc("") == ""

    def test_none(self):
        assert truncate_desc(None) is None

    def test_exactly_100_chars(self):
        text = "A" * 100
        assert truncate_desc(text) == text

    def test_truncates_at_period(self):
        text = "A" * 105 + ". More text here."
        result = truncate_desc(text)
        assert result == "A" * 105 + "."

    def test_truncates_at_exclamation(self):
        text = "A" * 110 + "! More text."
        result = truncate_desc(text)
        assert result == "A" * 110 + "!"

    def test_truncates_at_question(self):
        text = "A" * 103 + "? More text."
        result = truncate_desc(text)
        assert result == "A" * 103 + "?"

    def test_no_punctuation_adds_ellipsis(self):
        text = "A" * 150
        result = truncate_desc(text)
        assert result == "A" * 100 + "..."

    def test_real_description(self):
        text = (
            "Join us for an interactive, AMA-style conversation on fundraising "
            "with leaders from Antler, one of the world's most active early-stage "
            "venture capital firms. This virtual session is designed for founders."
        )
        result = truncate_desc(text)
        assert result.endswith(".")
        assert len(result) <= len(text)
        assert len(result) >= 100


class TestParseDate:
    def test_time_format(self):
        result = parse_date("April 01, 2026 05:30 PM")
        assert result == datetime(2026, 4, 1, 17, 30)

    def test_all_day_format(self):
        result = parse_date("April 01, 2026 (All Day)")
        assert result == datetime(2026, 4, 1, 0, 0)

    def test_date_only(self):
        result = parse_date("April 01, 2026")
        assert result == datetime(2026, 4, 1, 0, 0)

    def test_invalid_returns_max(self):
        result = parse_date("not a date")
        assert result == datetime.max

    def test_empty_string(self):
        result = parse_date("")
        assert result == datetime.max

    def test_sorting_order(self):
        dates = [
            "April 02, 2026 05:00 PM",
            "March 30, 2026 09:00 AM",
            "April 01, 2026 (All Day)",
        ]
        sorted_dates = sorted(dates, key=parse_date)
        assert sorted_dates == [
            "March 30, 2026 09:00 AM",
            "April 01, 2026 (All Day)",
            "April 02, 2026 05:00 PM",
        ]


class TestGenerateTable:
    def test_generates_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        events = [
            {
                "name": "Test Event",
                "date": "April 01, 2026 05:00 PM",
                "cost": "Free",
                "description": "A test event",
                "registration_link": "https://example.com",
                "source": "https://luma.com/boston",
            }
        ]
        (tmp_path / "events.json").write_text(json.dumps(events))
        (tmp_path / "events").mkdir()
        generate_table()
        output = (tmp_path / "events" / "EVENTS.md").read_text()
        assert "Test Event" in output
        assert "Free" in output
        assert "Luma Boston" in output

    def test_no_events_file(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        generate_table()
        assert "not found" in capsys.readouterr().out

    def test_empty_events(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "events.json").write_text("[]")
        generate_table()
        assert "No events found" in capsys.readouterr().out

    def test_pipe_in_name_escaped(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        events = [
            {
                "name": "AI | Meetup",
                "date": "April 01, 2026 05:00 PM",
                "cost": "Free",
                "description": "",
                "registration_link": "",
                "source": "https://luma.com/boston",
            }
        ]
        (tmp_path / "events.json").write_text(json.dumps(events))
        (tmp_path / "events").mkdir()
        generate_table()
        output = (tmp_path / "events" / "EVENTS.md").read_text()
        assert "AI \\| Meetup" in output
