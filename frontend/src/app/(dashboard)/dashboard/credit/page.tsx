"use client";

import { Header } from "@/components/layout/header";
import { useState, useEffect, useCallback } from "react";
import {
  Landmark,
  Upload,
  FileSpreadsheet,
  Plus,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  TrendingUp,
  Shield,
  Loader2,
} from "lucide-react";
import api from "@/lib/api";
import { toast } from "sonner";
import type { CreditPortfolio } from "@/types";

export default function CreditPage() {
  const [portfolios, setPortfolios] = useState<CreditPortfolio[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showUpload, setShowUpload] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  const fetchPortfolios = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get("/credit/portfolios");
      setPortfolios(res.data);
    } catch {
      setError("Failed to load portfolios. Please try again.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPortfolios();
  }, [fetchPortfolios]);

  const formatCurrency = (v: number) => {
    if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
    if (v >= 1e6) return `$${(v / 1e6).toFixed(0)}M`;
    return `$${v.toLocaleString()}`;
  };

  const handleUpload = async (file: File) => {
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      await api.post("/credit/upload-loan-tape", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      toast.success("Loan tape uploaded. Verification started.");
      setShowUpload(false);
      fetchPortfolios();
    } catch {
      toast.error("Failed to upload loan tape. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleUpload(file);
  };

  const totalNAV = portfolios.reduce((sum, p) => sum + p.nav_value, 0);
  const totalLoans = portfolios.reduce((sum, p) => sum + p.loan_count, 0);
  const avgRate =
    portfolios.length > 0
      ? portfolios.reduce((sum, p) => sum + p.weighted_avg_rate, 0) / portfolios.length
      : 0;

  return (
    <div>
      <Header
        title="Private Credit"
        description="Verify loan portfolios with zero-knowledge proofs"
        actions={
          <button
            onClick={() => setShowUpload(true)}
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90"
          >
            <Upload className="h-4 w-4" />
            Upload Loan Tape
          </button>
        }
      />

      <div className="p-6">
        {/* Loading State */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-24">
            <Loader2 className="mb-4 h-10 w-10 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">Loading portfolios...</p>
          </div>
        )}

        {/* Error State */}
        {!loading && error && (
          <div className="flex flex-col items-center justify-center py-24">
            <AlertCircle className="mb-4 h-10 w-10 text-destructive" />
            <p className="mb-4 text-sm text-muted-foreground">{error}</p>
            <button
              onClick={fetchPortfolios}
              className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90"
            >
              Retry
            </button>
          </div>
        )}

        {/* Loaded Content */}
        {!loading && !error && (
          <>
            {/* Stats */}
            <div className="mb-8 grid gap-4 md:grid-cols-4">
              {[
                { label: "Total NAV", value: formatCurrency(totalNAV), icon: TrendingUp, color: "text-chart-2 bg-chart-2/10" },
                { label: "Portfolios", value: portfolios.length.toString(), icon: Landmark, color: "text-primary bg-primary/10" },
                { label: "Total Loans", value: totalLoans.toLocaleString(), icon: FileSpreadsheet, color: "text-chart-3 bg-chart-3/10" },
                { label: "Avg Rate", value: `${(avgRate * 100).toFixed(2)}%`, icon: TrendingUp, color: "text-chart-4 bg-chart-4/10" },
              ].map((s) => (
                <div key={s.label} className="rounded-xl border bg-card p-5">
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

            {/* Empty State */}
            {portfolios.length === 0 && (
              <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed py-24">
                <Landmark className="mb-4 h-10 w-10 text-muted-foreground" />
                <p className="mb-1 text-sm font-medium text-foreground">No portfolios yet</p>
                <p className="mb-4 text-xs text-muted-foreground">Upload a loan tape to create your first portfolio</p>
                <button
                  onClick={() => setShowUpload(true)}
                  className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90"
                >
                  <Upload className="h-4 w-4" />
                  Upload Loan Tape
                </button>
              </div>
            )}

            {/* Portfolios Grid */}
            {portfolios.length > 0 && (
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {portfolios.map((p) => {
                  const allCompliant = Object.values(p.covenant_compliance_status).every(Boolean);
                  return (
                    <div key={p.id} className="rounded-xl border bg-card p-6 transition-shadow hover:shadow-md">
                      <div className="mb-4 flex items-start justify-between">
                        <div>
                          <h3 className="font-semibold text-foreground">{p.portfolio_name}</h3>
                          <p className="text-sm text-muted-foreground">{p.fund_name}</p>
                        </div>
                        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-chart-2/10">
                          <Shield className="h-5 w-5 text-chart-2" />
                        </div>
                      </div>

                      <div className="mb-4 grid grid-cols-2 gap-3">
                        <div className="rounded-lg bg-secondary/50 p-3">
                          <div className="text-xs text-muted-foreground">NAV</div>
                          <div className="text-lg font-bold text-foreground">{formatCurrency(p.nav_value)}</div>
                        </div>
                        <div className="rounded-lg bg-secondary/50 p-3">
                          <div className="text-xs text-muted-foreground">Loans</div>
                          <div className="text-lg font-bold text-foreground">{p.loan_count}</div>
                        </div>
                        <div className="rounded-lg bg-secondary/50 p-3">
                          <div className="text-xs text-muted-foreground">Avg Rate</div>
                          <div className="text-lg font-bold text-foreground">{(p.weighted_avg_rate * 100).toFixed(2)}%</div>
                        </div>
                        <div className="rounded-lg bg-secondary/50 p-3">
                          <div className="text-xs text-muted-foreground">Avg LTV</div>
                          <div className="text-lg font-bold text-foreground">{(p.avg_ltv_ratio * 100).toFixed(1)}%</div>
                        </div>
                      </div>

                      <div className="mb-4 flex items-center gap-2">
                        {allCompliant ? (
                          <span className="inline-flex items-center gap-1 rounded-full border border-emerald-200 bg-emerald-50 dark:bg-emerald-950 dark:border-emerald-800 px-2.5 py-0.5 text-xs font-medium text-emerald-700 dark:text-emerald-400">
                            <CheckCircle2 className="h-3 w-3" />
                            All Covenants Met
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 rounded-full border border-amber-200 bg-amber-50 dark:bg-amber-950 dark:border-amber-800 px-2.5 py-0.5 text-xs font-medium text-amber-700 dark:text-amber-400">
                            <AlertCircle className="h-3 w-3" />
                            Covenant Breach
                          </span>
                        )}
                      </div>

                      <button className="flex w-full items-center justify-center gap-2 rounded-lg border py-2 text-sm font-medium text-foreground transition-colors hover:bg-secondary">
                        View Details
                        <ArrowRight className="h-4 w-4" />
                      </button>
                    </div>
                  );
                })}

                {/* Add New Card */}
                <button
                  onClick={() => setShowUpload(true)}
                  className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-6 text-muted-foreground transition-colors hover:border-primary hover:text-primary"
                >
                  <Plus className="mb-2 h-10 w-10" />
                  <span className="text-sm font-medium">Add New Portfolio</span>
                  <span className="text-xs">Upload a loan tape to get started</span>
                </button>
              </div>
            )}
          </>
        )}

        {/* Upload Modal */}
        {showUpload && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="w-full max-w-lg rounded-xl bg-card p-6">
              <h2 className="mb-4 text-lg font-semibold">Upload Loan Tape</h2>
              <div
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                className={`mb-4 flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-12 transition-colors ${
                  dragOver ? "border-primary bg-primary/5" : "border-border"
                }`}
              >
                {uploading ? (
                  <>
                    <Loader2 className="mb-3 h-10 w-10 animate-spin text-primary" />
                    <p className="text-sm font-medium">Processing loan tape...</p>
                  </>
                ) : (
                  <>
                    <Upload className="mb-3 h-10 w-10 text-muted-foreground" />
                    <p className="mb-1 text-sm font-medium">Drag and drop your loan tape file</p>
                    <p className="mb-4 text-xs text-muted-foreground">CSV, XLSX, or JSON format</p>
                    <label className="cursor-pointer rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90">
                      Browse Files
                      <input
                        type="file"
                        className="hidden"
                        accept=".csv,.xlsx,.json"
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) handleUpload(file);
                        }}
                      />
                    </label>
                  </>
                )}
              </div>
              <div className="flex justify-end">
                <button
                  onClick={() => setShowUpload(false)}
                  className="rounded-lg border px-4 py-2 text-sm font-medium hover:bg-secondary"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
