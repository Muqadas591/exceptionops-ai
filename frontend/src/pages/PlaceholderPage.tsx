interface PlaceholderPageProps {
  title: string;
  description: string;
  phase: string;
}

export default function PlaceholderPage({
  title,
  description,
  phase,
}: PlaceholderPageProps) {
  return (
    <main className="page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">
            APPLICATION MODULE
          </p>

          <h2>{title}</h2>

          <p className="muted">
            {description}
          </p>
        </div>
      </div>

      <section className="panel placeholder-panel">
        <div className="placeholder-icon">
          ◇
        </div>

        <h3>Module implementation in progress</h3>

        <p className="muted">
          This module is scheduled for {phase}.
          Its interface will be connected to the
          existing backend APIs before it is presented
          as a completed feature.
        </p>
      </section>
    </main>
  );
}