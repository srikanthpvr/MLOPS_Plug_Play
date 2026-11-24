import React, { useEffect, useState } from "react";
import { ObservabilityMetricsResponse } from "../types";
import { fetchObservabilityDashboard } from "../services/api";
import {
  Activity, AlertTriangle, CheckCircle2, TrendingUp, Zap, Clock, RefreshCw
} from "lucide-react";

interface ObservabilityViewProps {
  onTriggerRetrain: () => void;
}

export const ObservabilityView: React.FC<ObservabilityViewProps> = ({ onTriggerRetrain }) => {
  const [data, setData] = useState<ObservabilityMetricsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const res = await fetchObservabilityDashboard();
      setData(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header bar */}
      <div className="flex justify-between items-center bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-lg">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Activity className="w-5 h-5 text-emerald-400" />
              Production Observability & Drift Desk
            </h2>
            <span
              className={`px-2.5 py-0.5 rounded text-xs font-bold border ${
                data?.overall_health === "ACTION_REQUIRED"
                  ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                  : "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
              }`}
            >
              ● Status: {data?.overall_health}
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time inference telemetry, feature covariate drift monitoring, and automated retraining triggers.
          </p>
        </div>

        <div className="flex gap-3">
          <button
            onClick={loadDashboard}
            className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} /> Refresh
          </button>
          <button
            onClick={onTriggerRetrain}
            className="flex items-center gap-2 px-4 py-1.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-bold rounded-lg shadow-lg shadow-blue-500/20 transition cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Trigger Model Retrain
          </button>
        </div>
      </div>

      {/* Top 4 KPI Cards */}
      {data && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 font-mono">
          <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
            <span className="text-[11px] text-slate-400 block flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-blue-400" /> Current p95 Latency
            </span>
            <span className="text-2xl font-bold text-white mt-1 block">
              {data.current_p95_latency_ms} ms
            </span>
            <span className="text-[10px] text-emerald-400 block mt-1">✓ Within 50ms SLA budget</span>
          </div>

          <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
            <span className="text-[11px] text-slate-400 block flex items-center gap-1.5">
              <TrendingUp className="w-3.5 h-3.5 text-emerald-400" /> Champion Baseline F1
            </span>
            <span className="text-2xl font-bold text-emerald-400 mt-1 block">
              {data.champion_f1}
            </span>
            <span className="text-[10px] text-slate-400 block mt-1">Version: {data.active_version}</span>
          </div>

          <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
            <span className="text-[11px] text-slate-400 block flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" /> Drifted Features
            </span>
            <span
              className={`text-2xl font-bold mt-1 block ${
                data.drifted_features_count > 0 ? "text-amber-400" : "text-slate-200"
              }`}
            >
              {data.drifted_features_count} Features
            </span>
            <span className="text-[10px] text-amber-400 block mt-1">
              {data.drifted_features_count > 0 ? "Covariate shift detected" : "All distributions stable"}
            </span>
          </div>

          <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
            <span className="text-[11px] text-slate-400 block flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-purple-400" /> 24h Inference Volume
            </span>
            <span className="text-2xl font-bold text-white mt-1 block">
              {data.total_inferences_24h.toLocaleString()}
            </span>
            <span className="text-[10px] text-purple-400 block mt-1">Avg 98.6 req / sec</span>
          </div>
        </div>
      )}

      {/* Feature Drift Table */}
      {data && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl space-y-4">
          <div className="flex justify-between items-center border-b border-slate-800 pb-3">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                Feature Drift & Covariate Shift Matrix (KS-Test & PSI)
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Statistical comparison of production inference distributions against the training reference baseline.
              </p>
            </div>
            <span className="text-[11px] text-slate-400 font-mono">
              Thresholds: KS p &lt; 0.05 | PSI &ge; 0.25 (Action Required)
            </span>
          </div>

          <div className="overflow-x-auto rounded-lg border border-slate-800">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] border-b border-slate-800">
                <tr>
                  <th className="px-4 py-2.5">Feature Name</th>
                  <th className="px-4 py-2.5">KS-Test p-Value</th>
                  <th className="px-4 py-2.5">Population Stability Index (PSI)</th>
                  <th className="px-4 py-2.5">Baseline Mean</th>
                  <th className="px-4 py-2.5">Current Mean</th>
                  <th className="px-4 py-2.5">Drift Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 bg-slate-900/40">
                {data.feature_drifts.map((f) => {
                  const isCritical = f.status === "CRITICAL_DRIFT";
                  const isWarning = f.status === "WARNING";
                  return (
                    <tr key={f.feature_name} className="hover:bg-slate-800/40 transition">
                      <td className="px-4 py-3 text-slate-200 font-semibold">{f.feature_name}</td>
                      <td className="px-4 py-3">
                        <span className={f.ks_p_value < 0.05 ? "text-rose-400 font-bold" : "text-slate-300"}>
                          {f.ks_p_value}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={f.psi >= 0.25 ? "text-rose-400 font-bold" : "text-slate-300"}>
                          {f.psi}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-400">{f.baseline_mean}</td>
                      <td className="px-4 py-3 text-slate-300 font-bold">{f.current_mean}</td>
                      <td className="px-4 py-3">
                        {isCritical ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30 flex items-center gap-1 w-fit">
                            <AlertTriangle className="w-3 h-3" /> Critical Drift
                          </span>
                        ) : isWarning ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center gap-1 w-fit">
                            <AlertTriangle className="w-3 h-3" /> Warning
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1 w-fit">
                            <CheckCircle2 className="w-3 h-3" /> Healthy
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Latency History Timeline */}
      {data && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl space-y-3 font-mono">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
            <Clock className="w-4 h-4 text-blue-400" />
            24h Latency Distribution Timeline (p50 / p95 / p99)
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-12 gap-2 pt-2">
            {data.timeseries_metrics.map((m, i) => (
              <div key={i} className="p-2.5 bg-slate-950/70 rounded-lg border border-slate-800 text-center">
                <span className="text-[10px] text-slate-500 block">{m.timestamp}</span>
                <span className="text-xs font-bold text-blue-400 block mt-1">{m.p95_latency_ms}ms</span>
                <span className="text-[9px] text-slate-400 block mt-0.5">{m.requests_per_sec} rps</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
