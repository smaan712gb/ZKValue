"use client";

import { Header } from "@/components/layout/header";
import { useState, useEffect, useCallback } from "react";
import {
  AlertCircle,
  Loader2,
  Play,
  TrendingDown,
  BarChart3,
  Sliders,
  Shuffle,
  ChevronDown,
  FileText,
} from "lucide-react";
import api from "@/lib/api";
import { toast } from "sonner";

// ─── Types ────────────────────────────────────────────────────────────────────

interface Verification {
  id: string;
  metadata: Record<string, string>;
  status: string;
}

interface ScenarioResult {
  scenario_key: string;
  scenario_name: string;
  loss_rate: number;
  stressed_nav: number;
  loans_underwater: number;
  avg_default_probability: number;
}

interface CustomResult {
  loss_rate: number;
  stressed_nav: number;
  loans_underwater: number;
  avg_default_probability: number;
}

interface MonteCarloResult {
  var_95: number;
  var_99: number;
  expected_loss_rate: number;
  nav_p5: number;
  nav_median: number;
  nav_p95: number;
}

interface NarrativeResult {
  narrative: string;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatCurrency(v: number) {
  if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
  if (v >= 1e3) return `$${(v / 1e3).toFixed(0)}K`;
  return `$${v.toLocaleString()}`;
}

function formatPercent(v: number) {
  return `${(v * 100).toFixed(2)}%`;
}

function severityClass(lossRate: number) {
  if (lossRate < 0.05) return "border-emerald-200 bg-emerald-50";
  if (lossRate < 0.15) return "border-amber-200 bg-amber-50";
  return "border-red-200 bg-red-50";
}

function severityBadge(lossRate: number) {
  if (lossRate < 0.05)
    return "bg-emerald-100 text-emerald-700 border-emerald-200";
  if (lossRate < 0.15) return "bg-amber-100 text-amber-700 border-amber-200";
  return "bg-red-100 text-red-700 border-red-200";
}

function severityLabel(lossRate: number) {
  if (lossRate < 0.05) return "Low";
  if (lossRate < 0.15) return "Moderate";
  return "High";
}

// ─── Tab type ─────────────────────────────────────────────────────────────────

type Tab = "presets" | "custom" | "montecarlo";

// ─── Scenario Presets Tab ─────────────────────────────────────────────────────

function PresetsTab({ verificationId }: { verificationId: string }) {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<ScenarioResult[]>([]);
  const [error, setError] = useState<string | null>(null);

  const runAll = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.post(
        `/stress-testing/run/${verificationId}?scenario_key=all`
      );
      const data = res.data;
      // Accept array or keyed object
      if (Array.isArray(data)) {
        setResults(data);
      } else if (data.results && Array.isArray(data.results)) {
        setResults(data.results);
      } else {
        // Transform object of scenario_key → result
        setResults(
          Object.entries(data).map(([key, val]) => ({
            scenario_key: key,
            ...(val as Omit<ScenarioResult, "scenario_key">),
          }))
        );
      }
      toast.success("Stress scenarios completed.");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Failed to run scenarios.";
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Run all predefined stress scenarios against the selected verification.
        </p>
        <button
          onClick={runAll}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Play className="h-4 w-4" />
          )}
          Run All Scenarios
        </button>
      </div>

      {loading && (
        <div className="flex flex-col items-center justify-center rounded-xl border bg-secondary/30 py-16">
          <Loader2 className="mb-4 h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">
            Running stress scenarios...
          </p>
        </div>
      )}

      {!loading && error && (
        <div className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4">
          <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-red-500" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {!loading && results.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {results.map((r) => (
            <div
              key={r.scenario_key}
              className={`rounded-xl border p-5 ${severityClass(r.loss_rate)}`}
            >
              <div className="mb-3 flex items-start justify-between">
                <h3 className="text-sm font-semibold text-foreground">
                  {r.scenario_name ?? r.scenario_key}
                </h3>
                <span
                  className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${severityBadge(r.loss_rate)}`}
                >
                  {severityLabel(r.loss_rate)}
                </span>
              </div>
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Loss Rate</dt>
                  <dd className="font-semibold text-foreground">
                    {formatPercent(r.loss_rate)}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Stressed NAV</dt>
                  <dd className="font-semibold text-foreground">
                    {formatCurrency(r.stressed_nav)}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Loans Underwater</dt>
                  <dd className="font-semibold text-foreground">
                    {r.loans_underwater}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Avg Default Prob.</dt>
                  <dd className="font-semibold text-foreground">
                    {formatPercent(r.avg_default_probability)}
                  </dd>
                </div>
              </dl>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Custom Scenario Tab ──────────────────────────────────────────────────────

function CustomTab({ verificationId }: { verificationId: string }) {
  const [rateShock, setRateShock] = useState(200);
  const [defaultMultiplier, setDefaultMultiplier] = useState(2);
  const [collateralHaircut, setCollateralHaircut] = useState(20);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<CustomResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.post(`/stress-testing/custom/${verificationId}`, {
        rate_shock_bps: rateShock,
        default_multiplier: defaultMultiplier,
        collateral_haircut_pct: collateralHaircut / 100,
      });
      setResult(res.data);
      toast.success("Custom scenario completed.");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Custom scenario failed.";
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="grid gap-6 sm:grid-cols-3">
        {/* Rate Shock */}
        <div className="rounded-xl border bg-white p-5">
          <label className="mb-1 block text-sm font-medium text-foreground">
            Rate Shock (bps)
          </label>
          <p className="mb-3 text-xs text-muted-foreground">
            Range: -500 to +1000
          </p>
          <input
            type="range"
            min={-500}
            max={1000}
            step={25}
            value={rateShock}
            onChange={(e) => setRateShock(Number(e.target.value))}
            className="mb-2 w-full accent-primary"
          />
          <input
            type="number"
            min={-500}
            max={1000}
            value={rateShock}
            onChange={(e) =>
              setRateShock(
                Math.max(-500, Math.min(1000, Number(e.target.value)))
              )
            }
            className="w-full rounded-lg border px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
          />
        </div>

        {/* Default Multiplier */}
        <div className="rounded-xl border bg-white p-5">
          <label className="mb-1 block text-sm font-medium text-foreground">
            Default Multiplier
          </label>
          <p className="mb-3 text-xs text-muted-foreground">Range: 0.1× to 10×</p>
          <input
            type="range"
            min={0.1}
            max={10}
            step={0.1}
            value={defaultMultiplier}
            onChange={(e) => setDefaultMultiplier(Number(e.target.value))}
            className="mb-2 w-full accent-primary"
          />
          <input
            type="number"
            min={0.1}
            max={10}
            step={0.1}
            value={defaultMultiplier}
            onChange={(e) =>
              setDefaultMultiplier(
                Math.max(0.1, Math.min(10, Number(e.target.value)))
              )
            }
            className="w-full rounded-lg border px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
          />
        </div>

        {/* Collateral Haircut */}
        <div className="rounded-xl border bg-white p-5">
          <label className="mb-1 block text-sm font-medium text-foreground">
            Collateral Haircut (%)
          </label>
          <p className="mb-3 text-xs text-muted-foreground">Range: 0% to 80%</p>
          <input
            type="range"
            min={0}
            max={80}
            step={1}
            value={collateralHaircut}
            onChange={(e) => setCollateralHaircut(Number(e.target.value))}
            className="mb-2 w-full accent-primary"
          />
          <input
            type="number"
            min={0}
            max={80}
            value={collateralHaircut}
            onChange={(e) =>
              setCollateralHaircut(
                Math.max(0, Math.min(80, Number(e.target.value)))
              )
            }
            className="w-full rounded-lg border px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
          />
        </div>
      </div>

      <div className="flex justify-end">
        <button
          onClick={run}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2 text-sm font-medium text-white hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Play className="h-4 w-4" />
          )}
          Run Custom Scenario
        </button>
      </div>

      {loading && (
        <div className="flex flex-col items-center justify-center rounded-xl border bg-secondary/30 py-16">
          <Loader2 className="mb-4 h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Running scenario...</p>
        </div>
      )}

      {!loading && error && (
        <div className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4">
          <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-red-500" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {!loading && result && (
        <div
          className={`rounded-xl border p-6 ${severityClass(result.loss_rate)}`}
        >
          <h3 className="mb-4 font-semibold text-foreground">
            Custom Scenario Results
          </h3>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            {[
              { label: "Loss Rate", value: formatPercent(result.loss_rate) },
              { label: "Stressed NAV", value: formatCurrency(result.stressed_nav) },
              { label: "Loans Underwater", value: result.loans_underwater.toString() },
              {
                label: "Avg Default Prob.",
                value: formatPercent(result.avg_default_probability),
              },
            ].map((m) => (
              <div key={m.label} className="rounded-lg bg-white/70 p-4">
                <p className="text-xs text-muted-foreground">{m.label}</p>
                <p className="mt-1 text-xl font-bold text-foreground">
                  {m.value}
                </p>
              </div>
            ))}
          </div>
          <div className="mt-3 flex items-center gap-2">
            <span
              className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${severityBadge(result.loss_rate)}`}
            >
              {severityLabel(result.loss_rate)} Severity
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Monte Carlo Tab ──────────────────────────────────────────────────────────

function MonteCarloTab({ verificationId }: { verificationId: string }) {
  const [simulations, setSimulations] = useState(1000);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<MonteCarloResult | null>(null);
  const [narrative, setNarrative] = useState<string | null>(null);
  const [narrativeLoading, setNarrativeLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    setNarrative(null);
    try {
      const res = await api.post(
        `/stress-testing/monte-carlo/${verificationId}`,
        { simulations }
      );
      setResult(res.data);
      toast.success("Monte Carlo simulation completed.");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Monte Carlo simulation failed.";
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const generateNarrative = async () => {
    setNarrativeLoading(true);
    try {
      const res = await api.post<NarrativeResult>(
        `/stress-testing/narrative/${verificationId}`
      );
      setNarrative(res.data.narrative);
      toast.success("Narrative generated.");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Failed to generate narrative.";
      toast.error(msg);
    } finally {
      setNarrativeLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="rounded-xl border bg-white p-5">
        <label className="mb-1 block text-sm font-medium text-foreground">
          Number of Simulations
        </label>
        <p className="mb-3 text-xs text-muted-foreground">
          Range: 100 to 10,000. Higher values are more accurate but take longer.
        </p>
        <div className="flex items-center gap-4">
          <input
            type="range"
            min={100}
            max={10000}
            step={100}
            value={simulations}
            onChange={(e) => setSimulations(Number(e.target.value))}
            className="flex-1 accent-primary"
          />
          <input
            type="number"
            min={100}
            max={10000}
            step={100}
            value={simulations}
            onChange={(e) =>
              setSimulations(
                Math.max(100, Math.min(10000, Number(e.target.value)))
              )
            }
            className="w-28 rounded-lg border px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
          />
        </div>
      </div>

      <div className="flex justify-end">
        <button
          onClick={run}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2 text-sm font-medium text-white hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Shuffle className="h-4 w-4" />
          )}
          Run Monte Carlo
        </button>
      </div>

      {loading && (
        <div className="flex flex-col items-center justify-center rounded-xl border bg-secondary/30 py-16">
          <Loader2 className="mb-4 h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">
            Running {simulations.toLocaleString()} simulations...
          </p>
        </div>
      )}

      {!loading && error && (
        <div className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4">
          <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-red-500" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {!loading && result && (
        <div className="space-y-4">
          {/* Key Metrics */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[
              { label: "VaR 95%", value: formatPercent(result.var_95), desc: "Value at Risk (95th percentile)" },
              { label: "VaR 99%", value: formatPercent(result.var_99), desc: "Value at Risk (99th percentile)" },
              {
                label: "Expected Loss Rate",
                value: formatPercent(result.expected_loss_rate),
                desc: "Mean loss across simulations",
              },
            ].map((m) => (
              <div key={m.label} className="rounded-xl border bg-white p-5">
                <p className="text-xs text-muted-foreground">{m.desc}</p>
                <p className="mt-1 text-2xl font-bold text-foreground">
                  {m.value}
                </p>
                <p className="text-sm font-medium text-muted-foreground">
                  {m.label}
                </p>
              </div>
            ))}
          </div>

          {/* NAV Distribution */}
          <div className="rounded-xl border bg-white p-6">
            <h3 className="mb-4 font-semibold text-foreground">
              NAV Distribution
            </h3>
            <div className="grid grid-cols-3 gap-4 text-center">
              {[
                {
                  label: "5th Percentile",
                  value: formatCurrency(result.nav_p5),
                  color: "text-red-600",
                },
                {
                  label: "Median",
                  value: formatCurrency(result.nav_median),
                  color: "text-foreground",
                },
                {
                  label: "95th Percentile",
                  value: formatCurrency(result.nav_p95),
                  color: "text-emerald-600",
                },
              ].map((p) => (
                <div
                  key={p.label}
                  className="rounded-lg bg-secondary/50 p-4"
                >
                  <p className="text-xs text-muted-foreground">{p.label}</p>
                  <p className={`mt-1 text-xl font-bold ${p.color}`}>
                    {p.value}
                  </p>
                </div>
              ))}
            </div>
            {/* Visual distribution bar */}
            <div className="mt-5">
              <div className="relative h-4 overflow-hidden rounded-full bg-secondary">
                <div
                  className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-red-400 via-amber-400 to-emerald-400"
                  style={{ width: "100%" }}
                />
              </div>
              <div className="mt-1 flex justify-between text-[11px] text-muted-foreground">
                <span>Worst case</span>
                <span>Most likely</span>
                <span>Best case</span>
              </div>
            </div>
          </div>

          {/* Generate Narrative */}
          <div className="rounded-xl border bg-white p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-foreground">AI Narrative</h3>
                <p className="text-xs text-muted-foreground">
                  Generate a plain-English summary of the stress test results.
                </p>
              </div>
              <button
                onClick={generateNarrative}
                disabled={narrativeLoading}
                className="inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium text-foreground hover:bg-secondary disabled:cursor-not-allowed disabled:opacity-50"
              >
                {narrativeLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <FileText className="h-4 w-4" />
                )}
                Generate Narrative
              </button>
            </div>

            {narrativeLoading && (
              <div className="mt-4 flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Generating narrative...
              </div>
            )}

            {narrative && (
              <div className="mt-4 rounded-lg border border-primary/20 bg-primary/5 p-4">
                <p className="text-sm leading-relaxed text-foreground whitespace-pre-wrap">
                  {narrative}
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

const TABS: { key: Tab; label: string; icon: typeof BarChart3 }[] = [
  { key: "presets", label: "Scenario Presets", icon: BarChart3 },
  { key: "custom", label: "Custom Scenario", icon: Sliders },
  { key: "montecarlo", label: "Monte Carlo", icon: Shuffle },
];

export default function StressTestingPage() {
  const [verifications, setVerifications] = useState<Verification[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [vLoading, setVLoading] = useState(true);
  const [vError, setVError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("presets");

  const fetchVerifications = useCallback(async () => {
    setVLoading(true);
    setVError(null);
    try {
      const res = await api.get("/verifications", {
        params: { module: "private_credit", status: "completed", page_size: 100 },
      });
      const items: Verification[] = res.data?.items ?? res.data ?? [];
      setVerifications(items);
      if (items.length > 0) setSelectedId(items[0].id);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Failed to load verifications.";
      setVError(msg);
      toast.error(msg);
    } finally {
      setVLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchVerifications();
  }, [fetchVerifications]);

  const selectedVerification = verifications.find((v) => v.id === selectedId);
  const verificationName = selectedVerification
    ? (selectedVerification.metadata?.portfolio_name ??
      selectedVerification.metadata?.asset_name ??
      selectedId)
    : "";

  return (
    <div>
      <Header
        title="Stress Testing"
        description="Simulate adverse scenarios and assess portfolio resilience"
      />

      <div className="space-y-6 p-6">
        {/* Verification Selector */}
        <div className="rounded-xl border bg-white p-5">
          <label className="mb-2 block text-sm font-medium text-foreground">
            Select Verification
          </label>

          {vLoading && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading verifications...
            </div>
          )}

          {!vLoading && vError && (
            <div className="flex items-center gap-2 text-sm text-red-600">
              <AlertCircle className="h-4 w-4" />
              {vError}
              <button
                onClick={fetchVerifications}
                className="underline hover:no-underline"
              >
                Retry
              </button>
            </div>
          )}

          {!vLoading && !vError && verifications.length === 0 && (
            <p className="text-sm text-muted-foreground">
              No completed private credit verifications found. Complete a
              verification first.
            </p>
          )}

          {!vLoading && !vError && verifications.length > 0 && (
            <div className="relative">
              <select
                value={selectedId}
                onChange={(e) => setSelectedId(e.target.value)}
                className="w-full appearance-none rounded-lg border bg-white py-2 pl-4 pr-10 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
              >
                {verifications.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.metadata?.portfolio_name ??
                      v.metadata?.asset_name ??
                      v.id}
                  </option>
                ))}
              </select>
              <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            </div>
          )}

          {selectedId && verificationName && (
            <p className="mt-2 text-xs text-muted-foreground">
              ID:{" "}
              <span className="font-mono">{selectedId}</span>
            </p>
          )}
        </div>

        {/* Tabs + Content */}
        {selectedId && (
          <div className="rounded-xl border bg-white">
            {/* Tab Bar */}
            <div className="flex border-b">
              {TABS.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.key}
                    onClick={() => setActiveTab(tab.key)}
                    className={`flex items-center gap-2 border-b-2 px-5 py-4 text-sm font-medium transition-colors ${
                      activeTab === tab.key
                        ? "border-primary text-primary"
                        : "border-transparent text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    {tab.label}
                  </button>
                );
              })}
            </div>

            {/* Tab Content */}
            <div className="p-6">
              {activeTab === "presets" && (
                <PresetsTab verificationId={selectedId} />
              )}
              {activeTab === "custom" && (
                <CustomTab verificationId={selectedId} />
              )}
              {activeTab === "montecarlo" && (
                <MonteCarloTab verificationId={selectedId} />
              )}
            </div>
          </div>
        )}

        {/* Empty state when no verification selected */}
        {!vLoading && !vError && verifications.length === 0 && (
          <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed py-20">
            <TrendingDown className="mb-4 h-10 w-10 text-muted-foreground" />
            <p className="text-sm font-medium text-foreground">
              No completed verifications
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              Complete a private credit verification to run stress tests.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
