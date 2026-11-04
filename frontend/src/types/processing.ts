export interface ExtractedField {
  value: string | null;
  confidence: number;
  evidence: string | null;
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

export type FindingSeverity =
  | "info"
  | "low"
  | "medium"
  | "high"
  | "critical";

export interface BusinessFinding {
  rule_code: string;
  severity: FindingSeverity;
  message: string;
  field: string | null;
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