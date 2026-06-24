import React from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import { Activity, Users, Target, Clock, BarChart3, TrendingUp, AlertTriangle } from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  BarChart,
  Bar
} from "recharts";

const Dashboard: React.FC = () => {
  const { userRole, userEmail } = useAuth();
  const currentRole = userRole || "Employee";

  const { data: dashboardData, isLoading } = useQuery({
    queryKey: ["dashboard", currentRole],
    queryFn: () => api.dashboards.getByRole(currentRole),
  });

  const getRoleIcon = () => {
    switch(currentRole) {
      case "HR": return Users;
      case "Reporting Manager": return Target;
      case "Process Engineer": return Activity;
      default: return Clock;
    }
  };

  const RoleIcon = getRoleIcon();

  // Mock data for visualizations
  const productivityData = [
    { name: "Mon", productivity: 85 },
    { name: "Tue", productivity: 90 },
    { name: "Wed", productivity: 88 },
    { name: "Thu", productivity: 92 },
    { name: "Fri", productivity: 95 },
  ];

  const utilizationData = [
    { name: "W1", utilized: 80, bench: 20 },
    { name: "W2", utilized: 85, bench: 15 },
    { name: "W3", utilized: 90, bench: 10 },
    { name: "W4", utilized: 88, bench: 12 },
  ];

  return (
    <div className="space-y-8 pb-10">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-brand-primary/20 flex items-center justify-center text-brand-primary">
              <RoleIcon className="w-5 h-5" />
            </div>
            <h1 className="text-3xl font-extrabold text-white">Workforce Command Center</h1>
          </div>
          <p className="text-slate-400 text-sm mt-1">Welcome back, {userEmail}. You are viewing the <strong className="text-white">{currentRole}</strong> workspace.</p>
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-20">
          <div className="w-8 h-8 border-4 border-brand-primary/30 border-t-brand-primary rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-400">Loading {currentRole} metrics...</p>
        </div>
      ) : (
        <>
          {/* Dynamic Metric Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {dashboardData?.metrics?.map((metric: any, idx: number) => {
              const Icon = idx === 0 ? Activity : idx === 1 ? AlertTriangle : BarChart3;
              const colorClass = idx === 0 ? "text-brand-primary" : idx === 1 ? "text-brand-danger" : "text-brand-warning";
              
              return (
                <div key={idx} className="glass-card p-6 rounded-2xl relative overflow-hidden">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-500">{metric.label}</span>
                    <Icon className={`w-5 h-5 ${colorClass}`} />
                  </div>
                  <div className="text-3xl font-extrabold text-white mb-2">{metric.value}</div>
                  <div className={`text-xs ${colorClass} font-semibold flex items-center gap-1`}>
                    <TrendingUp className="w-3 h-3" /> Updated just now
                  </div>
                </div>
              );
            })}
          </div>

          {/* Visualizations */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Area Chart: Productivity Trend */}
            <div className="glass-card p-6 rounded-2xl">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-lg font-bold text-white">Productivity Trend</h3>
                  <p className="text-xs text-slate-500">Weekly aggregated productivity score</p>
                </div>
              </div>

              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={productivityData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorProd" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#4F46E5" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#4F46E5" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="name" stroke="#475569" fontSize={11} tickLine={false} />
                    <YAxis stroke="#475569" fontSize={11} tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ backgroundColor: "#1E293B", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "12px", color: "#FFF", fontSize: "12px" }} />
                    <Area type="monotone" dataKey="productivity" stroke="#4F46E5" strokeWidth={3} fillOpacity={1} fill="url(#colorProd)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Bar Chart: Resource Utilization */}
            <div className="glass-card p-6 rounded-2xl">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-lg font-bold text-white">Resource Utilization</h3>
                  <p className="text-xs text-slate-500">Allocated vs Bench</p>
                </div>
              </div>

              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={utilizationData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <XAxis dataKey="name" stroke="#475569" fontSize={11} tickLine={false} />
                    <YAxis stroke="#475569" fontSize={11} tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ backgroundColor: "#1E293B", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "12px", color: "#FFF", fontSize: "12px" }} cursor={{fill: 'rgba(255,255,255,0.05)'}} />
                    <Bar dataKey="utilized" stackId="a" fill="#10B981" radius={[0, 0, 4, 4]} barSize={30} />
                    <Bar dataKey="bench" stackId="a" fill="#EF4444" radius={[4, 4, 0, 0]} barSize={30} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default Dashboard;
