import { formatGraphQLError, formatServerError } from "@openimis/fe-core";

const initialState = {
  fetchingPaymentBatches: false,
  fetchedPaymentBatches: false,
  paymentBatches: [],
  errorPaymentBatches: null,

  fetchingFacilityPaymentSummary: false,
  fetchedFacilityPaymentSummary: false,
  facilityPaymentSummary: [],
  errorFacilityPaymentSummary: null,

  submittingMutation: false,
  mutation: {},
};

function reducer(state = initialState, action) {
  switch (action.type) {
    case "PHC_PULSE_PAYMENT_BATCHES_REQ":
      return { ...state, fetchingPaymentBatches: true, fetchedPaymentBatches: false };
    case "PHC_PULSE_PAYMENT_BATCHES_RESP":
      return {
        ...state,
        fetchingPaymentBatches: false,
        fetchedPaymentBatches: true,
        paymentBatches: action.payload?.data?.paymentBatches || [],
        errorPaymentBatches: formatGraphQLError(action.payload),
      };
    case "PHC_PULSE_PAYMENT_BATCHES_ERR":
      return { ...state, fetchingPaymentBatches: false, errorPaymentBatches: formatServerError(action.payload) };

    case "PHC_PULSE_FACILITY_PAYMENT_SUMMARY_REQ":
      return { ...state, fetchingFacilityPaymentSummary: true, fetchedFacilityPaymentSummary: false };
    case "PHC_PULSE_FACILITY_PAYMENT_SUMMARY_RESP":
      return {
        ...state,
        fetchingFacilityPaymentSummary: false,
        fetchedFacilityPaymentSummary: true,
        facilityPaymentSummary: action.payload?.data?.facilityPaymentSummary || [],
        errorFacilityPaymentSummary: formatGraphQLError(action.payload),
      };
    case "PHC_PULSE_FACILITY_PAYMENT_SUMMARY_ERR":
      return {
        ...state,
        fetchingFacilityPaymentSummary: false,
        errorFacilityPaymentSummary: formatServerError(action.payload),
      };

    case "PHC_PULSE_MUTATION_REQ":
      return { ...state, submittingMutation: true };
    case "PHC_PULSE_APPROVE_BATCH_RESP":
      return { ...state, submittingMutation: false, mutation: action.payload?.data?.approvePaymentBatch || {} };
    case "PHC_PULSE_MUTATION_ERR":
      return { ...state, submittingMutation: false };

    default:
      return state;
  }
}

export default reducer;
