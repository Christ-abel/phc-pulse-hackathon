from datetime import date
from decimal import Decimal

from core.models.openimis_graphql_test_case import openIMISGraphQLTestCase
from core.models import Language
from core.test_helpers import create_test_interactive_user
from graphql_jwt.shortcuts import get_token
from location.test_helpers import create_test_health_facility
from product.test_helpers import create_test_product

from phc_pulse.models import CapitationRate, FacilityEnrolment, PaymentBatch

TEST_PERIOD = (date(2026, 1, 1), date(2026, 1, 31))


class PhcPulseGraphQLTest(openIMISGraphQLTestCase):
    """
    Uses the real openIMISGraphQLTestCase/send_mutation() harness (found in
    core.models.openimis_graphql_test_case) rather than a bespoke GraphQL test
    client, so these tests exercise the same mutation-log/signal pipeline
    production requests go through.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # --nomigrations test DBs don't carry the "en" Language fixture row
        # that create_test_interactive_user() assumes exists.
        Language.objects.get_or_create(code="en", defaults={"name": "English", "sort_order": 1})
        cls.user = create_test_interactive_user(username="phcpulsegraphqltestuser")
        cls.token = get_token(cls.user)
        cls.facility = create_test_health_facility()
        cls.product = create_test_product()
        cls.period_start, cls.period_end = TEST_PERIOD

    def test_payment_batches_query(self):
        batch = PaymentBatch(
            period_start=self.period_start,
            period_end=self.period_end,
            status=PaymentBatch.STATUS_DRAFT,
        )
        batch.save(user=self.user)

        response = self.query(
            """
            query {
                paymentBatches(status: "draft") {
                    id
                    status
                }
            }
            """,
            headers={"HTTP_AUTHORIZATION": f"Bearer {self.token}"},
        )
        self.assertResponseNoErrors(response)
        content = response.json()
        ids = [b["id"] for b in content["data"]["paymentBatches"]]
        self.assertIn(str(batch.id), ids)

    def test_run_capitation_cycle_mutation(self):
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

        self.send_mutation(
            "runCapitationCycle",
            {"periodStart": self.period_start, "periodEnd": self.period_end},
            self.token,
        )

        batch = PaymentBatch.objects.filter(
            period_start=self.period_start, period_end=self.period_end
        ).first()
        self.assertIsNotNone(batch)
        self.assertEqual(batch.lines.count(), 1)
        self.assertEqual(batch.lines.first().amount, Decimal("75000.00"))

    def test_approve_payment_batch_mutation(self):
        batch = PaymentBatch(
            period_start=self.period_start,
            period_end=self.period_end,
            status=PaymentBatch.STATUS_DRAFT,
        )
        batch.save(user=self.user)

        self.send_mutation(
            "approvePaymentBatch",
            {"batchId": str(batch.id)},
            self.token,
        )

        batch.refresh_from_db()
        self.assertEqual(batch.status, PaymentBatch.STATUS_APPROVED)
