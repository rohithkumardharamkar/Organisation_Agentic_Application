import React, { useState, useEffect, useRef } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import { Bot, Send, User, Sparkles, RefreshCw, AlertTriangle, Check } from "lucide-react";
import { useAuth } from "../context/AuthContext";

const Copilot: React.FC = () => {
  const { userRole } = useAuth();
  const queryClient = useQueryClient();
  const [message, setMessage] = useState("");
  const [localMessages, setLocalMessages] = useState<any[]>([]);
  const [isChatPending, setIsChatPending] = useState(false);
  const [isApprovePending, setIsApprovePending] = useState(false);
  const [lastMetadata, setLastMetadata] = useState<any>(null);
  const [activeInspectorTab, setActiveInspectorTab] = useState<string>("trace");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Queries
  const { data: chatHistory = [], isLoading, refetch } = useQuery({
    queryKey: ["chatHistory"],
    queryFn: api.copilot.history
  });

  const { data: statusData } = useQuery({
    queryKey: ["copilotStatus"],
    queryFn: api.copilot.status,
    refetchInterval: 3000 // Poll status every 3s
  });

  const currentStatus = statusData?.status || "COMPLETED";

  // Sync localMessages with chatHistory when not streaming
  useEffect(() => {
    if (chatHistory && !isChatPending && !isApprovePending) {
      setLocalMessages(chatHistory);
    }
  }, [chatHistory, isChatPending, isApprovePending]);

  const handleSend = async (e?: React.FormEvent, customMsg?: string) => {
    if (e) e.preventDefault();
    const queryToSend = customMsg || message;
    if (!queryToSend.trim() || isChatPending || currentStatus === "PAUSED_FOR_APPROVAL") return;

    setIsChatPending(true);
    if (!customMsg) setMessage("");
    setLastMetadata(null);

    // Optimistically add user message and empty assistant message
    const newUserMsg = { role: "user", message: queryToSend };
    const newAsstMsg = { role: "assistant", message: "" };
    setLocalMessages(prev => [...prev, newUserMsg, newAsstMsg]);

    try {
      const token = localStorage.getItem("finpilot_token");
      const response = await fetch("http://localhost:8000/api/v1/copilot/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ message: queryToSend })
      });

      if (!response.ok) {
        throw new Error("Failed to send message");
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let assistantText = "";

      if (reader) {
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;

          const chunkText = decoder.decode(value, { stream: true });
          const lines = chunkText.split("\n\n");
          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6));
                if (data.type === "content") {
                  assistantText += data.delta;
                  setLocalMessages(prev => {
                    const updated = [...prev];
                    if (updated.length > 0) {
                      updated[updated.length - 1] = {
                        role: "assistant",
                        message: assistantText
                      };
                    }
                    return updated;
                  });
                } else if (data.type === "metadata") {
                  setLastMetadata(data.metadata);
                }
              } catch (err) {
                // Ignore partial JSON parsing errors
              }
            }
          }
        }
      }
    } catch (err) {
      console.error(err);
      setLocalMessages(prev => {
        const updated = [...prev];
        if (updated.length > 0 && updated[updated.length - 1].message === "") {
          updated[updated.length - 1] = {
            role: "assistant",
            message: "Sorry, I encountered an error while processing your request."
          };
        }
        return updated;
      });
    } finally {
      setIsChatPending(false);
      queryClient.invalidateQueries({ queryKey: ["chatHistory"] });
      queryClient.invalidateQueries({ queryKey: ["copilotStatus"] });
    }
  };

  const handleApprove = async (approve: boolean) => {
    if (isApprovePending) return;
    setIsApprovePending(true);
    setLastMetadata(null);

    // Optimistically add assistant message for streaming the response
    const newAsstMsg = { role: "assistant", message: "" };
    setLocalMessages(prev => [...prev, newAsstMsg]);

    try {
      const token = localStorage.getItem("finpilot_token");
      const response = await fetch("http://localhost:8000/api/v1/copilot/approve", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ approve })
      });

      if (!response.ok) {
        throw new Error("Failed to submit approval choice");
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let assistantText = "";

      if (reader) {
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;

          const chunkText = decoder.decode(value, { stream: true });
          const lines = chunkText.split("\n\n");
          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6));
                if (data.type === "content") {
                  assistantText += data.delta;
                  setLocalMessages(prev => {
                    const updated = [...prev];
                    if (updated.length > 0) {
                      updated[updated.length - 1] = {
                        role: "assistant",
                        message: assistantText
                      };
                    }
                    return updated;
                  });
                } else if (data.type === "metadata") {
                  setLastMetadata(data.metadata);
                }
              } catch (err) {
                // Ignore partial JSON parsing errors
              }
            }
          }
        }
      }
    } catch (err) {
      console.error(err);
      setLocalMessages(prev => {
        const updated = [...prev];
        if (updated.length > 0 && updated[updated.length - 1].message === "") {
          updated[updated.length - 1] = {
            role: "assistant",
            message: "Sorry, I encountered an error while processing the approval response."
          };
        }
        return updated;
      });
    } finally {
      setIsApprovePending(false);
      queryClient.invalidateQueries({ queryKey: ["chatHistory"] });
      queryClient.invalidateQueries({ queryKey: ["copilotStatus"] });
    }
  };

  // Scroll to bottom whenever history updates
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [localMessages, isChatPending, isApprovePending]);

  const getSuggestionsByRole = (role: string | null) => {
    switch (role) {
      case "Employee":
        return [
          "What projects am I currently assigned to?",
          "How many hours did I log on timesheets last week?",
          "What is my location and joining date?",
          "Suggest training courses or learning pathways based on my skills."
        ];
      case "Process Engineer":
        return [
          "Analyze and run diagnostics on our current sprint timesheet submissions.",
          "What is the standard sprint process standard defined in our documentation?",
          "Generate a timesheet diagnostics report for our current sprint."
        ];
      case "Reporting Manager":
        return [
          "Are there any at-risk projects, and who is allocated to them?",
          "Identify which projects are at risk and recommend resources to add to them.",
          "Show me the skill gap analysis for my team on the Yottaflex AI Migration project."
        ];
      case "HR":
        return [
          "Which employees have 'Expert' proficiency in Python?",
          "Identify any mid-level software engineers available to allocate.",
          "Provide a summary of the leaves requested and approved this month."
        ];
      default:
        return [
          "Identify underutilized employees on the bench.",
          "Which projects are currently at risk of missing deadlines?",
          "Generate a summary of the organizational health score."
        ];
    }
  };

  const quickPrompts = getSuggestionsByRole(userRole);

  const renderInspectorContent = () => {
    if (!lastMetadata) {
      return (
        <div className="flex flex-col items-center justify-center h-full text-slate-400 p-6 text-center min-h-[220px]">
          <Bot className="w-8 h-8 text-slate-300 mb-2 animate-pulse" />
          <p className="text-xs font-semibold text-slate-600">Awaiting Agent Execution Data</p>
          <p className="text-[10px] text-slate-400 mt-1 max-w-[240px] leading-relaxed">
            Submit a message or request in the chat to view real-time traces, capabilities, selected memories, and citations.
          </p>
        </div>
      );
    }

    switch (activeInspectorTab) {
      case "trace":
        const trace = lastMetadata.agent_trace || [];
        const activeAgent = lastMetadata.active_agent || "supervisor";
        const selectedAgents: string[] = lastMetadata.selected_agents || [];
        return (
          <div className="space-y-4 overflow-y-auto max-h-[360px] pr-2">
            <div className="flex items-center justify-between text-xs border-b border-slate-100 pb-2">
              <span className="font-bold text-slate-400 uppercase tracking-wider">Node Sequence</span>
              <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-bold text-[10px]">{trace.length} Steps</span>
            </div>
            {trace.length === 0 ? (
              <div className="text-xs text-slate-400 italic py-2">No node execution steps recorded.</div>
            ) : (
              <div className="relative border-l-2 border-slate-200 ml-3 pl-4 space-y-4 py-2">
                {trace.map((node: string, index: number) => {
                  const isLast = index === trace.length - 1;
                  return (
                    <div key={index} className="relative">
                      <span className={`absolute -left-[23px] top-1 w-2.5 h-2.5 rounded-full border-2 border-white flex items-center justify-center shadow-sm ${
                        isLast ? "bg-emerald-500 animate-pulse" : "bg-slate-300"
                      }`} />
                      <div className="bg-slate-50 hover:bg-slate-100 transition-all p-2.5 rounded-xl border border-slate-200">
                        <p className="text-xs font-bold text-slate-700">{node.replace(/Node/g, " Node")}</p>
                        <p className="text-[9px] text-slate-400 mt-0.5">Step {index + 1}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {selectedAgents.length > 0 && (
              <div className="bg-violet-50/60 rounded-xl p-3 border border-violet-100/70">
                <span className="text-[9px] text-violet-500 font-bold uppercase tracking-wider">Dispatched Agents</span>
                <div className="flex flex-wrap gap-1.5 mt-1.5">
                  {selectedAgents.map((a: string) => (
                    <span key={a} className="px-2 py-0.5 bg-violet-100 text-violet-800 text-[9px] font-bold rounded-full border border-violet-200">
                      {a.replace(/_/g, " ").replace(/agent/gi, "").trim().toUpperCase()}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {lastMetadata.supervisor_reasoning && (
              <div className="bg-slate-50 rounded-xl p-3 border border-slate-200">
                <span className="text-[9px] text-slate-500 font-bold uppercase tracking-wider">Supervisor Reasoning</span>
                <p className="text-[10px] text-slate-600 mt-1 leading-relaxed italic">{lastMetadata.supervisor_reasoning}</p>
              </div>
            )}
            
            <div className="bg-blue-50/50 rounded-xl p-3 border border-blue-100/50 flex items-center justify-between">
              <div>
                <span className="text-[9px] text-blue-500 font-bold uppercase tracking-wider">Primary Agent</span>
                <p className="text-xs font-bold text-slate-800 mt-0.5">{activeAgent.replace(/_/g, " ").toUpperCase()}</p>
              </div>
              {lastMetadata.risk_level && (
                <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold uppercase ${
                  lastMetadata.risk_level === "high" || lastMetadata.risk_level === "critical"
                    ? "bg-red-100 text-red-700 border border-red-200"
                    : "bg-amber-100 text-amber-700 border border-amber-200"
                }`}>
                  {lastMetadata.risk_level}
                </span>
              )}
            </div>
          </div>
        );

      case "tools":
        const tools = lastMetadata.tool_calls || [];
        const confidence = lastMetadata.agent_confidence || {};
        return (
          <div className="space-y-4 overflow-y-auto max-h-[360px] pr-2">
            <div className="flex items-center justify-between text-xs border-b border-slate-100 pb-2">
              <span className="font-bold text-slate-400 uppercase tracking-wider">Executed Tools</span>
              <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-bold text-[10px]">{tools.length} Called</span>
            </div>
            {tools.length === 0 ? (
              <div className="text-xs text-slate-400 italic py-2">No external tools triggered during this plan.</div>
            ) : (
              <div className="space-y-2">
                {tools.map((tool: string, index: number) => (
                  <div key={index} className="bg-slate-50 border border-slate-200 p-2.5 rounded-xl flex items-center justify-between">
                    <span className="text-xs font-mono text-slate-600 font-bold">{tool}</span>
                    <span className="px-1.5 py-0.5 bg-slate-200/50 text-slate-500 text-[8px] font-bold rounded uppercase">Active</span>
                  </div>
                ))}
              </div>
            )}

            <div className="border-t border-slate-100 pt-3">
              <span className="text-[9px] text-slate-400 font-bold uppercase tracking-wider">Confidence Threshold Verification</span>
              {Object.keys(confidence).length === 0 ? (
                <p className="text-xs text-slate-400 italic mt-1 py-1">No confidence outputs available.</p>
              ) : (
                <div className="space-y-2 mt-2">
                  {Object.entries(confidence).map(([agent, score]: [string, any]) => {
                    const scoreVal = typeof score === "number" ? score : parseFloat(score);
                    const formattedScore = isNaN(scoreVal) ? "N/A" : `${(scoreVal * 100).toFixed(0)}%`;
                    return (
                      <div key={agent} className="space-y-1">
                        <div className="flex justify-between text-[10px] font-semibold text-slate-600">
                          <span>{agent.replace(/_agent/g, "").toUpperCase()}</span>
                          <span className="text-blue-600">{formattedScore}</span>
                        </div>
                        <div className="w-full bg-slate-150 h-1.5 rounded-full overflow-hidden">
                          <div 
                            className={`h-full rounded-full transition-all duration-500 ${
                              scoreVal >= 0.85 ? "bg-emerald-500" : scoreVal >= 0.70 ? "bg-blue-500" : "bg-amber-500"
                            }`}
                            style={{ width: `${(scoreVal * 100)}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        );

      case "memory":
        const memorySources = lastMetadata.selected_memory_sources || [];
        const retrieved = lastMetadata.retrieved_memories || {};
        return (
          <div className="space-y-4 overflow-y-auto max-h-[360px] pr-2">
            <div className="flex items-center justify-between text-xs border-b border-slate-100 pb-2">
              <span className="font-bold text-slate-400 uppercase tracking-wider">Memory Channels</span>
              <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-bold text-[10px]">{memorySources.length} Active</span>
            </div>
            
            <div className="space-y-2">
              <span className="text-[9px] text-slate-400 font-bold uppercase tracking-wider">Selected Memory Sources</span>
              <div className="flex flex-wrap gap-1.5">
                {memorySources.length === 0 ? (
                  <span className="text-xs text-slate-400 italic">None selected</span>
                ) : (
                  memorySources.map((src: string) => (
                    <span key={src} className="px-2 py-0.5 bg-violet-50 text-violet-700 border border-violet-100 text-[9px] font-bold rounded uppercase">
                      {src}
                    </span>
                  ))
                )}
              </div>
            </div>

            <div className="border-t border-slate-100 pt-3">
              <span className="text-[9px] text-slate-400 font-bold uppercase tracking-wider">Retrieved Knowledge Context</span>
              <div className="mt-2 space-y-2">
                {Object.keys(retrieved).length === 0 ? (
                  <p className="text-xs text-slate-400 italic">No retrieved memories context.</p>
                ) : (
                  Object.entries(retrieved).map(([key, val]: [string, any]) => {
                    const strVal = typeof val === "string" ? val : JSON.stringify(val, null, 2);
                    return (
                      <div key={key} className="bg-slate-50 border border-slate-200 p-2.5 rounded-xl">
                        <span className="text-[9px] font-bold text-slate-500 uppercase">{key}</span>
                        <pre className="text-[10px] text-slate-600 font-mono mt-1 whitespace-pre-wrap overflow-x-auto max-h-32">
                          {strVal}
                        </pre>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>
        );

      case "citations":
        const citations = lastMetadata.citations || [];
        return (
          <div className="space-y-4 overflow-y-auto max-h-[360px] pr-2">
            <div className="flex items-center justify-between text-xs border-b border-slate-100 pb-2">
              <span className="font-bold text-slate-400 uppercase tracking-wider">Cited Sources</span>
              <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-bold text-[10px]">{citations.length} References</span>
            </div>
            {citations.length === 0 ? (
              <div className="text-xs text-slate-400 italic py-2">No references cited in synthesized response.</div>
            ) : (
              <div className="space-y-2">
                {citations.map((cite: any, index: number) => {
                  const title = typeof cite === "string" ? cite : cite.source || cite.title || "Policy Reference";
                  const snippet = cite.snippet || cite.content || "";
                  return (
                    <div key={index} className="bg-slate-50 border border-slate-200 p-3 rounded-xl space-y-1.5">
                      <div className="flex items-center gap-1.5">
                        <span className="w-3.5 h-3.5 rounded bg-blue-100 text-blue-700 flex items-center justify-center text-[8px] font-bold">
                          {index + 1}
                        </span>
                        <span className="text-[11px] font-bold text-slate-700">{title}</span>
                      </div>
                      {snippet && (
                        <p className="text-[10px] text-slate-500 italic pl-5 border-l border-slate-350 leading-relaxed">
                          "{snippet}"
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        );
      case "verification": {
        const vStatus = lastMetadata.verification_status || "N/A";
        const vDetails = lastMetadata.verification_details || "";
        const supConf = lastMetadata.supervisor_confidence;
        const isPassed = vStatus === "PASSED";
        return (
          <div className="space-y-4 overflow-y-auto max-h-[360px] pr-2">
            <div className="flex items-center justify-between text-xs border-b border-slate-100 pb-2">
              <span className="font-bold text-slate-400 uppercase tracking-wider">Fact-Check Result</span>
              <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold uppercase border ${
                isPassed ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-red-50 text-red-700 border-red-200"
              }`}>{vStatus}</span>
            </div>

            <div className={`p-3 rounded-xl border ${
              isPassed ? "bg-emerald-50/50 border-emerald-100" : "bg-red-50/50 border-red-100"
            }`}>
              <span className="text-[9px] font-bold uppercase tracking-wider text-slate-500">Verification Reasoning</span>
              <p className="text-[10px] text-slate-700 mt-1 leading-relaxed">
                {vDetails || "No verification details available for this response."}
              </p>
            </div>

            {supConf !== undefined && supConf !== null && (
              <div className="bg-slate-50 rounded-xl p-3 border border-slate-200">
                <span className="text-[9px] text-slate-400 font-bold uppercase tracking-wider">Supervisor Confidence</span>
                <div className="mt-2 space-y-1">
                  <div className="flex justify-between text-[10px] font-semibold text-slate-600">
                    <span>Routing Score</span>
                    <span className="text-blue-600">{typeof supConf === "number" ? `${(supConf * 100).toFixed(0)}%` : supConf}</span>
                  </div>
                  <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        supConf >= 0.85 ? "bg-emerald-500" : supConf >= 0.70 ? "bg-blue-500" : "bg-amber-500"
                      }`}
                      style={{ width: `${(supConf * 100)}%` }}
                    />
                  </div>
                </div>
              </div>
            )}
          </div>
        );
      }

      default:
        return null;
    }
  };

  return (
    <div className="space-y-6 pb-10 flex flex-col h-[calc(100vh-6rem)]">
      {/* Header */}
      <div className="flex items-center justify-between flex-shrink-0">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900">AI Copilot</h1>
          <p className="text-slate-500 text-sm mt-1">Chat statefully with your agent team</p>
        </div>
        <button
          onClick={() => refetch()}
          className="p-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-500 hover:text-slate-700 transition-all duration-200 shadow-sm"
        >
          <RefreshCw className="w-5 h-5" />
        </button>
      </div>

      {/* Chat Area Panel */}
      <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Side: Message logs */}
        <div className="lg:col-span-7 bg-white rounded-2xl flex flex-col justify-between overflow-hidden border border-slate-200 shadow-sm">
          {/* Scrollable logs */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {isLoading ? (
              <div className="text-center py-10 text-slate-500 font-semibold text-xs">Connecting to copilot session...</div>
            ) : localMessages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center text-slate-500 py-10">
                <Bot className="w-12 h-12 text-slate-400 mb-4 animate-bounce" />
                <span className="font-bold text-slate-700 text-lg">Workforce OS Agent is online.</span>
                <p className="text-sm text-slate-500 max-w-md mt-2 leading-relaxed">
                  Ask me about employee utilization, project risks, skill gaps, or request executive health reports.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {localMessages.map((m: any, idx: number) => {
                  const isAgent = m.role === "assistant";
                  return (
                    <div key={idx} className={`flex items-start gap-3.5 ${isAgent ? "justify-start" : "justify-end"}`}>
                      {/* Avatar */}
                      {isAgent && (
                        <div className="w-8 h-8 rounded-lg bg-brand-primary/15 border border-brand-primary/25 text-brand-primary flex items-center justify-center flex-shrink-0">
                          <Bot className="w-4.5 h-4.5" />
                        </div>
                      )}
                      
                      {/* Bubble */}
                      <div className={`p-4 rounded-2xl text-sm leading-relaxed max-w-xl whitespace-pre-wrap ${
                        isAgent
                          ? "bg-slate-50 border border-slate-200 text-slate-700"
                          : "bg-blue-600 text-white font-medium"
                      }`}>
                        {m.message}
                      </div>

                      {/* User Avatar */}
                      {!isAgent && (
                        <div className="w-8 h-8 rounded-lg bg-slate-200 flex items-center justify-center text-slate-600 flex-shrink-0">
                          <User className="w-4.5 h-4.5" />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
            
            {/* Typing Indicator */}
            {isChatPending && localMessages.length > 0 && localMessages[localMessages.length - 1].message === "" && (
              <div className="flex items-start gap-3.5 justify-start">
                <div className="w-8 h-8 rounded-lg bg-brand-primary/15 border border-brand-primary/25 text-brand-primary flex items-center justify-center flex-shrink-0">
                  <Bot className="w-4.5 h-4.5" />
                </div>
                <div className="px-5 py-4.5 rounded-2xl bg-slate-50 border border-slate-200 flex gap-1.5 items-center justify-center">
                  <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></div>
                  <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:0.2s]"></div>
                  <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:0.4s]"></div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Approval Gate Banner */}
          {currentStatus === "PAUSED_FOR_APPROVAL" && (
            <div className="p-4 border-t border-slate-200 bg-amber-50 text-amber-600 flex flex-col sm:flex-row sm:items-center justify-between gap-4 flex-shrink-0">
              <div className="flex items-start gap-3">
                <div className="w-9 h-9 rounded-lg bg-amber-100 border border-amber-200 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <AlertTriangle className="w-5 h-5 text-amber-500 animate-pulse" />
                </div>
                <div>
                  <span className="font-bold text-slate-800 text-sm">Human Approval Requested</span>
                  <p className="text-xs text-slate-600 mt-1 max-w-md">
                    The AI agent has paused and is awaiting confirmation for this action. Please approve or reject below.
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => handleApprove(false)}
                  disabled={isApprovePending}
                  className="px-3.5 py-2 rounded-xl border border-brand-danger/30 hover:bg-brand-danger/5 text-brand-danger text-xs font-bold transition-all"
                >
                  Reject Action
                </button>
                <button
                  type="button"
                  onClick={() => handleApprove(true)}
                  disabled={isApprovePending}
                  className="px-3.5 py-2 rounded-xl bg-brand-success hover:bg-brand-success/90 text-white text-xs font-bold transition-all shadow-md shadow-brand-success/15 flex items-center gap-1.5"
                >
                  {isApprovePending ? (
                    <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  ) : (
                    <Check className="w-3.5 h-3.5" />
                  )}
                  Approve Action
                </button>
              </div>
            </div>
          )}

          {/* Form input */}
          <form onSubmit={(e) => handleSend(e)} className="p-4 border-t border-slate-200 bg-slate-50 flex gap-3 flex-shrink-0">
            <input
              type="text"
              required
              disabled={isChatPending || currentStatus === "PAUSED_FOR_APPROVAL"}
              placeholder={currentStatus === "PAUSED_FOR_APPROVAL" ? "Awaiting human verification response..." : "Ask Workforce Agent a question..."}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              className="flex-1 px-4 py-3 rounded-xl bg-white border border-slate-300 text-slate-900 text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all"
            />
            <button
              type="submit"
              disabled={isChatPending || currentStatus === "PAUSED_FOR_APPROVAL" || !message.trim()}
              className="p-3.5 rounded-xl bg-brand-primary hover:bg-brand-primary/90 text-white font-bold transition-all flex items-center justify-center shadow-md shadow-brand-primary/10"
            >
              <Send className="w-4.5 h-4.5" />
            </button>
          </form>
        </div>

        {/* Right Side: Agentic Execution Inspector & Prompts */}
        <div className="lg:col-span-5 flex flex-col gap-6 h-full min-h-0 overflow-hidden">
          
          {/* Inspector Panel */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 flex flex-col min-h-0 flex-1">
            <h3 className="text-sm font-bold text-slate-800 border-b border-slate-100 pb-3 flex-shrink-0">
              Agentic Execution Inspector
            </h3>
            
            {/* Tabs Selector */}
            <div className="flex border-b border-slate-100 py-2.5 gap-1 flex-shrink-0">
              {["trace", "tools", "memory", "citations", "verification"].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveInspectorTab(tab)}
                  className={`flex-1 py-1.5 text-center text-[9px] font-bold rounded-lg uppercase tracking-wider transition-all duration-150 ${
                    activeInspectorTab === tab
                      ? tab === "verification"
                        ? "bg-emerald-50 text-emerald-700 shadow-xs border border-emerald-200"
                        : "bg-slate-100 text-slate-800 shadow-xs border border-slate-200"
                      : "text-slate-400 hover:text-slate-600 hover:bg-slate-50"
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>
            
            {/* Tab Contents */}
            <div className="flex-1 overflow-y-auto pt-4 min-h-0">
              {renderInspectorContent()}
            </div>
          </div>
          
          {/* Quick Prompts Panel */}
          <div className="flex-shrink-0">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2.5">Suggested Inquiries</h3>
            
            <div className="flex flex-col gap-2">
              {quickPrompts.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => handleSend(undefined, prompt)}
                  disabled={isChatPending || currentStatus === "PAUSED_FOR_APPROVAL"}
                  className="w-full flex items-center gap-3 p-3 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-left text-xs font-semibold text-slate-600 hover:text-slate-900 transition-all duration-150 shadow-sm"
                >
                  <Sparkles className="w-3.5 h-3.5 text-brand-success flex-shrink-0" />
                  <span className="truncate">{prompt}</span>
                </button>
              ))}
            </div>
          </div>
          
        </div>

      </div>
    </div>
  );
};

export default Copilot;
