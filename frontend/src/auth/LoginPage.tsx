import { useState } from "react";

import {
  Navigate,
  useLocation,
  useNavigate,
} from "react-router-dom";

import { useAuth } from "./AuthContext";

export default function LoginPage() {
  const {
    login,
    authenticated,
  } = useAuth();

  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (authenticated) {
    return <Navigate to="/" replace />;
  }

  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      await login({
        email: email.trim(),
        password,
      });

      const destination =
        location.state?.from || "/";

      navigate(destination, {
        replace: true,
      });
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to sign in.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-visual">
        <div className="login-brand">
          <div className="brand-symbol">E</div>

          <div>
            <h1>ExceptionOps AI</h1>
            <p>Intelligent Invoice Operations</p>
          </div>
        </div>

        <div className="login-hero">
          <p className="eyebrow">
            BUSINESS AUTOMATION PLATFORM
          </p>

          <h2>
            From invoice processing
            <br />
            to controlled resolution.
          </h2>

          <p>
            Identify invoice exceptions, investigate
            business discrepancies, involve human
            reviewers, and maintain an auditable
            operational process.
          </p>

          <div className="login-flow">
            <span>Invoice intake</span>
            <span>Extraction</span>
            <span>Validation</span>
            <span>Human review</span>
            <span>Controlled action</span>
          </div>
        </div>

        <div className="login-visual-footer">
          AI-assisted processing · Human oversight ·
          Operational traceability
        </div>
      </div>

      <div className="login-form-area">
        <div className="login-form-card">
          <p className="eyebrow">WELCOME BACK</p>

          <h2>Sign in to your workspace</h2>

          <p className="login-description">
            Access your invoice operations dashboard.
          </p>

          {error && (
            <div className="notice notice-error">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <label className="form-label">
              Email address

              <input
                type="email"
                value={email}
                onChange={(event) =>
                  setEmail(event.target.value)
                }
                placeholder="you@company.com"
                autoComplete="username"
                required
              />
            </label>

            <label className="form-label">
              Password

              <input
                type="password"
                value={password}
                onChange={(event) =>
                  setPassword(event.target.value)
                }
                placeholder="Enter your password"
                autoComplete="current-password"
                required
              />
            </label>

            <button
              type="submit"
              className="button button-primary login-submit"
              disabled={loading}
            >
              {loading ? "Signing in..." : "Sign in"}
            </button>
          </form>

          <div className="login-security-note">
            <strong>Secure access</strong>

            <p>
              Your account permissions determine
              which operational functions you can access.
            </p>
          </div>

          <p className="login-demo-note">
            Demo access is created by the application
            administrator.
          </p>
        </div>
      </div>
    </div>
  );
}