import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  Card,
  CardHeader,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
} from "@mui/material";

import { fetchPaymentBatches, approvePaymentBatch } from "../actions";

// For the scheme administrator: review draft capitation batches and approve
// them. Approve flow is deliberately two clicks (Approve -> confirm) to stay
// within the plan's "3 clicks or fewer" requirement.
const SchemeConsole = () => {
  const dispatch = useDispatch();
  const { paymentBatches, fetchingPaymentBatches } = useSelector((state) => state.phcPulse);
  const [confirmBatch, setConfirmBatch] = useState(null);

  useEffect(() => {
    dispatch(fetchPaymentBatches("draft"));
  }, [dispatch]);

  const handleApproveClick = (batch) => setConfirmBatch(batch);

  const handleConfirmApprove = () => {
    // Re-fetch after the approve mutation resolves so the approved batch
    // drops off the draft list. Relies on core's graphql() action awaiting
    // the mutation-log response -- not yet exercised against a live backend.
    dispatch(approvePaymentBatch(confirmBatch, `Approve batch ${confirmBatch.id}`)).then(() => {
      dispatch(fetchPaymentBatches("draft"));
    });
    setConfirmBatch(null);
  };

  return (
    <Card>
      <CardHeader title="Scheme Console — Draft Capitation Batches" />
      <CardContent>
        {fetchingPaymentBatches && <CircularProgress />}
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Period</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Created</TableCell>
              <TableCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {(paymentBatches || []).map((batch) => (
              <TableRow key={batch.id}>
                <TableCell>
                  {batch.periodStart} - {batch.periodEnd}
                </TableCell>
                <TableCell>{batch.status}</TableCell>
                <TableCell>{batch.dateCreated}</TableCell>
                <TableCell>
                  <Button variant="contained" onClick={() => handleApproveClick(batch)}>
                    Approve Batch
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>

      <Dialog open={!!confirmBatch} onClose={() => setConfirmBatch(null)}>
        <DialogTitle>Approve this payment batch?</DialogTitle>
        <DialogContent>
          This will move batch {confirmBatch?.id} for period {confirmBatch?.periodStart} -{" "}
          {confirmBatch?.periodEnd} from draft to approved.
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmBatch(null)}>Cancel</Button>
          <Button variant="contained" color="primary" onClick={handleConfirmApprove}>
            Yes, Approve
          </Button>
        </DialogActions>
      </Dialog>
    </Card>
  );
};

export default SchemeConsole;
