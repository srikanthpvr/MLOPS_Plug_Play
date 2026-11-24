import React, { useEffect, useState } from "react";
import { DatasetSummary, DatasetPreviewResponse } from "../types";
import { fetchDatasets, fetchDatasetPreview } from "../services/api";
import { Database, Table, AlertCircle, CheckCircle2, RefreshCw, Layers } from "lucide-react";

interface DataHubViewProps {
  onSelectDatasetForTraining: (datasetName: string) => void;
}

export const DataHubView: React.FC<DataHubViewProps> = ({ onSelectDatasetForTraining }) => {
  const [datasets, setDatasets] = useState<DatasetSummary[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<string>("");
  const [preview, setPreview] = useState<DatasetPreviewResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadDatasets();
  }, []);

  const loadDatasets = async () => {
    setLoading(true);
    try {
      const data = await fetchDatasets();
      setDatasets(data);
      if (data.length > 0) {
        // Default to current drifted dataset if exists
        const defaultDs = data.find(d => !d.is_baseline) || data[0];
        setSelectedDataset(defaultDs.name);
        loadPreview(defaultDs.name);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadPreview = async (name: string) => {
    try {
      const p = await fetchDatasetPreview(name);
      setPreview(p);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSelect = (name: string) => {
    setSelectedDataset(name);
    loadPreview(name);
  };

  return (
    <div className="space-y-6">
      {/* Header bar */}
      <div className="flex justify-between items-center bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-lg">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Database className="w-5 h-5 text-blue-400" />
            Data Hub & Feature Store Studio
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Connect Azure Blob, ADLS Gen2, DVC remotes, or inspect dataset schemas and drift baselines.
          </p>
        </div>
        <button
          onClick={loadDatasets}
          className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} /> Refresh Hub
        </button>
      </div>

      {/* Dataset Selection Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {datasets.map((ds) => {
          const isSelected = selectedDataset === ds.name;
          return (
            <div
              key={ds.name}
              onClick={() => handleSelect(ds.name)}
              className={`p-4 rounded-xl border cursor-pointer transition-all ${
                isSelected
                  ? "bg-blue-950/40 border-blue-500 shadow-md shadow-blue-500/10"
                  : "bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-850"
              }`}
            >
              <div className="flex justify-between items-start mb-2">
                <span className="font-mono text-sm font-bold text-white truncate max-w-[200px]">
                  {ds.name}
                </span>
                {ds.is_baseline ? (
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/10 text-purple-400 border border-purple-500/30 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" /> Baseline
                  </span>
                ) : (
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" /> Inference Batch
                  </span>
                )}
              </div>
              <div className="grid grid-cols-3 gap-2 mt-3 text-[11px] text-slate-400">
                <div>
                  <span className="block text-slate-500 text-[10px]">Rows</span>
                  <span className="font-semibold text-slate-200">{ds.rows.toLocaleString()}</span>
                </div>
                <div>
                  <span className="block text-slate-500 text-[10px]">Columns</span>
                  <span className="font-semibold text-slate-200">{ds.columns}</span>
                </div>
                <div>
                  <span className="block text-slate-500 text-[10px]">Size</span>
                  <span className="font-semibold text-slate-200">{ds.size_kb} KB</span>
                </div>
              </div>
              <div className="mt-4 flex gap-2">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelectDatasetForTraining(ds.name);
                  }}
                  className="w-full py-1.5 px-3 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg transition text-center"
                >
                  Configure Retraining ➜
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Dataset Preview & Schema Profiler */}
      {preview && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl space-y-4">
          <div className="flex justify-between items-center border-b border-slate-800 pb-3">
            <div>
              <h3 className="text-md font-bold text-white flex items-center gap-2">
                <Table className="w-4 h-4 text-emerald-400" />
                Schema & Profile: <span className="font-mono text-blue-400">{preview.name}</span>
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Total Columns: {preview.total_columns} | Total Rows: {preview.total_rows.toLocaleString()}
              </p>
            </div>
            <button
              onClick={() => onSelectDatasetForTraining(preview.name)}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs rounded-lg transition shadow-md shadow-emerald-500/10"
            >
              Train Model with this Dataset
            </button>
          </div>

          {/* Column Profiles */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
            {preview.columns.map((col) => (
              <div key={col.name} className="p-2.5 bg-slate-950/80 rounded-lg border border-slate-800 text-xs">
                <span className="font-semibold text-slate-200 block truncate" title={col.name}>
                  {col.name}
                </span>
                <span className="text-[10px] text-blue-400 font-mono block mt-0.5">{col.dtype}</span>
                <div className="mt-2 text-[10px] text-slate-400 flex justify-between">
                  <span>Nulls:</span>
                  <span className={col.null_pct > 0 ? "text-amber-400" : "text-emerald-400"}>
                    {col.null_pct}%
                  </span>
                </div>
                <div className="text-[10px] text-slate-400 flex justify-between mt-0.5">
                  <span>Unique:</span>
                  <span className="text-slate-300 font-mono">{col.unique_count}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Sample Rows Table */}
          <div className="mt-4">
            <h4 className="text-xs font-semibold text-slate-400 mb-2 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-slate-400" /> First 10 Sample Ingestion Rows
            </h4>
            <div className="overflow-x-auto rounded-lg border border-slate-800">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] border-b border-slate-800">
                  <tr>
                    {preview.columns.map((c) => (
                      <th key={c.name} className="px-3 py-2 whitespace-nowrap">
                        {c.name}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 bg-slate-900/40">
                  {preview.preview_rows.map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/50 transition">
                      {preview.columns.map((c) => (
                        <td key={c.name} className="px-3 py-2 text-slate-300 whitespace-nowrap">
                          {String(row[c.name])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
