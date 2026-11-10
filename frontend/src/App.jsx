import { Navigate, Route, Routes } from "react-router-dom";

import ProtectedRoute from "./components/ProtectedRoute";
import Analysis from "./pages/Analysis";
import AuthPage from "./pages/AuthPage";
import Dashboard from "./pages/Dashboard";
import JobMatches from "./pages/JobMatches";
import Landing from "./pages/Landing";
import Review from "./pages/Review";
import SkillGap from "./pages/SkillGap";
import Upload from "./pages/Upload";
import AnalysisHistory from "./pages/AnalysisHistory";

export default function App() {
  return (
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
  );
}
