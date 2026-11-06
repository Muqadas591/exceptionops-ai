const stages = [
  {
    number: "01",
    title: "Invoice intake",
    description:
      "Receive and store supplier invoice documents.",
    detail: "Document ingestion",
  },
  {
    number: "02",
    title: "Data extraction",
    description:
      "Extract relevant invoice information and evidence.",
    detail: "Extraction service",
  },
  {
    number: "03",
    title: "Business validation",
    description:
      "Evaluate invoice data against business rules.",
    detail: "Evaluation engine",
  },
  {
    number: "04",
    title: "Exception detection",
    description:
      "Identify discrepancies that need investigation.",
    detail: "Exception workflow",
  },
  {
    number: "05",
    title: "Human review",
    description:
      "Assign cases and record reviewer decisions.",
    detail: "Human review",
  },
  {
    number: "06",
    title: "Controlled action",
    description:
      "Run authorized connector simulations and record outcomes.",
    detail: "Action connectors",
  },
];

export default function WorkflowOverview() {
  return (
    <section className="panel workflow-overview">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">PROCESS OVERVIEW</p>

          <h3>How ExceptionOps AI works</h3>

          <p className="muted">
            A controlled process for handling invoice
            exceptions from intake to resolution.
          </p>
        </div>
      </div>

      <div className="workflow-stage-grid">
        {stages.map((stage) => (
          <article
            className="workflow-stage"
            key={stage.number}
          >
            <span className="workflow-stage-number">
              {stage.number}
            </span>

            <h4>{stage.title}</h4>

            <p>{stage.description}</p>

            <span className="workflow-stage-detail">
              {stage.detail}
            </span>
          </article>
        ))}
      </div>

      <div className="workflow-principle">
        <strong>Human oversight is part of the process.</strong>

        <p>
          Automated extraction and business-rule evaluation
          help identify issues. Review decisions remain
          controlled by authorized users. Connector
          operations in this portfolio implementation
          are simulations and drafts.
        </p>
      </div>
    </section>
  );
}