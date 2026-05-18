import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { AuthGuard } from "@/components/guards/AuthGuard";
import { AdminGuard } from "@/components/guards/AdminGuard";
import { ToastHost } from "@/components/feedback/Toast";
import { Skeleton } from "@/components/feedback/Skeleton";

// Eager: login (first paint) + introduce (public landing) + feishu callback
import { LoginPage } from "@/pages/login/LoginPage";
import { IntroducePage } from "@/pages/introduce/IntroducePage";
import { FeishuCallbackPage } from "@/pages/auth_callback/FeishuCallbackPage";

// User pages — lazy
const DashboardPage = lazy(() => import("@/pages/dashboard/DashboardPage").then((m) => ({ default: m.DashboardPage })));
const WorkspacePage = lazy(() => import("@/pages/workspace/WorkspacePage").then((m) => ({ default: m.WorkspacePage })));
const CreateTaskPage = lazy(() => import("@/pages/create_task/CreateTaskPage").then((m) => ({ default: m.CreateTaskPage })));
const ScheduledTasksPage = lazy(() => import("@/pages/scheduled/ScheduledTasksPage").then((m) => ({ default: m.ScheduledTasksPage })));
const AgentDetailPage = lazy(() => import("@/pages/agent_detail/AgentDetailPage").then((m) => ({ default: m.AgentDetailPage })));
const GuidePage = lazy(() => import("@/pages/guide/GuidePage").then((m) => ({ default: m.GuidePage })));
const PublicFilePage = lazy(() => import("@/pages/public_file/PublicFilePage").then((m) => ({ default: m.PublicFilePage })));

// Admin shell + pages — bundled together (admin users will hit them in sequence)
const AdminLayout = lazy(() => import("@/pages/admin/AdminLayout").then((m) => ({ default: m.AdminLayout })));
const AdminOverview = lazy(() => import("@/pages/admin/AdminOverview").then((m) => ({ default: m.AdminOverview })));
const AdminUsers = lazy(() => import("@/pages/admin/AdminUsers").then((m) => ({ default: m.AdminUsers })));
const AdminAgents = lazy(() => import("@/pages/admin/AdminAgents").then((m) => ({ default: m.AdminAgents })));
const AdminAgentEdit = lazy(() => import("@/pages/admin/AdminAgentEdit").then((m) => ({ default: m.AdminAgentEdit })));
const AdminAuditLogs = lazy(() => import("@/pages/admin/AdminAuditLogs").then((m) => ({ default: m.AdminAuditLogs })));
const AdminUsage = lazy(() => import("@/pages/admin/AdminUsage").then((m) => ({ default: m.AdminUsage })));
const AdminSqlAudit = lazy(() => import("@/pages/admin/AdminSqlAudit").then((m) => ({ default: m.AdminSqlAudit })));
const AdminSettings = lazy(() => import("@/pages/admin/AdminSettings").then((m) => ({ default: m.AdminSettings })));
const AdminExperienceCards = lazy(() => import("@/pages/admin/AdminExperienceCards").then((m) => ({ default: m.AdminExperienceCards })));
const AdminPublicTasks = lazy(() => import("@/pages/admin/AdminPublicTasks").then((m) => ({ default: m.AdminPublicTasks })));
const AdminReviewCenter = lazy(() => import("@/pages/admin/AdminReviewCenter").then((m) => ({ default: m.AdminReviewCenter })));
const AdminFiles = lazy(() => import("@/pages/admin/AdminFiles").then((m) => ({ default: m.AdminFiles })));
const AdminSkills = lazy(() => import("@/pages/admin/AdminSkills").then((m) => ({ default: m.AdminSkills })));
const AdminKnowledgeBases = lazy(() => import("@/pages/admin/AdminKnowledgeBases").then((m) => ({ default: m.AdminKnowledgeBases })));
const AdminTemplates = lazy(() => import("@/pages/admin/AdminTemplates").then((m) => ({ default: m.AdminTemplates })));

function PageFallback() {
  return (
    <div style={{ padding: 32, maxWidth: 720, margin: "60px auto" }}>
      <Skeleton lines={6} />
    </div>
  );
}

function authed(node: React.ReactNode) {
  return <AuthGuard>{node}</AuthGuard>;
}
function admined(node: React.ReactNode) {
  return (
    <AuthGuard>
      <AdminGuard>{node}</AdminGuard>
    </AuthGuard>
  );
}

export default function App() {
  return (
    <>
      <Suspense fallback={<PageFallback />}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/auth/feishu/callback" element={<FeishuCallbackPage />} />
          <Route path="/introduce" element={<IntroducePage />} />

          <Route path="/dashboard" element={authed(<DashboardPage />)} />
          <Route path="/workspace/:taskId" element={authed(<WorkspacePage />)} />
          <Route path="/create-task" element={authed(<CreateTaskPage />)} />
          <Route path="/scheduled-tasks" element={authed(<ScheduledTasksPage />)} />
          <Route path="/agent/:agentId" element={authed(<AgentDetailPage />)} />
          <Route path="/guide" element={authed(<GuidePage />)} />
          <Route path="/public-files/:fileId" element={authed(<PublicFilePage />)} />

          <Route path="/admin" element={admined(<AdminLayout />)}>
            <Route index element={<AdminOverview />} />
            <Route path="users" element={<AdminUsers />} />
            <Route path="agents" element={<AdminAgents />} />
            <Route path="agents/:agentId" element={<AdminAgentEdit />} />
            <Route path="audit" element={<AdminAuditLogs />} />
            <Route path="usage" element={<AdminUsage />} />
            <Route path="sql-audit" element={<AdminSqlAudit />} />
            <Route path="review-center" element={<AdminReviewCenter />} />
            <Route path="experience-cards" element={<AdminExperienceCards />} />
            <Route path="public-tasks" element={<AdminPublicTasks />} />
            <Route path="files" element={<AdminFiles />} />
            <Route path="skills" element={<AdminSkills />} />
            <Route path="knowledge-bases" element={<AdminKnowledgeBases />} />
            <Route path="templates" element={<AdminTemplates />} />
            <Route
              path="settings"
              element={
                <AdminGuard superOnly={false}>
                  <AdminSettings />
                </AdminGuard>
              }
            />
          </Route>

          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Suspense>
      <ToastHost />
    </>
  );
}
