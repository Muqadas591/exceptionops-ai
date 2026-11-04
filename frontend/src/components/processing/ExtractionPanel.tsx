import type { ExtractionResult } from "../../types/processing";

interface ExtractionPanelProps {
  extraction: ExtractionResult | null;
  loading: boolean;
  running: boolean;
  error: string;
  onRunExtraction: () => void;
}

function formatConfidence(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export default function ExtractionPanel({
  extraction,
  loading,
  running,
  error,
  onRunExtraction,
}: ExtractionPanelProps) {
  return (
    <section className="processing-card">
      <div className="processing-card-heading">
        <div>
          <span className="processing-step">STEP 1</span>
          <h2>Invoice extraction</h2>
          <p>
            Extract invoice fields from the uploaded document.
          </p>
        </div>

        <button
          type="button"
          className="processing-primary-button"
          onClick={onRunExtraction}
          disabled={running || loading}
        >
          {running
            ? "Extracting..."
            : extraction
              ? "Run extraction again"
              : "Run extraction"}
        </button>
      </div>

      {loading && (
        <div className="processing-empty">
          Loading existing extraction...
        </div>
      )}

      {error && (
        <div className="processing-error" role="alert">
          {error}
        </div>
      )}

      {!loading && !extraction && !error && (
        <div className="processing-empty">
          <h3>No extraction result yet</h3>
          <p>
            Run extraction to identify invoice number,
            supplier, dates, currency, and total amount.
          </p>
        </div>
      )}

      {extraction && (
        <>
          <div className="processing-summary-grid">
            <div>
              <span>Extraction ID</span>
              <strong>#{extraction.id}</strong>
            </div>

            <div>
              <span>Provider</span>
              <strong>{extraction.provider_name}</strong>
            </div>

            <div>
              <span>Status</span>
              <strong className="processing-value">
                {extraction.status.replaceAll("_", " ")}
              </strong>
            </div>

            <div>
              <span>Extracted text length</span>
              <strong>
                {extraction.extracted_text_length.toLocaleString()}
                {" characters"}
              </strong>
            </div>
          </div>

          {extraction.error_message && (
            <div className="processing-warning">
              {extraction.error_message}
            </div>
          )}

          <h3 className="processing-subheading">
            Extracted fields
          </h3>

          {Object.keys(extraction.fields).length === 0 ? (
            <div className="processing-empty">
              No fields were returned by the extraction provider.
            </div>
          ) : (
            <div className="extracted-fields-grid">
              {Object.entries(extraction.fields).map(
                ([fieldName, field]) => {
                  const value = field.value;
                  const confidence = field.confidence;
                  const evidence = field.evidence;

                  return (
                    <article
                      className="extracted-field"
                      key={fieldName}
                    >
                      <span className="field-label">
                        {fieldName.replaceAll("_", " ")}
                      </span>

                      <strong className="field-value">
                        {value === null || value === undefined ||
                        value === ""
                          ? "Not extracted"
                          : String(value)}
                      </strong>

                      <div className="field-confidence">
                        <span>Confidence</span>

                        <strong>
                          {typeof confidence === "number"
                            ? formatConfidence(confidence)
                            : "Not provided"}
                        </strong>
                      </div>

                      <div className="confidence-track">
                        <div
                          className="confidence-fill"
                          style={{
                            width:
                              typeof confidence === "number"
                                ? `${Math.max(
                                    0,
                                    Math.min(100, confidence * 100),
                                  )}%`
                                : "0%",
                          }}
                        />
                      </div>

                      <div className="field-evidence">
                        <span>Source evidence</span>
                        <p>
                          {evidence || "No evidence supplied."}
                        </p>
                      </div>
                    </article>
                  );
                },
              )}
            </div>
          )}

          <p className="processing-footnote">
            Extraction confidence is a provider estimate. It is
            not a guarantee that a field is correct.
          </p>
        </>
      )}
    </section>
  );
}