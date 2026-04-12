import { AccountTree, Approval, Layers, Replay } from '@mui/icons-material';
import { Box, Card, Grid, Stack, Typography } from '@mui/material';
import { useEffect, useState } from 'react';

import { AppLayout } from '@/components/AppLayout';
import { StatusChip } from '@/components/StatusChip';
import { v2Api } from '@/services/api';
import { ChangeRequest, RollbackRequest, Service } from '@/types';

const MetricCard = ({ title, value, icon, helper }: { title: string; value: string | number; icon: React.ReactNode; helper: string }) => (
  <Card sx={{ p: 3 }}>
    <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
      <Typography variant="overline" sx={{ color: '#64748b', fontWeight: 800, letterSpacing: '0.14em' }}>
        {title}
      </Typography>
      <Box sx={{ p: 1.3, borderRadius: 3, bgcolor: 'rgba(91,77,245,0.08)', color: '#5b4df5' }}>{icon}</Box>
    </Stack>
    <Typography variant="h4">{value}</Typography>
    <Typography sx={{ mt: 1, color: '#64748b' }}>{helper}</Typography>
  </Card>
);

const DashboardPage = () => {
  const [services, setServices] = useState<Service[]>([]);
  const [requests, setRequests] = useState<ChangeRequest[]>([]);
  const [rollbacks, setRollbacks] = useState<RollbackRequest[]>([]);

  useEffect(() => {
    Promise.all([v2Api.listServices(), v2Api.listChangeRequests(), v2Api.listRollbacks()]).then(([servicesData, requestsData, rollbacksData]) => {
      setServices(servicesData);
      setRequests(requestsData);
      setRollbacks(rollbacksData);
    });
  }, []);

  return (
    <AppLayout>
      <Typography variant="h3" sx={{ mb: 1 }}>
        Dashboard
      </Typography>
      <Typography sx={{ color: '#64748b', mb: 4 }}>
        Track governed configuration work across services, approval queues, propagation jobs, and rollback readiness.
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={3}>
          <MetricCard title="Services" value={services.length} icon={<Layers />} helper="Managed service trees" />
        </Grid>
        <Grid item xs={12} md={3}>
          <MetricCard title="Nodes" value={services.reduce((sum, service) => sum + service.node_count, 0)} icon={<AccountTree />} helper="Precomputed config nodes" />
        </Grid>
        <Grid item xs={12} md={3}>
          <MetricCard title="Requests" value={requests.length} icon={<Approval />} helper="Change requests in workflow" />
        </Grid>
        <Grid item xs={12} md={3}>
          <MetricCard title="Rollbacks" value={rollbacks.length} icon={<Replay />} helper="Rollback records and approvals" />
        </Grid>

        <Grid item xs={12} md={7}>
          <Card sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Recent Change Requests
            </Typography>
            <Stack spacing={1.5}>
              {requests.slice(0, 6).map((request) => (
                <Stack
                  key={request.request_id}
                  direction="row"
                  justifyContent="space-between"
                  alignItems="center"
                  sx={{ p: 2, borderRadius: 3, bgcolor: 'rgba(91,77,245,0.04)' }}
                >
                  <Box>
                    <Typography sx={{ fontWeight: 700 }}>{request.request_type}</Typography>
                    <Typography variant="body2" sx={{ color: '#64748b' }}>
                      Request {request.request_id.slice(0, 8)} • revision {request.latest_revision_number || '-'}
                    </Typography>
                  </Box>
                  <StatusChip value={request.status} />
                </Stack>
              ))}
            </Stack>
          </Card>
        </Grid>

        <Grid item xs={12} md={5}>
          <Card sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Design Summary
            </Typography>
            <Stack spacing={1.25}>
              <Typography>Authentication: Keycloak with dev fallback</Typography>
              <Typography>Storage: PostgreSQL + DynamoDB Local</Typography>
              <Typography>Execution: Async propagation via Kafka worker</Typography>
              <Typography>Conflict model: strict optimistic concurrency</Typography>
              <Typography>Rollback: implemented as new auditable active version</Typography>
            </Stack>
          </Card>
        </Grid>
      </Grid>
    </AppLayout>
  );
};

export default DashboardPage;

