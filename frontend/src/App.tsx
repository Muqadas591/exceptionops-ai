import { useState } from "react";
import {
  NavLink,
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import Header from "./components/Header";
import QueuePage from "./components/QueuePage";
import ReviewPage from "./components/ReviewPage";
import type { AuthTokens } from "./types";

export default function App() {
  const [tokens, setTokens] = useState<AuthTokens>({
    reviewerToken: "",
    actionToken: "",
  });

  return (
    <div className="app-shell">
      <Header tokens={tokens} onTokensChange={setTokens} />

      <nav className="main-nav">
        <NavLink
          to="/"
          end
          className={({ isActive }) =>
            isActive ? "nav-link active" : "nav-link"
          }
        >
          <span>▦</span>
          Exception queue
        </NavLink>
      </nav>

      <Routes>
        <Route
          path="/"
          element={<QueuePage tokens={tokens} />}
        />

        <Route
          path="/reviews/:reviewId"
          element={<ReviewPage tokens={tokens} />}
        />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>

      <footer className="app-footer">
        <span>ExceptionOps AI</span>
        <span>Human approval · Controlled actions · Audit history</span>
        <span>Phase 7 prototype</span>
      </footer>
    </div>
  );
}