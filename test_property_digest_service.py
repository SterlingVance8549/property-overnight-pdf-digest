from datetime import date

from property_digest_service import PropertyRecord, records_for_digest


def test_urgent_requests_and_due_inspections_make_the_morning_digest() -> None:
    today = date(2026, 9, 15)
    records = [
        PropertyRecord("MR-1", "maintenance request", "Aster House", "Water leak", urgent=True),
        PropertyRecord("TD-1", "tenant document", "Aster House", "Renewal received"),
        PropertyRecord("IN-1", "inspection reminder", "Birch Court", "Boiler review", due_on=today),
        PropertyRecord("IN-2", "inspection reminder", "Cedar Place", "Lift review", due_on=date(2026, 9, 16)),
    ]

    assert [record.record_id for record in records_for_digest(records, today)] == ["MR-1", "IN-1"]
