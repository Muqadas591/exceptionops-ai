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

export type ReconciliationOutcome =
  | "confirmed_succeeded"
  | "confirmed_not_executed";

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

export interface CreateActionRequest {
  action_type: ActionType;
  recipient?: string;
  subject?: string;
  message?: string;
}

export interface ReconcileActionRequest {
  outcome: ReconciliationOutcome;
  note: string;
}