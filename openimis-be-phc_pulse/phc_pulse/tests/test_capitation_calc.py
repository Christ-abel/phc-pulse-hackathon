from datetime import date
from decimal import Decimal

from django.test import TestCase
from location.models import HealthFacility
from location.test_helpers import create_test_health_facility
from core.models import Language
from core.test_helpers import create_test_interactive_user
from product.test_helpers import create_test_product

from phc_pulse.models import CapitationRate, FacilityEnrolment
from phc_pulse.services import (
    MissingCapitationRateError,
    calculate_capitation_for_facility,
    run_capitation_cycle,
)

TEST_PERIOD = (date(2026, 1, 1), date(2026, 1, 31))


class CapitationCalculationTest(TestCase):
    """
    Tests the pure calculate_capitation_for_facility function. Uses unsaved
    model instances as lightweight value objects (no DB writes needed).
    """

    def test_normal_calculation(self):
        facility = HealthFacility(code="TST", name="Test HF")
        rate = CapitationRate(rate_per_head=Decimal("500.00"))
        result = calculate_capitation_for_facility(
            facility, rate, enrolled_count=120, period=TEST_PERIOD
        )
        self.assertEqual(result, Decimal("60000.00"))

    def test_zero_enrollment(self):
        facility = HealthFacility(code="TST", name="Test HF")
        rate = CapitationRate(rate_per_head=Decimal("500.00"))
        result = calculate_capitation_for_facility(
            facility, rate, enrolled_count=0, period=TEST_PERIOD
        )
        self.assertEqual(result, Decimal("0.00"))

    def test_negative_enrollment_raises(self):
        facility = HealthFacility(code="TST", name="Test HF")
        rate = CapitationRate(rate_per_head=Decimal("500.00"))
        with self.assertRaises(ValueError):
            calculate_capitation_for_facility(
                facility, rate, enrolled_count=-1, period=TEST_PERIOD
            )

    def test_missing_rate_raises_clear_exception(self):
        facility = HealthFacility(code="TST", name="Test HF")
        with self.assertRaises(MissingCapitationRateError):
            calculate_capitation_for_facility(
                facility, rate=None, enrolled_count=10, period=TEST_PERIOD
            )


class CapitationCycleTest(TestCase):
    """
    Tests run_capitation_cycle against real openIMIS fixtures, built with the
    official test_helpers from core/location/product so field requirements
    match production models exactly.
    """

    def setUp(self):
        # --nomigrations test DBs don't carry the "en" Language fixture row
        # that create_test_interactive_user() assumes exists; create it
        # explicitly rather than relying on fixture data being present.
        Language.objects.get_or_create(code="en", defaults={"name": "English", "sort_order": 1})
        self.user = create_test_interactive_user(username="phcpulsetestuser")
        self.facility = create_test_health_facility()
        self.product = create_test_product()
        self.period_start, self.period_end = TEST_PERIOD

    def test_missing_rate_raises_clear_exception(self):
        FacilityEnrolment(
            health_facility=self.facility,
            product=self.product,
            period_start=self.period_start,
            period_end=self.period_end,
            enrolled_count=150,
        ).save(user=self.user)

        # No CapitationRate exists for this product/period -> must raise,
        # not silently skip the facility or disburse a zeroed batch.
        with self.assertRaises(MissingCapitationRateError):
            run_capitation_cycle(self.period_start, self.period_end, self.user)

    def test_full_cycle_creates_payment_line(self):
        FacilityEnrolment(
            health_facility=self.facility,
            product=self.product,
            period_start=self.period_start,
            period_end=self.period_end,
            enrolled_count=150,
        ).save(user=self.user)
        CapitationRate(
            product=self.product,
            rate_per_head=Decimal("500.00"),
            period_start=self.period_start,
            period_end=self.period_end,
        ).save(user=self.user)

        batch = run_capitation_cycle(self.period_start, self.period_end, self.user)

        self.assertEqual(batch.lines.count(), 1)
        line = batch.lines.first()
        self.assertEqual(line.amount, Decimal("75000.00"))
        self.assertEqual(line.health_facility_id, self.facility.id)
