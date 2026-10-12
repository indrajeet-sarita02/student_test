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

export interface OptionPublic {
  id: ID;
  option_text: string;
  option_order: number;
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

// ---------------------------------------------------------------- tests
export interface TestResponse {
  id: ID;
  exam_id: ID;
  name: string;
  code: string;
  description: string | null;
  instructions: string | null;
  duration_minutes: number;
  total_marks: number;
  passing_marks: number | null;
  negative_marking_enabled: boolean;
  negative_marks: number;
  randomize_questions: boolean;
  randomize_options: boolean;
  max_attempts: number;
  status: string;
  scheduled_start_at: string | null;
  scheduled_end_at: string | null;
  created_at: string | null;
  updated_at: string | null;
  question_count: number;
  assigned_count: number;
}

export interface TestBrief {
  id: ID;
  exam_id: ID;
  name: string;
  code: string;
  duration_minutes: number;
  total_marks: number;
  passing_marks: number | null;
  status: string;
  scheduled_start_at: string | null;
  scheduled_end_at: string | null;
  instructions: string | null;
}

export interface TestQuestionResponse {
  id: ID;
  test_id: ID;
  question_id: ID;
  question_order: number;
  marks_override: number | null;
  negative_marks_override: number | null;
  question_text: string | null;
  question_type: string | null;
  subject_id: number | null;
  difficulty: string | null;
}

export interface TestImportResponse {
  test_id: ID;
  test_code: string;
  name: string;
  status: string;
  questions_created: number;
  subjects_created: number;
  topics_created: number;
  total_marks: number;
}

// ---------------------------------------------------------------- assignments
export interface AssignmentResponse {
  id: ID;
  test_id: ID;
  student_id: ID;
  assigned_at: string | null;
  available_from: string | null;
  available_until: string | null;
  max_attempts: number | null;
  status: string;
  created_at: string | null;
  updated_at: string | null;
  test_name: string | null;
  student_name: string | null;
  student_email: string | null;
}

// ---------------------------------------------------------------- attempts
export interface AttemptResponse {
  id: ID;
  test_id: ID;
  student_id: ID;
  attempt_number: number;
  started_at: string | null;
  submitted_at: string | null;
  expires_at: string | null;
  status: string;
  score: number | null;
  max_score: number | null;
  percentage: number | null;
  submission_type: string | null;
  created_at: string | null;
  test_name: string | null;
  student_name: string | null;
}

export interface AttemptAnswerAdminResponse {
  id: ID;
  question_id: ID;
  question_text: string | null;
  selected_option_id: number | null;
  selected_option_ids: number[] | null;
  selected_option_text: string | null;
  answer_text: string | null;
  numerical_answer: string | null;
  is_marked_for_review: boolean;
  answered_at: string | null;
  is_correct: boolean | null;
  marks_awarded: number | null;
}

export interface AttemptDetailResponse {
  attempt: AttemptResponse;
  answers: AttemptAnswerAdminResponse[];
  result: ResultResponse | null;
}

// ---------------------------------------------------------------- student
export interface StudentQuestionView {
  id: ID;
  subject_id: ID;
  topic_id: number | null;
  question_type: string;
  question_text: string;
  difficulty: string;
  marks: number;
  negative_marks: number;
  options: OptionPublic[];
}

export interface StudentTestItem {
  test: TestBrief;
  assignment_id: ID;
  assignment_status: string;
  available_from: string | null;
  available_until: string | null;
  max_attempts: number | null;
  attempts_used: number;
  attempts_remaining: number;
  can_attempt: boolean;
  last_attempt_id: number | null;
  last_attempt_status: string | null;
  best_percentage: number | null;
  unavailable_reason: string | null;
}

export interface StudentAttemptAnswer {
  question_id: ID;
  selected_option_id: number | null;
  selected_option_ids: number[] | null;
  answer_text: string | null;
  numerical_answer: string | null;
  is_marked_for_review: boolean;
  answered_at: string | null;
}

export interface StartAttemptResponse {
  attempt: AttemptResponse;
  test: TestBrief;
  questions: StudentQuestionView[];
}

export interface StudentAttemptResponse {
  attempt: AttemptResponse;
  test: TestBrief;
  questions: StudentQuestionView[];
  answers: StudentAttemptAnswer[];
  remaining_seconds: number | null;
}

export interface AnswerItem {
  question_id: ID;
  selected_option_id?: number | null;
  selected_option_ids?: number[] | null;
  answer_text?: string | null;
  numerical_answer?: string | null;
  is_marked_for_review?: boolean;
}

export interface SaveAnswersResponse {
  attempt_id: ID;
  saved: number;
  answered_count: number;
  remaining_count: number;
  expires_at: string | null;
}

export interface SubmitAttemptResponse {
  attempt: AttemptResponse;
  result_id: number | null;
  score: number;
  max_score: number;
  percentage: number;
  pass_status: boolean;
  status: string;
}

// ---------------------------------------------------------------- results
export interface ResultResponse {
  id: ID;
  attempt_id: ID;
  student_id: ID;
  test_id: ID;
  score: number;
  max_score: number;
  percentage: number;
  correct_count: number;
  incorrect_count: number;
  unanswered_count: number;
  rank: number | null;
  percentile: number | null;
  pass_status: boolean;
  published_at: string | null;
  created_at: string | null;
  test_name: string | null;
  student_name: string | null;
  attempt_number: number | null;
}

export interface ReviewAnswer {
  question_id: ID;
  question_text: string;
  question_type: string;
  your_answer: string | null;
  correct_answer: string | null;
  is_correct: boolean | null;
  marks_awarded: number;
  marks_possible: number;
  explanation: string | null;
  options: Array<Record<string, unknown>>;
}

export interface ResultReviewResponse {
  result: ResultResponse;
  answers: ReviewAnswer[];
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

// ---------------------------------------------------------------- reports
export interface DashboardReport {
  total_users: number;
  total_students: number;
  total_exams: number;
  total_tests: number;
  total_questions: number;
  published_tests: number;
  total_attempts: number;
  active_attempts: number;
  total_results: number;
  average_percentage: number | null;
  pass_rate: number | null;
}

export interface ExamReportRow {
  exam_id: ID;
  exam_name: string;
  exam_code: string;
  status: string;
  subject_count: number;
  question_count: number;
  test_count: number;
  attempt_count: number;
  average_percentage: number | null;
}

export interface TestReportRow {
  test_id: ID;
  test_name: string;
  test_code: string;
  exam_id: ID;
  exam_name: string | null;
  status: string;
  question_count: number;
  assigned_count: number;
  attempt_count: number;
  evaluated_count: number;
  average_percentage: number | null;
  highest_percentage: number | null;
  lowest_percentage: number | null;
  pass_rate: number | null;
}

export interface QuestionReportRow {
  question_id: ID;
  subject_id: ID;
  subject_name: string | null;
  question_type: string;
  difficulty: string;
  status: string;
  times_used: number;
  times_answered: number;
  correct_count: number;
  incorrect_count: number;
  unattempted_count: number;
  accuracy: number | null;
}

export interface SubjectReportRow {
  subject_id: ID;
  subject_name: string;
  exam_id: ID;
  exam_name: string | null;
  question_count: number;
  topic_count: number;
  attempt_count: number;
  average_percentage: number | null;
  accuracy: number | null;
}

export interface StudentReportRow {
  student_id: ID;
  student_name: string;
  username: string;
  tests_assigned: number;
  attempts_taken: number;
  tests_completed: number;
  average_percentage: number | null;
  best_percentage: number | null;
  average_score: number | null;
  rank: number | null;
}

export interface PermissionModuleResponse {
  module: string;
  permissions: PermissionResponse[];
}
