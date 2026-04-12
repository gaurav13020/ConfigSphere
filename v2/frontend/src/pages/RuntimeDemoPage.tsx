import { Add, PlayArrow, Refresh, Sensors } from '@mui/icons-material';
import {
  Alert,
  Box,
  Button,
  Card,
  Grid,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import axios from 'axios';
import { useEffect, useMemo, useRef, useState } from 'react';

import { AppLayout } from '@/components/AppLayout';
import { v2Api } from '@/services/api';
import { ConfigNode, DeliveryConfig, DeliveryVersion, Service } from '@/types';

type RuntimeInstance = {
  instanceId: string;
  instanceName: string;
  path: string;
  status: 'idle' | 'polling' | 'healthy' | 'error';
  versionId: string | null;
  treeVersion: number | null;
  config: Record<string, string>;
  lastPollAt: string | null;
  lastUpdatedAt: string | null;
  errorMessage: string | null;
};

const RuntimeDemoPage = () => {
  const [services, setServices] = useState<Service[]>([]);
  const [selectedServiceId, setSelectedServiceId] = useState('');
  const [nodes, setNodes] = useState<ConfigNode[]>([]);
  const [configToken, setConfigToken] = useState('');
  const [instances, setInstances] = useState<RuntimeInstance[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState({ instanceName: '', path: '' });
  const timers = useRef<Record<string, number>>({});
  const instancesRef = useRef<RuntimeInstance[]>([]);

  const selectedService = useMemo(
    () => services.find((service) => service.service_id === selectedServiceId) || null,
    [services, selectedServiceId]
  );

  const loadServices = async () => {
    const data = await v2Api.listServices();
    setServices(data);
    if (!selectedServiceId && data[0]) setSelectedServiceId(data[0].service_id);
  };

  useEffect(() => {
    loadServices();
  }, []);

  useEffect(() => {
    if (!selectedServiceId) return;
    v2Api.listNodes(selectedServiceId).then(setNodes).catch(() => setNodes([]));
  }, [selectedServiceId]);

  useEffect(() => {
    return () => {
      Object.values(timers.current).forEach((timerId) => window.clearInterval(timerId));
    };
  }, []);

  useEffect(() => {
    instancesRef.current = instances;
  }, [instances]);

  const pollInstance = async (serviceName: string, instanceId: string, path: string, token: string) => {
    setInstances((current) =>
      current.map((instance) =>
        instance.instanceId === instanceId
          ? { ...instance, status: instance.status === 'idle' ? 'polling' : instance.status, lastPollAt: new Date().toISOString() }
          : instance
      )
    );

    try {
      const version: DeliveryVersion = await v2Api.getVersionWithToken(serviceName, path, token);
      const current = instancesRef.current.find((instance) => instance.instanceId === instanceId);
      if (!current || current.versionId !== version.versionId) {
        const config: DeliveryConfig = await v2Api.getConfigWithToken(serviceName, path, token);
        setInstances((existing) =>
          existing.map((instance) =>
            instance.instanceId === instanceId
              ? {
                  ...instance,
                  status: 'healthy',
                  versionId: version.versionId,
                  treeVersion: version.treeVersion,
                  config: config.materializedConfig,
                  lastPollAt: new Date().toISOString(),
                  lastUpdatedAt: new Date().toISOString(),
                  errorMessage: null,
                }
              : instance
          )
        );
      } else {
        setInstances((existing) =>
          existing.map((instance) =>
            instance.instanceId === instanceId
              ? {
                  ...instance,
                  status: 'healthy',
                  treeVersion: version.treeVersion,
                  lastPollAt: new Date().toISOString(),
                  errorMessage: null,
                }
              : instance
          )
        );
      }
    } catch (err) {
      const message = axios.isAxiosError(err) ? err.response?.data?.detail || err.message : 'Polling failed';
      setInstances((existing) =>
        existing.map((instance) =>
          instance.instanceId === instanceId
            ? {
                ...instance,
                status: 'error',
                lastPollAt: new Date().toISOString(),
                errorMessage: message,
              }
            : instance
        )
      );
    }
  };

  useEffect(() => {
    Object.values(timers.current).forEach((timerId) => window.clearInterval(timerId));
    timers.current = {};

    if (!selectedService || !configToken.trim()) return;

    instances.forEach((instance) => {
      void pollInstance(selectedService.service_name, instance.instanceId, instance.path, configToken.trim());
      timers.current[instance.instanceId] = window.setInterval(() => {
        void pollInstance(selectedService.service_name, instance.instanceId, instance.path, configToken.trim());
      }, 4000);
    });
  }, [instances.length, selectedService?.service_name, configToken]);

  return (
    <AppLayout>
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={2} sx={{ mb: 3 }}>
        <Box>
          <Typography variant="h3" sx={{ mb: 1 }}>
            Runtime Demo
          </Typography>
          <Typography sx={{ color: '#64748b' }}>
            Simulate service instances polling delivery every few seconds so config rollouts are visible during the demo.
          </Typography>
        </Box>
        <Button startIcon={<Refresh />} variant="outlined" onClick={() => loadServices()}>
          Refresh services
        </Button>
      </Stack>

      {error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      ) : null}

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card sx={{ p: 3 }}>
            <Stack spacing={2}>
              <TextField
                select
                label="Service"
                value={selectedServiceId}
                onChange={(event) => {
                  setSelectedServiceId(event.target.value);
                  setDraft((current) => ({ ...current, path: '' }));
                }}
              >
                {services.map((service) => (
                  <MenuItem key={service.service_id} value={service.service_id}>
                    {service.service_name}
                  </MenuItem>
                ))}
              </TextField>
              <TextField
                label="Delivery token"
                value={configToken}
                onChange={(event) => setConfigToken(event.target.value)}
                helperText="Paste a token created from the Services page. Instances use this token to poll delivery."
              />
              <TextField
                label="Instance alias"
                value={draft.instanceName}
                onChange={(event) => setDraft((current) => ({ ...current, instanceName: event.target.value }))}
                helperText="Example: payments-pod-1"
              />
              <TextField
                select
                label="Path"
                value={draft.path}
                onChange={(event) => setDraft((current) => ({ ...current, path: event.target.value }))}
              >
                {nodes.map((node) => (
                  <MenuItem key={node.config_node_id} value={node.path}>
                    {node.path}
                  </MenuItem>
                ))}
              </TextField>
              <Button
                startIcon={<Add />}
                variant="contained"
                disabled={!selectedService || !configToken.trim() || !draft.instanceName.trim() || !draft.path}
                onClick={() => {
                  const instanceId = crypto.randomUUID();
                  setInstances((current) => [
                    ...current,
                    {
                      instanceId,
                      instanceName: draft.instanceName.trim(),
                      path: draft.path,
                      status: 'idle',
                      versionId: null,
                      treeVersion: null,
                      config: {},
                      lastPollAt: null,
                      lastUpdatedAt: null,
                      errorMessage: null,
                    },
                  ]);
                  setDraft((current) => ({ ...current, instanceName: '' }));
                }}
              >
                Add polling instance
              </Button>
            </Stack>
          </Card>
        </Grid>

        <Grid item xs={12} md={8}>
          <Stack spacing={2}>
            {instances.map((instance) => (
              <Card key={instance.instanceId} sx={{ p: 3 }}>
                <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={2} sx={{ mb: 2 }}>
                  <Box>
                    <Typography variant="h6">{instance.instanceName}</Typography>
                    <Typography sx={{ color: '#64748b', mt: 0.5 }}>
                      Path {instance.path} • Version {instance.versionId ? instance.versionId.slice(0, 8) : 'pending'} • Tree {instance.treeVersion ?? '-'}
                    </Typography>
                  </Box>
                  <Stack direction="row" spacing={1} alignItems="center">
                    <Sensors sx={{ color: instance.status === 'healthy' ? '#16a34a' : instance.status === 'error' ? '#dc2626' : '#64748b' }} />
                    <Typography sx={{ fontWeight: 700, textTransform: 'capitalize' }}>{instance.status}</Typography>
                  </Stack>
                </Stack>
                <Typography variant="body2" sx={{ color: '#64748b', mb: 0.75 }}>
                  Last poll: {instance.lastPollAt ? new Date(instance.lastPollAt).toLocaleTimeString() : 'Not yet'} • Last update: {instance.lastUpdatedAt ? new Date(instance.lastUpdatedAt).toLocaleTimeString() : 'Not yet'}
                </Typography>
                {instance.errorMessage ? (
                  <Alert severity="error" sx={{ mb: 2 }}>
                    {instance.errorMessage}
                  </Alert>
                ) : null}
                <Box component="pre" sx={{ m: 0, p: 2.5, borderRadius: 4, bgcolor: '#0f172a', color: '#e2e8f0', overflow: 'auto', minHeight: 180 }}>
                  {JSON.stringify(instance.config, null, 2)}
                </Box>
              </Card>
            ))}
            {!instances.length ? (
              <Card sx={{ p: 3 }}>
                <Typography sx={{ color: '#94a3b8' }}>
                  Add one or more simulated instances to watch runtime config polling in action.
                </Typography>
              </Card>
            ) : null}
          </Stack>
        </Grid>
      </Grid>
    </AppLayout>
  );
};

export default RuntimeDemoPage;
