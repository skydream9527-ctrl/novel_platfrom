import { Route, BrowserRouter, Routes } from "react-router-dom";
import DashboardPage from "./pages/DashboardPage";
import WorkspacePage from "./pages/WorkspacePage";
import AdminPage from "./pages/AdminPage";
import SettingsPage from "./pages/SettingsPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/workspace/:taskId" element={<WorkspacePage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/admin/*" element={<AdminPage />} />
        <Route path="*" element={<DashboardPage />} />
      </Routes>
    </BrowserRouter>
  );
}
