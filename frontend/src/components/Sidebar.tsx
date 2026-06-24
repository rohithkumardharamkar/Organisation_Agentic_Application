import React from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  LayoutDashboard,
  BarChart3,
  ShieldAlert,
  Target,
  FileText,
  MessageSquareCode,
  LogOut,
  User,
  Clock,
  CheckCircle,
  Activity
} from "lucide-react";

const Sidebar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout, userEmail, userRole } = useAuth();
  
  const navItems = [
    { name: "Executive Command", path: "/executive", icon: LayoutDashboard, roles: ["HR"] },
    { name: "Workforce Intel", path: "/workforce", icon: BarChart3, roles: ["HR", "Reporting Manager"] },
    { name: "Project Intel", path: "/projects", icon: Target, roles: ["Reporting Manager"] },
    { name: "Talent Intel", path: "/talent", icon: User, roles: ["HR"] },
    { name: "Timesheet", path: "/timesheet", icon: Clock, roles: ["Employee", "Process Engineer", "Reporting Manager", "HR"] },
    { name: "Manager Approvals", path: "/approvals", icon: CheckCircle, roles: ["Reporting Manager", "HR"] },
    { name: "Process Engineering", path: "/process", icon: Activity, roles: ["Process Engineer", "Reporting Manager"] },
    { name: "Data Directory", path: "/directory", icon: FileText, roles: ["Employee", "Process Engineer", "Reporting Manager", "HR"] },
    { name: "AI Copilot", path: "/copilot", icon: MessageSquareCode, roles: ["Employee", "Process Engineer", "Reporting Manager", "HR"] },
    { name: "AI Operations", path: "/ai-ops", icon: ShieldAlert, roles: ["HR", "Reporting Manager"] },
  ];

  const filteredNavItems = navItems.filter(item => !item.roles || item.roles.includes(userRole || "Employee"));

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <aside className="fixed inset-y-0 left-0 w-64 glass-panel flex flex-col z-20">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 border-b border-slate-200 gap-2.5">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center font-bold text-white shadow-lg">
          Y
        </div>
        <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent truncate">
          Yottaflex OS
        </span>
      </div>

      {/* Navigation Items */}
      <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
        {filteredNavItems.map((item) => {
          const isActive = location.pathname === item.path;
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              to={item.path}
              className={`flex items-center gap-3.5 px-4 py-3 rounded-xl transition-all duration-200 group ${
                isActive
                  ? "bg-brand-primary/10 border border-brand-primary/30 text-slate-900 font-semibold shadow-sm shadow-brand-primary/5"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-transparent"
              }`}
            >
              <Icon className={`w-5 h-5 transition-transform duration-200 group-hover:scale-110 ${
                isActive ? "text-brand-primary" : "text-slate-500 group-hover:text-slate-700"
              }`} />
              <span className="text-sm">{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer Info */}
      <div className="p-4 border-t border-slate-200 bg-slate-50">
        <div className="flex items-center gap-3 p-2 rounded-xl bg-slate-100 mb-3 border border-slate-200">
          <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center text-slate-700 border border-slate-300">
            <User className="w-4 h-4" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs text-slate-500 truncate">Logged in as {userRole}</p>
            <p className="text-xs font-semibold text-slate-900 truncate">{userEmail || "admin@yottaflex.com"}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl border border-brand-danger/20 text-brand-danger bg-brand-danger/5 hover:bg-brand-danger/10 transition-colors duration-200 text-sm font-semibold"
        >
          <LogOut className="w-4 h-4" />
          Log Out
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
