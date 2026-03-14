"use client";

import { Header } from "@/components/layout/header";
import { useState, useEffect, useCallback } from "react";
import {
  BarChart3,
  GitBranch,
  Search,
  Loader2,
  AlertCircle,
  DollarSign,
  Cpu,
  Clock,
  Hash,
  CheckCircle2,
  XCircle,
  Activity,
  ArrowRight,
} from "lucide-react";
import api from "@/lib/api";
import { toast } from "sonner";

// ─── Types ────────────────────────────────────────────────────────────────────

interface ModelUsage {
  model_name: string;
  provider: string;
  calls: number;
  tokens: number;
  cost_usd: number;
  avg_latency_ms: number;
}

interface UsageStats {
  total_calls: number;
  total_tokens: number;
  total_cost_usd: number;
  avg_latency_ms: number;
  by_model: ModelUsage[];
}

interface LineageEvent {
  step: number;
  event_type: string;
  transformation: string;
  input_hash: string;
  output_hash: string;
  duration_ms: number;
}

interface LlmCall {
  provider: string;
  model: string;
  operation: string;
  tokens: number;
  cost_usd: number;
  latency_ms: number;
  success: boolean;
}

interface LineageData {
  verification_id: string;
  events: LineageEvent[];
  llm_calls: LlmCall[];
  summary: {
    total_events: number;
    total_llm_calls: number;
    total_tokens: number;
    total_cost_usd: number;
  };
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function fmt$(v: number) {
  return `$${v.toFixed(4)}`;
}
function fmtMs(v: number) {
  return `${v.toFixed(0)} ms`;
}
function fmtNum(v: number) {
  return v.toLocaleString();
}
function truncateHash(h: string, len = 12) {
  if (!h || h.length <= len * 2) return h;
  return `${h.slice(0, len)}…${h.slice(-6)}`;
}

// ─── Summary Card ─────────────────────────────────────────────────────────────

function SummaryCard({
  label,
  value,
  icon: Icon,
  color,
}: {
  label: string;
  value: string;
  icon: React.ElementType;
  color: string;
}) {
  return (
    <div className="rounded-xl border bg-card p-5 flex items-center gap-4">
      <div
        className={`flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-lg ${color}`}
      >
        <Icon className="h-5 w-5" />
      </div>
      <div>
        <p className="text-2xl font-bold text-foreground">{value}</p>
        <p className="text-sm text-muted-foreground">{label}</p>
      </div>
    </div>
  );
}

// ─── Model Usage Stats Tab ────────────────────────────────────────────────────

function ModelUsageTab() {
  const [period, setPeriod] = useState<7 | 30 | 90 | 365>(30);
  const [stats, setStats] = useState<UsageStats | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchStats = useCallback(async (days: number) => {
    setLoading(true);
    try {
      const res = await api.get("/model-registry/stats", {
        params: { days },
      });
      const data = res.data;
      const byModel = (data.by_model ?? []).map((m: Record<string, unknown>) => ({
        model_name: m.model_name as string,
        provider: m.provider as string,
        calls: (m.call_count ?? m.calls ?? 0) as number,
        tokens: (m.total_tokens ?? m.tokens ?? 0) as number,
        cost_usd: (m.total_cost_usd ?? m.cost_usd ?? 0) as number,
        avg_latency_ms: (m.avg_latency_ms ?? 0) as number,
      }));
      const avgLat = byModel.length > 0
        ? byModel.reduce((s: number, m: ModelUsage) => s + m.avg_latency_ms, 0) / byModel.length
        : 0;
      setStats({
        total_calls: data.total_calls ?? 0,
        total_tokens: data.total_tokens ?? 0,
        total_cost_usd: data.total_cost_usd ?? 0,
        avg_latency_ms: data.avg_latency_ms ?? avgLat,
        by_model: byModel,
      });
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(detail || "Failed to load model usage stats");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats(period);
  }, [fetchStats, period]);

  const periods: { label: string; value: 7 | 30 | 90 | 365 }[] = [
    { label: "7d", value: 7 },
    { label: "30d", value: 30 },
    { label: "90d", value: 90 },
    { label: "1y", value: 365 },
  ];

  return (
    <div className="space-y-6">
      {/* Period selector */}
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium text-muted-foreground">Period:</span>
        <div className="flex rounded-lg border bg-card p-0.5">
          {periods.map((p) => (
            <button
              key={p.value}
              onClick={() => setPeriod(p.value)}
              className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                period === p.value
                  ? "bg-primary text-white shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex h-48 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : !stats ? (
        <div className="flex h-48 flex-col items-center justify-center gap-2 text-muted-foreground">
          <AlertCircle className="h-8 w-8" />
          <p className="text-sm">Failed to load stats</p>
        </div>
      ) : (
        <>
          {/* Summary cards */}
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <SummaryCard
              label="Total Calls"
              value={fmtNum(stats.total_calls)}
              icon={Activity}
              color="bg-blue-50 text-blue-600"
            />
            <SummaryCard
              label="Total Tokens"
              value={fmtNum(stats.total_tokens)}
              icon={Hash}
              color="bg-violet-50 text-violet-600"
            />
            <SummaryCard
              label="Total Cost (USD)"
              value={fmt$(stats.total_cost_usd)}
              icon={DollarSign}
              color="bg-emerald-50 text-emerald-600"
            />
            <SummaryCard
              label="Avg Latency"
              value={fmtMs(stats.avg_latency_ms)}
              icon={Clock}
              color="bg-amber-50 text-amber-600"
            />
          </div>

          {/* Model table */}
          <div className="overflow-hidden rounded-xl border bg-card">
            <div className="border-b px-6 py-4">
              <h3 className="font-semibold text-foreground">
                Usage by Model
              </h3>
            </div>
            {stats.by_model.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
                <Cpu className="mb-3 h-10 w-10" />
                <p className="text-sm">No model usage data for this period</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-secondary/50">
                      {[
                        "Model Name",
                        "Provider",
                        "Calls",
                        "Tokens",
                        "Cost (USD)",
                        "Avg Latency",
                      ].map((h) => (
                        <th
                          key={h}
                          className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground"
                        >
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {stats.by_model.map((m, idx) => (
                      <tr
                        key={idx}
                        className="transition-colors hover:bg-secondary/30"
                      >
                        <td className="px-6 py-3 font-medium text-foreground">
                          {m.model_name}
                        </td>
                        <td className="px-6 py-3 capitalize text-muted-foreground">
                          {m.provider}
                        </td>
                        <td className="px-6 py-3 text-foreground">
                          {fmtNum(m.calls)}
                        </td>
                        <td className="px-6 py-3 text-foreground">
                          {fmtNum(m.tokens)}
                        </td>
                        <td className="px-6 py-3 font-mono text-foreground">
                          {fmt$(m.cost_usd)}
                        </td>
                        <td className="px-6 py-3 text-muted-foreground">
                          {fmtMs(m.avg_latency_ms)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

// ─── Verification Lineage Tab ─────────────────────────────────────────────────

function LineageTab() {
  const [verificationId, setVerificationId] = useState("");
  const [loading, setLoading] = useState(false);
  const [lineage, setLineage] = useState<LineageData | null>(null);

  const handleLoad = async () => {
    const id = verificationId.trim();
    if (!id) {
      toast.error("Please enter a verification ID");
      return;
    }
    setLoading(true);
    setLineage(null);
    try {
      const res = await api.get(
        `/model-registry/lineage/${encodeURIComponent(id)}`
      );
      const data = res.data;
      // Map backend field names to frontend interface
      const events: LineageEvent[] = (data.lineage_events ?? data.events ?? []).map(
        (e: Record<string, unknown>) => ({
          step: (e.step_order ?? e.step ?? 0) as number,
          event_type: e.event_type as string,
          transformation: e.transformation as string,
          input_hash: e.input_hash as string,
          output_hash: e.output_hash as string,
          duration_ms: (e.duration_ms ?? 0) as number,
        })
      );
      const llmCalls: LlmCall[] = (data.model_usage ?? data.llm_calls ?? []).map(
        (c: Record<string, unknown>) => ({
          provider: c.provider as string,
          model: (c.model_name ?? c.model ?? "") as string,
          operation: (c.operation ?? "") as string,
          tokens: (c.total_tokens ?? c.tokens ?? 0) as number,
          cost_usd: (c.cost_usd ?? 0) as number,
          latency_ms: (c.latency_ms ?? 0) as number,
          success: c.success === true || c.success === "true",
        })
      );
      setLineage({
        verification_id: data.verification_id ?? id,
        events,
        llm_calls: llmCalls,
        summary: data.summary ?? {
          total_events: data.total_events ?? events.length,
          total_llm_calls: data.total_llm_calls ?? llmCalls.length,
          total_tokens: data.total_tokens ?? llmCalls.reduce((s: number, c: LlmCall) => s + c.tokens, 0),
          total_cost_usd: data.total_cost_usd ?? llmCalls.reduce((s: number, c: LlmCall) => s + c.cost_usd, 0),
        },
      });
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(detail || "Failed to load lineage data");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Input */}
      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            value={verificationId}
            onChange={(e) => setVerificationId(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleLoad()}
            placeholder="Enter verification ID…"
            className="w-full rounded-lg border bg-card py-2 pl-10 pr-4 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
          />
        </div>
        <button
          onClick={handleLoad}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90 disabled:opacity-50 transition-colors"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <GitBranch className="h-4 w-4" />
          )}
          {loading ? "Loading…" : "Load Lineage"}
        </button>
      </div>

      {loading && (
        <div className="flex h-48 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      )}

      {lineage && (
        <div className="space-y-6">
          {/* Pipeline Timeline */}
          <div className="rounded-xl border bg-card p-6">
            <div className="mb-5 flex items-center gap-2">
              <GitBranch className="h-5 w-5 text-primary" />
              <h3 className="font-semibold text-foreground">
                Data Pipeline
              </h3>
              <span className="ml-auto text-xs text-muted-foreground">
                {lineage.events.length} events
              </span>
            </div>

            {lineage.events.length === 0 ? (
              <p className="text-sm text-muted-foreground py-8 text-center">
                No lineage events found.
              </p>
            ) : (
              <ol className="relative space-y-0">
                {lineage.events.map((event, idx) => (
                  <li key={idx} className="flex gap-4">
                    {/* Connector */}
                    <div className="flex flex-col items-center">
                      <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-primary text-xs font-bold text-white">
                        {event.step}
                      </div>
                      {idx < lineage.events.length - 1 && (
                        <div className="my-1 w-0.5 flex-1 bg-border" />
                      )}
                    </div>

                    {/* Content */}
                    <div
                      className={`flex-1 rounded-lg border p-4 ${
                        idx < lineage.events.length - 1 ? "mb-1" : ""
                      }`}
                    >
                      <div className="flex flex-wrap items-start justify-between gap-2">
                        <div>
                          <span className="inline-block rounded-md bg-primary/10 px-2 py-0.5 text-xs font-semibold text-primary">
                            {event.event_type.replace(/_/g, " ")}
                          </span>
                          <p className="mt-1 text-sm text-foreground">
                            {event.transformation}
                          </p>
                        </div>
                        <span className="flex items-center gap-1 text-xs text-muted-foreground">
                          <Clock className="h-3 w-3" />
                          {fmtMs(event.duration_ms)}
                        </span>
                      </div>

                      {/* Hash flow */}
                      <div className="mt-3 flex flex-wrap items-center gap-2 font-mono text-xs text-muted-foreground">
                        <span
                          title={event.input_hash}
                          className="rounded bg-secondary px-2 py-0.5"
                        >
                          {truncateHash(event.input_hash)}
                        </span>
                        <ArrowRight className="h-3 w-3 flex-shrink-0" />
                        <span
                          title={event.output_hash}
                          className="rounded bg-secondary px-2 py-0.5"
                        >
                          {truncateHash(event.output_hash)}
                        </span>
                      </div>
                    </div>
                  </li>
                ))}
              </ol>
            )}
          </div>

          {/* LLM Calls Table */}
          <div className="overflow-hidden rounded-xl border bg-card">
            <div className="border-b px-6 py-4 flex items-center gap-2">
              <Cpu className="h-5 w-5 text-primary" />
              <h3 className="font-semibold text-foreground">LLM Calls</h3>
              <span className="ml-auto text-xs text-muted-foreground">
                {lineage.llm_calls.length} calls
              </span>
            </div>
            {lineage.llm_calls.length === 0 ? (
              <p className="py-10 text-center text-sm text-muted-foreground">
                No LLM calls recorded.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-secondary/50">
                      {[
                        "Provider",
                        "Model",
                        "Operation",
                        "Tokens",
                        "Cost",
                        "Latency",
                        "Status",
                      ].map((h) => (
                        <th
                          key={h}
                          className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground"
                        >
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {lineage.llm_calls.map((c, idx) => (
                      <tr
                        key={idx}
                        className="transition-colors hover:bg-secondary/30"
                      >
                        <td className="px-4 py-3 capitalize text-muted-foreground">
                          {c.provider}
                        </td>
                        <td className="px-4 py-3 font-medium text-foreground">
                          {c.model}
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">
                          {c.operation}
                        </td>
                        <td className="px-4 py-3 text-foreground">
                          {fmtNum(c.tokens)}
                        </td>
                        <td className="px-4 py-3 font-mono text-foreground">
                          {fmt$(c.cost_usd)}
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">
                          {fmtMs(c.latency_ms)}
                        </td>
                        <td className="px-4 py-3">
                          {c.success ? (
                            <span className="inline-flex items-center gap-1 rounded-full border border-emerald-200 bg-emerald-50 dark:border-emerald-800 dark:bg-emerald-950 px-2.5 py-0.5 text-xs font-medium text-emerald-700 dark:text-emerald-400">
                              <CheckCircle2 className="h-3 w-3" />
                              Success
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 rounded-full border border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950 px-2.5 py-0.5 text-xs font-medium text-red-700 dark:text-red-400">
                              <XCircle className="h-3 w-3" />
                              Failed
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Summary */}
          <div className="rounded-xl border bg-card p-6">
            <h3 className="mb-4 font-semibold text-foreground">Summary</h3>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-lg bg-secondary/40 p-4 text-center">
                <p className="text-2xl font-bold text-foreground">
                  {fmtNum(lineage.summary.total_events)}
                </p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  Total Events
                </p>
              </div>
              <div className="rounded-lg bg-secondary/40 p-4 text-center">
                <p className="text-2xl font-bold text-foreground">
                  {fmtNum(lineage.summary.total_llm_calls)}
                </p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  LLM Calls
                </p>
              </div>
              <div className="rounded-lg bg-secondary/40 p-4 text-center">
                <p className="text-2xl font-bold text-foreground">
                  {fmtNum(lineage.summary.total_tokens)}
                </p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  Total Tokens
                </p>
              </div>
              <div className="rounded-lg bg-secondary/40 p-4 text-center">
                <p className="text-2xl font-bold text-foreground">
                  {fmt$(lineage.summary.total_cost_usd)}
                </p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  Total Cost
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

type Tab = "usage" | "lineage";

export default function ModelRegistryPage() {
  const [activeTab, setActiveTab] = useState<Tab>("usage");

  const tabs: { id: Tab; label: string; icon: React.ElementType }[] = [
    { id: "usage", label: "Model Usage Stats", icon: BarChart3 },
    { id: "lineage", label: "Verification Lineage", icon: GitBranch },
  ];

  return (
    <div>
      <Header
        title="Model Registry & Data Lineage"
        description="Track LLM usage, costs, and full data lineage for every verification"
      />

      <div className="p-6 space-y-6">
        {/* Tabs */}
        <div className="flex gap-1 rounded-xl border bg-card p-1 w-fit">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? "bg-primary text-white shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <tab.icon className="h-4 w-4" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === "usage" ? <ModelUsageTab /> : <LineageTab />}
      </div>
    </div>
  );
}
