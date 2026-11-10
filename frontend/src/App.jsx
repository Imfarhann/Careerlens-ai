import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import ProtectedRoute from "./components/ProtectedRoute";

const Analysis = lazy(() => import("./pages/Analysis"));
const AnalysisHistory = lazy(() => import("./pages/AnalysisHistory"));
const AuthPage = lazy(() => import("./pages/AuthPage"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const JobMatches = lazy(() => import("./pages/JobMatches"));
const Landing = lazy(() => import("./pages/Landing"));
const Review = lazy(() => import("./pages/Review"));
const SkillGap = lazy(() => import("./pages/SkillGap"));
const Upload = lazy(() => import("./pages/Upload"));

function PageFallback() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-navy">
      <div className="text-center">
        <span className="mx-auto block h-8 w-8 animate-spin rounded-full border-2 border-border border-t-accent" />
        <p className="mt-4 text-sm text-slate-400">Memuat halaman...</p>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Suspense fallback={<PageFallback />}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<AuthPage />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/upload"
          element={
            <ProtectedRoute>
              <Upload />
            </ProtectedRoute>
          }
        />
        <Route
          path="/history"
          element={
            <ProtectedRoute>
              <AnalysisHistory />
            </ProtectedRoute>
          }
        />
        <Route
          path="/review/:profileId"
          element={
            <ProtectedRoute>
              <Review />
            </ProtectedRoute>
          }
        />
        <Route
          path="/analysis/:analysisId"
          element={
            <ProtectedRoute>
              <Analysis />
            </ProtectedRoute>
          }
        />
        <Route
          path="/analysis/:analysisId/jobs"
          element={
            <ProtectedRoute>
              <JobMatches />
            </ProtectedRoute>
          }
        />
        <Route
          path="/analysis/:analysisId/skill-gap"
          element={
            <ProtectedRoute>
              <SkillGap />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}
