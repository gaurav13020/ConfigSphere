import axios, { AxiosInstance } from 'axios';
import { 
  Schema, ConfigItem, ConfigVersion, ResolvedConfig, AuditEvent 
} from '@/types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
const AUTH_URL = import.meta.env.VITE_AUTH_URL || 'http://localhost:8001/api/v1';

// Separate axios instance for auth-service calls
export const authApi = axios.create({
  baseURL: AUTH_URL,
  headers: { 'Content-Type': 'application/json' },
});

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Attach JWT token from localStorage (persisted by zustand)
    this.client.interceptors.request.use((config: any) => {
      const stored = localStorage.getItem('configsphere-auth');
      if (stored) {
        try {
          const { state } = JSON.parse(stored);
          if (state?.token) {
            config.headers = config.headers || {};
            config.headers['Authorization'] = `Bearer ${state.token}`;
          }
        } catch { /* ignore parse errors */ }
      }
      console.log('API Request:', config.method?.toUpperCase(), config.url);
      return config;
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response: any) => {
        console.log('API Response:', response.status, response.data);
        return response;
      },
      (error: any) => {
        console.error('API Error:', error.response?.status, error.response?.data);
        // Redirect to login on 401
        if (error.response?.status === 401) {
          localStorage.removeItem('configsphere-auth');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Schemas
  getSchemas(query?: Record<string, any>) {
    return this.client.get<Schema[]>('/schemas/', { params: query });
  }

  getSchema(id: number) {
    return this.client.get<Schema>(`/schemas/${id}/`);
  }

  createSchema(data: Omit<Schema, 'id' | 'created_at'>) {
    return this.client.post<Schema>('/schemas/', data);
  }

  updateSchema(id: number, data: Omit<Schema, 'id' | 'created_at'>) {
    return this.client.put<Schema>(`/schemas/${id}/`, data);
  }

  deleteSchema(id: number) {
    return this.client.delete(`/schemas/${id}/`);
  }

  // Config Items
  getConfigItems(query?: Record<string, any>) {
    return this.client.get<ConfigItem[]>('/config-items/', { params: query });
  }

  getConfigItem(id: number) {
    return this.client.get<ConfigItem>(`/config-items/${id}/`);
  }

  createConfigItem(data: Omit<ConfigItem, 'id' | 'created_at' | 'updated_at' | 'status' | 'active_version_id'>) {
    return this.client.post<ConfigItem>('/config-items/', data);
  }

  updateConfigItem(id: number, data: Omit<ConfigItem, 'id' | 'created_at' | 'updated_at' | 'status' | 'active_version_id'>) {
    return this.client.put<ConfigItem>(`/config-items/${id}/`, data);
  }

  deleteConfigItem(id: number) {
    return this.client.delete(`/config-items/${id}/`);
  }

  // Config Versions
  getConfigVersions(configItemId: number, query?: Record<string, any>) {
    return this.client.get<ConfigVersion[]>(
      `/config-items/${configItemId}/versions/`,
      { params: query }
    );
  }

  getConfigVersion(id: number) {
    return this.client.get<ConfigVersion>(`/config-versions/${id}/`);
  }

  createConfigVersion(configItemId: number, data: Omit<ConfigVersion, 'id' | 'created_at' | 'checksum' | 'status' | 'validation_error' | 'version_number'>) {
    return this.client.post<ConfigVersion>(
      `/config-items/${configItemId}/versions/`,
      data
    );
  }

  activateConfigVersion(versionId: number, data: { actor: string }) {
    return this.client.post<ConfigVersion>(
      `/config-versions/${versionId}/activate/`,
      data
    );
  }

  validateConfigVersion(versionId: number, data: { actor: string }) {
    return this.client.post<ConfigVersion>(
      `/config-versions/${versionId}/validate/`,
      data
    );
  }

  archiveConfigVersion(versionId: number, data: { actor: string }) {
    return this.client.post<ConfigVersion>(
      `/config-versions/${versionId}/archive/`,
      data
    );
  }

  // Resolved Config
  getResolvedConfig(query: Record<string, any>) {
    return this.client.get<ResolvedConfig>('/resolved-config/', { params: query });
  }

  // Audit Events
  getAuditEvents(query?: Record<string, any>) {
    return this.client.get<AuditEvent[]>('/audit-events/', { params: query });
  }
}

export const apiClient = new ApiClient();
