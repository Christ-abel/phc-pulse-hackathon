from django.db import models

from core.models import HistoryModel
from insuree.models import Insuree
from location.models import HealthFacility
from product.models import Product


class CapitationRate(HistoryModel):
    """Per-head monthly capitation rate for a given openIMIS benefit package (Product)."""

    product = models.ForeignKey(
        Product, models.DO_NOTHING, related_name="phc_pulse_capitation_rates"
    )
    rate_per_head = models.DecimalField(max_digits=18, decimal_places=2)
    period_start = models.DateField()
    period_end = models.DateField(blank=True, null=True)

    class Meta:
        db_table = "phc_pulse_CapitationRate"


class FacilityEnrolment(HistoryModel):
    """
    Snapshot of a health facility's enrolled population for a given product and
    billing period. Populated by a sync step that walks openIMIS's real
    HealthFacilityCatchment -> Location -> Family -> Insuree/Policy chain
    (there is no direct facility FK on Insuree/Policy in core openIMIS —
    enrolment is geographic via catchment, not a direct link); the capitation
    calculation functions consume this stored count rather than recomputing it
    live on every call.
    """

    health_facility = models.ForeignKey(
        HealthFacility, models.DO_NOTHING, related_name="phc_pulse_enrolments"
    )
    product = models.ForeignKey(
        Product, models.DO_NOTHING, related_name="phc_pulse_enrolments"
    )
    period_start = models.DateField()
    period_end = models.DateField()
    enrolled_count = models.PositiveIntegerField()

    class Meta:
        db_table = "phc_pulse_FacilityEnrolment"
        constraints = [
            models.UniqueConstraint(
                fields=["health_facility", "product", "period_start", "period_end"],
                condition=models.Q(is_deleted=False),
                name="phc_pulse_unique_facility_enrolment_period",
            )
        ]


class PaymentBatch(HistoryModel):
    STATUS_DRAFT = "draft"
    STATUS_APPROVED = "approved"
    STATUS_DISBURSED = "disbursed"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_DISBURSED, "Disbursed"),
    ]

    period_start = models.DateField()
    period_end = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_DRAFT)

    class Meta:
        db_table = "phc_pulse_PaymentBatch"


class PaymentLine(HistoryModel):
    batch = models.ForeignKey(PaymentBatch, models.DO_NOTHING, related_name="lines")
    health_facility = models.ForeignKey(
        HealthFacility, models.DO_NOTHING, related_name="phc_pulse_payment_lines"
    )
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    status = models.CharField(
        max_length=10, choices=PaymentBatch.STATUS_CHOICES, default=PaymentBatch.STATUS_DRAFT
    )

    class Meta:
        db_table = "phc_pulse_PaymentLine"


class ServiceRecord(HistoryModel):
    """
    Phase 3 placeholder: one CHW-recorded service visit, synced from the
    offline PWA (Phase 6) via the /webhook/chw-sync/ REST endpoint.
    `idempotency_key` is client-generated so retried/duplicate syncs from an
    unreliable field connection don't create duplicate records.
    """

    health_facility = models.ForeignKey(
        HealthFacility, models.DO_NOTHING, related_name="phc_pulse_service_records"
    )
    insuree = models.ForeignKey(
        Insuree, models.DO_NOTHING, related_name="phc_pulse_service_records"
    )
    service_type = models.CharField(max_length=100)
    service_timestamp = models.DateTimeField()
    idempotency_key = models.UUIDField(unique=True)

    class Meta:
        db_table = "phc_pulse_ServiceRecord"
