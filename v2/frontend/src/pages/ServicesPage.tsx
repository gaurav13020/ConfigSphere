import { Add, ContentCopy, DataObject, Key, Save } from '@mui/icons-material';
import {
  Alert,
  Box,
  Button,
  Card,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  Grid,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useEffect, useMemo, useState } from 'react';

import { AppLayout } from '@/components/AppLayout';
import { ServiceTree } from '@/components/ServiceTree';
import { v2Api } from '@/services/api';
import { ConfigNode, CreatedServiceApiKey, DeliveryConfig, Service, ServiceApiKey } from '@/types';

const parseConfigText = (value: string): Record<string, string> => {
  if (!value.trim()) return {};
  return JSON.parse(value) as Record<string, string>;
};

const ServicesPage = () => {
  const [services, setServices] = useState<Service[]>([]);
  const [selectedServiceId, setSelectedServiceId] = useState<string>('');
  const [nodes, setNodes] = useState<ConfigNode[]>([]);
  const [selectedNode, setSelectedNode] = useState<ConfigNode | null>(null);
  const [selectedConfig, setSelectedConfig] = useState<DeliveryConfig | null>(null);
  const [serviceApiKeys, setServiceApiKeys] = useState<ServiceApiKey[]>([]);
  const [serviceOpen, setServiceOpen] = useState(false);
  const [rootOpen, setRootOpen] = useState(false);
  const [childOpen, setChildOpen] = useState(false);
  const [apiKeyOpen, setApiKeyOpen] = useState(false);
  const [createdApiKey, setCreatedApiKey] = useState<CreatedServiceApiKey | null>(null);
  const [serviceError, setServiceError] = useState<string | null>(null);
  const [serviceDraft, setServiceDraft] = useState({ service_name: '', service_type: 'MICROSERVICE', owner_team: '' });
  const [rootDraft, setRootDraft] = useState({ path: '/global', base_config: '{\n  "timeout_ms": "1000"\n}' });
  const [childSegment, setChildSegment] = useState('');
  const [apiKeyDraft, setApiKeyDraft] = useState({ key_name: '' });

  const selectedService = useMemo(
    () => services.find((service) => service.service_id === selectedServiceId) || null,
    [services, selectedServiceId]
  );

  const loadServices = async () => {
    const data = await v2Api.listServices();
    setServices(data);
    if (!selectedServiceId && data[0]) setSelectedServiceId(data[0].service_id);
  };

  const loadNodes = async (service: Service | null) => {
    if (!service) return;
    const data = await v2Api.listNodes(service.service_id);
    setNodes(data);
  };

  const loadApiKeys = async (service: Service | null) => {
    if (!service) return;
    try {
      const keys = await v2Api.listServiceApiKeys(service.service_id);
      setServiceApiKeys(keys);
      setServiceError(null);
    } catch (_err) {
      setServiceApiKeys([]);
      setServiceError('You need service admin or global admin access to view delivery API keys.');
    }
  };

  useEffect(() => {
    loadServices();
  }, []);

  useEffect(() => {
    if (selectedService) {
      loadNodes(selectedService);
      loadApiKeys(selectedService);
    }
  }, [selectedServiceId, services.length]);

  useEffect(() => {
    if (selectedNode && selectedService) {
      v2Api.getConfig(selectedService.service_name, selectedNode.path).then(setSelectedConfig).catch(() => setSelectedConfig(null));
    }
  }, [selectedNode, selectedService]);

  return (
    <AppLayout>
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" alignItems={{ xs: 'flex-start', md: 'center' }} spacing={2} sx={{ mb: 3 }}>
        <Box>
          <Typography variant="h3" sx={{ mb: 1 }}>
            Services & Hierarchy
          </Typography>
          <Typography sx={{ color: '#64748b' }}>
            Create services, define the hierarchy, and inspect the exact precomputed payload any client would receive.
          </Typography>
        </Box>
        <Stack direction="row" spacing={1.5} flexWrap="wrap">
          <Button startIcon={<Add />} variant="contained" onClick={() => setServiceOpen(true)}>
            New service
          </Button>
          <Button startIcon={<DataObject />} variant="outlined" onClick={() => setRootOpen(true)} disabled={!selectedService}>
            Add root config
          </Button>
          <Button startIcon={<ContentCopy />} variant="outlined" onClick={() => setChildOpen(true)} disabled={!selectedNode}>
            Create subconfig
          </Button>
          <Button startIcon={<Key />} variant="outlined" onClick={() => setApiKeyOpen(true)} disabled={!selectedService}>
            Delivery token
          </Button>
        </Stack>
      </Stack>

      <Grid container spacing={3}>
        <Grid item xs={12} md={3.5}>
          <Card sx={{ p: 2.5 }}>
            <TextField
              select
              fullWidth
              label="Service"
              value={selectedServiceId}
              onChange={(event) => {
                setSelectedServiceId(event.target.value);
                setSelectedNode(null);
                setSelectedConfig(null);
              }}
              sx={{ mb: 2 }}
            >
              {services.map((service) => (
                <MenuItem key={service.service_id} value={service.service_id}>
                  {service.service_name}
                </MenuItem>
              ))}
            </TextField>
            {selectedService ? (
              <>
                <Stack direction="row" justifyContent="space-between" sx={{ mb: 2 }}>
                  <Typography variant="body2" sx={{ color: '#64748b' }}>
                    Nodes
                  </Typography>
                  <Typography sx={{ fontWeight: 700 }}>{selectedService.node_count}</Typography>
                </Stack>
                <ServiceTree nodes={nodes} selectedId={selectedNode?.config_node_id || null} onSelect={setSelectedNode} />
              </>
            ) : (
              <Typography sx={{ color: '#94a3b8' }}>Create a service to start building the hierarchy.</Typography>
            )}
          </Card>
        </Grid>
        <Grid item xs={12} md={8.5}>
          <Stack spacing={3}>
            <Card sx={{ p: 3 }}>
              {selectedNode ? (
                <>
                  <Typography variant="h5">{selectedNode.path}</Typography>
                  <Typography sx={{ color: '#64748b', mt: 1 }}>
                    Active node id: {selectedNode.config_node_id}
                  </Typography>
                  <Divider sx={{ my: 3 }} />
                  <Typography variant="h6" sx={{ mb: 2 }}>
                    Materialized config
                  </Typography>
                  <Box
                    component="pre"
                    sx={{
                      m: 0,
                      p: 2.5,
                      borderRadius: 4,
                      overflow: 'auto',
                      bgcolor: '#0f172a',
                      color: '#e2e8f0',
                      fontSize: 13,
                    }}
                  >
                    {JSON.stringify(selectedConfig?.materializedConfig || {}, null, 2)}
                  </Box>
                </>
              ) : (
                <Typography sx={{ color: '#94a3b8' }}>
                  Select a node from the hierarchy to inspect its exact precomputed config.
                </Typography>
              )}
            </Card>

            <Card sx={{ p: 3 }}>
              <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={2} sx={{ mb: 2 }}>
                <Box>
                  <Typography variant="h6">Delivery API Keys</Typography>
                  <Typography sx={{ color: '#64748b', mt: 0.5 }}>
                    Machine tokens used by SDKs and demo pollers to access delivery for this service.
                  </Typography>
                </Box>
                <Button startIcon={<Key />} variant="contained" onClick={() => setApiKeyOpen(true)} disabled={!selectedService}>
                  Create token
                </Button>
              </Stack>

              {serviceError ? (
                <Alert severity="warning" sx={{ mb: 2 }}>
                  {serviceError}
                </Alert>
              ) : null}

              {createdApiKey ? (
                <Alert severity="success" sx={{ mb: 2 }}>
                  Token created for <strong>{createdApiKey.key_name}</strong>. Copy it now; this is the only time the full token is shown.
                  <Box component="pre" sx={{ mt: 1.5, mb: 1, p: 1.5, borderRadius: 2, bgcolor: 'rgba(15,23,42,0.92)', color: '#e2e8f0', overflow: 'auto' }}>
                    {createdApiKey.plain_token}
                  </Box>
                </Alert>
              ) : null}

              <Stack spacing={1.5}>
                {serviceApiKeys.map((apiKey) => (
                  <Card key={apiKey.api_key_id} variant="outlined" sx={{ p: 2 }}>
                    <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={2}>
                      <Box>
                        <Typography sx={{ fontWeight: 700 }}>{apiKey.key_name}</Typography>
                        <Typography variant="body2" sx={{ color: '#64748b', mt: 0.5 }}>
                          Prefix: {apiKey.token_prefix} • Created {new Date(apiKey.created_at).toLocaleString()}
                        </Typography>
                        <Typography variant="body2" sx={{ color: '#64748b', mt: 0.5 }}>
                          Status: {apiKey.revoked_at ? 'Revoked' : 'Active'}
                        </Typography>
                      </Box>
                      <Stack direction="row" spacing={1}>
                        <Button
                          color="error"
                          variant="outlined"
                          disabled={!!apiKey.revoked_at || !selectedService}
                          onClick={async () => {
                            if (!selectedService) return;
                            await v2Api.revokeServiceApiKey(selectedService.service_id, apiKey.api_key_id);
                            await loadApiKeys(selectedService);
                          }}
                        >
                          Revoke
                        </Button>
                      </Stack>
                    </Stack>
                  </Card>
                ))}
                {!serviceApiKeys.length && !serviceError ? (
                  <Typography sx={{ color: '#94a3b8' }}>No delivery tokens created yet for this service.</Typography>
                ) : null}
              </Stack>
            </Card>
          </Stack>
        </Grid>
      </Grid>

      <Dialog open={serviceOpen} onClose={() => setServiceOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Create service</DialogTitle>
        <DialogContent sx={{ pt: 1 }}>
          <Stack spacing={2}>
            <TextField label="Service name" value={serviceDraft.service_name} onChange={(e) => setServiceDraft({ ...serviceDraft, service_name: e.target.value })} />
            <TextField select label="Service type" value={serviceDraft.service_type} onChange={(e) => setServiceDraft({ ...serviceDraft, service_type: e.target.value })}>
              <MenuItem value="MICROSERVICE">Microservice</MenuItem>
              <MenuItem value="MONOLITH">Monolith</MenuItem>
              <MenuItem value="OTHER">Other</MenuItem>
            </TextField>
            <TextField label="Owner team" value={serviceDraft.owner_team} onChange={(e) => setServiceDraft({ ...serviceDraft, owner_team: e.target.value })} />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setServiceOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            startIcon={<Save />}
            onClick={async () => {
              await v2Api.createService(serviceDraft);
              setServiceOpen(false);
              setServiceDraft({ service_name: '', service_type: 'MICROSERVICE', owner_team: '' });
              await loadServices();
            }}
          >
            Save
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={rootOpen} onClose={() => setRootOpen(false)} fullWidth maxWidth="md">
        <DialogTitle>Create root config</DialogTitle>
        <DialogContent sx={{ pt: 1 }}>
          <Stack spacing={2}>
            <TextField label="Path" value={rootDraft.path} onChange={(e) => setRootDraft({ ...rootDraft, path: e.target.value })} />
            <TextField
              label="Base config JSON"
              multiline
              minRows={10}
              value={rootDraft.base_config}
              onChange={(e) => setRootDraft({ ...rootDraft, base_config: e.target.value })}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRootOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={async () => {
              if (!selectedService) return;
              await v2Api.createRootNode(selectedService.service_id, {
                path: rootDraft.path,
                base_config: parseConfigText(rootDraft.base_config),
              });
              setRootOpen(false);
              await loadNodes(selectedService);
            }}
          >
            Save root
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={childOpen} onClose={() => setChildOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Create subconfig</DialogTitle>
        <DialogContent sx={{ pt: 1 }}>
          <TextField label="New path segment" fullWidth value={childSegment} onChange={(e) => setChildSegment(e.target.value)} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setChildOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={async () => {
              if (!selectedService || !selectedNode) return;
              await v2Api.createChildNode(selectedService.service_id, selectedNode.config_node_id, { segment: childSegment });
              setChildOpen(false);
              setChildSegment('');
              await loadNodes(selectedService);
            }}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={apiKeyOpen} onClose={() => setApiKeyOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Create delivery token</DialogTitle>
        <DialogContent sx={{ pt: 1 }}>
          <Stack spacing={2}>
            <TextField
              label="Token name"
              value={apiKeyDraft.key_name}
              onChange={(e) => setApiKeyDraft({ key_name: e.target.value })}
              helperText="Example: payments-prod-sdk or demo-instance-poller"
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setApiKeyOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={async () => {
              if (!selectedService || !apiKeyDraft.key_name.trim()) return;
              const created = await v2Api.createServiceApiKey(selectedService.service_id, { key_name: apiKeyDraft.key_name });
              setCreatedApiKey(created);
              setApiKeyOpen(false);
              setApiKeyDraft({ key_name: '' });
              await loadApiKeys(selectedService);
            }}
          >
            Create token
          </Button>
        </DialogActions>
      </Dialog>
    </AppLayout>
  );
};

export default ServicesPage;
