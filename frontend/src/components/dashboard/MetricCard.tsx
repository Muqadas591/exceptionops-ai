interface MetricCardProps {
  label: string;
  value: number | string;
  description: string;
  icon: string;
  tone?: "blue" | "green" | "amber" | "red";
  loading?: boolean;
}

export default function MetricCard({
  label,
  value,
  description,
  icon,
  tone = "blue",
  loading = false,
}: MetricCardProps) {
  return (
    <article className={`metric-card metric-${tone}`}>
      <div className="metric-top">
        <span className="metric-icon">{icon}</span>

        <span className="metric-label">
          {label}
        </span>
      </div>

      <strong className="metric-value">
        {loading ? "—" : value}
      </strong>

      <p>{description}</p>
    </article>
  );
}