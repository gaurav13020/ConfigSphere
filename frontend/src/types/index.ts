/* Global type definitions */

export interface Schema {
  id: number;
  name: string;
  description: string;
  schema_json: Record<string, any>;
  created_at: string;
}

export interface ConfigItem {
  id: number;
  key: string;
  scope_level: 'global' | 'region' | 'group' | 'service';
  global_name: string;
  region_name: string;
  group_name: string;
  service_name: string;
  schema: number | null;
  status: string;
  active_version_id: number | null;
  description: string;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConfigVersion {
  id: number;
  config_item: number;
  version_number: number;
  payload: Record<string, any>;
  checksum: string;
  status: 'draft' | 'validated' | 'validation_failed' | 'active' | 'archived';
  validation_error: string;
  change_summary: string;
  created_by: string;
  created_at: string;
}

export interface AuditEvent {
  id: number;
  event_type: string;
  actor: string | null;
  config_item_id: number | null;
  config_version_id: number | null;
  schema_id: number | null;
  payload: Record<string, any>;
  created_at: string;
}

export interface ResolvedConfig {
  payload: Record<string, any>;
  checksum: string;
  layers: ConfigLayer[];
  scope_params: ScopeParams;
}

export interface ConfigLayer {
  scope_level: string;
  config_item_id: number;
  config_version_id: number;
  version_number: number;
  checksum: string;
  key: string;
}

export interface ScopeParams {
  global: string;
  region: string | null;
  group: string | null;
  service: string | null;
}

export interface ErrorResponse {
  error: string;
  message: string;
  details?: Record<string, string[]>;
}
