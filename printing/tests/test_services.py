from __future__ import annotations

import io
import json
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from printing.models import Department, PrintEvent
from printing.services import import_users_from_csv_stream, import_print_events


class ImportUsersServiceTests(TestCase):
    def test_import_users_csv_basic(self):
        csv_content = "SamAccountName,DisplayName,OU\nuser1,User One,IT\nuser2,User Two,HR\n"
        result = import_users_from_csv_stream(io.BytesIO(csv_content.encode("utf-8")))
        self.assertEqual(result["created"], 2)
        self.assertFalse(result["errors"])
        self.assertTrue(User.objects.filter(username="user1").exists())
        self.assertTrue(Department.objects.filter(code="it").exists())


class ImportPrintEventsServiceTests(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(code="it", name="IT")
        self.user = User.objects.create_user(username="user1", password="x", department=self.dept)

    def test_import_events_basic(self):
        events = [
            {
                "Param3": "user1",
                "Param2": "doc.pdf",
                "Param1": 123,
                "Param7": 1024,
                "Param8": 3,
                "TimeCreated": f"/Date({int(timezone.now().timestamp() * 1000)})/",
                "JobID": "job-1",
                "Param5": "HP-1-it-101-1",
            }
        ]
        result = import_print_events(events)
        self.assertEqual(result["created"], 1)
        self.assertFalse(result["errors"])
        self.assertTrue(PrintEvent.objects.filter(job_id="job-1").exists())


