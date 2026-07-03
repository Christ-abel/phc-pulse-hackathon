import logging
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Q

from .models import CapitationRate, FacilityEnrolment, PaymentBatch, PaymentLine

logger = logging.getLogger(__name__)


class MissingCapitationRateError(Exception):
    """Raised when no CapitationRate covers a facility's product/period —
    surfaced explicitly so an incomplete batch can't be disbursed silently."""


def calculate_capitation_for_facility(facility, rate, enrolled_count, period):
    """
    Pure function: no DB writes, no I/O — safe to unit-test without a database.

    `facility` is a HealthFacility instance (kept for signature parity and for
    future proration logic; unused in this flat-rate calculation). `rate` is a
    CapitationRate instance (or any object exposing `.rate_per_head`).
    `enrolled_count` is a non-negative int. `period` is a
    (period_start, period_end) tuple, reserved for future partial-period
    proration.
    """
    if rate is None:
        raise MissingCapitationRateError(
            f"No capitation rate provided for facility "
            f"{getattr(facility, 'code', facility)}"
        )
    if enrolled_count < 0:
        raise ValueError(f"enrolled_count cannot be negative, got {enrolled_count}")

    amount = Decimal(rate.rate_per_head) * Decimal(enrolled_count)
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _find_capitation_rate(product, period_start, period_end):
    return (
        CapitationRate.objects.filter(is_deleted=False, product=product)
        .filter(period_start__lte=period_start)
        .filter(Q(period_end__gte=period_end) | Q(period_end__isnull=True))
        .order_by("-period_start")
        .first()
    )


def run_capitation_cycle(period_start: date, period_end: date, user):
    """
    Creates a draft PaymentBatch with one PaymentLine per FacilityEnrolment
    snapshot recorded for the period. If any facility/product pair has no
    matching CapitationRate, the batch is still created (so partial progress
    isn't lost) but MissingCapitationRateError is raised afterward listing
    exactly which pairs were skipped, rather than disbursing an incomplete
    batch silently.
    """
    batch = PaymentBatch(
        period_start=period_start, period_end=period_end, status=PaymentBatch.STATUS_DRAFT
    )
    batch.save(user=user)

    enrolments = FacilityEnrolment.objects.filter(
        is_deleted=False, period_start=period_start, period_end=period_end
    )

    missing_rate_for = []
    for enrolment in enrolments:
        rate = _find_capitation_rate(enrolment.product, period_start, period_end)
        if rate is None:
            missing_rate_for.append((enrolment.health_facility_id, enrolment.product_id))
            logger.warning(
                "No CapitationRate for facility=%s product=%s period=%s..%s; "
                "skipping payment line.",
                enrolment.health_facility_id,
                enrolment.product_id,
                period_start,
                period_end,
            )
            continue

        amount = calculate_capitation_for_facility(
            enrolment.health_facility,
            rate,
            enrolment.enrolled_count,
            (period_start, period_end),
        )
        line = PaymentLine(
            batch=batch,
            health_facility=enrolment.health_facility,
            amount=amount,
            status=PaymentBatch.STATUS_DRAFT,
        )
        line.save(user=user)

    if missing_rate_for:
        raise MissingCapitationRateError(
            f"Batch {batch.id} created but incomplete: no CapitationRate found "
            f"for (health_facility_id, product_id) pairs: {missing_rate_for}"
        )

    return batch
