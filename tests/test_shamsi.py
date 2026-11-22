"""Tests for Shamsi date conversion helpers."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date
import pytest
from backend.shamsi import (
    gregorian_to_shamsi,
    shamsi_to_gregorian,
    today_shamsi,
    now_shamsi,
    shamsi_month_name,
    shamsi_year_month,
    format_shamsi_display,
    MONTH_NAMES,
)


# ── round-trip ───────────────────────────────────────────────────────────────
class TestRoundTrip:
    def test_known_date_1(self):
        # 2024-03-19 Gregorian = 1402-12-29 Shamsi (second-last day of 1402)
        s = gregorian_to_shamsi(date(2024, 3, 19))
        assert s == "1402-12-29"
        assert shamsi_to_gregorian(s) == date(2024, 3, 19)

    def test_known_date_2(self):
        # Nowruz 1403: jdatetime says 2024-03-20 = 1403-01-01
        s = gregorian_to_shamsi(date(2024, 3, 20))
        assert s == "1403-01-01"
        assert shamsi_to_gregorian(s) == date(2024, 3, 20)

    def test_known_date_3(self):
        # 2025-04-20 ≈ 1404-01-31
        s = gregorian_to_shamsi(date(2025, 4, 20))
        g = shamsi_to_gregorian(s)
        assert g == date(2025, 4, 20)

    def test_round_trip_full_year(self):
        """Round-trip every day in 1403."""
        from jdatetime import date as jdate
        for month in range(1, 13):
            days = 29 if month == 12 else (30 if month <= 6 else 29)
            for day in range(1, days + 1):
                shamsi_str = f"1403-{month:02d}-{day:02d}"
                g = shamsi_to_gregorian(shamsi_str)
                back = gregorian_to_shamsi(g)
                assert back == shamsi_str, f"Round-trip failed for {shamsi_str}"


# ── 1404 (year after Nowruz 2025) ────────────────────────────────────────────
class Test1404:
    def test_1404_01_01(self):
        # Nowruz 1404 = 2025-03-21
        assert shamsi_to_gregorian("1404-01-01") == date(2025, 3, 21)

    def test_1404_last_day(self):
        # 1404 is NOT a leap year → Esfand has 29 days
        s = "1404-12-29"
        g = shamsi_to_gregorian(s)
        back = gregorian_to_shamsi(g)
        assert back == s


# ── leap year ────────────────────────────────────────────────────────────────
class TestLeapYear:
    def test_1403_is_leap(self):
        # 1403 is a leap year → Esfand has 30 days
        s = "1403-12-30"
        g = shamsi_to_gregorian(s)
        back = gregorian_to_shamsi(g)
        assert back == s

    def test_1404_is_not_leap(self):
        with pytest.raises(Exception):
            shamsi_to_gregorian("1404-12-30")  # day 30 doesn't exist


# ── month boundaries ─────────────────────────────────────────────────────────
class TestMonthBoundaries:
    def test_month_6_has_31_days(self):
        # Months 1-6 have 31 days in Solar Hijri
        s = "1403-06-31"
        g = shamsi_to_gregorian(s)
        back = gregorian_to_shamsi(g)
        assert back == s

    def test_month_7_has_30_days(self):
        # Months 7-11 have 30 days
        s = "1403-07-30"
        g = shamsi_to_gregorian(s)
        assert gregorian_to_shamsi(g) == s

    def test_month_7_day_31_invalid(self):
        with pytest.raises(Exception):
            shamsi_to_gregorian("1403-07-31")


# ── month names ──────────────────────────────────────────────────────────────
class TestMonthNames:
    def test_all_12_month_names(self):
        expected = ["حمل", "ثور", "جوزا", "سرطان", "اسد", "سنبله",
                    "میزان", "عقرب", "قوس", "جدی", "دلو", "حوت"]
        for i, name in enumerate(expected, start=1):
            assert shamsi_month_name(i) == name

    def test_invalid_month_raises(self):
        with pytest.raises(ValueError):
            shamsi_month_name(0)
        with pytest.raises(ValueError):
            shamsi_month_name(13)


# ── utility functions ────────────────────────────────────────────────────────
class TestUtils:
    def test_today_shamsi_format(self):
        s = today_shamsi()
        parts = s.split("-")
        assert len(parts) == 3
        assert len(parts[0]) == 4   # year 4 digits
        assert 1 <= int(parts[1]) <= 12
        assert 1 <= int(parts[2]) <= 31

    def test_now_shamsi_format(self):
        s = now_shamsi()
        assert " " in s
        date_part, time_part = s.split(" ")
        assert len(date_part.split("-")) == 3
        assert len(time_part.split(":")) == 3

    def test_shamsi_year_month(self):
        y, m = shamsi_year_month("1403-07-15")
        assert y == 1403
        assert m == 7

    def test_format_display(self):
        result = format_shamsi_display("1403-01-15")
        assert "حمل" in result
        assert "1403" in result
        assert "15" in result

    def test_format_display_none(self):
        assert format_shamsi_display(None) == "—"
        assert format_shamsi_display("") == "—"
