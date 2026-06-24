import React, { useEffect, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import { 
  CheckCircle2, 
  XCircle, 
  Play, 
  ShieldAlert, 
  Terminal, 
  RefreshCw
} from "lucide-react";

const AIOperationsCenter: React.FC = () => {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<"ops" | "evals" | "registry" | "metrics">("ops");
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null);
  const [isTriggering, setIsTriggering] = useState(false);

  // Queries - Operations
  const { 
    data: approvals = [], 
    isLoading: isApprovalsLoading, 
    refetch: refetchApprovals 
  } = useQuery({
    queryKey: ["pendingApprovals"],
    queryFn: api.aiOps.approvals,
    refetchInterval: activeTab === "ops" ? 5000 : undefined
  });

  const { 
    data: activities = [], 
    isLoading: isActivitiesLoading, 
    refetch: refetchActivities 
  } = useQuery({
    queryKey: ["agentActivities"],
    queryFn: api.aiOps.activities,
    refetchInterval: activeTab === "ops" ? 5000 : undefined
  });

  // Queries - Evaluations
  const { 
    data: runs = [], 
    isLoading: isRunsLoading
  } = useQuery({
    queryKey: ["evaluationRuns"],
    queryFn: api.evaluations.runs,
    enabled: activeTab === "evals"
  });

  const { 
    data: runResults = [], 
    isLoading: isResultsLoading 
  } = useQuery({
    queryKey: ["evaluationResults", selectedRunId],
    queryFn: () => api.evaluations.results(selectedRunId!),
    enabled: activeTab === "evals" && selectedRunId !== null
  });

  // Queries - Registry & Metrics
  const { data: registry = [] } = useQuery({
    queryKey: ["agentRegistry"],
    queryFn: api.aiOps.registry,
    enabled: activeTab === "registry",
    staleTime: 60000
  });

  const { data: metrics, refetch: refetchMetrics } = useQuery({
    queryKey: ["opsMetrics"],
    queryFn: api.aiOps.metrics,
    enabled: activeTab === "metrics",
    refetchInterval: activeTab === "metrics" ? 10000 : undefined
  });

  // Automatically select first run when runs list loads
  useEffect(() => {
    if (runs && runs.length > 0 && selectedRunId === null) {
      setSelectedRunId(runs[0].id);
    }
  }, [runs, selectedRunId]);

  // Mutations
  const approveMutation = useMutation({
    mutationFn: (id: string) => api.aiOps.approve(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pendingApprovals"] });
      queryClient.invalidateQueries({ queryKey: ["agentActivities"] });
    }
  });

  const rejectMutation = useMutation({
    mutationFn: (id: string) => api.aiOps.reject(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pendingApprovals"] });
      queryClient.invalidateQueries({ queryKey: ["agentActivities"] });
    }
  });

  const triggerEvalMutation = useMutation({
    mutationFn: api.evaluations.run,
    onMutate: () => {
      setIsTriggering(true);
    },
    onSuccess: (data) => {
      setIsTriggering(false);
      queryClient.invalidateQueries({ queryKey: ["evaluationRuns"] });
      if (data && data.run_id) {
        setSelectedRunId(data.run_id);
      }
      alert("Evaluation suite triggered! Running in the background.");
    },
    onError: (err) => {
      setIsTriggering(false);
      alert("Failed to trigger evaluation run: " + err);
    }
  });

  const handleApprove = (id: string) => {
    approveMutation.mutate(id);
  };

  const handleReject = (id: string) => {
    rejectMutation.mutate(id);
  };

  const handleTriggerEval = () => {
    triggerEvalMutation.mutate();
  };

  const selectedRunSummary = runs.find((r: any) => r.id === selectedRunId);

  return (
    <div className="space-y-6 pb-10">
      {/* Title Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900">AI Operations & Control</h1>
          <p className="text-slate-500 text-sm mt-1">Real-time human gating, telemetry, and quality evaluation</p>
        </div>
        
        {/* Toggle View Tabs */}
        <div className="flex bg-slate-100 p-1 rounded-xl border border-slate-200 self-start md:self-auto gap-0.5">
          {([
            { key: "ops", label: "Human-in-the-Loop" },
            { key: "evals", label: "AI Performance Evals" },
            { key: "registry", label: "Agent Registry" },
            { key: "metrics", label: "Live Metrics" },
          ] as const).map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={`px-4 py-2 text-xs font-bold rounded-lg transition-all ${
                activeTab === key
                  ? "bg-white text-slate-800 shadow-sm"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {activeTab === "ops" ? (
        // ================= HUMAN IN THE LOOP & AUDIT VIEW =================
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Left Column: Pending Approvals (col-span-7) */}
          <div className="lg:col-span-7 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-amber-500" />
                Pending Agent Approvals
              </h2>
              <button 
                onClick={() => refetchApprovals()}
                className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-500"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>

            {isApprovalsLoading ? (
              <div className="p-8 text-center bg-white border border-slate-200 rounded-2xl text-slate-400 text-xs font-semibold">
                Loading pending approvals...
              </div>
            ) : approvals.length === 0 ? (
              <div className="p-8 bg-white border border-slate-200 shadow-sm rounded-2xl text-center text-slate-500 min-h-[160px] flex flex-col justify-center items-center">
                <CheckCircle2 className="w-10 h-10 text-emerald-400 mb-2" />
                <span className="font-bold text-slate-700 text-sm">System is fully verified</span>
                <p className="text-xs text-slate-400 mt-1">No agent actions are currently queued for approval.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {approvals.map((app: any) => {
                  const isPending = app.status === "Pending";
                  return (
                    <div 
                      key={app.id} 
                      className={`p-5 bg-white border rounded-2xl shadow-xs transition-all ${
                        isPending ? "border-amber-200 hover:border-amber-300 bg-amber-50/10" : "border-slate-200"
                      }`}
                    >
                      <div className="flex justify-between items-start gap-4">
                        <div>
                          <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider ${
                            app.risk_level === "high" || app.risk_level === "critical"
                              ? "bg-red-100 text-red-700 border border-red-200"
                              : "bg-amber-100 text-amber-700 border border-amber-200"
                          }`}>
                            {app.risk_level} Risk
                          </span>
                          <h3 className="font-bold text-base text-slate-800 mt-2">{app.description}</h3>
                          <p className="text-slate-500 text-xs mt-1">
                            Type: <strong className="text-slate-700">{app.action}</strong> | Thread ID: <code className="bg-slate-100 px-1 py-0.5 rounded text-[10px] text-slate-600">{app.thread_id}</code>
                          </p>
                        </div>

                        <span className={`px-2.5 py-1 rounded-xl text-[10px] font-bold uppercase border ${
                          app.status === "Approved"
                            ? "bg-emerald-50 text-emerald-700 border-emerald-25"
                            : app.status === "Rejected"
                            ? "bg-red-50 text-red-700 border-red-25"
                            : "bg-amber-50 text-amber-700 border-amber-25 animate-pulse"
                        }`}>
                          {app.status}
                        </span>
                      </div>

                      {isPending && (
                        <div className="flex gap-3 mt-5 border-t border-slate-100 pt-4">
                          <button 
                            disabled={approveMutation.isPending || rejectMutation.isPending}
                            onClick={() => handleReject(app.id)}
                            className="flex-1 bg-white hover:bg-red-50 border border-red-200 hover:border-red-300 text-red-600 py-2 rounded-xl text-xs font-bold transition-all"
                          >
                            Reject
                          </button>
                          <button 
                            disabled={approveMutation.isPending || rejectMutation.isPending}
                            onClick={() => handleApprove(app.id)}
                            className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white py-2 rounded-xl text-xs font-bold transition-all shadow-md shadow-emerald-600/10 flex items-center justify-center gap-1.5"
                          >
                            Approve Action
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Right Column: Agent Activity Logs (col-span-5) */}
          <div className="lg:col-span-5 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                <Terminal className="w-5 h-5 text-slate-600" />
                Agent Activity Logs
              </h2>
              <button 
                onClick={() => refetchActivities()}
                className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-500"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>

            {isActivitiesLoading ? (
              <div className="p-8 text-center bg-white border border-slate-200 rounded-2xl text-slate-400 text-xs font-semibold">
                Loading activities...
              </div>
            ) : (
              <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm divide-y divide-slate-100 max-h-[500px] overflow-y-auto">
                {activities.length === 0 ? (
                  <div className="p-8 text-center text-slate-400 text-xs">No activity logs recorded.</div>
                ) : (
                  activities.map((act: any, i: number) => (
                    <div key={i} className="p-4 hover:bg-slate-50/50 transition duration-150 font-medium">
                      <div className="flex justify-between items-start gap-4">
                        <span className="font-bold text-blue-600 text-xs uppercase tracking-wide">
                          {act.agent.replace(/_/g, " ").replace(/Agent/g, "")}
                        </span>
                        <span className="text-slate-400 text-[9px] font-medium">
                          {new Date(act.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                        </span>
                      </div>
                      <p className="text-slate-700 text-xs mt-1.5 font-medium leading-relaxed">{act.action}</p>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </div>
      ) : activeTab === "registry" ? (
        // ================= AGENT REGISTRY VIEW =================
        <div className="space-y-4">
          <h2 className="text-lg font-bold text-slate-800">Active Agent Registry</h2>
          {registry.length === 0 ? (
            <div className="p-8 text-center text-slate-400 text-xs font-semibold bg-white border border-slate-200 rounded-2xl">Loading registry...</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {registry.map((agent: any) => (
                <div key={agent.name} className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm hover:shadow-md transition-all">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="font-bold text-slate-800 text-sm">{agent.display_name}</h3>
                      <p className="text-[10px] text-slate-400 font-mono mt-0.5">{agent.name}</p>
                    </div>
                    <span className="px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 text-[9px] font-bold border border-blue-100 uppercase whitespace-nowrap flex-shrink-0">
                      {(agent.confidence_threshold * 100).toFixed(0)}% threshold
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 mt-2 leading-relaxed">{agent.description}</p>
                  <div className="mt-3 border-t border-slate-100 pt-3">
                    <p className="text-[9px] font-bold uppercase text-slate-400 mb-1.5">Permissions</p>
                    <div className="flex flex-wrap gap-1">
                      {(agent.permissions || []).map((p: string) => (
                        <span key={p} className="px-1.5 py-0.5 bg-violet-50 text-violet-700 text-[8px] font-bold rounded border border-violet-100">{p}</span>
                      ))}
                    </div>
                  </div>
                  <div className="mt-3 border-t border-slate-100 pt-3">
                    <p className="text-[9px] font-bold uppercase text-slate-400 mb-1.5">Tools ({(agent.tools || []).length})</p>
                    <div className="flex flex-wrap gap-1">
                      {(agent.tools || []).slice(0, 4).map((t: string) => (
                        <span key={t} className="px-1.5 py-0.5 bg-slate-100 text-slate-600 text-[8px] font-mono rounded">{t}</span>
                      ))}
                      {(agent.tools || []).length > 4 && (
                        <span className="px-1.5 py-0.5 bg-slate-100 text-slate-500 text-[8px] font-bold rounded">+{agent.tools.length - 4} more</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : activeTab === "metrics" ? (
        // ================= LIVE METRICS VIEW =================
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-slate-800">Live Platform Metrics</h2>
            <button onClick={() => refetchMetrics()} className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-500">
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
          {!metrics ? (
            <div className="p-8 text-center text-slate-400 text-xs font-semibold bg-white border border-slate-200 rounded-2xl">Loading metrics...</div>
          ) : (
            <div className="space-y-6">
              {/* KPI Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { label: "Queries Processed", value: metrics.user_queries_processed, color: "blue" },
                  { label: "Success Rate", value: `${metrics.success_rate_percentage}%`, color: "emerald" },
                  { label: "Verification Rate", value: `${metrics.verification_rate_percentage}%`, color: "violet" },
                  { label: "Avg Latency", value: `${metrics.average_latency_seconds}s`, color: "amber" },
                ].map(({ label, value, color }) => (
                  <div key={label} className={`bg-white border border-slate-200 rounded-2xl p-4 shadow-sm`}>
                    <p className="text-[10px] font-bold uppercase text-slate-400 tracking-wider">{label}</p>
                    <p className={`text-2xl font-extrabold mt-1 text-${color}-600`}>{value}</p>
                  </div>
                ))}
              </div>
              {/* Secondary Stats */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
                  <h3 className="font-bold text-slate-800 text-sm mb-3">Execution Health</h3>
                  <div className="space-y-3">
                    {[
                      { label: "Total Tool Calls", value: metrics.tool_calls_executed },
                      { label: "Retries", value: metrics.retries_count },
                      { label: "Failures", value: metrics.failures_count },
                      { label: "Guardrail Events", value: metrics.guardrail_events_triggered },
                      { label: "Human Approvals", value: metrics.human_approvals_requested },
                    ].map(({ label, value }) => (
                      <div key={label} className="flex justify-between items-center py-1 border-b border-slate-100 last:border-0">
                        <span className="text-xs text-slate-600 font-medium">{label}</span>
                        <span className="text-xs font-bold text-slate-800">{value}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
                  <h3 className="font-bold text-slate-800 text-sm mb-3">Token & Cost Usage</h3>
                  <div className="space-y-3">
                    {[
                      { label: "Total Tokens Consumed", value: metrics.total_tokens_consumed?.toLocaleString() },
                      { label: "Total Cost (USD)", value: `$${metrics.total_cost_usd}` },
                      { label: "Retry Rate", value: `${metrics.retry_rate_percentage}%` },
                      { label: "Guardrail Block Rate", value: `${metrics.guardrail_block_rate_percentage}%` },
                    ].map(({ label, value }) => (
                      <div key={label} className="flex justify-between items-center py-1 border-b border-slate-100 last:border-0">
                        <span className="text-xs text-slate-600 font-medium">{label}</span>
                        <span className="text-xs font-bold text-slate-800">{value}</span>
                      </div>
                    ))}
                  </div>
                  {metrics.model_distribution && Object.keys(metrics.model_distribution).length > 0 && (
                    <div className="mt-4 border-t border-slate-100 pt-3">
                      <p className="text-[9px] font-bold uppercase text-slate-400 mb-2">Model Distribution</p>
                      {Object.entries(metrics.model_distribution).map(([model, count]: [string, any]) => (
                        <div key={model} className="flex justify-between items-center text-[10px] py-0.5">
                          <span className="font-mono text-slate-600 truncate max-w-[160px]">{model}</span>
                          <span className="font-bold text-blue-600">{count} calls</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      ) : (
        // ================= EVALUATIONS VIEW =================
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Left Column: Runs List & Trigger (col-span-4) */}
          <div className="lg:col-span-4 space-y-5">
            <div className="bg-white border border-slate-200 rounded-2xl shadow-sm p-4 space-y-4">
              <h3 className="font-bold text-slate-800 text-sm">Evaluation Engine</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Run our suite of 20 workforce agent scenarios covering RBAC restrictions, project risk synthesis, security injections, and RAG grounding.
              </p>
              
              <button
                disabled={isTriggering}
                onClick={handleTriggerEval}
                className="w-full bg-slate-900 hover:bg-slate-800 disabled:bg-slate-300 text-white py-2.5 rounded-xl text-xs font-bold transition-all shadow-md flex items-center justify-center gap-1.5"
              >
                {isTriggering ? (
                  <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                ) : (
                  <Play className="w-3.5 h-3.5 fill-white" />
                )}
                Trigger Evaluation Suite
              </button>
            </div>

            <div className="space-y-3">
              <h3 className="font-bold text-slate-400 text-[10px] uppercase tracking-wider">Run History</h3>
              
              {isRunsLoading ? (
                <div className="text-xs text-slate-400 italic">Loading run logs...</div>
              ) : runs.length === 0 ? (
                <div className="text-xs text-slate-400 italic">No evaluation runs recorded yet.</div>
              ) : (
                <div className="space-y-2">
                  {runs.map((r: any) => {
                    const isSelected = r.id === selectedRunId;
                    const runDate = new Date(r.timestamp);
                    const formattedDate = runDate.toLocaleDateString() + " " + runDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                    return (
                      <button
                        key={r.id}
                        onClick={() => setSelectedRunId(r.id)}
                        className={`w-full text-left p-3.5 rounded-xl border transition-all flex justify-between items-center ${
                          isSelected 
                            ? "bg-slate-950 border-slate-950 text-white shadow-md shadow-slate-950/10" 
                            : "bg-white border-slate-200 hover:bg-slate-50 text-slate-700"
                        }`}
                      >
                        <div>
                          <p className="text-xs font-bold">Run #{r.id}</p>
                          <p className={`text-[9px] mt-0.5 ${isSelected ? "text-slate-300" : "text-slate-400"}`}>
                            {formattedDate}
                          </p>
                        </div>
                        <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold ${
                          isSelected 
                            ? "bg-white/20 text-white" 
                            : "bg-slate-100 text-slate-800"
                        }`}>
                          {(r.agent_success_rate * 100).toFixed(0)}% Pass
                        </span>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Run Details & Metrics (col-span-8) */}
          <div className="lg:col-span-8 space-y-6">
            {selectedRunId === null ? (
              <div className="p-8 text-center bg-white border border-slate-200 rounded-2xl text-slate-400 text-xs">
                Select an evaluation run from the left panel to inspect detailed metrics.
              </div>
            ) : (
              <>
                {/* Metric Summary Grid Cards */}
                {selectedRunSummary && (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-xs text-center">
                      <span className="text-[9px] text-slate-400 font-bold uppercase">Task Success</span>
                      <p className="text-2xl font-extrabold text-slate-900 mt-1">
                        {(selectedRunSummary.agent_success_rate * 100).toFixed(0)}%
                      </p>
                    </div>
                    <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-xs text-center">
                      <span className="text-[9px] text-slate-400 font-bold uppercase">Routing Accuracy</span>
                      <p className="text-2xl font-extrabold text-slate-900 mt-1">
                        {(selectedRunSummary.routing_accuracy * 100).toFixed(0)}%
                      </p>
                    </div>
                    <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-xs text-center">
                      <span className="text-[9px] text-slate-400 font-bold uppercase">RAG Grounding</span>
                      <p className="text-2xl font-extrabold text-slate-900 mt-1">
                        {(selectedRunSummary.rag_precision * 100).toFixed(0)}%
                      </p>
                    </div>
                    <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-xs text-center">
                      <span className="text-[9px] text-slate-400 font-bold uppercase">Hallucination Rate</span>
                      <p className="text-2xl font-extrabold text-red-600 mt-1">
                        {(selectedRunSummary.hallucination_rate * 100).toFixed(0)}%
                      </p>
                    </div>
                  </div>
                )}

                {/* Case Results Drill Down */}
                <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
                  <div className="px-5 py-4 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
                    <h3 className="font-bold text-slate-800 text-sm">Test Case Drill Down</h3>
                    <span className="text-xs text-slate-500 font-medium">Run #{selectedRunId} Results</span>
                  </div>

                  {isResultsLoading ? (
                    <div className="p-10 text-center text-slate-400 text-xs font-semibold">
                      Fetching test case data...
                    </div>
                  ) : runResults.length === 0 ? (
                    <div className="p-10 text-center text-slate-400 text-xs italic">
                      This run contains no case logs. If the run was triggered recently, it may still be executing in the background. Refresh in a few moments.
                    </div>
                  ) : (
                    <div className="divide-y divide-slate-100 overflow-y-auto max-h-[500px]">
                      {runResults.map((caseRes: any) => {
                        return (
                          <div key={caseRes.id} className="p-5 hover:bg-slate-50/30 transition duration-150 space-y-3">
                            <div className="flex justify-between items-start gap-4">
                              <div>
                                <span className="bg-slate-100 text-slate-600 px-2 py-0.5 rounded text-[8px] font-bold uppercase tracking-wider">
                                  {caseRes.role}
                                </span>
                                <h4 className="font-bold text-sm text-slate-800 mt-1.5">{caseRes.query}</h4>
                              </div>

                              <div className="flex items-center gap-1.5">
                                {caseRes.success ? (
                                  <span className="flex items-center gap-1 text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-lg border border-emerald-100 text-[10px] font-bold uppercase">
                                    <CheckCircle2 className="w-3.5 h-3.5" />
                                    Pass
                                  </span>
                                ) : (
                                  <span className="flex items-center gap-1 text-red-600 bg-red-50 px-2 py-0.5 rounded-lg border border-red-100 text-[10px] font-bold uppercase">
                                    <XCircle className="w-3.5 h-3.5" />
                                    Fail
                                  </span>
                                )}
                              </div>
                            </div>

                            {/* Telemetry Breakdown */}
                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-slate-50/50 p-3 rounded-xl border border-slate-100 text-[11px] text-slate-600">
                              <div>
                                <strong className="text-slate-400 uppercase text-[9px] tracking-wide block">Agent Routing</strong>
                                <span className={caseRes.routing_correct ? "text-emerald-700 font-bold" : "text-red-700 font-bold"}>
                                  {caseRes.actual_agent ? caseRes.actual_agent.replace(/_/g, " ").toUpperCase() : "None"} 
                                  {caseRes.routing_correct ? " (Correct)" : " (Incorrect)"}
                                </span>
                              </div>
                              <div>
                                <strong className="text-slate-400 uppercase text-[9px] tracking-wide block">RAG Precision</strong>
                                <span className="font-semibold">{(caseRes.rag_precision * 100).toFixed(0)}% Relevancy</span>
                              </div>
                              <div>
                                <strong className="text-slate-400 uppercase text-[9px] tracking-wide block">Hallucination Alert</strong>
                                <span className={caseRes.hallucination_detected ? "text-red-600 font-bold" : "text-emerald-600 font-bold"}>
                                  {caseRes.hallucination_detected ? "DETECTED" : "CLEAN"}
                                </span>
                              </div>
                            </div>

                            {caseRes.feedback && (
                              <p className="text-[11px] text-slate-500 leading-relaxed bg-slate-100/30 p-2.5 rounded-lg italic">
                                Feedback: {caseRes.feedback}
                              </p>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </>
            )}
          </div>

        </div>
      )}
    </div>
  );
};

export default AIOperationsCenter;
