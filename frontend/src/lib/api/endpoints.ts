"use client";

// One typed function per backend endpoint. Keeps UI code free of raw paths.

import { api, qs } from "@/lib/api/client";
import type {
  AuditLogResponse,
  ExamResponse,
  MessageResponse,
  MeResponse,
  NotificationBulkCreate,
  NotificationCreate,
  NotificationResponse,
  Page,
  PermissionModuleResponse,
  PermissionResponse,
  QuestionImportRequest,
  QuestionImportResponse,
  QuestionResponse,
  RoleResponse,
  SettingResponse,
  SubjectResponse,
  TokenResponse,
  TopicResponse,
  UnreadCountResponse,
  UserPermissionsResponse,
  UserResponse,
  ForgotPasswordResponseShape,
} from "@/lib/types";

type Dict = Record<string, unknown>;
type PageParams = Dict;

// ------------------------------------------------------------------ auth
export const authApi = {
  login: (username: string, password: string) =>
    api.post<TokenResponse>("/auth/login", { username, password }, { skipAuth: true }),
  refresh: (refresh_token: string) =>
    api.post<TokenResponse>("/auth/refresh", { refresh_token }, { skipAuth: true, skipRefresh: true }),
  logout: () => api.post<MessageResponse>("/auth/logout"),
  me: () => api.get<MeResponse>("/auth/me"),
  changePassword: (current_password: string, new_password: string) =>
    api.post<MessageResponse>("/auth/change-password", { current_password, new_password }),
  forgotPassword: (email: string) =>
    api.post<ForgotPasswordResponseShape>("/auth/forgot-password", { email }, { skipAuth: true }),
  resetPassword: (token: string, new_password: string) =>
    api.post<MessageResponse>("/auth/reset-password", { token, new_password }, { skipAuth: true }),
};

// ------------------------------------------------------------------ users
export const usersApi = {
  list: (params: PageParams = {}) => api.get<Page<UserResponse>>(`/users/${qs(params)}`),
  create: (body: Dict) => api.post<UserResponse>("/users/", body),
  get: (id: number) => api.get<UserResponse>(`/users/${id}`),
  update: (id: number, body: Dict) => api.put<UserResponse>(`/users/${id}`, body),
  remove: (id: number) => api.delete<void>(`/users/${id}`),
  setStatus: (id: number, status: string) =>
    api.patch<UserResponse>(`/users/${id}/status`, { status }),
  assignRoles: (id: number, role_ids: number[]) =>
    api.post<UserResponse>(`/users/${id}/roles`, { role_ids }),
  permissions: (id: number) =>
    api.get<UserPermissionsResponse>(`/users/${id}/permissions`),
};

// ------------------------------------------------------------------ roles
export const rolesApi = {
  list: (params: PageParams = {}) => api.get<Page<RoleResponse>>(`/roles/${qs(params)}`),
  create: (body: Dict) => api.post<RoleResponse>("/roles/", body),
  get: (id: number) => api.get<RoleResponse>(`/roles/${id}`),
  update: (id: number, body: Dict) => api.put<RoleResponse>(`/roles/${id}`, body),
  remove: (id: number) => api.delete<void>(`/roles/${id}`),
  setPermissions: (id: number, permission_ids: number[]) =>
    api.put<RoleResponse>(`/roles/${id}/permissions`, { permission_ids }),
};

// ------------------------------------------------------------------ permissions
export const permissionsApi = {
  list: () => api.get<PermissionResponse[]>("/permissions/"),
  modules: () => api.get<PermissionModuleResponse[]>("/permissions/modules"),
};

// ------------------------------------------------------------------ exams
export const examsApi = {
  list: (params: PageParams = {}) => api.get<Page<ExamResponse>>(`/exams/${qs(params)}`),
  create: (body: Dict) => api.post<ExamResponse>("/exams/", body),
  get: (id: number) => api.get<ExamResponse>(`/exams/${id}`),
  update: (id: number, body: Dict) => api.put<ExamResponse>(`/exams/${id}`, body),
  remove: (id: number) => api.delete<void>(`/exams/${id}`),
  publish: (id: number) => api.post<ExamResponse>(`/exams/${id}/publish`),
  archive: (id: number) => api.post<ExamResponse>(`/exams/${id}/archive`),
};

// ------------------------------------------------------------------ subjects
export const subjectsApi = {
  list: (params: PageParams = {}) => api.get<Page<SubjectResponse>>(`/subjects/${qs(params)}`),
  create: (body: Dict) => api.post<SubjectResponse>("/subjects/", body),
  get: (id: number) => api.get<SubjectResponse>(`/subjects/${id}`),
  update: (id: number, body: Dict) => api.put<SubjectResponse>(`/subjects/${id}`, body),
  remove: (id: number) => api.delete<void>(`/subjects/${id}`),
};

// ------------------------------------------------------------------ topics
export const topicsApi = {
  list: (params: PageParams = {}) => api.get<Page<TopicResponse>>(`/topics/${qs(params)}`),
  create: (body: Dict) => api.post<TopicResponse>("/topics/", body),
  get: (id: number) => api.get<TopicResponse>(`/topics/${id}`),
  update: (id: number, body: Dict) => api.put<TopicResponse>(`/topics/${id}`, body),
  remove: (id: number) => api.delete<void>(`/topics/${id}`),
};

// ------------------------------------------------------------------ questions
export const questionsApi = {
  list: (params: PageParams = {}) =>
    api.get<Page<QuestionResponse>>(`/questions/${qs(params)}`),
  create: (body: Dict) => api.post<QuestionResponse>("/questions/", body),
  get: (id: number) => api.get<QuestionResponse>(`/questions/${id}`),
  update: (id: number, body: Dict) => api.put<QuestionResponse>(`/questions/${id}`, body),
  remove: (id: number) => api.delete<void>(`/questions/${id}`),
  publish: (id: number) => api.post<QuestionResponse>(`/questions/${id}/publish`),
  import: (body: QuestionImportRequest) =>
    api.post<QuestionImportResponse>("/questions/import", body),
};

// ------------------------------------------------------------------ notifications
export const notificationsApi = {
  list: (params: PageParams = {}) =>
    api.get<Page<NotificationResponse>>(`/notifications/${qs(params)}`),
  create: (body: NotificationCreate) =>
    api.post<NotificationResponse>("/notifications/", body),
  bulk: (body: NotificationBulkCreate) =>
    api.post<{ created: number; skipped: number }>("/notifications/bulk", body),
  unreadCount: () => api.get<UnreadCountResponse>("/notifications/unread-count"),
  markRead: (id: number) =>
    api.patch<NotificationResponse>(`/notifications/${id}/read`),
  readAll: () => api.patch<{ updated: number }>("/notifications/read-all"),
};

// ------------------------------------------------------------------ audit logs
export const auditLogsApi = {
  list: (params: PageParams = {}) =>
    api.get<Page<AuditLogResponse>>(`/audit-logs/${qs(params)}`),
  get: (id: number) => api.get<AuditLogResponse>(`/audit-logs/${id}`),
};

// ------------------------------------------------------------------ settings
export const settingsApi = {
  list: () => api.get<SettingResponse[]>("/settings/"),
  public: () => api.get<SettingResponse[]>("/settings/public"),
  get: (key: string) => api.get<SettingResponse>(`/settings/${encodeURIComponent(key)}`),
  update: (key: string, body: Dict) =>
    api.put<SettingResponse>(`/settings/${encodeURIComponent(key)}`, body),
  remove: (key: string) => api.delete<void>(`/settings/${encodeURIComponent(key)}`),
};
