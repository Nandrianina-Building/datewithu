from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from apps.invitations.models import Invitation
from apps.planner.models import DatePlan

from .date_builder import _is_future_date


class DateBuilderScheduleTests(SimpleTestCase):
    @patch("apps.api.date_builder.timezone.localdate", return_value=date(2026, 9, 22))
    def test_future_date_is_accepted(self, localdate):
        self.assertTrue(_is_future_date(date(2026, 9, 23)))

    @patch("apps.api.date_builder.timezone.localdate", return_value=date(2026, 9, 22))
    def test_today_and_past_dates_are_rejected(self, localdate):
        self.assertFalse(_is_future_date(date(2026, 9, 22)))
        self.assertFalse(_is_future_date(date(2026, 9, 21)))


class PastInvitationSharingTests(TestCase):
    def test_public_api_rejects_past_invitation(self):
        creator = get_user_model().objects.create_user(
            username="date-creator", password="test-pass", is_verified=True,
        )
        plan = DatePlan.objects.create(
            creator=creator,
            date_value=timezone.localdate() - timedelta(days=1),
            status=DatePlan.STATUS_COMPLETED,
        )
        invitation = Invitation.objects.create(
            date_plan=plan,
            expires_at=timezone.now() + timedelta(days=7),
        )
        self.client.force_login(creator)

        response = self.client.get(f"/api/invitations/{invitation.token}/public/")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Cette invitation n'existe plus.")

    def test_creator_cannot_open_share_card_for_past_invitation(self):
        creator = get_user_model().objects.create_user(
            username="date-creator", password="test-pass", is_verified=True,
        )
        plan = DatePlan.objects.create(
            creator=creator,
            date_value=timezone.localdate() - timedelta(days=1),
            status=DatePlan.STATUS_COMPLETED,
        )
        invitation = Invitation.objects.create(
            date_plan=plan,
            expires_at=timezone.now() + timedelta(days=7),
        )
        self.client.force_login(creator)

        response = self.client.get(f"/invite/{invitation.token}/qr.png")

        self.assertEqual(response.status_code, 404)