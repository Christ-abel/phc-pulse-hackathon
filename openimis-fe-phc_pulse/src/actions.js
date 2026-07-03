import { graphql, formatQuery, formatMutation } from "@openimis/fe-core";

// Our GraphQL types (Phase 3) are plain lists, not relay connections, so we
// use formatQuery (flat list) rather than formatPageQuery/formatPageQueryWithCount
// which build the pageInfo/edges/node shape other openIMIS modules use.

export function fetchPaymentBatches(status) {
  const filters = status ? [`status: "${status}"`] : [];
  const projections = ["id", "periodStart", "periodEnd", "status", "dateCreated"];
  const payload = formatQuery("paymentBatches", filters, projections);
  return graphql(payload, "PHC_PULSE_PAYMENT_BATCHES");
}

export function fetchFacilityPaymentSummary(facilityId, periodStart, periodEnd) {
  const filters = [
    `facilityId: "${facilityId}"`,
    `periodStart: "${periodStart}"`,
    `periodEnd: "${periodEnd}"`,
  ];
  const projections = [
    "id",
    "amount",
    "status",
    "dateCreated",
    "healthFacility{id, code, name}",
    "batch{id, periodStart, periodEnd, status}",
    "fhirPaymentNotice",
  ];
  const payload = formatQuery("facilityPaymentSummary", filters, projections);
  return graphql(payload, "PHC_PULSE_FACILITY_PAYMENT_SUMMARY");
}

export function approvePaymentBatch(batch, clientMutationLabel) {
  const payload = `batchId: "${batch.id}"`;
  const mutation = formatMutation("approvePaymentBatch", payload, clientMutationLabel);
  batch.clientMutationId = mutation.clientMutationId;
  return graphql(
    mutation.payload,
    ["PHC_PULSE_MUTATION_REQ", "PHC_PULSE_APPROVE_BATCH_RESP", "PHC_PULSE_MUTATION_ERR"],
    { clientMutationId: mutation.clientMutationId, clientMutationLabel },
  );
}
