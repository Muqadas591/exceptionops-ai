import type { AuthTokens } from "../types";

interface HeaderProps {
  tokens: AuthTokens;
  onTokensChange: (tokens: AuthTokens) => void;
}

export default function Header({
  tokens,
  onTokensChange,
}: HeaderProps) {
  return (
    <header className="app-header">
      <div className="brand">
        <div className="brand-mark">E</div>
        <div>
          <h1>ExceptionOps</h1>
          <p>Invoice Operations Platform</p>
        </div>
      </div>

      <div className="token-controls">
        <label>
          Reviewer token
          <input
            type="password"
            autoComplete="off"
            placeholder="Reviewer token"
            value={tokens.reviewerToken}
            onChange={(event) =>
              onTokensChange({
                ...tokens,
                reviewerToken: event.target.value,
              })
            }
          />
        </label>

        <label>
          Action token
          <input
            type="password"
            autoComplete="off"
            placeholder="Action token"
            value={tokens.actionToken}
            onChange={(event) =>
              onTokensChange({
                ...tokens,
                actionToken: event.target.value,
              })
            }
          />
        </label>
      </div>
    </header>
  );
}