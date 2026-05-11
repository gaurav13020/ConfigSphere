import axios from 'axios';

import { useAuthStore } from '@/stores/auth';
import {
  BootstrapAdminResponse,
  BootstrapAdminStatus,
  ChangeRequest,
  ConfigNode,
  ConfigNodeVersion,
  CreatedServiceApiKey,
  DeliveryConfig,
  DeliveryVersion,
  RbacAuditEvent,
  RequestActivity,
  RoleBinding,
  RollbackRequest,
  Service,
  ServiceApiKey,
  UserSummary,
} from '@/types';

const CONTROL_PLANE_URL = import.meta.env.VITE_CONTROL_PLANE_URL || 'http://localhost:8100';
const DELIVERY_URL = import.meta.env.VITE_DELIVERY_URL || 'http://localhost:8101';
const KEYCLOAK_URL = import.meta.env.VITE_KEYCLOAK_URL || 'http://localhost:8080';
const KEYCLOAK_REALM = import.meta.env.VITE_KEYCLOAK_REALM || 'configsphere';
const KEYCLOAK_CLIENT_ID = import.meta.env.VITE_KEYCLOAK_CLIENT_ID || '';
const KEYCLOAK_REDIRECT_URI = import.meta.env.VITE_KEYCLOAK_REDIRECT_URI || '';

const controlPlane = axios.create({
  baseURL: CONTROL_PLANE_URL,
  headers: { 'Content-Type': 'application/json' },
});

const delivery = axios.create({
  baseURL: DELIVERY_URL,
  headers: { 'Content-Type': 'application/json' },
});

const attachAuth = (config: any) => {
  const { token, user, devMode } = useAuthStore.getState();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  if (devMode && user) {
    config.headers['X-Dev-User'] = user.email;
    config.headers['X-Dev-Name'] = user.displayName;
  }
  return config;
};

controlPlane.interceptors.request.use(attachAuth);
delivery.interceptors.request.use(attachAuth);

const deliveryHeaders = (configToken?: string) =>
  configToken ? { 'X-Config-Token': configToken } : undefined;

const buildKeycloakAuthLink = (action: 'login' | 'signup') => {
  if (!KEYCLOAK_CLIENT_ID || !KEYCLOAK_REDIRECT_URI) {
    return null;
  }
  const authUrl = new URL(`${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/auth`);
  authUrl.searchParams.set('client_id', KEYCLOAK_CLIENT_ID);
  authUrl.searchParams.set('redirect_uri', KEYCLOAK_REDIRECT_URI);
  authUrl.searchParams.set('response_type', 'code');
  authUrl.searchParams.set('scope', 'openid');
  if (action === 'signup') {
    authUrl.searchParams.set('kc_action', 'register');
  }
  return authUrl.toString();
};

export const authLinks = {
  login: buildKeycloakAuthLink('login'),
  signup: buildKeycloakAuthLink('signup'),
  adminConsole: `${KEYCLOAK_URL}/admin/`,
};

export const v2Api = {
  listServices: async () => (await controlPlane.get<Service[]>('/v1/services')).data,
  createService: async (payload: { service_name: string; service_type: string; owner_team?: string }) =>
    (await controlPlane.post<Service>('/v1/services', payload)).data,
  createRootNode: async (serviceId: string, payload: { path: string; base_config: Record<string, string> }) =>
    (await controlPlane.post<ConfigNode>(`/v1/services/${serviceId}/nodes/root`, payload)).data,
  listNodes: async (serviceId: string) =>
    (await controlPlane.get<ConfigNode[]>(`/v1/services/${serviceId}/nodes`)).data,
  createChildNode: async (serviceId: string, nodeId: string, payload: { segment: string }) =>
    (await controlPlane.post<ConfigNode>(`/v1/services/${serviceId}/nodes/${nodeId}/children`, payload)).data,
  listVersions: async (serviceId: string, nodeId: string) =>
    (await controlPlane.get<ConfigNodeVersion[]>(`/v1/services/${serviceId}/nodes/${nodeId}/versions`)).data,
  listServiceApiKeys: async (serviceId: string) =>
    (await controlPlane.get<ServiceApiKey[]>(`/v1/services/${serviceId}/api-keys`)).data,
  createServiceApiKey: async (serviceId: string, payload: { key_name: string }) =>
    (await controlPlane.post<CreatedServiceApiKey>(`/v1/services/${serviceId}/api-keys`, payload)).data,
  revokeServiceApiKey: async (serviceId: string, apiKeyId: string) =>
    (await controlPlane.delete<ServiceApiKey>(`/v1/services/${serviceId}/api-keys/${apiKeyId}`)).data,

  listChangeRequests: async (params?: Record<string, string>) =>
    (await controlPlane.get<ChangeRequest[]>('/v1/change-requests', { params })).data,
  getRequestActivity: async (requestId: string) =>
    (await controlPlane.get<RequestActivity>(`/v1/change-requests/${requestId}/activity`)).data,
  createChangeRequest: async (payload: {
    service_id: string;
    target_config_node_id: string;
    request_type?: 'EDIT_NODE' | 'CREATE_SUBCONFIG' | 'ROLLBACK';
    assigned_reviewer_id?: string | null;
  }) => (await controlPlane.post<ChangeRequest>('/v1/change-requests', payload)).data,
  createRevision: async (
    requestId: string,
    payload: { proposed_overrides: Record<string, string>; change_note?: string }
  ) =>
    (await controlPlane.post<ChangeRequest>(`/v1/change-requests/${requestId}/revisions`, payload)).data,
  submitRequest: async (requestId: string, note?: string) =>
    (await controlPlane.post<ChangeRequest>(`/v1/change-requests/${requestId}/submit`, { note })).data,
  addComment: async (requestId: string, body: string, revision_id?: string | null) =>
    (await controlPlane.post(`/v1/change-requests/${requestId}/comments`, { body, revision_id })).data,
  reviewRequest: async (requestId: string, payload: { revision_id: string; decision: string; note?: string }) =>
    (await controlPlane.post<ChangeRequest>(`/v1/change-requests/${requestId}/review`, payload)).data,
  implementRequest: async (requestId: string) =>
    (await controlPlane.post(`/v1/change-requests/${requestId}/implement`)).data,

  listRollbacks: async (params?: Record<string, string>) =>
    (await controlPlane.get<RollbackRequest[]>('/v1/rollbacks', { params })).data,
  createRollback: async (payload: { service_id: string; target_config_node_id: string; target_version_id: string }) =>
    (await controlPlane.post<RollbackRequest>('/v1/rollbacks', payload)).data,
  approveRollback: async (rollbackId: string, note?: string) =>
    (await controlPlane.post<RollbackRequest>(`/v1/rollbacks/${rollbackId}/approve`, { note })).data,
  implementRollback: async (rollbackId: string) =>
    (await controlPlane.post(`/v1/rollbacks/${rollbackId}/implement`)).data,

  getBootstrapStatus: async () =>
    (await controlPlane.get<BootstrapAdminStatus>('/v1/admin/bootstrap/status')).data,
  bootstrapAdmin: async () =>
    (await controlPlane.post<BootstrapAdminResponse>('/v1/admin/bootstrap')).data,
  listUsers: async () =>
    (await controlPlane.get<UserSummary[]>('/v1/admin/users')).data,
  listUserBindings: async (userId: string) =>
    (await controlPlane.get<RoleBinding[]>(`/v1/admin/users/${userId}/bindings`)).data,
  grantRoleBinding: async (payload: {
    target_user_id: string;
    role_name: 'CONFIG_AUTHOR' | 'CONFIG_REVIEWER' | 'CONFIG_IMPLEMENTER' | 'CONFIG_ADMIN' | 'CONFIG_AUDITOR';
    scope_type: 'GLOBAL' | 'SERVICE';
    scope_id?: string | null;
    note?: string | null;
  }) => (await controlPlane.post<RoleBinding>('/v1/admin/role-bindings', payload)).data,
  revokeRoleBinding: async (bindingId: string, note?: string) =>
    (await controlPlane.delete(`/v1/admin/role-bindings/${bindingId}`, { params: note ? { note } : {} })).data,
  listRbacAudit: async (targetUserId?: string) =>
    (await controlPlane.get<RbacAuditEvent[]>('/v1/admin/audit', { params: targetUserId ? { target_user_id: targetUserId } : {} })).data,
  listAllUsers: async () =>
    (await controlPlane.get<UserSummary[]>('/v1/users')).data,
  listMyBindings: async () =>
    (await controlPlane.get<RoleBinding[]>('/v1/me/bindings')).data,

  getConfig: async (service: string, path: string) =>
    (await delivery.get<DeliveryConfig>('/v1/config', { params: { service, path } })).data,
  getVersion: async (service: string, path: string) =>
    (await delivery.get<DeliveryVersion>('/v1/config/version', { params: { service, path } })).data,
  getConfigWithToken: async (service: string, path: string, configToken: string) =>
    (await delivery.get<DeliveryConfig>('/v1/config', { params: { service, path }, headers: deliveryHeaders(configToken) })).data,
  getVersionWithToken: async (service: string, path: string, configToken: string) =>
    (await delivery.get<DeliveryVersion>('/v1/config/version', { params: { service, path }, headers: deliveryHeaders(configToken) })).data,
  cancelRequest: async (requestId: string, note?: string) =>
    (await controlPlane.post<ChangeRequest>(`/v1/change-requests/${requestId}/cancel`, { note })).data,
};
