import logging

from insuree.models import Insuree
from location.models import HealthFacility
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.models import TechnicalUser
from core.models import User as CoreUser

from .models import ServiceRecord

logger = logging.getLogger(__name__)

CHW_SYNC_SYSTEM_USERNAME = "phc_pulse_chw_sync"


def _get_chw_sync_system_user():
    """
    CHW field devices don't have interactive openIMIS sessions, but
    HistoryModel requires a real core.User for its audit fields. Attribute
    all synced records to a dedicated system account for now.

    TODO(Phase 6): replace with real per-device/per-CHW authentication before
    the actual submission — this shared system account is a placeholder, not
    a security design.
    """
    t_user, _ = TechnicalUser.objects.get_or_create(
        username=CHW_SYNC_SYSTEM_USERNAME,
        defaults={
            "email": "phc-pulse-system@openimis.local",
            "is_staff": False,
            "is_superuser": False,
        },
    )
    user, _ = CoreUser.objects.get_or_create(
        username=CHW_SYNC_SYSTEM_USERNAME, defaults={"t_user": t_user}
    )
    return user


# TODO(Phase 6): AllowAny is a placeholder so the offline PWA can sync before
# real device/CHW authentication is designed. Do not ship this permission to
# the actual submission without revisiting it.
@api_view(["POST"])
@permission_classes([AllowAny])
def chw_sync_webhook(request):
    payload = request.data

    required_fields = [
        "facility_id",
        "insuree_id",
        "service_type",
        "timestamp",
        "idempotency_key",
    ]
    missing = [f for f in required_fields if f not in payload]
    if missing:
        return Response(
            {"error": f"missing required fields: {missing}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    existing = ServiceRecord.objects.filter(
        idempotency_key=payload["idempotency_key"], is_deleted=False
    ).first()
    if existing:
        logger.info(
            "chw_sync_webhook: duplicate idempotency_key=%s, returning existing record %s",
            payload["idempotency_key"],
            existing.id,
        )
        return Response({"id": str(existing.id), "duplicate": True}, status=status.HTTP_200_OK)

    facility = HealthFacility.objects.filter(id=payload["facility_id"]).first()
    if facility is None:
        return Response(
            {"error": f"unknown facility_id {payload['facility_id']}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    insuree = Insuree.objects.filter(id=payload["insuree_id"]).first()
    if insuree is None:
        return Response(
            {"error": f"unknown insuree_id {payload['insuree_id']}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    system_user = _get_chw_sync_system_user()
    record = ServiceRecord(
        health_facility=facility,
        insuree=insuree,
        service_type=payload["service_type"],
        service_timestamp=payload["timestamp"],
        idempotency_key=payload["idempotency_key"],
    )
    record.save(user=system_user)

    logger.info(
        "chw_sync_webhook: recorded service_type=%s insuree=%s facility=%s record=%s",
        payload["service_type"],
        insuree.id,
        facility.id,
        record.id,
    )

    return Response({"id": str(record.id), "duplicate": False}, status=status.HTTP_201_CREATED)
