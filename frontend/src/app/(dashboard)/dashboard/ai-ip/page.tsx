"use client";

import { Header } from "@/components/layout/header";
import { useState, useEffect, useCallback } from "react";
import {
  Brain,
  Plus,
  Database,
  Cpu,
  Server,
  Globe,
  CheckCircle2,
  ArrowRight,
  TrendingUp,
  Loader2,
  Shield,
  AlertCircle,
} from "lucide-react";
import api from "@/lib/api";
import { toast } from "sonner";
import type { AIAssetInput, AssetType } from "@/types";

const assetTypeConfig: Record<AssetType, { icon: typeof Database; label: string; color: string }> = {
  training_data: { icon: Database, label: "Training Data", color: "text-chart-1 bg-chart-1/10" },
  model_weights: { icon: Cpu, label: "Model Weights", color: "text-chart-4 bg-chart-4/10" },
  inference_infra: { icon: Server, label: "Inference Infra", color: "text-chart-3 bg-chart-3/10" },
  deployed_app: { icon: Globe, label: "Deployed App", color: "text-chart-2 bg-chart-2/10" },
};

interface AIAsset {
  id: string;
  asset_name: string;
  asset_type: AssetType;
  estimated_value: number;
  confidence_score: number;
  valuation_method: string;
  ias38_compliant: boolean;
  asc350_compliant: boolean;
  description: string;
}

export default function AIIPPage() {
  const [assets, setAssets] = useState<AIAsset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showNewAsset, setShowNewAsset] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [newAsset, setNewAsset] = useState<AIAssetInput>({
    asset_name: "",
    asset_type: "training_data",
    description: "",
  });

  const fetchAssets = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get("/ai-ip/assets");
      setAssets(res.data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to load AI assets";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAssets();
  }, [fetchAssets]);

  const totalValue = assets.reduce((s, a) => s + a.estimated_value, 0);
  const avgConfidence = assets.length > 0
    ? assets.reduce((s, a) => s + a.confidence_score, 0) / assets.length
    : 0;

  const formatCurrency = (v: number) => {
    if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
    if (v >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
    if (v >= 1e3) return `$${(v / 1e3).toFixed(0)}K`;
    return `$${v}`;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post("/ai-ip/valuate", newAsset);
      toast.success("AI-IP valuation started!");
      setShowNewAsset(false);
      setNewAsset({ asset_name: "", asset_type: "training_data", description: "" });
      fetchAssets();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to start valuation";
      toast.error(message);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div>
        <Header
          title="AI-IP Valuation"
          description="Value your AI intellectual property with cryptographic proofs"
        />
        <div className="flex items-center justify-center p-24">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <Header
          title="AI-IP Valuation"
          description="Value your AI intellectual property with cryptographic proofs"
        />
        <div className="flex flex-col items-center justify-center gap-4 p-24">
          <AlertCircle className="h-10 w-10 text-destructive" />
          <p className="text-sm text-muted-foreground">{error}</p>
          <button
            onClick={fetchAssets}
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <Header
        title="AI-IP Valuation"
        description="Value your AI intellectual property with cryptographic proofs"
        actions={
          <button
            onClick={() => setShowNewAsset(true)}
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" />
            New Valuation
          </button>
        }
      />

      <div className="p-6">
        {/* Stats */}
        <div className="mb-8 grid gap-4 md:grid-cols-4">
          {[
            { label: "Total AI-IP Value", value: formatCurrency(totalValue), icon: TrendingUp, color: "text-chart-4 bg-chart-4/10" },
            { label: "Assets Valued", value: assets.length.toString(), icon: Brain, color: "text-primary bg-primary/10" },
            { label: "Avg Confidence", value: assets.length > 0 ? `${(avgConfidence * 100).toFixed(0)}%` : "N/A", icon: Shield, color: "text-chart-2 bg-chart-2/10" },
            { label: "IAS 38 Compliant", value: `${assets.filter(a => a.ias38_compliant).length}/${assets.length}`, icon: CheckCircle2, color: "text-chart-3 bg-chart-3/10" },
          ].map((s) => (
            <div key={s.label} className="rounded-xl border bg-white p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">{s.label}</p>
                  <p className="mt-1 text-2xl font-bold text-foreground">{s.value}</p>
                </div>
                <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${s.color}`}>
                  <s.icon className="h-5 w-5" />
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Value Breakdown */}
        <div className="mb-8 rounded-xl border bg-white p-6">
          <h2 className="mb-4 font-semibold text-foreground">Value Breakdown by Asset Type</h2>
          <div className="flex gap-4">
            {(Object.entries(assetTypeConfig) as [AssetType, typeof assetTypeConfig.training_data][]).map(([type, config]) => {
              const typeAssets = assets.filter(a => a.asset_type === type);
              const typeValue = typeAssets.reduce((s, a) => s + a.estimated_value, 0);
              const pct = totalValue > 0 ? (typeValue / totalValue) * 100 : 0;
              return (
                <div key={type} className="flex-1 rounded-lg border p-4">
                  <div className="mb-2 flex items-center gap-2">
                    <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${config.color}`}>
                      <config.icon className="h-4 w-4" />
                    </div>
                    <span className="text-sm font-medium">{config.label}</span>
                  </div>
                  <div className="text-xl font-bold text-foreground">{formatCurrency(typeValue)}</div>
                  <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-secondary">
                    <div className="h-full rounded-full bg-primary" style={{ width: `${pct}%` }} />
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">{pct.toFixed(1)}% of total</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* New Valuation Modal */}
        {showNewAsset && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="w-full max-w-2xl rounded-xl bg-white p-6">
              <h2 className="mb-6 text-lg font-semibold">New AI-IP Valuation</h2>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="mb-1.5 block text-sm font-medium">Asset Name</label>
                  <input
                    type="text"
                    value={newAsset.asset_name}
                    onChange={(e) => setNewAsset(p => ({ ...p, asset_name: e.target.value }))}
                    placeholder="e.g., Proprietary LLM Training Dataset"
                    required
                    className="w-full rounded-lg border px-4 py-2.5 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                  />
                </div>

                <div>
                  <label className="mb-1.5 block text-sm font-medium">Asset Type</label>
                  <div className="grid grid-cols-2 gap-3">
                    {(Object.entries(assetTypeConfig) as [AssetType, typeof assetTypeConfig.training_data][]).map(([type, config]) => (
                      <button
                        key={type}
                        type="button"
                        onClick={() => setNewAsset(p => ({ ...p, asset_type: type }))}
                        className={`flex items-center gap-3 rounded-lg border p-3 text-left transition-colors ${
                          newAsset.asset_type === type
                            ? "border-primary bg-primary/5"
                            : "hover:bg-secondary"
                        }`}
                      >
                        <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${config.color}`}>
                          <config.icon className="h-4 w-4" />
                        </div>
                        <span className="text-sm font-medium">{config.label}</span>
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="mb-1.5 block text-sm font-medium">Description</label>
                  <textarea
                    value={newAsset.description}
                    onChange={(e) => setNewAsset(p => ({ ...p, description: e.target.value }))}
                    placeholder="Describe the asset, including key characteristics, size, and any relevant metrics..."
                    rows={3}
                    className="w-full rounded-lg border px-4 py-2.5 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="mb-1.5 block text-sm font-medium">Training Cost ($)</label>
                    <input
                      type="number"
                      value={newAsset.training_cost || ""}
                      onChange={(e) => setNewAsset(p => ({ ...p, training_cost: Number(e.target.value) }))}
                      placeholder="e.g., 500000"
                      className="w-full rounded-lg border px-4 py-2.5 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                    />
                  </div>
                  <div>
                    <label className="mb-1.5 block text-sm font-medium">Compute Hours</label>
                    <input
                      type="number"
                      value={newAsset.training_compute_hours || ""}
                      onChange={(e) => setNewAsset(p => ({ ...p, training_compute_hours: Number(e.target.value) }))}
                      placeholder="e.g., 10000"
                      className="w-full rounded-lg border px-4 py-2.5 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                    />
                  </div>
                  <div>
                    <label className="mb-1.5 block text-sm font-medium">Monthly Revenue ($)</label>
                    <input
                      type="number"
                      value={newAsset.monthly_revenue || ""}
                      onChange={(e) => setNewAsset(p => ({ ...p, monthly_revenue: Number(e.target.value) }))}
                      placeholder="e.g., 150000"
                      className="w-full rounded-lg border px-4 py-2.5 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                    />
                  </div>
                  <div>
                    <label className="mb-1.5 block text-sm font-medium">Model Parameters</label>
                    <input
                      type="number"
                      value={newAsset.model_parameters || ""}
                      onChange={(e) => setNewAsset(p => ({ ...p, model_parameters: Number(e.target.value) }))}
                      placeholder="e.g., 70000000000"
                      className="w-full rounded-lg border px-4 py-2.5 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                    />
                  </div>
                </div>

                <div className="flex justify-end gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowNewAsset(false)}
                    className="rounded-lg border px-4 py-2 text-sm font-medium hover:bg-secondary"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="inline-flex items-center gap-2 rounded-lg bg-primary px-6 py-2 text-sm font-medium text-white hover:bg-primary/90 disabled:opacity-50"
                  >
                    {submitting ? (
                      <><Loader2 className="h-4 w-4 animate-spin" /> Processing...</>
                    ) : (
                      <>Start Valuation<ArrowRight className="h-4 w-4" /></>
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Assets Grid */}
        {assets.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-xl border bg-white p-16">
            <Brain className="mb-4 h-12 w-12 text-muted-foreground/50" />
            <h3 className="mb-1 text-lg font-semibold text-foreground">No AI assets yet</h3>
            <p className="mb-6 text-sm text-muted-foreground">
              Start by creating a new valuation to assess your AI intellectual property.
            </p>
            <button
              onClick={() => setShowNewAsset(true)}
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90"
            >
              <Plus className="h-4 w-4" />
              New Valuation
            </button>
          </div>
        ) : (
          <div className="grid gap-6 md:grid-cols-2">
            {assets.map((asset) => {
              const config = assetTypeConfig[asset.asset_type];
              return (
                <div key={asset.id} className="rounded-xl border bg-white p-6 transition-shadow hover:shadow-md">
                  <div className="mb-4 flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${config.color}`}>
                        <config.icon className="h-5 w-5" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-foreground">{asset.asset_name}</h3>
                        <p className="text-sm text-muted-foreground">{config.label}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xl font-bold text-foreground">{formatCurrency(asset.estimated_value)}</div>
                      <div className="text-xs text-chart-2">{(asset.confidence_score * 100).toFixed(0)}% confidence</div>
                    </div>
                  </div>

                  <p className="mb-4 text-sm text-muted-foreground">{asset.description}</p>

                  <div className="mb-4 flex flex-wrap gap-2">
                    <span className="rounded-md bg-secondary px-2 py-0.5 text-xs font-medium capitalize text-foreground">
                      {asset.valuation_method.replace(/_/g, " ")}
                    </span>
                    {asset.ias38_compliant && (
                      <span className="inline-flex items-center gap-1 rounded-md bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700">
                        <CheckCircle2 className="h-3 w-3" /> IAS 38
                      </span>
                    )}
                    {asset.asc350_compliant && (
                      <span className="inline-flex items-center gap-1 rounded-md bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700">
                        <CheckCircle2 className="h-3 w-3" /> ASC 350
                      </span>
                    )}
                  </div>

                  {/* Confidence Bar */}
                  <div>
                    <div className="mb-1 flex items-center justify-between text-xs">
                      <span className="text-muted-foreground">Confidence Score</span>
                      <span className="font-medium">{(asset.confidence_score * 100).toFixed(0)}%</span>
                    </div>
                    <div className="h-1.5 overflow-hidden rounded-full bg-secondary">
                      <div
                        className="h-full rounded-full bg-chart-2"
                        style={{ width: `${asset.confidence_score * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
