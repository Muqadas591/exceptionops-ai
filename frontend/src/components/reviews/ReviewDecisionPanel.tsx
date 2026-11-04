import { useState } from "react";

interface ReviewDecisionPanelProps {
  assigned: boolean;
  completed: boolean;
  submitting: boolean;
  onApprove: (note: string) => Promise<void>;
  onReject: (note: string) => Promise<void>;
}

export default function ReviewDecisionPanel({
  assigned,
  completed,
  submitting,
  onApprove,
  onReject,
}: ReviewDecisionPanelProps) {
  const [note, setNote] = useState("");

  async function handleDecision(
    decision: "approve" | "reject",
  ) {
    const cleanNote = note.trim();

    if (cleanNote.length < 3) return;

    const confirmed = window.confirm(
      decision === "approve"
        ? "Are you sure you want to approve this review?"
        : "Are you sure you want to reject this review?",
    );

    if (!confirmed) return;

    if (decision === "approve") {
      await onApprove(cleanNote);
    } else {
      await onReject(cleanNote);
    }

    setNote("");
  }

  if (completed) {
    return (
      <section className="review-card">
        <h2>Final decision</h2>
        <p>
          This review already has a final decision.
          The backend does not permit changing it.
        </p>
      </section>
    );
  }

  return (
    <section className="review-card">
      <h2>Review decision</h2>

      {!assigned && (
        <div className="review-warning">
          Assign a reviewer before making a decision.
        </div>
      )}

      <label htmlFor="decision-note">
        Decision note
      </label>

      <textarea
        id="decision-note"
        value={note}
        onChange={(event) =>
          setNote(event.target.value)
        }
        rows={4}
        minLength={3}
        maxLength={2000}
        placeholder="Explain the reason for your decision..."
      />

      <div className="review-form-footer">
        <span>{note.length}/2000</span>

        <div className="review-decision-actions">
          <button
            type="button"
            className="review-danger-button"
            disabled={
              !assigned ||
              submitting ||
              note.trim().length < 3
            }
            onClick={() => void handleDecision("reject")}
          >
            Reject
          </button>

          <button
            type="button"
            className="review-primary-button"
            disabled={
              !assigned ||
              submitting ||
              note.trim().length < 3
            }
            onClick={() => void handleDecision("approve")}
          >
            Approve
          </button>
        </div>
      </div>
    </section>
  );
}