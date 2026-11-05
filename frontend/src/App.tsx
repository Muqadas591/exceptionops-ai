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
import ExceptionQueuePage from "./pages/ExceptionQueuePage";
import ReviewDetailsPage from "./pages/ReviewDetailsPage";
import "./styles/reviews.css";
import ActionCenterPage from "./pages/ActionCenterPage";
import "./styles/actions.css";
import AuditHistoryPage from "./pages/AuditHistoryPage";
import WorkflowHistoryPage from "./pages/WorkflowHistoryPage";
import WorkflowDetailsPage from "./pages/WorkflowDetailsPage";
import "./styles/operations-history.css";

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
  path="/actions"
  element={
    <RoleGuard allowedRoles={["admin", "action_operator"]}>
      <ActionCenterPage />
    </RoleGuard>
  }
/>
            <Route
              path="/exceptions"
              element={
                <RoleGuard
                  allowedRoles={["admin", "reviewer"]}
                >
                  <ExceptionQueuePage />
                </RoleGuard>
              }
            />

            <Route
              path="/reviews/:reviewId"
              element={
                <RoleGuard
                  allowedRoles={["admin", "reviewer"]}
                >
                  <ReviewDetailsPage />
                </RoleGuard>
              }
            />

            <Route
              path="/workflows"
              element={
                <RoleGuard
                  allowedRoles={["admin", "reviewer"]}
                >
                  <WorkflowHistoryPage />
                </RoleGuard>
              }
            />

            <Route
              path="/workflows/:workflowId"
              element={
                <RoleGuard
                  allowedRoles={["admin", "reviewer"]}
                >
                  <WorkflowDetailsPage />
                </RoleGuard>
              }
            />

            <Route
              path="/audit"
              element={
                <RoleGuard
                  allowedRoles={["admin", "action_operator"]}
                >
                  <AuditHistoryPage />
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