import type { ActionStatus } from "../../types/action";

interface Props {
  status: ActionStatus;
}

const labels: Record<ActionStatus, string> = {
  pending: "Pending",
  in_progress: "In progress",
  succeeded: "Succeeded",
  failed: "Failed",
  uncertain: "Needs reconciliation",
};

export default function ActionStatusBadge({ status }: Props) {
  return (
    <span className={`action-status action-status-${status}`}>
      {labels[status]}
    </span>
  );
}