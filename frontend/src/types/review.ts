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

export type ReviewStatusFilter =
  | ""
  | ReviewStatus;

export interface ReviewQueueResponse {
  items: HumanReview[];
  total: number;
  limit: number;
  offset: number;
  hasMore: boolean;
}

export interface ReviewActionPayload {
  note: string;
}