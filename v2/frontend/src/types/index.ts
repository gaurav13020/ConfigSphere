export interface AuthUser {
  email: string;
  displayName: string;
}

export type RoleName =
  | 'CONFIG_AUTHOR'
  | 'CONFIG_REVIEWER'
  | 'CONFIG_IMPLEMENTER'
  | 'CONFIG_ADMIN'
  | 'CONFIG_AUDITOR';

export type ScopeType = 'GLOBAL' | 'SERVICE';

export interface Service {
  service_id: string;
  service_name: string;
  service_type: 'MICROSERVICE' | 'MONOLITH' | 'OTHER';
  owner_team: string | null;
  node_count: number;
  current_tree_version: number;
}

export interface ConfigNode {
  config_node_id: string;
  service_id: string;
  parent_config_node_id: string | null;
  path: string;
  depth: number;
  active_version_id: string | null;
}

export interface ConfigNodeVersion {
  version_id: string;
  config_node_id: string;
  service_id: string;
  tree_version: number;
  document_id: string;
  version_status: string;
  created_at: string;
}

export interface ServiceApiKey {
  api_key_id: string;
  service_id: string;
  key_name: string;
  token_prefix: string;
  created_by: string | null;
  revoked_at: string | null;
  created_at: string;
}

export interface CreatedServiceApiKey extends ServiceApiKey {
  plain_token: string;
}

export interface DeliveryConfig {
  serviceId: string;
  serviceName: string;
  configNodeId: string;
  path: string;
  versionId: string;
  treeVersion: number;
  materializedConfig: Record<string, string>;
  keyCount: number;
}

export interface DeliveryVersion {
  serviceName: string;
  path: string;
  versionId: string;
  treeVersion: number;
}

export interface ChangeRequest {
  request_id: string;
  service_id: string;
  target_config_node_id: string;
  request_type: 'EDIT_NODE' | 'CREATE_SUBCONFIG' | 'ROLLBACK';
  status: string;
  assigned_reviewer_id: string | null;
  jira_issue_key: string | null;
  current_revision_id: string | null;
  submitted_at: string | null;
  approved_at: string | null;
  implemented_at: string | null;
  created_at: string;
  updated_at: string;
  latest_revision_number: number | null;
  latest_diff_summary: Record<string, unknown> | null;
  created_by?: string;
}

export interface Revision {
  revision_id: string;
  request_id: string;
  revision_number: number;
  proposed_document_id: string;
  diff_summary_json: Record<string, unknown>;
  proposed_overrides: Record<string, string>;
  base_tree_version: number;
  change_note: string | null;
  created_by: string;
  created_at: string;
}

export interface RequestComment {
  comment_id: string;
  request_id: string;
  revision_id: string | null;
  author_id: string;
  body: string;
  created_at: string;
}

export interface RequestReview {
  review_id: string;
  request_id: string;
  revision_id: string;
  reviewer_id: string;
  decision: 'COMMENT' | 'REQUEST_CHANGES' | 'APPROVE' | 'REJECT';
  note: string | null;
  created_at: string;
}

export interface RequestActivity {
  request: ChangeRequest;
  revisions: Revision[];
  comments: RequestComment[];
  reviews: RequestReview[];
}

export interface RollbackRequest {
  rollback_request_id: string;
  service_id: string;
  target_config_node_id: string;
  target_version_id: string;
  status: 'REQUESTED' | 'APPROVED' | 'IMPLEMENTING' | 'ROLLED_BACK' | 'FAILED';
  jira_issue_key: string | null;
}

export interface BootstrapAdminStatus {
  bootstrap_required: boolean;
  global_admin_count: number;
}

export interface BootstrapAdminResponse {
  status: string;
  user_id: string;
  email: string;
}

export interface UserSummary {
  user_id: string;
  email: string;
  display_name: string;
  external_subject: string;
  jira_account_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface RoleBinding {
  binding_id: string;
  user_id: string;
  role_id: string;
  role_name: RoleName;
  scope_type: ScopeType;
  scope_id: string | null;
  created_at: string;
}

export interface RbacAuditEvent {
  audit_event_id: string;
  actor_user_id: string;
  target_user_id: string;
  role_id: string;
  role_name: RoleName;
  scope_type: ScopeType;
  scope_id: string | null;
  action: string;
  note: string | null;
  created_at: string;
}
