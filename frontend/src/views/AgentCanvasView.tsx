import React, { useEffect, useState, useRef } from "react";
import { AgentRunStatusResponse } from "../types";
import { fetchAgentRunStatus, approveDeployment } from "../services/api";
import {
  Terminal, ShieldCheck, CheckCircle2, XCircle, AlertTriangle, Clock, ExternalLink
} from "lucide-react";

interface AgentCanvasViewProps {
  runId: string;
}

export const AgentCanvasView: React.FC<AgentCanvasViewProps> = ({ runId }) => {
  const [statusData, setStatusData] = useState<AgentRunStatusResponse | null>(null);
  const [liveLogs, setLiveLogs] = useState<string[]>([]);
  const [approving, setApproving] = useState<boolean>(false);
  const logEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!runId) return;

    // Initial fetch
    fetchStatus();

    // Setup WebSocket for live real-time agent log streaming
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/api/agents/ws/${runId}`;
    
    const socket = new WebSocket(wsUrl);
    wsRef.current = socket;

    socket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.log) {
          setLiveLogs((prev) => [...prev, msg.log]);
        }
        if (msg.state_snapshot) {
          setStatusData(msg.state_snapshot);
        }
      } catch (e) {
        console.error("WS Parse error", e);
      }
    };

    // Fallback polling every 2s
    const interval = setInterval(fetchStatus, 2000);

    return () => {
      clearInterval(interval);
      if (wsRef.current) wsRef.current.close();
    };
  }, [runId]);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [liveLogs, statusData?.logs]);

  const fetchStatus = async () => {
    try {
      const data = await fetchAgentRunStatus(runId);
      setStatusData(data);
      if (data.logs && data.logs.length > 0) {
        setLiveLogs(data.logs);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleApproval = async (approved: boolean) => {
    setApproving(true);
    try {
      await approveDeployment(runId, approved, approved ? "Approved by Lead MLOps Engineer" : "Rejected");
      await fetchStatus();
    } catch (err) {
      alert(`Approval error: ${err}`);
    } finally {
      setApproving(false);
    }
  };

  // Determine stage active status
  const currentStep = statusData?.current_step || "initialized";
  const isDataDone = [
    "data_sentinel_complete", "training_complete", "eval_gate_complete",
    "awaiting_approval", "pipeline_complete", "security_audit_complete"
  ].includes(currentStep);
  const isTrainDone = [
    "training_complete", "eval_gate_complete", "awaiting_approval",
    "pipeline_complete", "security_audit_complete"
  ].includes(currentStep);
  const isEvalDone = [
    "eval_gate_complete", "awaiting_approval", "pipeline_complete", "security_audit_complete"
  ].includes(currentStep);
  const isSecurityDone = [
    "awaiting_approval", "pipeline_complete", "security_audit_complete"
  ].includes(currentStep);
  const isDeployDone = currentStep === "pipeline_complete";

  const isAwaitingHITL = statusData?.awaiting_hitl_approval || currentStep === "awaiting_approval";

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex justify-between items-center bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-lg">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-blue-500 animate-pulse"></span>
              Autonomous LangGraph Agent Canvas
            </h2>
            <span className="px-2.5 py-0.5 rounded text-xs font-mono font-bold bg-slate-800 text-blue-400 border border-slate-700">
              Run: {runId}
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time state transitions, agent thought streams, and Human-in-the-Loop approval checkpoints.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span
            className={`px-3 py-1 rounded-full text-xs font-bold border ${
              isAwaitingHITL
                ? "bg-amber-500/10 text-amber-400 border-amber-500/40 animate-pulse"
                : statusData?.status === "COMPLETED"
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/40"
                : statusData?.status === "REJECTED"
                ? "bg-rose-500/10 text-rose-400 border-rose-500/40"
                : "bg-blue-500/10 text-blue-400 border-blue-500/40"
            }`}
          >
            ● {statusData?.status || "RUNNING"}
          </span>
          <a
            href="https://smith.langchain.com"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 px-3 py-1 bg-purple-950/60 hover:bg-purple-900/60 border border-purple-500/40 text-purple-300 text-xs font-semibold rounded-lg transition"
          >
            <span>LangSmith Trace</span> <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>

      {/* Visual LangGraph State Machine Canvas */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-6 flex items-center gap-2">
          StateGraph Execution Pipeline (LangGraph Supervisor)
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 relative">
          {/* Node 08: Data Sentinel */}
          <div
            className={`p-4 rounded-xl border relative transition ${
              isDataDone
                ? "bg-blue-950/40 border-blue-500/80 shadow-md shadow-blue-500/10"
                : "bg-slate-950/60 border-slate-800"
            }`}
          >
            <span className="w-6 h-6 rounded-full bg-blue-600 text-white font-bold text-xs flex items-center justify-center absolute -top-2.5 -left-2.5 shadow">
              08
            </span>
            <span className="text-xs font-bold text-white block mt-1">Data Sentinel</span>
            <span className="text-[10px] text-slate-400 block mt-0.5">KS-test & PSI Drift</span>
            <div className="mt-3 flex items-center gap-1.5 text-[11px]">
              {isDataDone ? (
                <span className="text-emerald-400 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Validated
                </span>
              ) : (
                <span className="text-blue-400 flex items-center gap-1 animate-pulse">
                  <Clock className="w-3.5 h-3.5" /> Running
                </span>
              )}
            </div>
          </div>

          {/* Node 09: Training & HP Agent */}
          <div
            className={`p-4 rounded-xl border relative transition ${
              isTrainDone
                ? "bg-blue-950/40 border-blue-500/80 shadow-md shadow-blue-500/10"
                : "bg-slate-950/60 border-slate-800"
            }`}
          >
            <span className="w-6 h-6 rounded-full bg-blue-600 text-white font-bold text-xs flex items-center justify-center absolute -top-2.5 -left-2.5 shadow">
              09
            </span>
            <span className="text-xs font-bold text-white block mt-1">Training & HP Agent</span>
            <span className="text-[10px] text-slate-400 block mt-0.5">Model Weights (.pkl)</span>
            <div className="mt-3 flex items-center gap-1.5 text-[11px]">
              {isTrainDone ? (
                <span className="text-emerald-400 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Trained
                </span>
              ) : isDataDone ? (
                <span className="text-blue-400 flex items-center gap-1 animate-pulse">
                  <Clock className="w-3.5 h-3.5" /> Training
                </span>
              ) : (
                <span className="text-slate-500">Pending</span>
              )}
            </div>
          </div>

          {/* Node 10: Eval Gate Agent */}
          <div
            className={`p-4 rounded-xl border relative transition ${
              isEvalDone
                ? "bg-emerald-950/40 border-emerald-500/80 shadow-md shadow-emerald-500/10"
                : "bg-slate-950/60 border-slate-800"
            }`}
          >
            <span className="w-6 h-6 rounded-full bg-emerald-600 text-white font-bold text-xs flex items-center justify-center absolute -top-2.5 -left-2.5 shadow">
              10
            </span>
            <span className="text-xs font-bold text-white block mt-1">Eval Gate Agent</span>
            <span className="text-[10px] text-slate-400 block mt-0.5">SLA Benchmarking</span>
            <div className="mt-3 flex items-center gap-1.5 text-[11px]">
              {isEvalDone ? (
                <span className="text-emerald-400 flex items-center gap-1 font-semibold">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Promoted
                </span>
              ) : isTrainDone ? (
                <span className="text-emerald-400 flex items-center gap-1 animate-pulse">
                  <Clock className="w-3.5 h-3.5" /> Benchmarking
                </span>
              ) : (
                <span className="text-slate-500">Pending</span>
              )}
            </div>
          </div>

          {/* Node 11: Security Sentinel */}
          <div
            className={`p-4 rounded-xl border relative transition ${
              isSecurityDone
                ? "bg-rose-950/30 border-rose-500/70 shadow-md shadow-rose-500/10"
                : "bg-slate-950/60 border-slate-800"
            }`}
          >
            <span className="w-6 h-6 rounded-full bg-rose-600 text-white font-bold text-xs flex items-center justify-center absolute -top-2.5 -left-2.5 shadow">
              11
            </span>
            <span className="text-xs font-bold text-white block mt-1">Security Sentinel</span>
            <span className="text-[10px] text-slate-400 block mt-0.5">AgentShield Invariants</span>
            <div className="mt-3 flex items-center gap-1.5 text-[11px]">
              {isSecurityDone ? (
                <span className="text-emerald-400 flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5" /> 0 Secrets Found
                </span>
              ) : isEvalDone ? (
                <span className="text-rose-400 flex items-center gap-1 animate-pulse">
                  <Clock className="w-3.5 h-3.5" /> Scanning
                </span>
              ) : (
                <span className="text-slate-500">Pending</span>
              )}
            </div>
          </div>

          {/* Node 12: Packager & Deployer */}
          <div
            className={`p-4 rounded-xl border relative transition ${
              isDeployDone
                ? "bg-amber-950/40 border-amber-500/80 shadow-md shadow-amber-500/10"
                : isAwaitingHITL
                ? "bg-amber-950/30 border-amber-500/70 animate-pulse shadow-md"
                : "bg-slate-950/60 border-slate-800"
            }`}
          >
            <span className="w-6 h-6 rounded-full bg-amber-600 text-white font-bold text-xs flex items-center justify-center absolute -top-2.5 -left-2.5 shadow">
              12
            </span>
            <span className="text-xs font-bold text-white block mt-1">Packager & Deployer</span>
            <span className="text-[10px] text-slate-400 block mt-0.5">Azure Container Apps</span>
            <div className="mt-3 flex items-center gap-1.5 text-[11px]">
              {isDeployDone ? (
                <span className="text-emerald-400 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Live in Azure
                </span>
              ) : isAwaitingHITL ? (
                <span className="text-amber-400 font-bold flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5" /> Awaiting Sign-off
                </span>
              ) : (
                <span className="text-slate-500">Pending</span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* HUMAN-IN-THE-LOOP (HITL) APPROVAL MODAL BANNER */}
      {isAwaitingHITL && (
        <div className="bg-gradient-to-r from-amber-950/60 via-slate-900 to-amber-950/60 border-2 border-amber-500/80 p-6 rounded-xl shadow-2xl space-y-4 animate-fade-in">
          <div className="flex justify-between items-start">
            <div>
              <span className="px-2.5 py-1 rounded text-xs font-bold bg-amber-500 text-slate-950 uppercase tracking-wider inline-flex items-center gap-1">
                <AlertTriangle className="w-3.5 h-3.5" /> Human-in-the-Loop Checkpoint
              </span>
              <h3 className="text-lg font-bold text-white mt-2">
                Candidate Model Qualified: Authorization Required for Azure Cloud Deployment
              </h3>
              <p className="text-xs text-slate-300 mt-1 max-w-2xl leading-relaxed">
                The candidate model successfully passed all statistical drift gates, defeated the production champion baseline, met the p95 latency budget, and certified AgentShield zero-secret compliance. Confirm promotion to live Azure Container Apps.
              </p>
            </div>

            <div className="flex gap-3">
              <button
                disabled={approving}
                onClick={() => handleApproval(false)}
                className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-rose-400 border border-rose-500/30 rounded-lg text-xs font-bold transition flex items-center gap-1.5"
              >
                <XCircle className="w-4 h-4" /> Reject Deployment
              </button>
              <button
                disabled={approving}
                onClick={() => handleApproval(true)}
                className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold transition shadow-lg shadow-emerald-500/20 flex items-center gap-2 cursor-pointer"
              >
                <CheckCircle2 className="w-4 h-4" /> {approving ? "Deploying..." : "Approve & Deploy to Azure"}
              </button>
            </div>
          </div>

          {/* Quick Metrics Comparison Table inside HITL Modal */}
          {statusData?.eval_gate_result && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2 text-xs font-mono">
              <div className="bg-slate-950/80 p-3 rounded-lg border border-slate-800">
                <span className="text-slate-500 block text-[10px]">Challenger F1</span>
                <span className="text-emerald-400 text-base font-bold">
                  {statusData.eval_gate_result.challenger_f1}
                </span>
                <span className="text-[10px] text-slate-500 block mt-0.5">
                  Champion: {statusData.eval_gate_result.champion_f1}
                </span>
              </div>
              <div className="bg-slate-950/80 p-3 rounded-lg border border-slate-800">
                <span className="text-slate-500 block text-[10px]">Benchmark p95 Latency</span>
                <span className="text-blue-400 text-base font-bold">
                  {statusData.eval_gate_result.p95_ms} ms
                </span>
                <span className="text-[10px] text-slate-500 block mt-0.5">
                  SLA Budget: {statusData.eval_gate_result.sla_p95_budget_ms} ms
                </span>
              </div>
              <div className="bg-slate-950/80 p-3 rounded-lg border border-slate-800">
                <span className="text-slate-500 block text-[10px]">Security Audit</span>
                <span className="text-emerald-400 text-base font-bold">PASS</span>
                <span className="text-[10px] text-slate-500 block mt-0.5">0 Hardcoded Secrets</span>
              </div>
              <div className="bg-slate-950/80 p-3 rounded-lg border border-slate-800">
                <span className="text-slate-500 block text-[10px]">Azure Target</span>
                <span className="text-purple-400 text-base font-bold">ACA</span>
                <span className="text-[10px] text-slate-500 block mt-0.5">Blue-Green Split (100%)</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Deployment Live Success Banner */}
      {statusData?.deploy_result && (
        <div className="bg-emerald-950/30 border border-emerald-500/50 p-5 rounded-xl text-xs space-y-2">
          <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            Candidate Model Live in Production (Azure Container Apps)
          </div>
          <div className="text-slate-300 font-mono flex items-center gap-2">
            <span>Prediction API:</span>
            <a
              href={statusData.deploy_result.endpoint}
              target="_blank"
              rel="noreferrer"
              className="text-blue-400 underline font-semibold"
            >
              {statusData.deploy_result.endpoint}
            </a>
          </div>
        </div>
      )}

      {/* Streaming Terminal for Agent Thoughts & Tool Logs */}
      <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden shadow-2xl">
        <div className="bg-slate-900/90 px-4 py-2.5 border-b border-slate-800 flex justify-between items-center text-xs">
          <span className="font-mono text-slate-300 font-semibold flex items-center gap-2">
            <Terminal className="w-4 h-4 text-emerald-400" />
            Live Agent Execution & Tool Stream (LangGraph State)
          </span>
          <span className="text-[10px] text-slate-500 font-mono">
            {liveLogs.length} events logged
          </span>
        </div>
        <div className="p-4 font-mono text-xs text-slate-300 space-y-1.5 max-h-96 overflow-y-auto bg-slate-950/90">
          {liveLogs.map((log, i) => (
            <div key={i} className="leading-relaxed hover:bg-slate-900/40 px-1 rounded">
              {log.includes("Error") ? (
                <span className="text-rose-400">{log}</span>
              ) : log.includes("PROMOTED") || log.includes("PASSED") ? (
                <span className="text-emerald-400 font-semibold">{log}</span>
              ) : log.includes("Security Sentinel") ? (
                <span className="text-rose-300">{log}</span>
              ) : log.includes("Eval Gate") ? (
                <span className="text-purple-300">{log}</span>
              ) : log.includes("Training Agent") ? (
                <span className="text-blue-300">{log}</span>
              ) : (
                <span className="text-slate-300">{log}</span>
              )}
            </div>
          ))}
          <div ref={logEndRef} />
        </div>
      </div>
    </div>
  );
};
