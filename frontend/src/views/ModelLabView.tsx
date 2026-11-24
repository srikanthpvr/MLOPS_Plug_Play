import React, { useEffect, useState } from "react";
import { ModelCatalogItem, ChampionModelMetadata } from "../types";
import { fetchModelCatalog, fetchChampionModel, triggerAgentRun } from "../services/api";
import { Sliders, Cpu, Play, Award, Zap } from "lucide-react";

interface ModelLabViewProps {
  initialDataset: string;
  onLaunchAgentSuite: (runId: string) => void;
}

export const ModelLabView: React.FC<ModelLabViewProps> = ({
  initialDataset,
  onLaunchAgentSuite
}) => {
  const [catalog, setCatalog] = useState<ModelCatalogItem[]>([]);
  const [champion, setChampion] = useState<ChampionModelMetadata | null>(null);
  const [selectedModelId, setSelectedModelId] = useState<string>("lightgbm");
  const [hyperparams, setHyperparams] = useState<Record<string, any>>({});
  const [slaP95Ms, setSlaP95Ms] = useState<number>(50.0);
  const [targetColumn, setTargetColumn] = useState<string>("churn");
  const [selectedDataset, setSelectedDataset] = useState<string>(initialDataset || "current_drifted_churn.csv");
  const [launching, setLaunching] = useState<boolean>(false);

  useEffect(() => {
    loadModels();
  }, []);

  useEffect(() => {
    if (initialDataset) {
      setSelectedDataset(initialDataset);
    }
  }, [initialDataset]);

  const loadModels = async () => {
    try {
      const [cats, champ] = await Promise.all([fetchModelCatalog(), fetchChampionModel()]);
      setCatalog(cats);
      setChampion(champ);
      if (cats.length > 0) {
        setSelectedModelId(cats[0].id);
        setHyperparams(cats[0].default_hyperparameters);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleModelChange = (modelId: string) => {
    setSelectedModelId(modelId);
    const item = catalog.find(m => m.id === modelId);
    if (item) {
      setHyperparams(item.default_hyperparameters);
    }
  };

  const handleParamChange = (name: string, value: any) => {
    setHyperparams(prev => ({ ...prev, [name]: value }));
  };

  const handleLaunch = async () => {
    setLaunching(true);
    try {
      const res = await triggerAgentRun({
        dataset_name: selectedDataset,
        target_column: targetColumn,
        model_type: selectedModelId,
        hyperparameters: hyperparams,
        sla_p95_ms: slaP95Ms
      });
      onLaunchAgentSuite(res.run_id);
    } catch (err) {
      alert(`Failed to start agent run: ${err}`);
    } finally {
      setLaunching(false);
    }
  };

  const activeModel = catalog.find(m => m.id === selectedModelId);

  return (
    <div className="space-y-6">
      {/* Header bar */}
      <div className="flex justify-between items-center bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-lg">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Sliders className="w-5 h-5 text-purple-400" />
            Model Lab & Hyperparameter Workbench
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Select model architectures, configure optimization parameters, set latency SLA budgets, and dispatch the LangGraph build agents.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Model Selection & Production Champion Baseline */}
        <div className="space-y-6">
          {/* Production Champion Baseline Card */}
          {champion && (
            <div className="bg-gradient-to-br from-slate-900 to-blue-950/40 border border-blue-500/30 rounded-xl p-5 shadow-lg">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold text-blue-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Award className="w-4 h-4 text-blue-400" /> Production Champion
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                  Active in ACA
                </span>
              </div>
              <h3 className="font-bold text-white text-md">{champion.name}</h3>
              <p className="text-[11px] text-slate-400 mt-0.5">Version: {champion.version} | Target: {champion.deployment_target}</p>

              <div className="grid grid-cols-2 gap-3 mt-4 text-xs font-mono">
                <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
                  <span className="text-slate-500 block text-[10px]">Champion F1</span>
                  <span className="text-emerald-400 text-lg font-bold">{champion.f1_score}</span>
                </div>
                <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
                  <span className="text-slate-500 block text-[10px]">p95 Latency</span>
                  <span className="text-blue-400 text-lg font-bold">{champion.p95_latency_ms}ms</span>
                </div>
              </div>
            </div>
          )}

          {/* Model Catalog Selection */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-3">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <Cpu className="w-4 h-4 text-blue-400" /> Candidate Model Framework
            </h3>
            <div className="space-y-2">
              {catalog.map((m) => {
                const isSelected = selectedModelId === m.id;
                return (
                  <div
                    key={m.id}
                    onClick={() => handleModelChange(m.id)}
                    className={`p-3 rounded-lg border cursor-pointer transition ${
                      isSelected
                        ? "bg-purple-950/40 border-purple-500 text-white"
                        : "bg-slate-950/60 border-slate-800 text-slate-300 hover:border-slate-700"
                    }`}
                  >
                    <div className="flex justify-between items-center">
                      <span className="font-semibold text-xs">{m.name}</span>
                      <span className="text-[10px] text-slate-400 font-mono">{m.family}</span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">{m.description}</p>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Middle/Right: Interactive Hyperparameter Controls & SLA Config */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-6">
            <div className="border-b border-slate-800 pb-4 flex justify-between items-center">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-emerald-400" />
                  Hyperparameter Tuner: {activeModel?.name}
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  Adjust parameter boundaries. The Training Agent will train and evaluate the candidate model using these values.
                </p>
              </div>
            </div>

            {/* General Target & Dataset Config */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-slate-950/60 p-4 rounded-xl border border-slate-800 text-xs">
              <div>
                <label className="block text-slate-400 font-semibold mb-1">Target Training Dataset</label>
                <input
                  type="text"
                  value={selectedDataset}
                  onChange={(e) => setSelectedDataset(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 font-mono text-xs focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-slate-400 font-semibold mb-1">Target Classification Column</label>
                <input
                  type="text"
                  value={targetColumn}
                  onChange={(e) => setTargetColumn(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 font-mono text-xs focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>

            {/* Dynamic Model Parameter Sliders */}
            <div className="space-y-4">
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                Model Parameter Optimization
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                {activeModel?.specs.map((spec) => {
                  const currentValue = hyperparams[spec.name] ?? spec.default;
                  const isNumber = spec.type === "float" || spec.type === "int";
                  return (
                    <div key={spec.name} className="p-3.5 bg-slate-950/80 rounded-xl border border-slate-800 space-y-2">
                      <div className="flex justify-between items-center text-xs">
                        <span className="font-semibold text-slate-200">{spec.name}</span>
                        <span className="font-mono text-blue-400 font-bold bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
                          {currentValue}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500">{spec.description}</p>

                      {isNumber && spec.min_val !== undefined && spec.max_val !== undefined ? (
                        <div className="flex items-center gap-3">
                          <input
                            type="range"
                            min={spec.min_val}
                            max={spec.max_val}
                            step={spec.type === "float" ? 0.005 : 1}
                            value={currentValue}
                            onChange={(e) =>
                              handleParamChange(
                                spec.name,
                                spec.type === "float" ? parseFloat(e.target.value) : parseInt(e.target.value, 10)
                              )
                            }
                            className="w-full accent-blue-500 cursor-pointer h-1.5 bg-slate-800 rounded-lg"
                          />
                        </div>
                      ) : (
                        <input
                          type="number"
                          value={currentValue}
                          onChange={(e) => handleParamChange(spec.name, parseFloat(e.target.value))}
                          className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200 text-xs font-mono"
                        />
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Latency SLA Budget */}
            <div className="p-4 bg-slate-950/80 rounded-xl border border-slate-800 space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-xs font-bold text-amber-400 flex items-center gap-1.5">
                  <Zap className="w-3.5 h-3.5" /> Max Allowable p95 Latency SLA Budget
                </span>
                <span className="font-mono text-xs font-bold text-amber-400">{slaP95Ms} ms</span>
              </div>
              <p className="text-[11px] text-slate-400">
                The Evaluation Gate Agent will benchmark 150 batch inferences. If the candidate model's p95 latency exceeds this threshold, the model is automatically rejected.
              </p>
              <input
                type="range"
                min={5}
                max={200}
                step={5}
                value={slaP95Ms}
                onChange={(e) => setSlaP95Ms(parseFloat(e.target.value))}
                className="w-full accent-amber-500 cursor-pointer h-1.5 bg-slate-800 rounded-lg"
              />
            </div>

            {/* Launch Action */}
            <div className="pt-2">
              <button
                disabled={launching}
                onClick={handleLaunch}
                className="w-full py-3.5 px-6 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold text-sm rounded-xl transition shadow-xl shadow-indigo-500/20 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
              >
                <Play className="w-4 h-4 fill-white" />
                {launching ? "Starting LangGraph Agent Suite..." : "Dispatch Autonomous MLOps Agent Suite"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
