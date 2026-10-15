// TypeScript types mirroring the FastAPI OpenAPI schemas (snake_case fields).

export type ID = number;

export interface Page<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface MessageResponse {
  success: boolean;
  message: string;
}

export interface ForgotPasswordResponseShape {
  success?: boolean;
  message: string;
  /** Only present in debug mode (no SMTP configured). */
  reset_token?: string | null;
}

export interface ApiErrorShape {
  success: false;
  error: { code: string; message: string; details?: unknown };
}

// ---------------------------------------------------------------- auth
export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface RoleBrief {
  id: ID;
  name: string;
  code: string;
}

export interface StudentProfile {
  id: ID;
  user_id: ID;
  student_code: string | null;
  date_of_birth: string | null;
  gender: string | null;
  institution: string | null;
  class: string | null;
  roll_number: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface MeResponse {
  id: ID;
  username: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  mobile: string | null;
  status: string;
  is_verified: boolean;
  last_login_at: string | null;
  created_at?: string | null;
  roles: RoleBrief[];
  permissions: string[];
  student_profile: StudentProfile | null;
}

// ---------------------------------------------------------------- users
export interface UserResponse {
  id: ID;
  username: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  mobile: string | null;
  status: string;
  is_verified: boolean;
  last_login_at: string | null;
  created_at: string | null;
  updated_at: string | null;
  roles: RoleBrief[];
  student_profile: StudentProfile | null;
}

export interface UserCreate {
  username: string;
  email: string;
  password: string;
  first_name?: string | null;
  last_name?: string | null;
  mobile?: string | null;
  status?: string;
  is_verified?: boolean;
  role_ids?: number[];
  student_profile?: Record<string, unknown> | null;
}

export interface UserPermissionsResponse {
  user_id: ID;
  permissions: string[];
  roles: RoleBrief[];
}

// ---------------------------------------------------------------- roles
export interface PermissionResponse {
  id: ID;
  name: string;
  code: string;
  module: string;
  action: string;
  description: string | null;
}

export interface RoleResponse {
  id: ID;
  name: string;
  code: string;
  description: string | null;
  is_system_role: boolean;
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
  permissions: PermissionResponse[];
}

export interface RoleCreate {
  name: string;
  code: string;
  description?: string | null;
  is_active?: boolean;
  permission_ids?: number[];
}

// ---------------------------------------------------------------- exams
export interface ExamResponse {
  id: ID;
  name: string;
  code: string;
  description: string | null;
  exam_type: string;
  status: string;
  duration_minutes: number | null;
  passing_percentage: number | null;
  start_at: string | null;
  end_at: string | null;
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
}

// ---------------------------------------------------------------- subjects
export interface SubjectResponse {
  id: ID;
  exam_id: ID;
  name: string;
  code: string;
  description: string | null;
  sort_order: number;
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
}

// ---------------------------------------------------------------- topics
export interface TopicResponse {
  id: ID;
  subject_id: ID;
  parent_topic_id: number | null;
  name: string;
  description: string | null;
  sort_order: number;
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
}

// ---------------------------------------------------------------- questions
export interface OptionResponse {
  id: ID;
  question_id: ID;
  option_text: string;
  option_order: number;
  is_correct: boolean;
}

export interface QuestionResponse {
  id: ID;
  subject_id: ID;
  topic_id: number | null;
  question_type: string;
  question_text: string;
  explanation: string | null;
  difficulty: string;
  marks: number;
  negative_marks: number;
  status: string;
  source: string | null;
  created_at: string | null;
  updated_at: string | null;
  options: OptionResponse[];
}

export interface OptionInput {
  id?: number;
  option_text: string;
  option_order?: number | null;
  is_correct?: boolean;
}

export interface QuestionCreate {
  subject_id: ID;
  topic_id?: number | null;
  question_type: string;
  question_text: string;
  explanation?: string | null;
  difficulty?: string;
  marks?: number;
  negative_marks?: number;
  status?: string;
  source?: string | null;
  options?: OptionInput[];
}

export interface QuestionImportRequest {
  questions: Array<Omit<QuestionCreate, "status" | "source">>;
}

export interface QuestionImportResponse {
  imported: number;
  failed: number;
  errors: string[];
}

// ---------------------------------------------------------------- notifications
export interface NotificationResponse {
  id: ID;
  user_id: ID;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  created_at: string | null;
}

export interface UnreadCountResponse {
  count: number;
}

export interface NotificationCreate {
  user_id: ID;
  title: string;
  message: string;
  type?: string;
}

export interface NotificationBulkCreate {
  user_ids?: number[];
  title: string;
  message: string;
  type?: string;
}

// ---------------------------------------------------------------- audit
export interface AuditLogResponse {
  id: ID;
  user_id: number | null;
  username: string | null;
  module: string;
  action: string;
  entity_type: string | null;
  entity_id: number | null;
  old_data: unknown;
  new_data: unknown;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string | null;
}

// ---------------------------------------------------------------- settings
export interface SettingResponse {
  id: ID;
  setting_key: string;
  setting_value: string | null;
  description: string | null;
  is_public: boolean;
  updated_by: number | null;
  updated_at: string | null;
}

export interface PermissionModuleResponse {
  module: string;
  permissions: PermissionResponse[];
}
