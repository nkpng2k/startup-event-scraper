"""Tests for scraper.py - deduplication logic."""

from models import Event
from scraper import deduplicate_events


def _make_event(name="Test Event", date="April 01, 2026 05:00 PM", **kwargs):
    defaults = dict(
        cost="Free",
        description="",
        registration_link="https://example.com",
        source="https://luma.com/boston",
    )
    defaults.update(kwargs)
    return Event(name=name, date=date, **defaults)


class TestDeduplicateEvents:
    def test_no_duplicates(self):
        events = [_make_event(name="A"), _make_event(name="B")]
        result = deduplicate_events(events)
        assert len(result) == 2

    def test_exact_duplicates(self):
        events = [_make_event(name="A"), _make_event(name="A")]
        result = deduplicate_events(events)
        assert len(result) == 1

    def test_case_insensitive(self):
        events = [_make_event(name="AI Meetup"), _make_event(name="ai meetup")]
        result = deduplicate_events(events)
        assert len(result) == 1

    def test_whitespace_stripped(self):
        events = [_make_event(name="AI Meetup"), _make_event(name="  AI Meetup  ")]
        result = deduplicate_events(events)
        assert len(result) == 1

    def test_different_dates_not_deduped(self):
        events = [
            _make_event(name="A", date="April 01, 2026 05:00 PM"),
            _make_event(name="A", date="April 02, 2026 05:00 PM"),
        ]
        result = deduplicate_events(events)
        assert len(result) == 2

    def test_preserves_first_occurrence(self):
        events = [
            _make_event(name="A", source="https://startupbos.org"),
            _make_event(name="A", source="https://luma.com/boston"),
        ]
        result = deduplicate_events(events)
        assert result[0].source == "https://startupbos.org"

    def test_empty_list(self):
        assert deduplicate_events([]) == []

    def test_empty_date(self):
        events = [_make_event(name="A", date=""), _make_event(name="A", date="")]
        result = deduplicate_events(events)
        assert len(result) == 1
