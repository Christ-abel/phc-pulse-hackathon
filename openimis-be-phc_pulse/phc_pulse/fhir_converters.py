from api_fhir_r4.configurations import R4IdentifierConfig
from api_fhir_r4.converters import BaseFHIRConverter, ReferenceConverterMixin
from api_fhir_r4.converters.healthFacilityOrganisationConverter import (
    HealthFacilityOrganisationConverter,
)
from fhir.resources.R4B.paymentnotice import PaymentNotice
from fhir.resources.R4B.reference import Reference

from .models import PaymentBatch, PaymentLine


class PaymentLineToFhirPaymentNoticeConverter(BaseFHIRConverter, ReferenceConverterMixin):
    """
    Converts a phc_pulse PaymentLine into a FHIR R4 PaymentNotice resource
    (hl7.org/fhir/R4/paymentnotice.html), built on the same base classes
    (BaseFHIRConverter, ReferenceConverterMixin), the same
    HealthFacilityOrganisationConverter used for Organization references, and
    the same validated fhir.resources.R4B.paymentnotice.PaymentNotice Pydantic
    model that openimis-be-api_fhir_r4's own PaymentNoticeToFhirConverter uses.

    Not subclassing that converter directly: its field-population methods
    assume core `payment.models.Payment` + `invoice`/`PaymentReconciliation`
    relations we don't have. Our domain object is PaymentLine/PaymentBatch.

    Two known simplifications (no dedicated resources exist yet for these):
    - `payment` references "PaymentReconciliation/{batch_id}" — a
      syntactically valid FHIR reference, but PaymentReconciliation isn't a
      real, dereferenceable resource in this module.
    - `recipient` (the org being notified of payment, required 1..1 by spec)
      points at the facility itself, since no distinct Payer/Scheme
      Organization is modelled yet. `payee` (the facility as the party paid,
      requested by the build plan) also points at the facility — same
      Organization, two different FHIR roles collapse onto it for now.
    """

    STATUS_MAP = {
        PaymentBatch.STATUS_DRAFT: "draft",
        PaymentBatch.STATUS_APPROVED: "active",
        PaymentBatch.STATUS_DISBURSED: "active",
    }

    @classmethod
    def to_fhir_obj(cls, payment_line: PaymentLine, reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE):
        fhir_payment_notice = {}
        cls.build_fhir_status(fhir_payment_notice, payment_line)
        cls.build_fhir_created(fhir_payment_notice, payment_line)
        cls.build_fhir_amount(fhir_payment_notice, payment_line)
        cls.build_fhir_payment(fhir_payment_notice, payment_line)
        cls.build_fhir_recipient(fhir_payment_notice, payment_line)
        cls.build_fhir_payee(fhir_payment_notice, payment_line, reference_type)
        fhir_payment_notice = PaymentNotice(**fhir_payment_notice)
        cls.build_fhir_pk(fhir_payment_notice, payment_line, reference_type)
        cls.build_fhir_request(fhir_payment_notice, payment_line)
        return fhir_payment_notice

    @classmethod
    def build_fhir_status(cls, fhir_payment_notice, payment_line):
        fhir_payment_notice["status"] = cls.STATUS_MAP.get(payment_line.status, "draft")

    @classmethod
    def build_fhir_created(cls, fhir_payment_notice, payment_line):
        fhir_payment_notice["created"] = payment_line.date_created.isoformat()

    @classmethod
    def build_fhir_amount(cls, fhir_payment_notice, payment_line):
        fhir_payment_notice["amount"] = cls.build_fhir_money(payment_line.amount)

    @classmethod
    def build_fhir_payment(cls, fhir_payment_notice, payment_line):
        reference = Reference.construct()
        reference.reference = f"PaymentReconciliation/{payment_line.batch_id}"
        fhir_payment_notice["payment"] = reference

    @classmethod
    def build_fhir_recipient(cls, fhir_payment_notice, payment_line):
        fhir_payment_notice["recipient"] = HealthFacilityOrganisationConverter.build_fhir_resource_reference(
            payment_line.health_facility, type="Organization"
        )

    @classmethod
    def build_fhir_payee(cls, fhir_payment_notice, payment_line, reference_type):
        fhir_payment_notice["payee"] = HealthFacilityOrganisationConverter.build_fhir_resource_reference(
            payment_line.health_facility, type="Organization", reference_type=reference_type
        )

    @classmethod
    def build_fhir_request(cls, fhir_payment_notice, payment_line):
        # "Basic" is FHIR's own generic/placeholder resource type, used here
        # since PaymentBatch has no dedicated FHIR resource of its own.
        reference = Reference.construct()
        reference.reference = f"Basic/{payment_line.batch_id}"
        fhir_payment_notice.request = reference

    @classmethod
    def get_reference_obj_uuid(cls, payment_line):
        return payment_line.id

    @classmethod
    def get_reference_obj_id(cls, payment_line):
        return payment_line.id

    @classmethod
    def get_fhir_resource_type(cls):
        return PaymentNotice

    @classmethod
    def get_fhir_code_identifier_type(cls):
        return R4IdentifierConfig.get_fhir_generic_type_code()
