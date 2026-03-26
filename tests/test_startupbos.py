"""Tests for startupbos.py - time formatting and link extraction."""

from startupbos import _format_time, _get_link


class TestFormatTime:
    def test_regular_event(self):
        raw = {"startDate": "2026-04-01", "startHour": 17, "startMinutes": 30}
        assert _format_time(raw) == "April 01, 2026 05:30 PM"

    def test_all_day_event(self):
        raw = {"startDate": "2026-04-01", "allday": True}
        assert _format_time(raw) == "April 01, 2026 (All Day)"

    def test_midnight(self):
        raw = {"startDate": "2026-04-01", "startHour": 0, "startMinutes": 0}
        assert _format_time(raw) == "April 01, 2026 12:00 AM"

    def test_no_date(self):
        assert _format_time({}) == ""

    def test_empty_date(self):
        assert _format_time({"startDate": ""}) == ""

    def test_invalid_date_format(self):
        raw = {"startDate": "not-a-date"}
        assert _format_time(raw) == "not-a-date"

    def test_defaults_hour_minute(self):
        raw = {"startDate": "2026-04-01"}
        assert _format_time(raw) == "April 01, 2026 12:00 AM"


class TestGetLink:
    def test_links_as_list(self):
        raw = {"links": [{"url": "https://example.com"}]}
        assert _get_link(raw) == "https://example.com"

    def test_links_as_dict(self):
        raw = {"links": {"0": {"url": "https://example.com"}}}
        assert _get_link(raw) == "https://example.com"

    def test_empty_list(self):
        assert _get_link({"links": []}) == ""

    def test_empty_dict(self):
        assert _get_link({"links": {}}) == ""

    def test_no_links_key(self):
        assert _get_link({}) == ""

    def test_dict_with_non_dict_value(self):
        assert _get_link({"links": {"0": "not a dict"}}) == ""
