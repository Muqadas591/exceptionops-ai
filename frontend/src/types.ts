export type UserRole =
  | "admin"
  | "reviewer"
  | "action_operator";

export interface User {
  id: number;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface Document {
  id: number;
  original_filename: string;
  extension: string;
  content_type: string;
  file_size_bytes: number;
  checksum_sha256: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export type WorkflowStatus =
  | "received"
  | "extracted"
  | "evaluated"
  | "needs_review"
  | "resolved"
  | "failed"
  | "cancelled";

export interface WorkflowEvent {
  id: number;
  workflow_run_id: number;
  event_type: string;
  from_status: string | null;
  to_status: string | null;
  message: string;
  event_metadata: Record<string, unknown>;
  created_at: string;
}

export interface WorkflowRun {
  id: number;
  document_id: number;
  status: WorkflowStatus;
  idempotency_key: string | null;
  attempt_count: number;
  last_error: string | null;
  resolution_note: string | null;
  created_at: string;
  updated_at: string;
  events: WorkflowEvent[];
}

export interface ExtractedField {
  value?: string | null;
  confidence?: number;
  evidence?: string | null;
  [key: string]: unknown;
}

export interface ExtractionResult {
  id: number;
  document_id: number;
  provider_name: string;
  status: string;
  fields: Record<string, ExtractedField>;
  extracted_text_length: number;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export type EvaluationDecision =
  | "ready_for_matching"
  | "needs_review"
  | "blocked";

export interface BusinessFinding {
  rule_code?: string;
  severity?: "info" | "low" | "medium" | "high" | "critical";
  message?: string;
  field?: string | null;
  [key: string]: unknown;
}

export interface BusinessEvaluation {
  id: number;
  document_id: number;
  decision: EvaluationDecision;
  risk_score: number;
  rules_version: string;
  findings: BusinessFinding[];
  summary: string;
  created_at: string;
  updated_at: string;
}

export type ReviewStatus =
  | "pending"
  | "correction_requested"
  | "approved"
  | "rejected";

export interface ReviewComment {
  id: number;
  review_id: number;
  author: string;
  comment_type: string;
  body: string;
  created_at: string;
}

export interface HumanReview {
  id: number;
  workflow_run_id: number;
  assigned_to: string | null;
  status: ReviewStatus;
  decision_note: string | null;
  decided_by: string | null;
  created_at: string;
  updated_at: string;
  comments: ReviewComment[];
}

export type ActionType =
  | "email_draft"
  | "accounting_simulation"
  | "webhook_simulation";

export type ActionStatus =
  | "pending"
  | "in_progress"
  | "succeeded"
  | "failed"
  | "uncertain";

export interface ActionExecution {
  id: number;
  review_id: number;
  action_type: ActionType;
  status: ActionStatus;
  attempt_count: number;
  idempotency_key: string;
  request_fingerprint: string;
  request_payload: Record<string, unknown>;
  result_payload: Record<string, unknown> | null;
  last_error: string | null;
  executed_by: string;
  created_at: string;
  updated_at: string;
}

export interface HealthResponse {
  status: string;
  app_name: string;
  environment: string;
}

export interface ReadinessResponse {
  status: string;
  database: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number | null;
  limit: number;
  offset: number;
  hasMore: boolean | null;
}
export interface AuditEvent {
  id: number;

  event_type: string;
  entity_type: string;
  entity_id: string | null;

  document_id: number | null;
  workflow_run_id: number | null;
  review_id: number | null;
  action_id: number | null;

  actor_type: string;
  actor_id: string | null;

  description: string;
  event_metadata: Record<string, unknown> | null;

  created_at: string;
  updated_at: string;
}

export interface AuditEventFilters {
  event_type?: string;
  entity_type?: string;
  actor_id?: string;
  document_id?: number;
  workflow_run_id?: number;
  review_id?: number;
  action_id?: number;
  search?: string;
  from_datetime?: string;
  to_datetime?: string;
  limit?: number;
  offset?: number;
}