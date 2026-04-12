import { DoneAll, RateReview, ReplayCircleFilled, RuleFolder } from '@mui/icons-material';
import { Box, Button, Card, Grid, Stack, Typography } from '@mui/material';
import { useEffect, useState } from 'react';

import { AppLayout } from '@/components/AppLayout';
import { StatusChip } from '@/components/StatusChip';
import { v2Api } from '@/services/api';
import { ChangeRequest } from '@/types';

const ReviewsPage = () => {
  const [requests, setRequests] = useState<ChangeRequest[]>([]);

  const load = async () => {
    const data = await v2Api.listChangeRequests();
    setRequests(data.filter((request) => ['SUBMITTED', 'IN_REVIEW', 'CHANGES_REQUESTED', 'APPROVED'].includes(request.status)));
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <AppLayout>
      <Typography variant="h3" sx={{ mb: 1 }}>
        Review Queue
      </Typography>
      <Typography sx={{ color: '#64748b', mb: 3 }}>
        Review the latest immutable revision, request changes when needed, and approve only when the request is ready to implement.
      </Typography>

      <Grid container spacing={3}>
        {requests.map((request) => (
          <Grid item xs={12} md={6} key={request.request_id}>
            <Card sx={{ p: 3 }}>
              <Stack direction="row" justifyContent="space-between" sx={{ mb: 2 }}>
                <Box>
                  <Typography variant="h6">{request.request_type}</Typography>
                  <Typography variant="body2" sx={{ color: '#64748b' }}>
                    {request.request_id.slice(0, 8)} • revision {request.latest_revision_number || '-'}
                  </Typography>
                </Box>
                <StatusChip value={request.status} />
              </Stack>
              <Stack direction="row" spacing={1.5} flexWrap="wrap">
                <Button
                  startIcon={<RateReview />}
                  variant="outlined"
                  onClick={async () => {
                    if (!request.current_revision_id) return;
                    await v2Api.reviewRequest(request.request_id, {
                      revision_id: request.current_revision_id,
                      decision: 'REQUEST_CHANGES',
                      note: 'Please revise the proposed config before approval.',
                    });
                    await load();
                  }}
                >
                  Request changes
                </Button>
                <Button
                  startIcon={<DoneAll />}
                  variant="contained"
                  onClick={async () => {
                    if (!request.current_revision_id) return;
                    await v2Api.reviewRequest(request.request_id, {
                      revision_id: request.current_revision_id,
                      decision: 'APPROVE',
                      note: 'Approved for implementation.',
                    });
                    await load();
                  }}
                >
                  Approve
                </Button>
                <Button
                  startIcon={<RuleFolder />}
                  variant="text"
                  onClick={async () => {
                    if (!request.current_revision_id) return;
                    await v2Api.reviewRequest(request.request_id, {
                      revision_id: request.current_revision_id,
                      decision: 'REJECT',
                      note: 'Rejected after review.',
                    });
                    await load();
                  }}
                >
                  Reject
                </Button>
              </Stack>
            </Card>
          </Grid>
        ))}
      </Grid>
    </AppLayout>
  );
};

export default ReviewsPage;

