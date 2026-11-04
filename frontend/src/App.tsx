import {
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import { AuthProvider } from "./auth/AuthContext";
import ProtectedRoute from "./auth/ProtectedRoute";
import RoleGuard from "./auth/RoleGuard";
import LoginPage from "./auth/LoginPage";

import AppLayout from "./components/layout/AppLayout";

import DashboardPage from "./pages/DashboardPage";
import PlaceholderPage from "./pages/PlaceholderPage";
import InvoicesPage from "./pages/InvoicesPage";
import UploadInvoicePage from "./pages/UploadInvoicePage";
import InvoiceDetailsPage from "./pages/InvoiceDetailsPage";
import "./styles/invoice-management.css";
import InvoiceProcessingPage from "./pages/InvoiceProcessingPage";
import "./styles/processing.css";
export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route
          path="/login"
          element={<LoginPage />}
        />

        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route
              index
              element={<DashboardPage />}
            />

           <Route
  path="/invoices"
  element={<InvoicesPage />}
/>


            <Route
  path="/invoices/upload"
  element={<UploadInvoicePage />}
/>

            
<Route
  path="/invoices/:documentId"
  element={<InvoiceDetailsPage />}
/>
<Route
  path="/invoices/:documentId/process"
  element={<InvoiceProcessingPage />}
/>
            <Route
              path="/exceptions"
              element={
                <RoleGuard
                  allowedRoles={["admin", "reviewer"]}
                >
                  <PlaceholderPage
                    title="Exception queue"
                    description="Investigate invoice exceptions and manage human reviews."
                    phase="Review workspace implementation"
                  />
                </RoleGuard>
              }
            />

            <Route
              path="/reviews/:reviewId"
              element={
                <RoleGuard
                  allowedRoles={["admin", "reviewer"]}
                >
                  <PlaceholderPage
                    title="Review workspace"
                    description="Inspect business findings, assign reviewers and record decisions."
                    phase="Review workspace implementation"
                  />
                </RoleGuard>
              }
            />

            <Route
              path="/actions"
              element={
                <RoleGuard
                  allowedRoles={["admin", "action_operator"]}
                >
                  <PlaceholderPage
                    title="Action center"
                    description="Inspect authorized connector actions and recover eligible executions."
                    phase="Action center implementation"
                  />
                </RoleGuard>
              }
            />

            <Route
              path="/workflows"
              element={
                <RoleGuard
                  allowedRoles={["admin", "reviewer"]}
                >
                  <PlaceholderPage
                    title="Workflow history"
                    description="Inspect invoice workflow stages and recorded workflow events."
                    phase="Workflow history implementation"
                  />
                </RoleGuard>
              }
            />

            <Route
              path="/workflows/:workflowId"
              element={
                <RoleGuard
                  allowedRoles={["admin", "reviewer"]}
                >
                  <PlaceholderPage
                    title="Workflow details"
                    description="Inspect an individual workflow and its recorded events."
                    phase="Workflow history implementation"
                  />
                </RoleGuard>
              }
            />

            <Route
              path="/audit"
              element={
                <RoleGuard
                  allowedRoles={["admin", "action_operator"]}
                >
                  <PlaceholderPage
                    title="Audit history"
                    description="Inspect recorded action events and operational traceability."
                    phase="Audit history implementation"
                  />
                </RoleGuard>
              }
            />

            <Route
              path="/profile"
              element={
                <PlaceholderPage
                  title="My profile"
                  description="View your authenticated account and assigned application role."
                  phase="Account module implementation"
                />
              }
            />
          </Route>
        </Route>

        <Route
          path="*"
          element={<Navigate to="/" replace />}
        />
      </Routes>
    </AuthProvider>
  );
}