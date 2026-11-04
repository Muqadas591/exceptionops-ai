import type {
  BusinessEvaluation,
  FindingSeverity,
} from "../../types/processing";

interface EvaluationPanelProps {
  evaluation: BusinessEvaluation | null;
  loading: boolean;
  running: boolean;
  disabled: boolean;
  stale: boolean;
  error: string;
  onRunEvaluation: () => void;
}

function decisionLabel(decision: string): string {
  switch (decision) {
    case "ready_for_matching":
      return "Ready for matching";

    case "needs_review":
      return "Needs review";

    case "blocked":
      return "Blocked";

    default:
      return decision.replaceAll("_", " ");
  }
}

function severityClass(severity: FindingSeverity): string {
  return `severity-${severity}`;
}

export default function EvaluationPanel({
  evaluation,
  loading,
  running,
  disabled,
  stale,
  error,
  onRunEvaluation,
}: EvaluationPanelProps) {
  return (
    <section className="processing-card">
      <div className="processing-card-heading">
        <div>
          <span className="processing-step">STEP 2</span>
          <h2>Business evaluation</h2>
          <p>
            Validate extracted data against deterministic
            business rules.
          </p>
        </div>

        <button
          type="button"
          className="processing-primary-button"
          onClick={onRunEvaluation}
          disabled={disabled || running || loading}
        >
          {running
            ? "Evaluating..."
            : evaluation
              ? "Run evaluation again"
              : "Run evaluation"}
        </button>
      </div>

      {disabled && !stale && (
        <div className="processing-info">
          Run invoice extraction before evaluating this document.
        </div>
      )}

      {stale && (
        <div className="processing-warning">
          The extraction was updated after this evaluation.
          Run evaluation again to ensure findings correspond
          to the latest extracted fields.
        </div>
      )}

      {error && (
        <div className="processing-error" role="alert">
          {error}
        </div>
      )}

      {loading && (
        <div className="processing-empty">
          Loading existing evaluation...
        </div>
      )}

      {!loading && !evaluation && !error && !stale && !disabled && (
        <div className="processing-empty">
          <h3>No evaluation result yet</h3>
          <p>
            Run business evaluation to inspect missing fields,
            confidence issues, invalid values, and possible
            duplicate invoices.
          </p>
        </div>
      )}

      {evaluation && !stale && (
        <>
          <div className="evaluation-overview">
            <div className="evaluation-decision">
              <span>Business decision</span>

              <strong
                className={`decision-${evaluation.decision}`}
              >
                {decisionLabel(evaluation.decision)}
              </strong>
            </div>

            <div className="risk-score">
              <span>Risk score</span>
              <strong>{evaluation.risk_score}/100</strong>

              <div className="risk-track">
                <div
                  className="risk-fill"
                  style={{
                    width: `${evaluation.risk_score}%`,
                  }}
                />
              </div>
            </div>

            <div className="evaluation-version">
              <span>Rules version</span>
              <strong>{evaluation.rules_version}</strong>
            </div>
          </div>

          <div className="evaluation-summary">
            <strong>Evaluation summary</strong>
            <p>{evaluation.summary}</p>
          </div>

          <div className="findings-heading">
            <h3>Business rule findings</h3>
            <span>
              {evaluation.findings.length} finding(s)
            </span>
          </div>

          {evaluation.findings.length === 0 ? (
            <div className="processing-success">
              No business-rule findings were returned.
            </div>
          ) : (
            <div className="findings-list">
              {evaluation.findings.map((finding, index) => (
                <article
                  className="finding-item"
                  key={`${finding.rule_code}-${index}`}
                >
                  <div className="finding-topline">
                    <strong>{finding.rule_code}</strong>

                    <span
                      className={`severity-badge ${severityClass(
                        finding.severity,
                      )}`}
                    >
                      {finding.severity}
                    </span>
                  </div>

                  <p>{finding.message}</p>

                  {finding.field && (
                    <span className="finding-field">
                      Related field: {finding.field}
                    </span>
                  )}
                </article>
              ))}
            </div>
          )}

          <p className="processing-footnote">
            These results are generated by the backend's
            configured business rules. A result of
            "ready for matching" is not payment approval.
          </p>
        </>
      )}
    </section>
  );
}