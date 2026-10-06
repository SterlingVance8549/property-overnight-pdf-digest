"""Run the overnight property digest with three representative records."""

from datetime import date

from property_digest_service import InfraiClient, PropertyRecord, ship_overnight_digest


def main() -> None:
    records = [
        PropertyRecord("MR-12", "maintenance request", "Harbor View", "Lift alarm needs a technician", urgent=True),
        PropertyRecord("TD-08", "tenant document", "Harbor View", "Lease renewal signed"),
        PropertyRecord("IN-31", "inspection reminder", "Maple Court", "Fire-door inspection", due_on=date.today()),
    ]
    result = ship_overnight_digest(records, date.today(), InfraiClient.from_environment())
    print(result)


if __name__ == "__main__":
    main()
