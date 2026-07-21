import { Navigate, Route, Routes } from "react-router-dom";

import { useAuth } from "./auth";
import Layout from "./components/Layout";
import { Spinner } from "./components/ui";
import ActivitiesPage from "./pages/Activities";
import ActivityDetailPage from "./pages/ActivityDetail";
import Dashboard from "./pages/Dashboard";
import InsightsPage from "./pages/Insights";
import LoginPage from "./pages/Login";
import PlanPage from "./pages/Plan";
import RegisterPage from "./pages/Register";
import SettingsPage from "./pages/Settings";
import TrendsPage from "./pages/Trends";

function Protected({ children }: { children: React.ReactNode }) {
  const { authed, ready } = useAuth();
  if (!ready) return <Spinner />;
  if (!authed) return <Navigate to="/login" replace />;
  return <Layout>{children}</Layout>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/" element={<Protected><Dashboard /></Protected>} />
      <Route path="/activities" element={<Protected><ActivitiesPage /></Protected>} />
      <Route path="/activities/:id" element={<Protected><ActivityDetailPage /></Protected>} />
      <Route path="/trends" element={<Protected><TrendsPage /></Protected>} />
      <Route path="/plan" element={<Protected><PlanPage /></Protected>} />
      <Route path="/insights" element={<Protected><InsightsPage /></Protected>} />
      <Route path="/settings" element={<Protected><SettingsPage /></Protected>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
