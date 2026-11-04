import { useState } from "react";
import type { FormEvent } from "react";
import type { ReviewComment } from "../../types/review";

interface ReviewCommentsProps {
  comments: ReviewComment[];
  completed: boolean;
  submitting: boolean;
  onAddComment: (body: string) => Promise<void>;
  onRequestCorrection: (
    instructions: string,
  ) => Promise<void>;
}

export default function ReviewComments({
  comments,
  completed,
  submitting,
  onAddComment,
  onRequestCorrection,
}: ReviewCommentsProps) {
  const [comment, setComment] = useState("");
  const [correction, setCorrection] = useState("");
  const [mode, setMode] = useState<
    "comment" | "correction"
  >("comment");

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (mode === "comment") {
      if (!comment.trim()) return;

      try {
        await onAddComment(comment.trim());
        setComment("");
      } catch {
        return;
      }

      return;
    }

    if (!correction.trim()) return;

    try {
      await onRequestCorrection(correction.trim());
      setCorrection("");
    } catch {
      return;
    }
  }

  return (
    <section className="review-card">
      <div className="review-section-heading">
        <div>
          <h2>Review discussion</h2>
          <p>
            Comments, assignment events, correction requests,
            and decision notes.
          </p>
        </div>

        <span className="review-count">
          {comments.length} event(s)
        </span>
      </div>

      <div className="review-comments">
        {comments.length === 0 ? (
          <div className="review-empty">
            No discussion has been recorded yet.
          </div>
        ) : (
          comments.map((item) => (
            <article
              className="review-comment"
              key={item.id}
            >
              <div className="review-comment-header">
                <div>
                  <strong>{item.author}</strong>
                  <span className="review-comment-type">
                    {item.comment_type.replaceAll("_", " ")}
                  </span>
                </div>

                <time>
                  {new Date(
                    item.created_at,
                  ).toLocaleString()}
                </time>
              </div>

              <p>{item.body}</p>
            </article>
          ))
        )}
      </div>

      {completed ? (
        <div className="review-info">
          This review is complete. New comments and
          correction requests are disabled.
        </div>
      ) : (
        <form
          className="review-comment-form"
          onSubmit={handleSubmit}
        >
          <div className="review-mode-switch">
            <button
              type="button"
              className={
                mode === "comment"
                  ? "review-mode-active"
                  : ""
              }
              onClick={() => setMode("comment")}
            >
              Add comment
            </button>

            <button
              type="button"
              className={
                mode === "correction"
                  ? "review-mode-active"
                  : ""
              }
              onClick={() => setMode("correction")}
            >
              Request correction
            </button>
          </div>

          {mode === "comment" ? (
            <textarea
              value={comment}
              onChange={(event) =>
                setComment(event.target.value)
              }
              placeholder="Write a review comment..."
              rows={4}
              maxLength={4000}
              required
            />
          ) : (
            <textarea
              value={correction}
              onChange={(event) =>
                setCorrection(event.target.value)
              }
              placeholder="Explain what needs to be corrected..."
              rows={4}
              minLength={3}
              maxLength={4000}
              required
            />
          )}

          <div className="review-form-footer">
            <span>
              {mode === "comment"
                ? `${comment.length}/4000`
                : `${correction.length}/4000`}
            </span>

            <button
              type="submit"
              className="review-primary-button"
              disabled={
                submitting ||
                (mode === "comment"
                  ? !comment.trim()
                  : correction.trim().length < 3)
              }
            >
              {submitting
                ? "Submitting..."
                : mode === "comment"
                  ? "Post comment"
                  : "Submit correction request"}
            </button>
          </div>
        </form>
      )}
    </section>
  );
}