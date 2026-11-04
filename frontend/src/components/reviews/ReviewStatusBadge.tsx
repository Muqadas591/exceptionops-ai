import type { ReviewStatus } from "../../types/review";

interface ReviewStatusBadgeProps {
  status: ReviewStatus;
}

const labels: Record<ReviewStatus, string> = {
  pending: "Pending",
  correction_requested: "Correction requested",
  approved: "Approved",
  rejected: "Rejected",
};

export default function ReviewStatusBadge({
  status,
}: ReviewStatusBadgeProps) {
  return (
    <span className={`review-status-badge review-status-${status}`}>
      {labels[status]}
    </span>
  );
}