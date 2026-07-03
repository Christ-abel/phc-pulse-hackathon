import graphene
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext as _

from core.schema import OpenIMISMutation

from .gql_queries import PaymentBatchGQLType, PaymentLineGQLType
from .models import PaymentBatch, PaymentLine
from .services import MissingCapitationRateError, run_capitation_cycle

# Picked up by openIMIS core's dynamic schema aggregation (openIMIS/openIMIS/schema.py),
# which imports every installed module's schema.py and merges its Query/Mutation
# into the platform-wide GraphQL schema.


class Query(graphene.ObjectType):
    facility_payment_summary = graphene.List(
        PaymentLineGQLType,
        facility_id=graphene.String(required=True),
        period_start=graphene.Date(required=True),
        period_end=graphene.Date(required=True),
        description="A facility's payment lines and status for a given billing period.",
    )
    payment_batches = graphene.List(
        PaymentBatchGQLType,
        status=graphene.String(required=False),
        description="List capitation payment batches, optionally filtered by status.",
    )

    def resolve_facility_payment_summary(
        self, info, facility_id, period_start, period_end, **kwargs
    ):
        if info.context.user.is_anonymous:
            raise PermissionDenied(_("unauthorized"))
        return PaymentLine.objects.filter(
            is_deleted=False,
            health_facility__id=facility_id,
            batch__period_start=period_start,
            batch__period_end=period_end,
        )

    def resolve_payment_batches(self, info, status=None, **kwargs):
        if info.context.user.is_anonymous:
            raise PermissionDenied(_("unauthorized"))
        qs = PaymentBatch.objects.filter(is_deleted=False)
        if status:
            qs = qs.filter(status=status)
        return qs


class RunCapitationCycleMutation(OpenIMISMutation):
    """Triggers the capitation calculation from Phase 2 for a billing period."""

    _mutation_module = "phc_pulse"

    class Input(OpenIMISMutation.Input):
        period_start = graphene.Date(required=True)
        period_end = graphene.Date(required=True)

    @classmethod
    def async_mutate(cls, user, **data):
        try:
            if type(user) is AnonymousUser or not user.id:
                raise PermissionDenied(_("mutation.authentication_required"))
            run_capitation_cycle(data["period_start"], data["period_end"], user)
            return None
        except MissingCapitationRateError as exc:
            # Batch was still created (see services.run_capitation_cycle) —
            # surfaced as a mutation error so the caller knows it's incomplete.
            return [
                {
                    "message": "phc_pulse.mutation.missing_capitation_rate",
                    "detail": str(exc),
                }
            ]
        except Exception as exc:
            return [
                {
                    "message": "phc_pulse.mutation.failed_to_run_capitation_cycle",
                    "detail": str(exc),
                }
            ]


class ApprovePaymentBatchMutation(OpenIMISMutation):
    """Moves a PaymentBatch from draft to approved."""

    _mutation_module = "phc_pulse"

    class Input(OpenIMISMutation.Input):
        batch_id = graphene.String(required=True)

    @classmethod
    def async_mutate(cls, user, **data):
        try:
            if type(user) is AnonymousUser or not user.id:
                raise PermissionDenied(_("mutation.authentication_required"))

            batch = PaymentBatch.objects.filter(
                id=data["batch_id"], is_deleted=False
            ).first()
            if batch is None:
                return [
                    {
                        "message": "phc_pulse.mutation.batch_not_found",
                        "detail": data["batch_id"],
                    }
                ]
            if batch.status != PaymentBatch.STATUS_DRAFT:
                return [
                    {
                        "message": "phc_pulse.mutation.invalid_batch_status",
                        "detail": (
                            f"Batch {batch.id} is '{batch.status}', expected 'draft'"
                        ),
                    }
                ]

            batch.status = PaymentBatch.STATUS_APPROVED
            batch.save(user=user)
            return None
        except Exception as exc:
            return [
                {
                    "message": "phc_pulse.mutation.failed_to_approve_batch",
                    "detail": str(exc),
                }
            ]


class Mutation(graphene.ObjectType):
    run_capitation_cycle = RunCapitationCycleMutation.Field()
    approve_payment_batch = ApprovePaymentBatchMutation.Field()
