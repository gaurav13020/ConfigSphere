import { create } from 'zustand';
import { Schema, ConfigItem, ConfigVersion, ResolvedConfig, AuditEvent } from '@/types';

interface AppState {
  // Schemas
  schemas: Schema[];
  setSchemas: (schemas: Schema[]) => void;
  addSchema: (schema: Schema) => void;

  // Config Items
  configItems: ConfigItem[];
  setConfigItems: (items: ConfigItem[]) => void;
  addConfigItem: (item: ConfigItem) => void;

  // Config Versions
  configVersions: ConfigVersion[];
  setConfigVersions: (versions: ConfigVersion[]) => void;
  addConfigVersion: (version: ConfigVersion) => void;

  // Resolved Config
  resolvedConfig: ResolvedConfig | null;
  setResolvedConfig: (config: ResolvedConfig | null) => void;

  // Audit Events
  auditEvents: AuditEvent[];
  setAuditEvents: (events: AuditEvent[]) => void;

  // Loading states
  loading: boolean;
  setLoading: (loading: boolean) => void;

  // Current user
  currentUser: string;
  setCurrentUser: (user: string) => void;

  // Filters
  currentFilters: Record<string, any>;
  setCurrentFilters: (filters: Record<string, any>) => void;
}

export const useAppStore = create<AppState>((set) => ({
  schemas: [],
  setSchemas: (schemas: Schema[]) => set(() => ({ schemas })),
  addSchema: (schema: Schema) => set((state) => ({ schemas: [...state.schemas, schema] })),

  configItems: [],
  setConfigItems: (configItems: ConfigItem[]) => set(() => ({ configItems })),
  addConfigItem: (item: ConfigItem) => set((state) => ({ configItems: [...state.configItems, item] })),

  configVersions: [],
  setConfigVersions: (configVersions: ConfigVersion[]) => set(() => ({ configVersions })),
  addConfigVersion: (version: ConfigVersion) => set((state) => ({ configVersions: [...state.configVersions, version] })),

  resolvedConfig: null,
  setResolvedConfig: (resolvedConfig: ResolvedConfig | null) => set(() => ({ resolvedConfig })),

  auditEvents: [],
  setAuditEvents: (auditEvents: AuditEvent[]) => set(() => ({ auditEvents })),

  loading: false,
  setLoading: (loading: boolean) => set(() => ({ loading })),

  currentUser: 'admin',
  setCurrentUser: (currentUser: string) => set(() => ({ currentUser })),

  currentFilters: {},
  setCurrentFilters: (currentFilters: Record<string, any>) => set(() => ({ currentFilters })),
}));
