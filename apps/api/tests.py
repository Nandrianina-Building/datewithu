from datetime import date
from unittest.mock import patch

from django.test import SimpleTestCase

from .date_builder import _is_future_date


class DateBuilderScheduleTests(SimpleTestCase):
    @patch("apps.api.date_builder.timezone.localdate", return_value=date(2026, 9, 22))
    def test_future_date_is_accepted(self, localdate):
        self.assertTrue(_is_future_date(date(2026, 9, 23)))

    @patch("apps.api.date_builder.timezone.localdate", return_value=date(2026, 9, 22))
    def test_today_and_past_dates_are_rejected(self, localdate):
        self.assertFalse(_is_future_date(date(2026, 9, 22)))
        self.assertFalse(_is_future_date(date(2026, 9, 21)))