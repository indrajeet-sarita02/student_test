"use client";

// One typed function per backend endpoint. Keeps UI code free of raw paths.

import { api, qs } from "@/lib/api/client";
import type {
  AnswerItem,
  AssignmentResponse,
  AttemptAnswerAdminResponse,
  AttemptDetailResponse,
  AttemptResponse,
  AuditLogResponse,
  DashboardReport,
  ExamReportRow,
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
  QuestionReportRow,
  QuestionResponse,
  ResultResponse,
  ResultReviewResponse,
  RoleResponse,
  SaveAnswersResponse,
  SettingResponse,
  StartAttemptResponse,
  StudentAttemptResponse,
  StudentReportRow,
  StudentTestItem,
  SubjectReportRow,
  SubjectResponse,
  SubmitAttemptResponse,
  TestImportResponse,
  TestQuestionResponse,
  TestReportRow,
  TestResponse,
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

// ------------------------------------------------------------------ tests
export const testsApi = {
  list: (params: PageParams = {}) => api.get<Page<TestResponse>>(`/tests/${qs(params)}`),
  create: (body: Dict) => api.post<TestResponse>("/tests/", body),
  get: (id: number) => api.get<TestResponse>(`/tests/${id}`),
  update: (id: number, body: Dict) => api.put<TestResponse>(`/tests/${id}`, body),
  remove: (id: number) => api.delete<void>(`/tests/${id}`),
  publish: (id: number) => api.post<TestResponse>(`/tests/${id}/publish`),
  close: (id: number) => api.post<TestResponse>(`/tests/${id}/close`),
  questions: (id: number) =>
    api.get<TestQuestionResponse[]>(`/tests/${id}/questions`),
  addQuestion: (id: number, body: Dict) =>
    api.post<TestQuestionResponse>(`/tests/${id}/questions`, body),
  bulkAddQuestions: (id: number, question_ids: number[], start_order?: number) =>
    api.post<TestQuestionResponse[]>(`/tests/${id}/questions/bulk`, {
      question_ids,
      start_order,
    }),
  removeQuestion: (id: number, questionId: number) =>
    api.delete<void>(`/tests/${id}/questions/${questionId}`),
  importXlsx: (form: FormData) =>
    api.post<TestImportResponse>("/tests/import", form),
  importTemplate: () => api.download("/tests/import/template"),
};

// ------------------------------------------------------------------ assignments
export const assignmentsApi = {
  list: (params: PageParams = {}) =>
    api.get<Page<AssignmentResponse>>(`/assignments/${qs(params)}`),
  create: (body: Dict) => api.post<AssignmentResponse>("/assignments/", body),
  get: (id: number) => api.get<AssignmentResponse>(`/assignments/${id}`),
  remove: (id: number) => api.delete<void>(`/assignments/${id}`),
  bulk: (body: Dict) =>
    api.post<{ created: number; skipped: number; assignments: AssignmentResponse[] }>(
      "/assignments/bulk",
      body
    ),
};

// ------------------------------------------------------------------ attempts (admin)
export const attemptsApi = {
  list: (params: PageParams = {}) =>
    api.get<Page<AttemptResponse>>(`/attempts/${qs(params)}`),
  get: (id: number) => api.get<AttemptDetailResponse>(`/attempts/${id}`),
  answers: (id: number) =>
    api.get<AttemptAnswerAdminResponse[]>(`/attempts/${id}/answers`),
};

// ------------------------------------------------------------------ results (admin)
export const resultsApi = {
  list: (params: PageParams = {}) =>
    api.get<Page<ResultResponse>>(`/results/${qs(params)}`),
  get: (id: number) => api.get<ResultResponse>(`/results/${id}`),
  publish: (id: number) => api.post<ResultResponse>(`/results/${id}/publish`),
  exportCsv: (params: PageParams = {}) => api.download(`/results/export${qs(params)}`),
};

// ------------------------------------------------------------------ reports
export const reportsApi = {
  dashboard: () => api.get<DashboardReport>("/reports/dashboard"),
  exams: () => api.get<ExamReportRow[]>("/reports/exams"),
  tests: (exam_id?: number) =>
    api.get<TestReportRow[]>(`/reports/tests${qs({ exam_id })}`),
  questions: (subject_id?: number) =>
    api.get<QuestionReportRow[]>(`/reports/questions${qs({ subject_id })}`),
  subjects: (exam_id?: number) =>
    api.get<SubjectReportRow[]>(`/reports/subjects${qs({ exam_id })}`),
  student: (student_id: number) =>
    api.get<StudentReportRow>(`/reports/students/${student_id}`),
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

// ------------------------------------------------------------------ student
export const studentApi = {
  tests: (search?: string) =>
    api.get<StudentTestItem[]>(`/student/tests${qs({ search })}`),
  test: (id: number) => api.get<StudentTestItem>(`/student/tests/${id}`),
  start: (id: number) => api.post<StartAttemptResponse>(`/student/tests/${id}/start`),
  attempts: (params: PageParams = {}) =>
    api.get<Page<AttemptResponse>>(`/student/attempts${qs(params)}`),
  attempt: (id: number) => api.get<StudentAttemptResponse>(`/student/attempts/${id}`),
  saveAnswers: (id: number, answers: AnswerItem[]) =>
    api.put<SaveAnswersResponse>(`/student/attempts/${id}/answers`, { answers }),
  submit: (id: number) => api.post<SubmitAttemptResponse>(`/student/attempts/${id}/submit`),
  results: (params: PageParams = {}) =>
    api.get<Page<ResultResponse>>(`/student/results${qs(params)}`),
  review: (resultId: number) =>
    api.get<ResultReviewResponse>(`/student/results/${resultId}/review`),
};
