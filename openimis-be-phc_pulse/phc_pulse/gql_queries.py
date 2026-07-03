import graphene
from graphene_django import DjangoObjectType

from .fhir_converters import PaymentLineToFhirPaymentNoticeConverter
from .models import PaymentBatch, PaymentLine

# Plain DjangoObjectType (no relay Node interface / connection) — kept simple
# and queried via graphene.List rather than the relay-connection ceremony
# other openIMIS modules use for their filterable list queries. Revisit if
# the frontend later needs cursor pagination over large batch/line lists.


class PaymentBatchGQLType(DjangoObjectType):
    class Meta:
        model = PaymentBatch
        fields = ("id", "period_start", "period_end", "status", "date_created")


class PaymentLineGQLType(DjangoObjectType):
    fhir_payment_notice = graphene.JSONString(
        description="This PaymentLine as a FHIR R4 PaymentNotice resource (hl7.org/fhir/R4/paymentnotice.html)."
    )

    class Meta:
        model = PaymentLine
        fields = ("id", "batch", "health_facility", "amount", "status", "date_created")

    def resolve_fhir_payment_notice(self, info):
        fhir_obj = PaymentLineToFhirPaymentNoticeConverter.to_fhir_obj(self)
        return fhir_obj.json()
