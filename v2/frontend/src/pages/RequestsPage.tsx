import {
  Add,
  CancelOutlined,
  Comment,
  CompareArrows,
  EditNote,
  FactCheck,
  Publish,
  Visibility,
} from '@mui/icons-material';
import {
  Alert,
  Box,
  Button,
  Card,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  Grid,
  MenuItem,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material';
import axios from 'axios';
import { useEffect, useMemo, useState } from 'react';

import { AppLayout } from '@/components/AppLayout';
import { StatusChip } from '@/components/StatusChip';
import { useAuthStore } from '@/stores/auth';
import { v2Api } from '@/services/api';
import { ChangeRequest, ConfigNode, DeliveryConfig, RequestActivity, Revision, RoleBinding, Service, UserSummary } from '@/types';

type InspectorView = 'diff' | 'original';
type DiffKind = 'ADDED' | 'REMOVED' | 'CHANGED' | 'INHERITED';
type DiffRow = {
  kind: DiffKind;
  key: string;
  before: string;
  after: string;
};

const parseConfigText = (value: string): Record<string, string> => {
  if (!value.trim()) return {};
  return JSON.parse(value) as Record<string, string>;
};

const formatConfig = (config: Record<string, unknown>) => JSON.stringify(config, null, 2);

const stringifyValue = (value: unknown) => {
  if (value === null || value === undefined) return '—';
  if (typeof value === 'string') return value;
  return JSON.stringify(value, null, 2);
};

const buildDiffRows = (diffSummary: Record<string, any> | null | undefined): DiffRow[] => {
  if (!diffSummary) return [];

  const addedEntries = Object.entries(diffSummary.added || {}).map(([key, value]) => ({
    kind: 'ADDED' as const,
    key,
    before: '—',
    after: stringifyValue(value),
  }));

  const removedEntries = Object.entries(diffSummary.removed || {}).map(([key, value]) => ({
    kind: 'REMOVED' as const,
    key,
    before: stringifyValue(value),
    after: '—',
  }));

  const changedEntries = Object.entries(diffSummary.changed || {}).map(([key, value]) => ({
    kind: 'CHANGED' as const,
    key,
    before: stringifyValue((value as { before?: unknown }).before ?? '—'),
    after: stringifyValue((value as { after?: unknown }).after ?? '—'),
  }));

  const inheritedEntries = Object.entries(diffSummary.inherited || {}).map(([key, value]) => ({
    kind: 'INHERITED' as const,
    key,
    before: stringifyValue((value as { before?: unknown }).before ?? '—'),
    after: 'will inherit from the closest parent that defines this key',
  }));

  return [...changedEntries, ...inheritedEntries, ...addedEntries, ...removedEntries].sort((left, right) => left.key.localeCompare(right.key));
};

const diffChipColor = (kind: DiffKind): 'success' | 'error' | 'warning' | 'info' => {
  if (kind === 'ADDED') return 'success';
  if (kind === 'REMOVED') return 'error';
  if (kind === 'INHERITED') return 'info';
  return 'warning';
};

const deriveOverridesFromEffectiveConfig = (
  effectiveConfig: Record<string, string>,
  parentEffectiveConfig: Record<string, string>
) => {
  const overrides: Record<string, string> = {};
  Object.entries(effectiveConfig).forEach(([key, value]) => {
    if (parentEffectiveConfig[key] !== value) {
      overrides[key] = value;
    }
  });
  return overrides;
};

const buildRevisionDraft = (
  revision: Revision | undefined,
  originalConfig: DeliveryConfig | null,
  parentConfig: DeliveryConfig | null,
  isRootNode: boolean
) => {
  const explicitOverrides = revision?.proposed_overrides || {};
  const hasExplicitOverrides = Object.keys(explicitOverrides).length > 0;
  const parentEffectiveConfig = isRootNode ? {} : parentConfig?.materializedConfig || {};
  const fallbackOverrides = originalConfig
    ? deriveOverridesFromEffectiveConfig(originalConfig.materializedConfig, parentEffectiveConfig)
    : {};

  return {
    proposed_overrides: formatConfig(hasExplicitOverrides ? explicitOverrides : fallbackOverrides),
    change_note: revision?.change_note || '',
  };
};

const userAlias = (email: string | null | undefined) => {
  if (!email) return 'unknown';
  return email.split('@')[0] || email;
};

const userAliasById = (userId: string | null | undefined, users: UserSummary[]) => {
  if (!userId) return 'unknown';
  const user = users.find((entry) => entry.user_id === userId);
  return user ? userAlias(user.email) : userId;
};

const reviewerLabel = (reviewerId: string | null, users: UserSummary[]) =>
  reviewerId ? userAliasById(reviewerId, users) : 'Any eligible reviewer';

const RequestsPage = () => {
  const authUser = useAuthStore((state) => state.user);
  const [services, setServices] = useState<Service[]>([]);
  const [serviceMap, setServiceMap] = useState<Record<string, Service>>({});
  const [nodesByService, setNodesByService] = useState<Record<string, ConfigNode[]>>({});
  const [users, setUsers] = useState<UserSummary[]>([]);
  const [myBindings, setMyBindings] = useState<RoleBinding[]>([]);
  const [selectedServiceId, setSelectedServiceId] = useState('');
  const [requests, setRequests] = useState<ChangeRequest[]>([]);
  const [activeRequest, setActiveRequest] = useState<RequestActivity | null>(null);
  const [activeNode, setActiveNode] = useState<ConfigNode | null>(null);
  const [originalConfig, setOriginalConfig] = useState<DeliveryConfig | null>(null);
  const [parentConfig, setParentConfig] = useState<DeliveryConfig | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [commentDraft, setCommentDraft] = useState('');
  const [actionNote, setActionNote] = useState('');
  const [inspectorView, setInspectorView] = useState<InspectorView>('diff');
  const [error, setError] = useState<string | null>(null);
  const [revisionDraft, setRevisionDraft] = useState({
    proposed_overrides: '{\n  "timeout_ms": "1500"\n}',
    change_note: '',
  });
  const [requestDraft, setRequestDraft] = useState({
    target_config_node_id: '',
    assigned_reviewer_id: '',
    proposed_overrides: '{\n  "timeout_ms": "1500"\n}',
    change_note: '',
  });

  const selectedService = useMemo(
    () => services.find((service) => service.service_id === selectedServiceId) || null,
    [services, selectedServiceId]
  );

  const currentUser = useMemo(
    () => users.find((user) => user.email === authUser?.email) || null,
    [users, authUser?.email]
  );

  const canRole = (serviceId: string, acceptedRoles: string[]) => {
    return myBindings.some((binding) => {
      if (!acceptedRoles.includes(binding.role_name)) return false;
      if (binding.scope_type === 'GLOBAL') return true;
      return binding.scope_type === 'SERVICE' && binding.scope_id === serviceId;
    });
  };

  const requestPermissions = useMemo(() => {
    if (!activeRequest) {
      return {
        canSubmit: false,
        canApprove: false,
        canRequestChanges: false,
        canReject: false,
        canImplement: false,
        canCancel: false,
      };
    }
    const request = activeRequest.request;
    const isAuthor = !!currentUser && currentUser.user_id === request.created_by;
    const isAssignedReviewer = !request.assigned_reviewer_id || request.assigned_reviewer_id === currentUser?.user_id;
    const isAuthorRole = canRole(request.service_id, ['CONFIG_AUTHOR', 'CONFIG_ADMIN']);
    const isReviewerRole = canRole(request.service_id, ['CONFIG_REVIEWER', 'CONFIG_ADMIN']) && isAssignedReviewer;
    const isImplementerRole = canRole(request.service_id, ['CONFIG_IMPLEMENTER', 'CONFIG_ADMIN']);
    const canSubmit = isAuthorRole && ['DRAFT', 'CHANGES_REQUESTED'].includes(request.status) && !!request.current_revision_id;
    const canReview = isReviewerRole && !!request.current_revision_id && ['SUBMITTED', 'IN_REVIEW', 'CHANGES_REQUESTED', 'DRAFT'].includes(request.status);
    return {
      canSubmit,
      canApprove: canReview,
      canRequestChanges: canReview,
      canReject: canReview,
      canImplement: isImplementerRole && request.status === 'APPROVED',
      canCancel: (isAuthor || canRole(request.service_id, ['CONFIG_ADMIN'])) && !['IMPLEMENTING', 'IMPLEMENTED', 'REJECTED'].includes(request.status),
    };
  }, [activeRequest, currentUser, myBindings]);

  const loadRequestsPage = async () => {
    setError(null);
    try {
      const [servicesData, requestsData, usersData, bindingsData] = await Promise.all([
        v2Api.listServices(),
        v2Api.listChangeRequests(),
        v2Api.listAllUsers(),
        v2Api.listMyBindings(),
      ]);
      setServices(servicesData);
      setServiceMap(Object.fromEntries(servicesData.map((service) => [service.service_id, service])));
      setRequests(requestsData);
      setUsers(usersData);
      setMyBindings(bindingsData);
      if (!selectedServiceId && servicesData[0]) {
        setSelectedServiceId(servicesData[0].service_id);
      }
    } catch (_err) {
      setError('Unable to load change requests right now.');
    }
  };

  const ensureNodes = async (serviceId: string) => {
    if (nodesByService[serviceId]) return nodesByService[serviceId];
    const nodes = await v2Api.listNodes(serviceId);
    setNodesByService((current) => ({ ...current, [serviceId]: nodes }));
    return nodes;
  };

  useEffect(() => {
    loadRequestsPage();
  }, []);

  useEffect(() => {
    if (selectedServiceId && !nodesByService[selectedServiceId]) {
      ensureNodes(selectedServiceId);
    }
  }, [selectedServiceId]);

  const openRequest = async (request: ChangeRequest) => {
    setError(null);
    try {
      const [activity, nodes] = await Promise.all([
        v2Api.getRequestActivity(request.request_id),
        ensureNodes(request.service_id),
      ]);
      const node = nodes.find((item) => item.config_node_id === request.target_config_node_id) || null;
      setActiveRequest(activity);
      setActiveNode(node);
      setInspectorView('diff');
      if (node) {
        const service = serviceMap[request.service_id] || services.find((item) => item.service_id === request.service_id);
        if (service) {
          const parentNode = node.parent_config_node_id
            ? nodes.find((item) => item.config_node_id === node.parent_config_node_id) || null
            : null;
          const [config, parent] = await Promise.all([
            v2Api.getConfig(service.service_name, node.path),
            parentNode ? v2Api.getConfig(service.service_name, parentNode.path) : Promise.resolve(null),
          ]);
          setOriginalConfig(config);
          setParentConfig(parent);
          setRevisionDraft(buildRevisionDraft(activity.revisions[0], config, parent, !node.parent_config_node_id));
        } else {
          setOriginalConfig(null);
          setParentConfig(null);
          setRevisionDraft(buildRevisionDraft(activity.revisions[0], null, null, !node.parent_config_node_id));
        }
      } else {
        setOriginalConfig(null);
        setParentConfig(null);
        setRevisionDraft(buildRevisionDraft(activity.revisions[0], null, null, false));
      }
    } catch (_err) {
      setError('Unable to load the selected request.');
    }
  };

  const refreshActiveRequest = async () => {
    if (!activeRequest) return;
    await loadRequestsPage();
    const latest = await v2Api.listChangeRequests();
    const request = latest.find((item) => item.request_id === activeRequest.request.request_id);
    if (request) {
      await openRequest(request);
    }
  };

  const currentServiceNodes = selectedServiceId ? nodesByService[selectedServiceId] || [] : [];
  const diffRows = useMemo(
    () => buildDiffRows(activeRequest?.request.latest_diff_summary as Record<string, any> | undefined),
    [activeRequest?.request.latest_diff_summary]
  );
  const latestRevision = activeRequest?.revisions[0];
  const revisionOverrides = useMemo(() => {
    try {
      return parseConfigText(revisionDraft.proposed_overrides);
    } catch {
      return null;
    }
  }, [revisionDraft.proposed_overrides]);
  const effectiveConfigPreview = useMemo(() => {
    if (!activeNode) return null;
    if (!revisionOverrides) return null;
    const baseConfig = activeNode.parent_config_node_id ? parentConfig?.materializedConfig || {} : {};
    return { ...baseConfig, ...revisionOverrides };
  }, [activeNode, parentConfig, revisionOverrides]);
  const canEditRevision =
    !!activeRequest &&
    canRole(activeRequest.request.service_id, ['CONFIG_AUTHOR', 'CONFIG_ADMIN']) &&
    !['IMPLEMENTING', 'IMPLEMENTED', 'REJECTED'].includes(activeRequest.request.status);

  return (
    <AppLayout>
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" alignItems={{ xs: 'flex-start', md: 'center' }} sx={{ mb: 3 }} spacing={2}>
        <Box>
          <Typography variant="h3" sx={{ mb: 1 }}>
            Change Requests
          </Typography>
          <Typography sx={{ color: '#64748b' }}>
            Create, review, approve, implement, and cancel governed config changes from a single request workspace.
          </Typography>
        </Box>
        <Button startIcon={<Add />} variant="contained" onClick={() => setCreateOpen(true)}>
          New request
        </Button>
      </Stack>

      {error ? (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      ) : null}

      <Grid container spacing={3}>
        <Grid item xs={12} md={4.5}>
          <Card sx={{ p: 2.5 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Requests
            </Typography>
            <Stack spacing={1.25}>
              {requests.map((request) => {
                const service = serviceMap[request.service_id];
                const node = (nodesByService[request.service_id] || []).find((item) => item.config_node_id === request.target_config_node_id);
                const title = `${service?.service_name || 'service'} : ${node?.path || request.target_config_node_id.slice(0, 8)}`;
                return (
                  <Card
                    key={request.request_id}
                    variant="outlined"
                    sx={{ p: 2, cursor: 'pointer', borderColor: activeRequest?.request.request_id === request.request_id ? 'rgba(91,77,245,0.35)' : 'rgba(148,163,184,0.18)' }}
                    onClick={() => openRequest(request)}
                  >
                    <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
                      <Typography sx={{ fontWeight: 700 }}>{title}</Typography>
                      <StatusChip value={request.status} />
                    </Stack>
                    <Typography variant="body2" sx={{ color: '#64748b' }}>
                      by: {userAliasById(request.created_by, users)} • Reviewer: {reviewerLabel(request.assigned_reviewer_id, users)} • revision {request.latest_revision_number || '-'}
                    </Typography>
                  </Card>
                );
              })}
            </Stack>
          </Card>
        </Grid>
        <Grid item xs={12} md={7.5}>
          <Card sx={{ p: 3 }}>
            {activeRequest ? (
              <>
                <Stack direction={{ xs: 'column', lg: 'row' }} justifyContent="space-between" spacing={2} sx={{ mb: 2 }}>
                  <Box>
                    <Typography variant="h5">
                      {(serviceMap[activeRequest.request.service_id]?.service_name || 'service') + ' : ' + (activeNode?.path || activeRequest.request.target_config_node_id)}
                    </Typography>
                    <Typography sx={{ color: '#64748b', mt: 0.5 }}>
                      Reviewer: {reviewerLabel(activeRequest.request.assigned_reviewer_id, users)} • Current revision {activeRequest.request.latest_revision_number || '-'}
                    </Typography>
                  </Box>
                  <StatusChip value={activeRequest.request.status} />
                </Stack>

                <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={2} sx={{ mb: 2 }}>
                  <ToggleButtonGroup
                    exclusive
                    value={inspectorView}
                    onChange={(_, value) => value && setInspectorView(value)}
                    size="small"
                  >
                    <ToggleButton value="diff">
                      <CompareArrows sx={{ mr: 1 }} /> See diff
                    </ToggleButton>
                    <ToggleButton value="original">
                      <Visibility sx={{ mr: 1 }} /> Original config
                    </ToggleButton>
                  </ToggleButtonGroup>
                  <Stack direction="row" spacing={1} flexWrap="wrap">
                    <Button startIcon={<Publish />} variant="contained" disabled={!requestPermissions.canSubmit} onClick={async () => {
                      await v2Api.submitRequest(activeRequest.request.request_id);
                      await refreshActiveRequest();
                    }}>
                      Submit
                    </Button>
                    <Button startIcon={<FactCheck />} variant="outlined" disabled={!requestPermissions.canApprove} onClick={async () => {
                      if (!activeRequest.request.current_revision_id) return;
                      await v2Api.reviewRequest(activeRequest.request.request_id, {
                        revision_id: activeRequest.request.current_revision_id,
                        decision: 'APPROVE',
                        note: actionNote || 'Approved in request workspace.',
                      });
                      setActionNote('');
                      await refreshActiveRequest();
                    }}>
                      Approve
                    </Button>
                    <Button startIcon={<EditNote />} variant="outlined" disabled={!requestPermissions.canRequestChanges} onClick={async () => {
                      if (!activeRequest.request.current_revision_id) return;
                      await v2Api.reviewRequest(activeRequest.request.request_id, {
                        revision_id: activeRequest.request.current_revision_id,
                        decision: 'REQUEST_CHANGES',
                        note: actionNote || 'Please revise this request.',
                      });
                      setActionNote('');
                      await refreshActiveRequest();
                    }}>
                      Request change
                    </Button>
                    <Button variant="outlined" disabled={!requestPermissions.canImplement} onClick={async () => {
                      await v2Api.implementRequest(activeRequest.request.request_id);
                      await refreshActiveRequest();
                    }}>
                      Implement
                    </Button>
                    <Button color="error" startIcon={<CancelOutlined />} variant="text" disabled={!requestPermissions.canCancel} onClick={async () => {
                      await v2Api.cancelRequest(activeRequest.request.request_id, actionNote || 'Canceled from request workspace.');
                      setActionNote('');
                      await refreshActiveRequest();
                    }}>
                      Cancel request
                    </Button>
                  </Stack>
                </Stack>

                <TextField
                  fullWidth
                  label="Action note"
                  placeholder="Optional note for approve, request changes, or cancel"
                  value={actionNote}
                  onChange={(event) => setActionNote(event.target.value)}
                  sx={{ mb: 2.5 }}
                />

                <Typography variant="h6" sx={{ mb: 1.5 }}>
                  {inspectorView === 'diff' ? 'Override diff' : 'Current effective config'}
                </Typography>
                {inspectorView === 'diff' ? (
                  <Box
                    sx={{
                      borderRadius: 4,
                      border: '1px solid rgba(148,163,184,0.18)',
                      overflow: 'hidden',
                      minHeight: 260,
                      bgcolor: '#fff',
                    }}
                  >
                    {diffRows.length ? (
                      <Table size="small">
                        <TableHead>
                          <TableRow sx={{ bgcolor: '#f8fafc' }}>
                            <TableCell sx={{ fontWeight: 700, width: 120 }}>Type</TableCell>
                            <TableCell sx={{ fontWeight: 700, width: 220 }}>Key</TableCell>
                            <TableCell sx={{ fontWeight: 700 }}>Before</TableCell>
                            <TableCell sx={{ fontWeight: 700 }}>After</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {diffRows.map((row) => (
                            <TableRow
                              key={`${row.kind}-${row.key}`}
                              sx={{
                                bgcolor:
                                  row.kind === 'ADDED'
                                    ? 'rgba(34,197,94,0.08)'
                                    : row.kind === 'REMOVED'
                                      ? 'rgba(239,68,68,0.08)'
                                      : row.kind === 'INHERITED'
                                        ? 'rgba(14,165,233,0.08)'
                                      : 'rgba(245,158,11,0.08)',
                                '& td': {
                                  verticalAlign: 'top',
                                  borderColor: 'rgba(148,163,184,0.16)',
                                },
                              }}
                            >
                              <TableCell>
                                <Chip label={row.kind.toLowerCase()} color={diffChipColor(row.kind)} size="small" />
                              </TableCell>
                              <TableCell sx={{ fontFamily: '"IBM Plex Mono", monospace', fontWeight: 600 }}>
                                {row.key}
                              </TableCell>
                              <TableCell>
                                <Box
                                  component="pre"
                                  sx={{
                                    m: 0,
                                    whiteSpace: 'pre-wrap',
                                    wordBreak: 'break-word',
                                    fontFamily: '"IBM Plex Mono", monospace',
                                    fontSize: '0.85rem',
                                    color: '#0f172a',
                                  }}
                                >
                                  {row.before}
                                </Box>
                              </TableCell>
                              <TableCell>
                                <Box
                                  component="pre"
                                  sx={{
                                    m: 0,
                                    whiteSpace: 'pre-wrap',
                                    wordBreak: 'break-word',
                                    fontFamily: '"IBM Plex Mono", monospace',
                                    fontSize: '0.85rem',
                                    color: '#0f172a',
                                  }}
                                >
                                  {row.after}
                                </Box>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    ) : (
                      <Box sx={{ minHeight: 260, display: 'grid', placeItems: 'center', color: '#64748b', px: 3 }}>
                        No config changes are present in the latest revision yet.
                      </Box>
                    )}
                  </Box>
                ) : (
                  <Box component="pre" sx={{ m: 0, p: 2.5, borderRadius: 4, bgcolor: '#0f172a', color: '#e2e8f0', overflow: 'auto', minHeight: 260 }}>
                    {formatConfig(originalConfig?.materializedConfig || {})}
                  </Box>
                )}

                <Divider sx={{ my: 3 }} />
                <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={2} sx={{ mb: 1.5 }}>
                  <Box>
                    <Typography variant="h6">Revision editor</Typography>
                    <Typography variant="body2" sx={{ color: '#64748b', mt: 0.5 }}>
                      Edit only this node&apos;s local overrides. Any key missing here is inherited automatically from the parent.
                    </Typography>
                  </Box>
                  {latestRevision ? (
                    <Typography variant="body2" sx={{ color: '#64748b' }}>
                      Editing from revision {latestRevision.revision_number}
                    </Typography>
                  ) : null}
                </Stack>
                <Stack spacing={2}>
                  <Grid container spacing={2}>
                    <Grid item xs={12} lg={6}>
                      <TextField
                        label="Local overrides JSON"
                        multiline
                        minRows={12}
                        fullWidth
                        value={revisionDraft.proposed_overrides}
                        onChange={(event) => setRevisionDraft((current) => ({ ...current, proposed_overrides: event.target.value }))}
                        disabled={!canEditRevision}
                        helperText="Example: if the parent has {a,b,c} and you enter only {e:g}, this node overrides only e and inherits the rest."
                      />
                    </Grid>
                    <Grid item xs={12} lg={6}>
                      <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1 }}>
                        Effective config preview
                      </Typography>
                      <Typography variant="body2" sx={{ color: '#64748b', mb: 1.5 }}>
                        Preview of parent inheritance plus these local overrides.
                      </Typography>
                      <Box
                        component="pre"
                        sx={{
                          m: 0,
                          p: 2.5,
                          borderRadius: 4,
                          bgcolor: '#0f172a',
                          color: '#e2e8f0',
                          overflow: 'auto',
                          minHeight: 286,
                          border: '1px solid rgba(148,163,184,0.16)',
                        }}
                      >
                        {revisionOverrides
                          ? formatConfig(effectiveConfigPreview || {})
                          : 'Invalid JSON. Fix the overrides to preview the effective config.'}
                      </Box>
                    </Grid>
                  </Grid>
                  <TextField
                    label="Revision note"
                    value={revisionDraft.change_note}
                    onChange={(event) => setRevisionDraft((current) => ({ ...current, change_note: event.target.value }))}
                    disabled={!canEditRevision}
                  />
                  <Stack direction="row" spacing={1.5}>
                    <Button
                      variant="outlined"
                      disabled={!canEditRevision}
                      onClick={() =>
                        setRevisionDraft(
                          buildRevisionDraft(
                            activeRequest.revisions[0],
                            originalConfig,
                            parentConfig,
                            !activeNode?.parent_config_node_id
                          )
                        )
                      }
                    >
                      Reset draft
                    </Button>
                    <Button
                      variant="contained"
                      disabled={!canEditRevision}
                      onClick={async () => {
                        try {
                          await v2Api.createRevision(activeRequest.request.request_id, {
                            proposed_overrides: parseConfigText(revisionDraft.proposed_overrides),
                            change_note: revisionDraft.change_note || undefined,
                          });
                          await refreshActiveRequest();
                        } catch (_err) {
                          if (axios.isAxiosError(_err)) {
                            setError(_err.response?.data?.detail || 'Unable to save revision.');
                          } else {
                            setError('Unable to save revision.');
                          }
                        }
                      }}
                    >
                      Save revision
                    </Button>
                  </Stack>
                </Stack>

                <Divider sx={{ my: 3 }} />
                <Typography variant="h6" sx={{ mb: 1.5 }}>
                  Discussion
                </Typography>
                <Stack spacing={1.25} sx={{ mb: 2 }}>
                  {activeRequest.comments.map((comment) => (
                    <Card key={comment.comment_id} variant="outlined" sx={{ p: 1.5 }}>
                      <Typography variant="body2" sx={{ color: '#64748b', mb: 0.5 }}>
                        by: {userAliasById(comment.author_id, users)} • {new Date(comment.created_at).toLocaleString()}
                      </Typography>
                      <Typography>{comment.body}</Typography>
                    </Card>
                  ))}
                </Stack>
                <Stack direction="row" spacing={1.5}>
                  <TextField
                    fullWidth
                    placeholder="Add a comment for the reviewer or implementer"
                    value={commentDraft}
                    onChange={(event) => setCommentDraft(event.target.value)}
                  />
                  <Button
                    startIcon={<Comment />}
                    variant="outlined"
                    onClick={async () => {
                      await v2Api.addComment(activeRequest.request.request_id, commentDraft);
                      setCommentDraft('');
                      await refreshActiveRequest();
                    }}
                  >
                    Add
                  </Button>
                </Stack>
              </>
            ) : (
              <Typography sx={{ color: '#94a3b8' }}>
                Select a request to inspect its original config, requested diff, reviewer assignment, and governance actions.
              </Typography>
            )}
          </Card>
        </Grid>
      </Grid>

      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} fullWidth maxWidth="md">
        <DialogTitle>Create change request</DialogTitle>
        <DialogContent sx={{ pt: 1 }}>
          <Stack spacing={2}>
            <TextField
              select
              label="Service"
              value={selectedServiceId}
              onChange={(event) => {
                setSelectedServiceId(event.target.value);
                setRequestDraft((current) => ({ ...current, target_config_node_id: '' }));
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
              label="Target node"
              value={requestDraft.target_config_node_id}
              onChange={(event) => setRequestDraft({ ...requestDraft, target_config_node_id: event.target.value })}
            >
              {currentServiceNodes.map((node) => (
                <MenuItem key={node.config_node_id} value={node.config_node_id}>
                  {node.path}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              select
              label="Assigned reviewer"
              value={requestDraft.assigned_reviewer_id}
              onChange={(event) => setRequestDraft({ ...requestDraft, assigned_reviewer_id: event.target.value })}
            >
              <MenuItem value="">Any eligible reviewer</MenuItem>
              {users.map((user) => (
                <MenuItem key={user.user_id} value={user.user_id}>
                  {user.display_name} ({user.email})
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="Local overrides JSON"
              multiline
              minRows={10}
              value={requestDraft.proposed_overrides}
              onChange={(event) => setRequestDraft({ ...requestDraft, proposed_overrides: event.target.value })}
              helperText="Enter only the keys this node should override. Everything else is inherited from the parent."
            />
            <TextField
              label="Change note"
              value={requestDraft.change_note}
              onChange={(event) => setRequestDraft({ ...requestDraft, change_note: event.target.value })}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Close</Button>
          <Button
            variant="contained"
            onClick={async () => {
              if (!selectedServiceId || !requestDraft.target_config_node_id) return;
              try {
                const request = await v2Api.createChangeRequest({
                  service_id: selectedServiceId,
                  target_config_node_id: requestDraft.target_config_node_id,
                  assigned_reviewer_id: requestDraft.assigned_reviewer_id || null,
                });
                await v2Api.createRevision(request.request_id, {
                  proposed_overrides: parseConfigText(requestDraft.proposed_overrides),
                  change_note: requestDraft.change_note,
                });
                setCreateOpen(false);
                setRequestDraft({
                  target_config_node_id: '',
                  assigned_reviewer_id: '',
                  proposed_overrides: '{\n  "timeout_ms": "1500"\n}',
                  change_note: '',
                });
                await loadRequestsPage();
              } catch (_err) {
                setError('Unable to create change request.');
              }
            }}
          >
            Create request
          </Button>
        </DialogActions>
      </Dialog>
    </AppLayout>
  );
};

export default RequestsPage;
