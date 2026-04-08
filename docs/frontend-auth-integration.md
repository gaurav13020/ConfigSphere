# Frontend Auth Integration — Design Document

## Overview

This document covers how to wire Jira OAuth authentication into the existing React + TypeScript frontend so that:
- Users log in via their Jira account
- The JWT is stored and attached to every API request
- UI elements are shown/hidden based on the user's role (Viewer / Operator / Approver / Admin)
- The approval workflow has dedicated pages (submit, review, status)

**Auth service base URL:** `http://localhost:8001/api/v1` (env: `VITE_AUTH_URL`)
**Config server base URL:** `http://localhost:8000/api/v1` (env: `VITE_API_URL`)

---

## 1. Auth Flow

```
User clicks "Sign in with Jira"
  → GET {VITE_AUTH_URL}/oauth/jira/login/
  → Browser redirected to Atlassian consent screen
  → User approves
  → Atlassian redirects to auth-service callback
  → Auth-service issues JWT, sets httpOnly refresh_token cookie
  → Browser redirected to {VITE_APP_URL}/auth/callback?token=<jwt>
  → Frontend extracts token from URL, stores in memory / localStorage
  → All subsequent API calls include Authorization: Bearer <jwt>
  → On 401, call POST {VITE_AUTH_URL}/oauth/refresh/ to rotate token
```

---

## 2. Token Storage

Store the JWT in **memory** (a Zustand store) as the primary source, with `localStorage` as a fallback for page refreshes. Never store the refresh token — it lives in the httpOnly cookie and is handled by the browser automatically.

```ts
// src/stores/auth.ts
import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AuthUser {
  jira_account_id: string;
  email: string;
  display_name: string;
  role: "viewer" | "operator" | "approver" | "admin";
  avatar_url?: string;
}

interface AuthState {
  token: string | null;
  user: AuthUser | null;
  setToken: (token: string) => void;
  setUser: (user: AuthUser) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setToken: (token) => set({ token }),
      setUser: (user) => set({ user }),
      logout: () => set({ token: null, user: null }),
    }),
    { name: "configsphere-auth", partialize: (s) => ({ token: s.token }) }
  )
);

// Role hierarchy helper
const ROLE_ORDER = { viewer: 0, operator: 1, approver: 2, admin: 3 };
export const hasRole = (user: AuthUser | null, min: AuthUser["role"]) =>
  user ? ROLE_ORDER[user.role] >= ROLE_ORDER[min] : false;
```

---

## 3. Axios Interceptors

Update `src/services/api.ts` to attach the JWT and handle token refresh automatically.

```ts
// src/services/api.ts
import axios from "axios";
import { useAuthStore } from "../stores/auth";

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL });
const authApi = axios.create({ baseURL: import.meta.env.VITE_AUTH_URL });

// Attach JWT to every config-server request
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// On 401, attempt a silent token refresh then retry once
let refreshing = false;
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401 && !refreshing) {
      refreshing = true;
      try {
        const { data } = await authApi.post("/oauth/refresh/", null, {
          withCredentials: true, // send httpOnly refresh_token cookie
        });
        useAuthStore.getState().setToken(data.access_token);
        error.config.headers.Authorization = `Bearer ${data.access_token}`;
        return api(error.config); // retry original request
      } catch {
        useAuthStore.getState().logout();
        window.location.href = "/login";
      } finally {
        refreshing = false;
      }
    }
    return Promise.reject(error);
  }
);

export { api, authApi };
```

---

## 4. New Pages & Routes

Add these routes to `src/App.tsx` / React Router config:

| Path | Component | Notes |
|------|-----------|-------|
| `/login` | `LoginPage` | "Sign in with Jira" button |
| `/auth/callback` | `AuthCallback` | Reads `?token=` from URL, stores, redirects to `/` |
| `/auth/error` | `AuthError` | Shows OAuth error reason |
| `/approvals` | `ApprovalsListPage` | Lists all pending approvals (Approver+) |
| `/approvals/:id` | `ApprovalDetailPage` | Approve / reject with comment (Approver+) |

All existing routes should be wrapped in a `<ProtectedRoute>` that redirects to `/login` if no token is present.

---

## 5. LoginPage

```tsx
// src/pages/LoginPage.tsx
export default function LoginPage() {
  const handleLogin = () => {
    // Let the browser follow the redirect chain naturally
    window.location.href = `${import.meta.env.VITE_AUTH_URL}/oauth/jira/login/`;
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", mt: 16 }}>
      <Typography variant="h4" gutterBottom>ConfigSphere</Typography>
      <Button variant="contained" size="large" onClick={handleLogin}>
        Sign in with Jira
      </Button>
    </Box>
  );
}
```

---

## 6. AuthCallback

```tsx
// src/pages/AuthCallback.tsx
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../stores/auth";
import { authApi } from "../services/api";

export default function AuthCallback() {
  const navigate = useNavigate();
  const { setToken, setUser } = useAuthStore();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    if (!token) { navigate("/auth/error?reason=no_token"); return; }

    setToken(token);

    // Fetch user profile to populate the auth store
    authApi.get("/users/me/", {
      headers: { Authorization: `Bearer ${token}` },
    }).then(({ data }) => {
      setUser(data);
      navigate("/");
    }).catch(() => navigate("/auth/error?reason=profile_fetch_failed"));
  }, []);

  return <CircularProgress />;
}
```

---

## 7. ProtectedRoute

```tsx
// src/components/ProtectedRoute.tsx
import { Navigate } from "react-router-dom";
import { useAuthStore, hasRole } from "../stores/auth";

interface Props {
  children: React.ReactNode;
  minRole?: "viewer" | "operator" | "approver" | "admin";
}

export default function ProtectedRoute({ children, minRole = "viewer" }: Props) {
  const { token, user } = useAuthStore();
  if (!token) return <Navigate to="/login" replace />;
  if (!hasRole(user, minRole)) return <Navigate to="/" replace />;
  return <>{children}</>;
}

// Usage in App.tsx:
// <Route path="/approvals" element={<ProtectedRoute minRole="approver"><ApprovalsListPage /></ProtectedRoute>} />
```

---

## 8. Role-Aware UI

Use the `hasRole()` helper to show/hide buttons based on the current user's role.

```tsx
// src/components/ConfigVersionActions.tsx
import { useAuthStore, hasRole } from "../stores/auth";

export default function ConfigVersionActions({ version, onRefresh }) {
  const { user } = useAuthStore();

  return (
    <Stack direction="row" spacing={1}>
      {/* Operator+ can validate and submit for approval */}
      {hasRole(user, "operator") && version.status === "draft" && (
        <Button onClick={() => handleValidate(version.id)}>Validate</Button>
      )}
      {hasRole(user, "operator") && version.status === "validated" && !version.approval && (
        <Button onClick={() => setSubmitDialogOpen(true)}>Submit for Approval</Button>
      )}

      {/* Approver+ can approve/reject and activate */}
      {hasRole(user, "approver") && version.approval?.status === "pending" && (
        <>
          <Button color="success" onClick={() => handleApprove(version.approval.id)}>Approve</Button>
          <Button color="error" onClick={() => handleReject(version.approval.id)}>Reject</Button>
        </>
      )}
      {hasRole(user, "approver") && version.approval?.status === "approved" && (
        <Button color="primary" onClick={() => handleActivate(version.id)}>Activate</Button>
      )}

      {/* Admin can delete */}
      {hasRole(user, "admin") && (
        <Button color="error" onClick={() => handleDelete(version.config_item)}>Delete Item</Button>
      )}
    </Stack>
  );
}
```

---

## 9. Submit for Approval Dialog

Add a dialog to the ConfigVersions page that lets Operators submit a version with optional notes.

```tsx
// Inside ConfigVersionsPage or a separate SubmitApprovalDialog component
const handleSubmitForApproval = async (versionId: number, notes: string) => {
  await api.post(`/config-versions/${versionId}/submit-for-approval/`, { notes });
  // Show success snackbar with Jira ticket link
  onRefresh();
};
```

Response includes `jira_issue_url` — show it as a clickable link so the approver can go directly to Jira.

---

## 10. Approval Status Badge

On the version detail view, show an inline badge with the current approval state.

```tsx
const STATUS_COLORS = {
  pending:  "warning",
  approved: "success",
  rejected: "error",
};

{version.approval && (
  <Chip
    label={`Approval: ${version.approval.status}`}
    color={STATUS_COLORS[version.approval.status]}
    size="small"
    component="a"
    href={version.approval.jira_issue_url}
    target="_blank"
    clickable={!!version.approval.jira_issue_url}
  />
)}
```

---

## 11. API Service Methods to Add

Add these to `src/services/api.ts`:

```ts
// Auth
export const getMe = () => authApi.get("/users/me/");
export const logout = () => authApi.post("/oauth/logout/", null, { withCredentials: true });

// Approvals
export const submitForApproval = (versionId: number, notes: string) =>
  api.post(`/config-versions/${versionId}/submit-for-approval/`, { notes });

export const getApproval = (versionId: number) =>
  api.get(`/config-versions/${versionId}/approval/`);

export const approveRequest = (approvalId: number, comment: string) =>
  api.post(`/approvals/${approvalId}/approve/`, { comment });

export const rejectRequest = (approvalId: number, comment: string) =>
  api.post(`/approvals/${approvalId}/reject/`, { comment });
```

---

## 12. TypeScript Types to Add

```ts
// src/types/index.ts — add these

export type ConfigSphereRole = "viewer" | "operator" | "approver" | "admin";
export type ApprovalStatus = "pending" | "approved" | "rejected";

export interface AuthUser {
  id: number;
  jira_account_id: string;
  email: string;
  display_name: string;
  avatar_url: string;
  configsphere_role: ConfigSphereRole;
  jira_groups: string[];
  jira_project_roles: string[];
}

export interface ApprovalRequest {
  id: number;
  config_version: number;
  jira_issue_key: string;
  jira_issue_url: string;
  status: ApprovalStatus;
  submitted_by: string;
  reviewed_by: string;
  submission_notes: string;
  review_comment: string;
  submitted_at: string;
  reviewed_at: string | null;
}
```

---

## 13. TopBar Updates

- Add avatar + display name (from `useAuthStore().user`) to the top right
- Add a logout button that calls `POST /oauth/logout/` then clears the store and redirects to `/login`
- Show a role badge next to the user's name

---

## Implementation Order

```
1. src/stores/auth.ts              — Zustand auth store + hasRole helper
2. src/services/api.ts             — interceptors, auth API methods, approval API methods
3. src/types/index.ts              — AuthUser, ApprovalRequest types
4. src/pages/LoginPage.tsx         — Jira login button
5. src/pages/AuthCallback.tsx      — token extraction + /me fetch
6. src/components/ProtectedRoute.tsx — role-aware route guard
7. src/App.tsx                     — add /login, /auth/callback, /auth/error routes + wrap existing routes
8. src/components/TopBar.tsx       — avatar, display name, logout
9. src/pages/ConfigVersions.tsx    — submit-for-approval button + approval status badge
10. src/pages/ApprovalsListPage.tsx — list pending approvals (Approver+)
11. src/pages/ApprovalDetailPage.tsx — approve/reject with comment
```
