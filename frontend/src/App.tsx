import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Sidebar from "./components/Sidebar";

// Pages
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Dashboard from "./pages/Dashboard";
import Copilot from "./pages/Copilot";

// Workforce OS Pages
import ExecutiveCommandCenter from "./pages/ExecutiveCommandCenter";
import WorkforceIntelligence from "./pages/WorkforceIntelligence";
import ProjectIntelligence from "./pages/ProjectIntelligence";
import TalentIntelligence from "./pages/TalentIntelligence";
import AIOperationsCenter from "./pages/AIOperationsCenter";
import DataDirectory from "./pages/DataDirectory";
import TimesheetPortal from "./pages/TimesheetPortal";
import ManagerApprovals from "./pages/ManagerApprovals";
import ProcessEngineering from "./pages/ProcessEngineering";

const queryClient = new QueryClient();

// Private Route Wrapper
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? (
    <div className="min-h-screen bg-slate-50 flex">
      <Sidebar />
      <main className="flex-1 pl-64 min-h-screen">
        <div className="max-w-7xl mx-auto p-8 relative">
          <div className="glow-bg top-[-100px] right-[-100px]"></div>
          {children}
        </div>
      </main>
    </div>
  ) : (
    <Navigate to="/login" replace />
  );
};

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router>
          <Routes>
            {/* Public routes */}
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />

            {/* Protected dashboard routes */}
            <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/copilot" element={<ProtectedRoute><Copilot /></ProtectedRoute>} />

            {/* Workforce OS routes */}
            <Route path="/executive" element={<ProtectedRoute><ExecutiveCommandCenter /></ProtectedRoute>} />
            <Route path="/workforce" element={<ProtectedRoute><WorkforceIntelligence /></ProtectedRoute>} />
            <Route path="/projects" element={<ProtectedRoute><ProjectIntelligence /></ProtectedRoute>} />
            <Route path="/talent" element={<ProtectedRoute><TalentIntelligence /></ProtectedRoute>} />
            <Route path="/directory" element={<ProtectedRoute><DataDirectory /></ProtectedRoute>} />
            <Route path="/ai-ops" element={<ProtectedRoute><AIOperationsCenter /></ProtectedRoute>} />
            <Route path="/timesheet" element={<ProtectedRoute><TimesheetPortal /></ProtectedRoute>} />
            <Route path="/approvals" element={<ProtectedRoute><ManagerApprovals /></ProtectedRoute>} />
            <Route path="/process" element={<ProtectedRoute><ProcessEngineering /></ProtectedRoute>} />

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Router>
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;
