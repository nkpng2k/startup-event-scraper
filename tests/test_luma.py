"""Tests for luma.py - date formatting, geo filtering, cost parsing, dedup."""

from datetime import datetime, timedelta, timezone

from luma import _format_date, _entry_to_event, _is_boston_area, _is_within_2_weeks, _dedup_entries


def _make_entry(name="Test", start_at="2026-04-01T17:00:00Z", **event_extra):
    entry = {"event": {"name": name, "start_at": start_at, **event_extra}, "ticket_info": {}}
    return entry


class TestFormatDate:
    def test_utc_to_et(self):
        entry = _make_entry(start_at="2026-04-01T21:00:00Z")
        result = _format_date(entry)
        assert result == "April 01, 2026 05:00 PM"

    def test_empty_start(self):
        entry = _make_entry(start_at="")
        assert _format_date(entry) == ""

    def test_missing_event(self):
        assert _format_date({}) == ""

    def test_invalid_date_returns_raw(self):
        entry = _make_entry(start_at="not-a-date")
        assert _format_date(entry) == "not-a-date"


class TestEntryToEvent:
    def test_basic_fields(self):
        entry = {
            "event": {
                "name": "AI Meetup",
                "start_at": "2026-04-01T21:00:00Z",
                "url": "abc123",
                "description_short": "A short description",
            },
            "ticket_info": {"is_free": True},
        }
        event = _entry_to_event(entry, "https://luma.com/boston")
        assert event.name == "AI Meetup"
        assert event.cost == "Free"
        assert event.registration_link == "https://lu.ma/abc123"
        assert event.description == "A short description"
        assert event.source == "https://luma.com/boston"

    def test_price_in_cents_dict(self):
        entry = {
            "event": {"name": "Paid", "start_at": "2026-04-01T21:00:00Z"},
            "ticket_info": {"price": {"cents": 1500, "currency": "usd"}},
        }
        event = _entry_to_event(entry, "https://luma.com/boston")
        assert event.cost == "$15.00"

    def test_price_as_int(self):
        entry = {
            "event": {"name": "Paid", "start_at": "2026-04-01T21:00:00Z"},
            "ticket_info": {"price": 2500},
        }
        event = _entry_to_event(entry, "https://luma.com/boston")
        assert event.cost == "$25.00"

    def test_price_small_int(self):
        entry = {
            "event": {"name": "Paid", "start_at": "2026-04-01T21:00:00Z"},
            "ticket_info": {"price": 50},
        }
        event = _entry_to_event(entry, "https://luma.com/boston")
        assert event.cost == "$50"

    def test_no_price_info(self):
        entry = {
            "event": {"name": "Unknown", "start_at": "2026-04-01T21:00:00Z"},
            "ticket_info": {},
        }
        event = _entry_to_event(entry, "https://luma.com/boston")
        assert event.cost == "Not listed"

    def test_no_url(self):
        entry = {
            "event": {"name": "No Link", "start_at": "2026-04-01T21:00:00Z"},
            "ticket_info": {},
        }
        event = _entry_to_event(entry, "https://luma.com/boston")
        assert event.registration_link == ""

    def test_missing_description(self):
        entry = {
            "event": {"name": "No Desc", "start_at": "2026-04-01T21:00:00Z"},
            "ticket_info": {},
        }
        event = _entry_to_event(entry, "https://luma.com/boston")
        assert event.description == ""


class TestIsBostonArea:
    def test_boston_city(self):
        entry = _make_entry(geo_address_info={"city": "Boston"})
        assert _is_boston_area(entry) is True

    def test_cambridge(self):
        entry = _make_entry(geo_address_info={"city": "Cambridge"})
        assert _is_boston_area(entry) is True

    def test_massachusetts_region(self):
        entry = _make_entry(geo_address_info={"city": "Springfield", "region": "Massachusetts"})
        assert _is_boston_area(entry) is True

    def test_ma_region(self):
        entry = _make_entry(geo_address_info={"city": "Springfield", "region": "MA"})
        assert _is_boston_area(entry) is True

    def test_city_state_fallback(self):
        entry = _make_entry(geo_address_info={"city_state": "Somewhere, Massachusetts"})
        assert _is_boston_area(entry) is True

    def test_new_york_rejected(self):
        entry = _make_entry(geo_address_info={"city": "New York", "region": "New York"})
        assert _is_boston_area(entry) is False

    def test_no_geo_info(self):
        entry = _make_entry()
        assert _is_boston_area(entry) is False

    def test_none_geo_info(self):
        entry = {"event": {"geo_address_info": None}}
        assert _is_boston_area(entry) is False


class TestIsWithin2Weeks:
    def test_event_tomorrow(self):
        tomorrow = datetime.now(timezone.utc) + timedelta(days=2)
        entry = _make_entry(start_at=tomorrow.strftime("%Y-%m-%dT%H:%M:%SZ"))
        assert _is_within_2_weeks(entry) is True

    def test_event_in_3_weeks(self):
        future = datetime.now(timezone.utc) + timedelta(days=21)
        entry = _make_entry(start_at=future.strftime("%Y-%m-%dT%H:%M:%SZ"))
        assert _is_within_2_weeks(entry) is False

    def test_event_yesterday(self):
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        entry = _make_entry(start_at=yesterday.strftime("%Y-%m-%dT%H:%M:%SZ"))
        assert _is_within_2_weeks(entry) is False

    def test_empty_start(self):
        entry = _make_entry(start_at="")
        assert _is_within_2_weeks(entry) is False


class TestDedupEntries:
    def test_removes_duplicates(self):
        entries = [
            _make_entry(name="AI Meetup", start_at="2026-04-01T17:00:00Z"),
            _make_entry(name="AI Meetup", start_at="2026-04-01T19:00:00Z"),
        ]
        result = _dedup_entries(entries)
        assert len(result) == 1

    def test_case_insensitive(self):
        entries = [
            _make_entry(name="AI Meetup", start_at="2026-04-01T17:00:00Z"),
            _make_entry(name="ai meetup", start_at="2026-04-01T19:00:00Z"),
        ]
        result = _dedup_entries(entries)
        assert len(result) == 1

    def test_different_dates_kept(self):
        entries = [
            _make_entry(name="AI Meetup", start_at="2026-04-01T17:00:00Z"),
            _make_entry(name="AI Meetup", start_at="2026-04-02T17:00:00Z"),
        ]
        result = _dedup_entries(entries)
        assert len(result) == 2

    def test_empty_list(self):
        assert _dedup_entries([]) == []
