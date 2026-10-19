interface StatusBadgeProps {
  status: string;
}

export default function StatusBadge({
  status,
}: StatusBadgeProps) {
  const normalized = status.toLowerCase();

  const className =
    normalized === "approved" ||
    normalized === "resolved" ||
    normalized === "succeeded" ||
    normalized === "evaluated"
      ? "status-badge status-success"
      : normalized === "rejected" ||
          normalized === "failed" ||
          normalized === "cancelled"
        ? "status-badge status-danger"
        : normalized === "needs_review" ||
            normalized === "correction_requested"
          ? "status-badge status-warning"
          : "status-badge status-neutral";

  const label = status.replaceAll("_", " ");

  return (
    <span className={className}>
      {label}
    </span>
  );
}