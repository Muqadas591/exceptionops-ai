export type ReviewStatus =
  | "pending"
  | "correction_requested"
  | "approved"
  | "rejected";

export type WorkflowStatus =
  | "received"
  | "extracted"
  | "evaluated"
  | "needs_review"
  | "resolved"
  | "failed"
  | "cancelled";

export type ActionType =
  | "email_draft"
  | "accounting_simulation"
  | "webhook_simulation";

export type ActionStatus = "pending" | "succeeded" | "failed";

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

export interface ExtractionField {
  value: unknown;
  confidence?: number | null;
  evidence?: string | null;
}

export interface ExtractionResult {
  id: number;
  document_id: number;
  fields: Record<string, ExtractionField | unknown>;
  created_at?: string;
  updated_at?: string;
}

export interface BusinessFinding {
  code?: string;
  rule?: string;
  severity?: string;
  message?: string;
  field?: string;
  [key: string]: unknown;
}

export interface BusinessEvaluation {
  id: number;
  document_id: number;
  decision: string;
  risk_score: number;
  rules_version: string;
  findings: BusinessFinding[];
  summary: string;
  created_at?: string;
  updated_at?: string;
}

export interface ActionExecution {
  id: number;
  review_id: number;
  action_type: ActionType;
  status: ActionStatus;
  attempt_count: number;
  request_payload: Record<string, unknown>;
  result_payload: Record<string, unknown> | null;
  last_error: string | null;
  executed_by: string;
  created_at: string;
  updated_at: string;
}

export interface ActionRequest {
  action_type: ActionType;
  recipient?: string;
  subject?: string;
  message?: string;
}

export interface AuthTokens {
  reviewerToken: string;
  actionToken: string;
}