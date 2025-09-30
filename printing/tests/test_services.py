import pytest
from django.utils import timezone

from accounts.services import ensure_user
from printing.services import import_print_events


@pytest.mark.django_db
def test_ensure_user_creates_and_updates():
    res = ensure_user("alice", "Alice", "it")
    assert res.created is True
    assert res.user.username == "alice"
    assert res.user.department.code == "it"

    res2 = ensure_user("alice", "Alice Smith", "it")
    assert res2.created is False
    assert res2.user.fio == "Alice Smith"


@pytest.mark.django_db
def test_import_print_events_creates_event(user_factory, printer_factory):
    user = user_factory(username="bob")
    printer = printer_factory(name="hp-1-it-101-1")
    now_ms = int(timezone.now().timestamp() * 1000)
    events = [
        {
            "Param1": "123",
            "Param2": "doc.pdf",
            "Param3": user.username,
            "Param4": "pc-01",
            "Param5": printer.name,
            "Param6": "usb",
            "Param7": "2048",
            "Param8": "2",
            "TimeCreated": f"/Date({now_ms})/",
            "JobID": "job-1",
        }
    ]
    result = import_print_events(events)
    assert result["created"] == 1
    assert not result["errors"]


