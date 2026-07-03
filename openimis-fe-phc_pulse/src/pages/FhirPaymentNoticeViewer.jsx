import React from "react";
import { Paper, Typography } from "@mui/material";

// Pretty-prints the fhirPaymentNotice JSON already present on a PaymentLine
// (see actions.js's facilityPaymentSummary projection, Phase 4). Kept
// dependency-free (no new JSON-viewer library) since we can't verify a new
// npm package installs cleanly without a running Docker stack to test
// against -- swap in a syntax-highlighted viewer once that's confirmed.
const FhirPaymentNoticeViewer = ({ paymentLine }) => {
  if (!paymentLine?.fhirPaymentNotice) {
    return <Typography>No FHIR PaymentNotice available for this payment line yet.</Typography>;
  }

  let pretty;
  try {
    pretty = JSON.stringify(JSON.parse(paymentLine.fhirPaymentNotice), null, 2);
  } catch (e) {
    pretty = paymentLine.fhirPaymentNotice;
  }

  return (
    <Paper variant="outlined" style={{ padding: 16, backgroundColor: "#1e1e1e" }}>
      <Typography variant="subtitle2" style={{ color: "#9cdcfe", marginBottom: 8 }}>
        FHIR R4 PaymentNotice
      </Typography>
      <pre style={{ color: "#d4d4d4", fontFamily: "monospace", fontSize: 13, margin: 0, whiteSpace: "pre-wrap" }}>
        {pretty}
      </pre>
    </Paper>
  );
};

export default FhirPaymentNoticeViewer;
