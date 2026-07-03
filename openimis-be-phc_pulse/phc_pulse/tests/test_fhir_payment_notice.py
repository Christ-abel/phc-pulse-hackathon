import json
from datetime import date
from decimal import Decimal

from django.test import TestCase
from core.models import Language
from core.test_helpers import create_test_interactive_user
from location.test_helpers import create_test_health_facility

from phc_pulse.fhir_converters import PaymentLineToFhirPaymentNoticeConverter
from phc_pulse.models import PaymentBatch, PaymentLine


class FhirPaymentNoticeConverterTest(TestCase):
    def setUp(self):
        # --nomigrations test DBs don't carry the "en" Language fixture row
        # that create_test_interactive_user() assumes exists.
        Language.objects.get_or_create(code="en", defaults={"name": "English", "sort_order": 1})
        self.user = create_test_interactive_user(username="phcpulsefhirtestuser")
        self.facility = create_test_health_facility()
        self.batch = PaymentBatch(
            period_start=date(2026, 1, 1),
            period_end=date(2026, 1, 31),
            status=PaymentBatch.STATUS_DRAFT,
        )
        self.batch.save(user=self.user)
        self.line = PaymentLine(
            batch=self.batch,
            health_facility=self.facility,
            amount=Decimal("75000.00"),
            status=PaymentBatch.STATUS_DRAFT,
        )
        self.line.save(user=self.user)

    def test_payment_notice_has_required_fields(self):
        """
        hl7.org/fhir/R4/paymentnotice.html marks status, created, payment,
        recipient, and amount as required (1..1) -- these must be non-null,
        not just "the converter didn't crash".
        """
        fhir_obj = PaymentLineToFhirPaymentNoticeConverter.to_fhir_obj(self.line)

        self.assertIsNotNone(fhir_obj.status)
        self.assertIsNotNone(fhir_obj.created)
        self.assertIsNotNone(fhir_obj.payment)
        self.assertIsNotNone(fhir_obj.recipient)
        self.assertIsNotNone(fhir_obj.amount)

        self.assertIn(fhir_obj.status, ["active", "cancelled", "draft", "entered-in-error"])
        self.assertEqual(str(fhir_obj.amount.value), "75000.00")
        self.assertEqual(fhir_obj.payee.reference, f"Organization/{self.facility.uuid}")
        self.assertEqual(fhir_obj.payment.reference, f"PaymentReconciliation/{self.batch.id}")

    def test_payment_notice_serializes_to_valid_json(self):
        fhir_obj = PaymentLineToFhirPaymentNoticeConverter.to_fhir_obj(self.line)
        parsed = json.loads(fhir_obj.json())

        self.assertEqual(parsed["resourceType"], "PaymentNotice")
        for required_field in ("status", "created", "payment", "recipient", "amount"):
            self.assertIn(required_field, parsed)
