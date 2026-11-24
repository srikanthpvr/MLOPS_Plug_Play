import React, { useState } from "react";
import { DataHubView } from "./views/DataHubView";
import { ModelLabView } from "./views/ModelLabView";
import { AgentCanvasView } from "./views/AgentCanvasView";
import { ObservabilityView } from "./views/ObservabilityView";
import {
  Database, Sliders, PlayCircle, Activity, Cpu
} from "lucide-react";

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"data" | "model" | "agent" | "observability">("data");
  const [selectedDataset, setSelectedDataset] = useState<string>("current_drifted_churn.csv");
  const [activeRunId, setActiveRunId] = useState<string>("");

  const handleSelectDatasetForTraining = (datasetName: string) => {
    setSelectedDataset(datasetName);
    setActiveTab("model");
  };

  const handleLaunchAgentSuite = (runId: string) => {
    setActiveRunId(runId);
    setActiveTab("agent");
  };

  const handleTriggerRetrain = () => {
    setActiveTab("model");
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Navigation Bar */}
      <header className="bg-slate-900 border-b border-slate-800 px-6 py-4 sticky top-0 z-50 shadow-md">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Cpu className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold text-white tracking-tight">
                  MLOps Build Agent Suite
                </h1>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/30">
                  Azure + LangGraph
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Plug-and-Play Autonomous MLOps Engineering Console
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex bg-slate-950 p-1.5 rounded-xl border border-slate-800 text-xs font-semibold">
            <button
              onClick={() => setActiveTab("data")}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg transition cursor-pointer ${
                activeTab === "data"
                  ? "bg-blue-600 text-white shadow-md shadow-blue-500/20"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Database className="w-4 h-4" /> Data Hub
            </button>
            <button
              onClick={() => setActiveTab("model")}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg transition cursor-pointer ${
                activeTab === "model"
                  ? "bg-purple-600 text-white shadow-md shadow-purple-500/20"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Sliders className="w-4 h-4" /> Model Lab
            </button>
            <button
              onClick={() => setActiveTab("agent")}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg transition cursor-pointer relative ${
                activeTab === "agent"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-500/20"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <PlayCircle className="w-4 h-4" /> Agent Canvas
              {activeRunId && (
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping absolute top-1.5 right-1.5"></span>
              )}
            </button>
            <button
              onClick={() => setActiveTab("observability")}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg transition cursor-pointer ${
                activeTab === "observability"
                  ? "bg-emerald-600 text-white shadow-md shadow-emerald-500/20"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Activity className="w-4 h-4" /> Observability Desk
            </button>
          </nav>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl mx-auto w-full p-6">
        {activeTab === "data" && (
          <DataHubView onSelectDatasetForTraining={handleSelectDatasetForTraining} />
        )}
        {activeTab === "model" && (
          <ModelLabView
            initialDataset={selectedDataset}
            onLaunchAgentSuite={handleLaunchAgentSuite}
          />
        )}
        {activeTab === "agent" && (
          <AgentCanvasView runId={activeRunId || "demo-run-init"} />
        )}
        {activeTab === "observability" && (
          <ObservabilityView onTriggerRetrain={handleTriggerRetrain} />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 px-6 py-4 text-center text-xs text-slate-500">
        Autonomous MLOps Build Agent Suite • LangChain, LangSmith, LangGraph, Azure Container Apps • NCS / Antigravity Platform
      </footer>
    </div>
  );
};
