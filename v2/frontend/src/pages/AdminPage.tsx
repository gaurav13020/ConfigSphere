import {
  AdminPanelSettings,
  LockOpen,
  ManageAccounts,
  People,
  RemoveCircleOutline,
  RuleFolder,
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
  Grid,
  MenuItem,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import axios from 'axios';
import { useEffect, useMemo, useState } from 'react';

import { AppLayout } from '@/components/AppLayout';
import { StatusChip } from '@/components/StatusChip';
import { v2Api } from '@/services/api';
import { BootstrapAdminStatus, RbacAuditEvent, RoleBinding, RoleName, ScopeType, Service, UserSummary } from '@/types';

const roleOptions: { value: RoleName; label: string }[] = [
  { value: 'CONFIG_ADMIN', label: 'Config Admin' },
  { value: 'CONFIG_AUTHOR', label: 'Config Author' },
  { value: 'CONFIG_REVIEWER', label: 'Config Reviewer' },
  { value: 'CONFIG_IMPLEMENTER', label: 'Config Implementer' },
  { value: 'CONFIG_AUDITOR', label: 'Config Auditor' },
];

const scopeOptions: { value: ScopeType; label: string }[] = [
  { value: 'GLOBAL', label: 'Global' },
  { value: 'SERVICE', label: 'Service' },
];

const formatTimestamp = (value: string | null | undefined) => {
  if (!value) return '-';
  return new Date(value).toLocaleString();
};

const AdminPage = () => {
  const [bootstrap, setBootstrap] = useState<BootstrapAdminStatus | null>(null);
  const [services, setServices] = useState<Service[]>([]);
  const [users, setUsers] = useState<UserSummary[]>([]);
  const [selectedUserId, setSelectedUserId] = useState('');
  const [bindings, setBindings] = useState<RoleBinding[]>([]);
  const [audit, setAudit] = useState<RbacAuditEvent[]>([]);
  const [grantOpen, setGrantOpen] = useState(false);
  const [grantDraft, setGrantDraft] = useState<{
    target_user_id: string;
    role_name: RoleName;
    scope_type: ScopeType;
    scope_id: string;
    note: string;
  }>({
    target_user_id: '',
    role_name: 'CONFIG_AUTHOR',
    scope_type: 'SERVICE',
    scope_id: '',
    note: '',
  });
  const [revokeNote, setRevokeNote] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [accessDenied, setAccessDenied] = useState(false);
  const [busy, setBusy] = useState(false);

  const selectedUser = useMemo(
    () => users.find((user) => user.user_id === selectedUserId) || null,
    [users, selectedUserId]
  );

  const loadAdminData = async () => {
    setError(null);
    try {
      const bootstrapStatus = await v2Api.getBootstrapStatus();
      setBootstrap(bootstrapStatus);

      if (bootstrapStatus.bootstrap_required) {
        setAccessDenied(false);
        setUsers([]);
        setBindings([]);
        setAudit([]);
        return;
      }

      const [servicesData, usersData] = await Promise.all([v2Api.listServices(), v2Api.listUsers()]);
      setServices(servicesData);
      setUsers(usersData);
      setAccessDenied(false);
      if (!selectedUserId && usersData[0]) {
        setSelectedUserId(usersData[0].user_id);
      }
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 403) {
        setAccessDenied(true);
        setError(null);
        return;
      }
      setError('Unable to load admin controls right now.');
    }
  };

  const loadSelectedUserData = async (userId: string) => {
    if (!userId) return;
    try {
      const [bindingsData, auditData] = await Promise.all([v2Api.listUserBindings(userId), v2Api.listRbacAudit(userId)]);
      setBindings(bindingsData);
      setAudit(auditData);
    } catch (err) {
      if (!axios.isAxiosError(err) || err.response?.status !== 403) {
        setError('Unable to load role bindings for the selected user.');
      }
    }
  };

  useEffect(() => {
    loadAdminData();
  }, []);

  useEffect(() => {
    if (selectedUserId && !bootstrap?.bootstrap_required && !accessDenied) {
      loadSelectedUserData(selectedUserId);
    }
  }, [selectedUserId, bootstrap?.bootstrap_required, accessDenied]);

  const handleBootstrap = async () => {
    setBusy(true);
    setError(null);
    try {
      await v2Api.bootstrapAdmin();
      await loadAdminData();
    } catch (err) {
      setError('Bootstrap failed. Refresh once and try again.');
    } finally {
      setBusy(false);
    }
  };

  const handleGrant = async () => {
    setBusy(true);
    setError(null);
    try {
      await v2Api.grantRoleBinding({
        target_user_id: grantDraft.target_user_id,
        role_name: grantDraft.role_name,
        scope_type: grantDraft.scope_type,
        scope_id: grantDraft.scope_type === 'SERVICE' ? grantDraft.scope_id : null,
        note: grantDraft.note || null,
      });
      setGrantOpen(false);
      setGrantDraft({
        target_user_id: selectedUserId || '',
        role_name: 'CONFIG_AUTHOR',
        scope_type: 'SERVICE',
        scope_id: services[0]?.service_id || '',
        note: '',
      });
      await loadAdminData();
      if (selectedUserId) await loadSelectedUserData(selectedUserId);
    } catch (err) {
      setError('Unable to grant role binding.');
    } finally {
      setBusy(false);
    }
  };

  const handleRevoke = async (bindingId: string) => {
    setBusy(true);
    setError(null);
    try {
      await v2Api.revokeRoleBinding(bindingId, revokeNote || undefined);
      setRevokeNote('');
      if (selectedUserId) await loadSelectedUserData(selectedUserId);
      await loadAdminData();
    } catch (err) {
      setError('Unable to revoke role binding.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <AppLayout>
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" alignItems={{ xs: 'flex-start', md: 'center' }} spacing={2} sx={{ mb: 3 }}>
        <Box>
          <Typography variant="h3" sx={{ mb: 1 }}>
            Admin & Access
          </Typography>
          <Typography sx={{ color: '#64748b' }}>
            Bootstrap the first platform admin, assign service roles, and audit every RBAC change.
          </Typography>
        </Box>
        <Chip
          icon={<AdminPanelSettings />}
          label={
            bootstrap?.bootstrap_required
              ? 'Bootstrap required'
              : `Global admins: ${bootstrap?.global_admin_count ?? 0}`
          }
          sx={{ px: 1, py: 2.4, bgcolor: 'rgba(91,77,245,0.08)', color: '#5b4df5', fontWeight: 700 }}
        />
      </Stack>

      {error ? (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      ) : null}

      {bootstrap?.bootstrap_required ? (
        <Card sx={{ p: 4 }}>
          <Stack spacing={2.5} maxWidth={720}>
            <Stack direction="row" spacing={1.5} alignItems="center">
              <Box sx={{ p: 1.5, borderRadius: 3, bgcolor: 'rgba(91,77,245,0.08)', color: '#5b4df5' }}>
                <LockOpen />
              </Box>
              <Typography variant="h5">First admin bootstrap is still required</Typography>
            </Stack>
            <Typography sx={{ color: '#64748b' }}>
              No global admin exists yet. The current signed-in user can claim the first `CONFIG_ADMIN` role once, and after that all later access will be granted through the admin controls.
            </Typography>
            <Button variant="contained" onClick={handleBootstrap} disabled={busy} sx={{ alignSelf: 'flex-start' }}>
              Bootstrap current user as first admin
            </Button>
          </Stack>
        </Card>
      ) : accessDenied ? (
        <Card sx={{ p: 4 }}>
          <Stack spacing={2.5} maxWidth={720}>
            <Stack direction="row" spacing={1.5} alignItems="center">
              <Box sx={{ p: 1.5, borderRadius: 3, bgcolor: 'rgba(249,115,22,0.10)', color: '#f97316' }}>
                <ManageAccounts />
              </Box>
              <Typography variant="h5">Admin access required</Typography>
            </Stack>
            <Typography sx={{ color: '#64748b' }}>
              The platform already has at least one global admin. Ask an existing admin to grant you `CONFIG_ADMIN` if you need access to bootstrap, role assignment, or RBAC audit views.
            </Typography>
          </Stack>
        </Card>
      ) : (
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Card sx={{ p: 2.5, height: '100%' }}>
              <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
                <Typography variant="h6">Users</Typography>
                <Button
                  size="small"
                  variant="outlined"
                  startIcon={<RuleFolder />}
                  onClick={() => {
                    setGrantDraft((current) => ({
                      ...current,
                      target_user_id: selectedUserId || users[0]?.user_id || '',
                      scope_id: services[0]?.service_id || '',
                    }));
                    setGrantOpen(true);
                  }}
                >
                  Grant role
                </Button>
              </Stack>
              <Stack spacing={1.25}>
                {users.map((user) => {
                  const active = user.user_id === selectedUserId;
                  return (
                    <Box
                      key={user.user_id}
                      onClick={() => setSelectedUserId(user.user_id)}
                      sx={{
                        p: 2,
                        borderRadius: 3,
                        cursor: 'pointer',
                        border: active ? '1px solid rgba(91,77,245,0.35)' : '1px solid rgba(148,163,184,0.14)',
                        bgcolor: active ? 'rgba(91,77,245,0.06)' : 'transparent',
                      }}
                    >
                      <Typography sx={{ fontWeight: 700 }}>{user.display_name}</Typography>
                      <Typography variant="body2" sx={{ color: '#64748b' }}>
                        {user.email}
                      </Typography>
                    </Box>
                  );
                })}
              </Stack>
            </Card>
          </Grid>

          <Grid item xs={12} md={8}>
            <Stack spacing={3}>
              <Card sx={{ p: 3 }}>
                <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
                  <Box>
                    <Typography variant="h5">{selectedUser?.display_name || 'Select a user'}</Typography>
                    <Typography sx={{ color: '#64748b', mt: 0.5 }}>
                      {selectedUser?.email || 'Choose a user from the left to inspect current access.'}
                    </Typography>
                  </Box>
                  <Chip icon={<People />} label={`${bindings.length} bindings`} />
                </Stack>

                {selectedUser ? (
                  <>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Role</TableCell>
                          <TableCell>Scope</TableCell>
                          <TableCell>Scope target</TableCell>
                          <TableCell>Created</TableCell>
                          <TableCell align="right">Action</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {bindings.map((binding) => {
                          const service = services.find((item) => item.service_id === binding.scope_id);
                          return (
                            <TableRow key={binding.binding_id}>
                              <TableCell>
                                <StatusChip value={binding.role_name} />
                              </TableCell>
                              <TableCell>{binding.scope_type}</TableCell>
                              <TableCell>{binding.scope_type === 'GLOBAL' ? 'All services' : service?.service_name || binding.scope_id}</TableCell>
                              <TableCell>{formatTimestamp(binding.created_at)}</TableCell>
                              <TableCell align="right">
                                <Button
                                  color="error"
                                  startIcon={<RemoveCircleOutline />}
                                  onClick={() => handleRevoke(binding.binding_id)}
                                  disabled={busy}
                                >
                                  Revoke
                                </Button>
                              </TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>

                    {!bindings.length ? (
                      <Typography sx={{ color: '#94a3b8', mt: 2 }}>
                        This user does not have any role bindings yet.
                      </Typography>
                    ) : null}

                    <TextField
                      label="Optional revoke note"
                      placeholder="Reason for role removal"
                      value={revokeNote}
                      onChange={(event) => setRevokeNote(event.target.value)}
                      fullWidth
                      sx={{ mt: 2.5 }}
                    />
                  </>
                ) : null}
              </Card>

              <Card sx={{ p: 3 }}>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  RBAC Audit
                </Typography>
                <Stack spacing={1.25}>
                  {audit.map((event) => {
                    const service = services.find((item) => item.service_id === event.scope_id);
                    return (
                      <Box
                        key={event.audit_event_id}
                        sx={{ p: 2, borderRadius: 3, bgcolor: 'rgba(15,23,42,0.03)', border: '1px solid rgba(148,163,184,0.14)' }}
                      >
                        <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={1}>
                          <Typography sx={{ fontWeight: 700 }}>
                            {event.action} {event.role_name}
                          </Typography>
                          <Typography variant="body2" sx={{ color: '#64748b' }}>
                            {formatTimestamp(event.created_at)}
                          </Typography>
                        </Stack>
                        <Typography variant="body2" sx={{ color: '#64748b', mt: 0.5 }}>
                          Scope: {event.scope_type === 'GLOBAL' ? 'All services' : service?.service_name || event.scope_id || '-'}
                        </Typography>
                        {event.note ? (
                          <Typography variant="body2" sx={{ mt: 0.75 }}>
                            {event.note}
                          </Typography>
                        ) : null}
                      </Box>
                    );
                  })}
                  {!audit.length ? (
                    <Typography sx={{ color: '#94a3b8' }}>
                      No RBAC audit records yet for this user.
                    </Typography>
                  ) : null}
                </Stack>
              </Card>
            </Stack>
          </Grid>
        </Grid>
      )}

      <Dialog open={grantOpen} onClose={() => setGrantOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Grant role binding</DialogTitle>
        <DialogContent sx={{ pt: 1 }}>
          <Stack spacing={2}>
            <TextField
              select
              label="User"
              value={grantDraft.target_user_id}
              onChange={(event) => setGrantDraft({ ...grantDraft, target_user_id: event.target.value })}
            >
              {users.map((user) => (
                <MenuItem key={user.user_id} value={user.user_id}>
                  {user.display_name} ({user.email})
                </MenuItem>
              ))}
            </TextField>
            <TextField
              select
              label="Role"
              value={grantDraft.role_name}
              onChange={(event) => setGrantDraft({ ...grantDraft, role_name: event.target.value as RoleName })}
            >
              {roleOptions.map((role) => (
                <MenuItem key={role.value} value={role.value}>
                  {role.label}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              select
              label="Scope"
              value={grantDraft.scope_type}
              onChange={(event) => setGrantDraft({ ...grantDraft, scope_type: event.target.value as ScopeType })}
            >
              {scopeOptions.map((scope) => (
                <MenuItem key={scope.value} value={scope.value}>
                  {scope.label}
                </MenuItem>
              ))}
            </TextField>
            {grantDraft.scope_type === 'SERVICE' ? (
              <TextField
                select
                label="Service"
                value={grantDraft.scope_id}
                onChange={(event) => setGrantDraft({ ...grantDraft, scope_id: event.target.value })}
              >
                {services.map((service) => (
                  <MenuItem key={service.service_id} value={service.service_id}>
                    {service.service_name}
                  </MenuItem>
                ))}
              </TextField>
            ) : null}
            <TextField
              label="Note"
              multiline
              minRows={3}
              value={grantDraft.note}
              onChange={(event) => setGrantDraft({ ...grantDraft, note: event.target.value })}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setGrantOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleGrant} disabled={busy || !grantDraft.target_user_id}>
            Grant role
          </Button>
        </DialogActions>
      </Dialog>
    </AppLayout>
  );
};

export default AdminPage;
