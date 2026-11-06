interface ServiceHealthCardProps {
  title: string;
  status: "healthy" | "unavailable" | "checking";
  description: string;
}

export default function ServiceHealthCard({
  title,
  status,
  description,
}: ServiceHealthCardProps) {
  const statusLabel = {
    healthy: "Operational",
    unavailable: "Unavailable",
    checking: "Checking",
  }[status];

  return (
    <article className="service-health-card">
      <div className="service-health-heading">
        <div>
          <strong>{title}</strong>
          <p>{description}</p>
        </div>

        <span className={`health-pill health-${status}`}>
          <span className="health-dot" />
          {statusLabel}
        </span>
      </div>
    </article>
  );
}