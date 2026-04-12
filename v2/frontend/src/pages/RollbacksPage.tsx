import { History, Replay, TaskAlt } from '@mui/icons-material';
import {
  Box,
  Button,
  Card,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useEffect, useMemo, useState } from 'react';

import { AppLayout } from '@/components/AppLayout';
import { StatusChip } from '@/components/StatusChip';
import { v2Api } from '@/services/api';
import { ConfigNode, ConfigNodeVersion, RollbackRequest, Service } from '@/types';

const RollbacksPage = () => {
  const [services, setServices] = useState<Service[]>([]);
  const [selectedServiceId, setSelectedServiceId] = useState('');
  const [nodes, setNodes] = useState<ConfigNode[]>([]);
  const [versions, setVersions] = useState<ConfigNodeVersion[]>([]);
  const [rollbacks, setRollbacks] = useState<RollbackRequest[]>([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [draft, setDraft] = useState({ nodeId: '', versionId: '' });

  const selectedService = useMemo(
    () => services.find((service) => service.service_id === selectedServiceId) || null,
    [services, selectedServiceId]
  );

  const load = async () => {
    const [servicesData, rollbacksData] = await Promise.all([v2Api.listServices(), v2Api.listRollbacks()]);
    setServices(servicesData);
    setRollbacks(rollbacksData);
    if (!selectedServiceId && servicesData[0]) setSelectedServiceId(servicesData[0].service_id);
  };

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    if (!selectedServiceId) return;
    v2Api.listNodes(selectedServiceId).then(setNodes);
  }, [selectedServiceId]);

  useEffect(() => {
    if (!selectedServiceId || !draft.nodeId) return;
    v2Api.listVersions(selectedServiceId, draft.nodeId).then(setVersions);
  }, [selectedServiceId, draft.nodeId]);

  return (
    <AppLayout>
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" alignItems={{ xs: 'flex-start', md: 'center' }} sx={{ mb: 3 }}>
        <Box>
          <Typography variant="h3" sx={{ mb: 1 }}>
            Rollbacks
          </Typography>
          <Typography sx={{ color: '#64748b' }}>
            Recover from a bad configuration by promoting a known-good historical node version through the same governed activation model.
          </Typography>
        </Box>
        <Button startIcon={<Replay />} variant="contained" onClick={() => setDialogOpen(true)}>
          Request rollback
        </Button>
      </Stack>

      <Grid container spacing={3}>
        {rollbacks.map((rollback) => (
          <Grid item xs={12} md={6} key={rollback.rollback_request_id}>
            <Card sx={{ p: 3 }}>
              <Stack direction="row" justifyContent="space-between" sx={{ mb: 2 }}>
                <Box>
                  <Typography variant="h6">Rollback {rollback.rollback_request_id.slice(0, 8)}</Typography>
                  <Typography variant="body2" sx={{ color: '#64748b' }}>
                    Node {rollback.target_config_node_id.slice(0, 8)} • version {rollback.target_version_id.slice(0, 8)}
                  </Typography>
                </Box>
                <StatusChip value={rollback.status} />
              </Stack>
              <Stack direction="row" spacing={1.5}>
                <Button
                  startIcon={<TaskAlt />}
                  variant="outlined"
                  onClick={async () => {
                    await v2Api.approveRollback(rollback.rollback_request_id);
                    await load();
                  }}
                  disabled={rollback.status !== 'REQUESTED'}
                >
                  Approve
                </Button>
                <Button
                  startIcon={<History />}
                  variant="contained"
                  onClick={async () => {
                    await v2Api.implementRollback(rollback.rollback_request_id);
                    await load();
                  }}
                  disabled={rollback.status !== 'APPROVED'}
                >
                  Implement
                </Button>
              </Stack>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Create rollback request</DialogTitle>
        <DialogContent sx={{ pt: 1 }}>
          <Stack spacing={2}>
            <TextField
              select
              label="Service"
              value={selectedServiceId}
              onChange={(event) => {
                setSelectedServiceId(event.target.value);
                setDraft({ nodeId: '', versionId: '' });
                setVersions([]);
              }}
            >
              {services.map((service) => (
                <MenuItem key={service.service_id} value={service.service_id}>
                  {service.service_name}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              select
              label="Node"
              value={draft.nodeId}
              onChange={(event) => setDraft({ ...draft, nodeId: event.target.value, versionId: '' })}
            >
              {nodes.map((node) => (
                <MenuItem key={node.config_node_id} value={node.config_node_id}>
                  {node.path}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              select
              label="Target version"
              value={draft.versionId}
              onChange={(event) => setDraft({ ...draft, versionId: event.target.value })}
            >
              {versions.map((version) => (
                <MenuItem key={version.version_id} value={version.version_id}>
                  {version.version_status} • tree {version.tree_version} • {new Date(version.created_at).toLocaleString()}
                </MenuItem>
              ))}
            </TextField>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={async () => {
              if (!selectedServiceId || !draft.nodeId || !draft.versionId) return;
              await v2Api.createRollback({
                service_id: selectedServiceId,
                target_config_node_id: draft.nodeId,
                target_version_id: draft.versionId,
              });
              setDialogOpen(false);
              setDraft({ nodeId: '', versionId: '' });
              await load();
            }}
          >
            Create request
          </Button>
        </DialogActions>
      </Dialog>
    </AppLayout>
  );
};

export default RollbacksPage;

