from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand

from core.models import User
from location.models import HealthFacility, HealthFacilityLegalForm, HealthFacilitySubLevel, Location
from product.models import Product

from phc_pulse.models import CapitationRate, FacilityEnrolment

# Facility names are Kenyan (Kitui County, matching the PHC Pulse pitch),
# layered on top of openIMIS's existing Tanzania demo dataset -- the
# underlying Location records are reused from whatever demo data is already
# loaded, since building a full Kenyan location hierarchy is out of scope
# for a seed script. Facility addresses will show Tanzania location names;
# that's a known, deliberate simplification for Day 1, not a bug.
FACILITIES = [
    {"code": "KYW-DISP", "name": "Kyangwithya Dispensary", "level": "H"},
    {"code": "MWG-HC", "name": "Mwingi Health Centre", "level": "H"},
    {"code": "KTW-DISP", "name": "Katwanyaa Dispensary", "level": "H"},
]

CAPITATION_RATE_PER_HEAD = Decimal("450.00")


class Command(BaseCommand):
    help = (
        "Seeds demo data for PHC Pulse: 3 PHC facilities, a CapitationRate, "
        "and a FacilityEnrolment for the current period, layered on top of "
        "openIMIS's existing demo dataset -- so the dashboard has real "
        "numbers on Day 1 without manual data entry. Safe to re-run."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            type=str,
            default=None,
            help="core.User username to attribute seeded records to "
            "(defaults to the first interactive user found)",
        )

    def handle(self, *args, **options):
        username = options.get("username")
        if username:
            user = User.objects.filter(username=username).first()
            if user is None:
                self.stderr.write(self.style.ERROR(f"No core.User found with username={username}"))
                return
        else:
            user = User.objects.filter(i_user__isnull=False).order_by("id").first()
            if user is None:
                self.stderr.write(
                    self.style.ERROR(
                        "No core.User found -- log in via the UI once (or run "
                        "load_fixtures) before seeding, then re-run this command."
                    )
                )
                return

        location = Location.objects.filter(type="D", validity_to__isnull=True).first()
        if location is None:
            self.stderr.write(
                self.style.ERROR("No district-level Location found -- load openIMIS's demo dataset first.")
            )
            return

        legal_form, _ = HealthFacilityLegalForm.objects.get_or_create(
            code="G", defaults={"legal_form": "Government", "sort_order": 1}
        )
        sub_level, _ = HealthFacilitySubLevel.objects.get_or_create(
            code="D", defaults={"health_facility_sub_level": "Dispensary", "sort_order": 1}
        )

        product, created = Product.objects.get_or_create(
            code="PHCPULSE",
            validity_to__isnull=True,
            defaults={
                "name": "PHC Pulse Capitation Package",
                "location": location,
                "date_from": date(2026, 1, 1),
                "date_to": date(2030, 1, 1),
                "insurance_period": 12,
                "grace_period_enrolment": 1,
                "lump_sum": Decimal("0.00"),
                "max_members": 10000,
                "validity_from": date(2026, 1, 1),
                "audit_user_id": -1,
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created Product '{product.name}' ({product.code})"))

        today = date.today()
        period_start = today.replace(day=1)
        next_month = (period_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        period_end = next_month - timedelta(days=1)

        # CapitationRate/FacilityEnrolment are HistoryModel -- get_or_create's
        # internal create() call doesn't pass user=, so audit fields wouldn't
        # be set correctly. Check-then-construct-then-save(user=...) instead.
        rate = CapitationRate.objects.filter(
            is_deleted=False, product=product, period_start=period_start, period_end=period_end
        ).first()
        if rate is None:
            rate = CapitationRate(
                product=product,
                rate_per_head=CAPITATION_RATE_PER_HEAD,
                period_start=period_start,
                period_end=period_end,
            )
            rate.save(user=user)
            self.stdout.write(
                self.style.SUCCESS(f"Created CapitationRate {rate.rate_per_head}/head for {period_start}..{period_end}")
            )

        for fac_data in FACILITIES:
            facility, created = HealthFacility.objects.get_or_create(
                code=fac_data["code"],
                validity_to__isnull=True,
                defaults={
                    "name": fac_data["name"],
                    "level": fac_data["level"],
                    "care_type": "B",
                    "legal_form": legal_form,
                    "sub_level": sub_level,
                    "location": location,
                    "validity_from": date(2026, 1, 1),
                    "audit_user_id": -1,
                    "offline": False,
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created HealthFacility '{facility.name}' ({facility.code})"))

            enrolment = FacilityEnrolment.objects.filter(
                is_deleted=False,
                health_facility=facility,
                product=product,
                period_start=period_start,
                period_end=period_end,
            ).first()
            if enrolment is None:
                enrolled_count = 150 + (hash(facility.code) % 250)
                enrolment = FacilityEnrolment(
                    health_facility=facility,
                    product=product,
                    period_start=period_start,
                    period_end=period_end,
                    enrolled_count=enrolled_count,
                )
                enrolment.save(user=user)
                self.stdout.write(
                    self.style.SUCCESS(f"Created FacilityEnrolment for {facility.name}: {enrolled_count} enrolled")
                )

        self.stdout.write(
            self.style.SUCCESS(
                "Demo data seeded. Run `python manage.py run_capitation_cycle "
                f"{period_start.isoformat()} {period_end.isoformat()}` to generate a PaymentBatch."
            )
        )
