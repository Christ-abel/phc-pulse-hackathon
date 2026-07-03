import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  CircularProgress,
  Button,
} from "@mui/material";

import { fetchFacilityPaymentSummary } from "../actions";
import FhirPaymentNoticeViewer from "./FhirPaymentNoticeViewer";

// For a non-technical PHC facility administrator: what am I owed, why, and
// what's already been paid. No GraphQL/FHIR jargon here -- that lives in
// FhirPaymentNoticeViewer, one click away for whoever wants it.
//
// TODO(follow-up): facilityId/periodStart/periodEnd should come from the
// logged-in HF admin's own profile/route params, not be passed in as raw
// props -- not wired up yet since there's no live backend to test the real
// user->facility association against.
const FacilityDashboard = ({ facilityId, periodStart, periodEnd }) => {
  const dispatch = useDispatch();
  const { facilityPaymentSummary, fetchingFacilityPaymentSummary, fetchedFacilityPaymentSummary } = useSelector(
    (state) => state.phcPulse,
  );
  const [fhirViewerLine, setFhirViewerLine] = useState(null);

  useEffect(() => {
    if (facilityId && periodStart && periodEnd) {
      dispatch(fetchFacilityPaymentSummary(facilityId, periodStart, periodEnd));
    }
  }, [facilityId, periodStart, periodEnd, dispatch]);

  if (fetchingFacilityPaymentSummary) {
    return <CircularProgress />;
  }

  const currentLine =
    fetchedFacilityPaymentSummary && facilityPaymentSummary?.length
      ? facilityPaymentSummary[facilityPaymentSummary.length - 1]
      : null;

  return (
    <Card>
      <CardHeader title="Your PHC Pulse Payment Dashboard" />
      <CardContent>
        {!currentLine && <Typography>No payment has been calculated for this period yet.</Typography>}
        {currentLine && (
          <>
            <Typography variant="h4">
              {currentLine.amount} ({currentLine.status})
            </Typography>
            <Typography variant="body1" style={{ marginTop: 8 }}>
              This is your facility's capitation payment for {periodStart} to {periodEnd}, calculated as your
              enrolled population multiplied by the per-head rate for your scheme's benefit package.
            </Typography>
          </>
        )}

        <Typography variant="h6" style={{ marginTop: 24 }}>
          Payment history
        </Typography>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Period</TableCell>
              <TableCell>Amount</TableCell>
              <TableCell>Status</TableCell>
              <TableCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {(facilityPaymentSummary || []).map((line) => (
              <TableRow key={line.id}>
                <TableCell>
                  {line.batch?.periodStart} - {line.batch?.periodEnd}
                </TableCell>
                <TableCell>{line.amount}</TableCell>
                <TableCell>{line.status}</TableCell>
                <TableCell>
                  <Button size="small" onClick={() => setFhirViewerLine(line)}>
                    View FHIR PaymentNotice
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        {fhirViewerLine && (
          <div style={{ marginTop: 16 }}>
            <FhirPaymentNoticeViewer paymentLine={fhirViewerLine} />
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default FacilityDashboard;
