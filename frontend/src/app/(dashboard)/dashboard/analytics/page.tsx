"use client";

import { Header } from "@/components/layout/header";
import api from "@/lib/api";
import { toast } from "sonner";
import { useEffect, useState } from "react";
import {
  BarChart3,
  Loader2,
  AlertCircle,
  TrendingUp,
  DollarSign,
  Brain,
  ShieldCheck,
  Bell,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Info,
  Zap,
  PieChart,
} from "lucide-react";

interface VerificationTrend {
  date: string;
  total: number;
  completed: number;
  failed: number;
  success_rate: number;
}

interface PortfolioPerformance {
  total_portfolios: number;
  total_principal: number;
  total_nav: number;
  avg_rate: number;
  avg_ltv: number;
  nav_to_principal_ratio: number;
}

interface AIAssetPerformance {
  total_assets: number;
  total_value: number;
  avg_confidence: number;
  ias38_compliance_rate: number;
  asc350_compliance_rate: number;
}

interface AssetTypeBreakdown {
  asset_type: string;
  count: number;
  total_value: number;
  avg_confidence: number;
}

interface AlertSummary {
  total: number;
  active: number;
  by_severity: {
    info: number;
    warning: number;
    critical: number;
  };
}

interface ProcessingModuleStats {
  total_completed: number;
  avg_processing_seconds: number;
}

interface ProcessingStats {
  private_credit: ProcessingModuleStats;
  ai_ip_valuation: ProcessingModuleStats;
}

interface AnalyticsOverview {
  verification_trends: VerificationTrend[];
  portfolio_performance: PortfolioPerformance;
  ai_asset_performance: AIAssetPerformance;
  asset_type_breakdown: AssetTypeBreakdown[];
  alert_summary: AlertSummary;
  processing_stats: ProcessingStats;
}

function formatCurrency(value: number) {
  if (value >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(1)}B`;
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`;
  return `$${value.toFixed(0)}`;
}

function formatPercent(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

function formatMonth(dateStr: string) {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-US", { month: "short" });
}

// --- Section Components ---

function VerificationTrendsChart({ trends }: { trends: VerificationTrend[] }) {
  const maxTotal = Math.max(...trends.map((t) => t.total), 1);

  return (
    <div className="rounded-xl border bg-white p-6">
      <div className="mb-6 flex items-center gap-2">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
          <BarChart3 className="h-5 w-5 text-primary" />
        </div>
        <div>
          <h2 className="font-semibold text-foreground">Verification Trends</h2>
          <p className="text-xs text-muted-foreground">
            Monthly verification counts and success rates
          </p>
        </div>
      </div>

      {trends.length === 0 ? (
        <p className="py-8 text-center text-sm text-muted-foreground">
          No trend data available yet.
        </p>
      ) : (
        <>
          {/* Legend */}
          <div className="mb-4 flex items-center gap-4 text-xs text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <span className="inline-block h-2.5 w-2.5 rounded-sm bg-emerald-500" />
              Completed
            </span>
            <span className="flex items-center gap-1.5">
              <span className="inline-block h-2.5 w-2.5 rounded-sm bg-red-500" />
              Failed
            </span>
          </div>

          {/* Bar Chart */}
          <div className="flex items-end gap-2" style={{ height: 200 }}>
            {trends.map((t) => {
              const completedHeight = (t.completed / maxTotal) * 100;
              const failedHeight = (t.failed / maxTotal) * 100;

              return (
                <div
                  key={t.date}
                  className="group relative flex flex-1 flex-col items-center"
                >
                  {/* Tooltip */}
                  <div className="pointer-events-none absolute -top-16 z-10 hidden rounded-lg border bg-white px-3 py-2 text-xs shadow-lg group-hover:block">
                    <p className="font-medium text-foreground">
                      {formatMonth(t.date)}
                    </p>
                    <p className="text-muted-foreground">
                      Total: {t.total} | Rate: {formatPercent(t.success_rate)}
                    </p>
                  </div>

                  {/* Bars */}
                  <div
                    className="flex w-full flex-col justify-end"
                    style={{ height: 160 }}
                  >
                    <div
                      className="w-full rounded-t bg-red-500 transition-all"
                      style={{ height: `${failedHeight}%` }}
                    />
                    <div
                      className="w-full bg-emerald-500 transition-all"
                      style={{
                        height: `${completedHeight}%`,
                        borderRadius:
                          failedHeight > 0
                            ? "0"
                            : "0.25rem 0.25rem 0 0",
                      }}
                    />
                  </div>

                  {/* Label */}
                  <span className="mt-2 text-[10px] font-medium text-muted-foreground">
                    {formatMonth(t.date)}
                  </span>
                  <span className="text-[10px] text-muted-foreground">
                    {formatPercent(t.success_rate)}
                  </span>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}

function PortfolioPerformanceCard({
  data,
}: {
  data: PortfolioPerformance;
}) {
  const metrics = [
    {
      label: "Total NAV",
      value: formatCurrency(data.total_nav),
      icon: DollarSign,
      color: "bg-emerald-50 text-emerald-600",
    },
    {
      label: "Total Principal",
      value: formatCurrency(data.total_principal),
      icon: TrendingUp,
      color: "bg-blue-50 text-blue-600",
    },
    {
      label: "NAV / Principal",
      value: `${(data.nav_to_principal_ratio * 100).toFixed(1)}%`,
      icon: PieChart,
      color: "bg-violet-50 text-violet-600",
    },
    {
      label: "Avg Rate",
      value: `${(data.avg_rate * 100).toFixed(2)}%`,
      icon: TrendingUp,
      color: "bg-amber-50 text-amber-600",
    },
    {
      label: "Avg LTV",
      value: `${(data.avg_ltv * 100).toFixed(1)}%`,
      icon: ShieldCheck,
      color: "bg-sky-50 text-sky-600",
    },
  ];

  return (
    <div className="rounded-xl border bg-white p-6">
      <div className="mb-5 flex items-center gap-2">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-chart-2/10">
          <DollarSign className="h-5 w-5 text-chart-2" />
        </div>
        <div>
          <h2 className="font-semibold text-foreground">
            Portfolio Performance
          </h2>
          <p className="text-xs text-muted-foreground">
            {data.total_portfolios} portfolio{data.total_portfolios !== 1 ? "s" : ""}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
        {metrics.map((m) => (
          <div key={m.label} className="text-center">
            <div
              className={`mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-lg ${m.color}`}
            >
              <m.icon className="h-5 w-5" />
            </div>
            <p className="text-lg font-bold text-foreground">{m.value}</p>
            <p className="text-xs text-muted-foreground">{m.label}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function AIAssetPerformanceCard({
  data,
}: {
  data: AIAssetPerformance;
}) {
  const complianceItems = [
    {
      label: "IAS 38 Compliance",
      rate: data.ias38_compliance_rate,
      color: "bg-emerald-500",
    },
    {
      label: "ASC 350 Compliance",
      rate: data.asc350_compliance_rate,
      color: "bg-blue-500",
    },
  ];

  return (
    <div className="rounded-xl border bg-white p-6">
      <div className="mb-5 flex items-center gap-2">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-chart-4/10">
          <Brain className="h-5 w-5 text-chart-4" />
        </div>
        <div>
          <h2 className="font-semibold text-foreground">
            AI Asset Performance
          </h2>
          <p className="text-xs text-muted-foreground">
            {data.total_assets} asset{data.total_assets !== 1 ? "s" : ""} tracked
          </p>
        </div>
      </div>

      <div className="mb-5 grid grid-cols-2 gap-4">
        <div>
          <p className="text-sm text-muted-foreground">Total Value</p>
          <p className="text-2xl font-bold text-foreground">
            {formatCurrency(data.total_value)}
          </p>
        </div>
        <div>
          <p className="text-sm text-muted-foreground">Avg Confidence</p>
          <p className="text-2xl font-bold text-foreground">
            {formatPercent(data.avg_confidence)}
          </p>
        </div>
      </div>

      <div className="space-y-3">
        {complianceItems.map((c) => (
          <div key={c.label}>
            <div className="mb-1 flex items-center justify-between text-sm">
              <span className="font-medium text-foreground">{c.label}</span>
              <span className="text-muted-foreground">
                {formatPercent(c.rate)}
              </span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-secondary">
              <div
                className={`h-full rounded-full ${c.color} transition-all`}
                style={{ width: `${c.rate * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function AssetTypeBreakdownCard({
  data,
}: {
  data: AssetTypeBreakdown[];
}) {
  const maxValue = Math.max(...data.map((d) => d.total_value), 1);
  const totalCount = data.reduce((sum, d) => sum + d.count, 0) || 1;

  const colors = [
    "bg-primary",
    "bg-chart-2",
    "bg-chart-3",
    "bg-chart-4",
    "bg-emerald-500",
    "bg-amber-500",
  ];

  return (
    <div className="rounded-xl border bg-white p-6">
      <div className="mb-5 flex items-center gap-2">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-chart-3/10">
          <PieChart className="h-5 w-5 text-chart-3" />
        </div>
        <div>
          <h2 className="font-semibold text-foreground">
            Asset Type Breakdown
          </h2>
          <p className="text-xs text-muted-foreground">
            Distribution by type and value
          </p>
        </div>
      </div>

      {data.length === 0 ? (
        <p className="py-8 text-center text-sm text-muted-foreground">
          No asset data available.
        </p>
      ) : (
        <div className="space-y-4">
          {data.map((item, idx) => {
            const pct = (item.count / totalCount) * 100;
            const valuePct = (item.total_value / maxValue) * 100;
            const barColor = colors[idx % colors.length];

            return (
              <div key={item.asset_type}>
                <div className="mb-1.5 flex items-center justify-between">
                  <div>
                    <span className="text-sm font-medium text-foreground">
                      {item.asset_type}
                    </span>
                    <span className="ml-2 text-xs text-muted-foreground">
                      {item.count} asset{item.count !== 1 ? "s" : ""} ({pct.toFixed(0)}%)
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-semibold text-foreground">
                      {formatCurrency(item.total_value)}
                    </span>
                    <span className="ml-2 text-xs text-muted-foreground">
                      Conf: {formatPercent(item.avg_confidence)}
                    </span>
                  </div>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-secondary">
                  <div
                    className={`h-full rounded-full ${barColor} transition-all`}
                    style={{ width: `${valuePct}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function AlertSummaryCard({ data }: { data: AlertSummary }) {
  const severities = [
    {
      label: "Critical",
      count: data.by_severity.critical,
      icon: AlertCircle,
      badgeClass: "bg-red-50 text-red-700 border-red-200",
      dotClass: "bg-red-500",
    },
    {
      label: "Warning",
      count: data.by_severity.warning,
      icon: AlertTriangle,
      badgeClass: "bg-amber-50 text-amber-700 border-amber-200",
      dotClass: "bg-amber-500",
    },
    {
      label: "Info",
      count: data.by_severity.info,
      icon: Info,
      badgeClass: "bg-blue-50 text-blue-700 border-blue-200",
      dotClass: "bg-blue-500",
    },
  ];

  return (
    <div className="rounded-xl border bg-white p-6">
      <div className="mb-5 flex items-center gap-2">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-red-50">
          <Bell className="h-5 w-5 text-red-500" />
        </div>
        <div>
          <h2 className="font-semibold text-foreground">Alert Summary</h2>
          <p className="text-xs text-muted-foreground">
            {data.active} active of {data.total} total
          </p>
        </div>
      </div>

      <div className="space-y-3">
        {severities.map((s) => (
          <div
            key={s.label}
            className="flex items-center justify-between rounded-lg border px-4 py-3"
          >
            <div className="flex items-center gap-3">
              <span className={`h-2.5 w-2.5 rounded-full ${s.dotClass}`} />
              <s.icon className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium text-foreground">
                {s.label}
              </span>
            </div>
            <span
              className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${s.badgeClass}`}
            >
              {s.count}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function ProcessingPerformanceCard({ data }: { data: ProcessingStats }) {
  const modules = [
    {
      label: "Private Credit",
      stats: data.private_credit,
      icon: DollarSign,
      color: "bg-chart-2/10 text-chart-2",
    },
    {
      label: "AI-IP Valuation",
      stats: data.ai_ip_valuation,
      icon: Brain,
      color: "bg-chart-4/10 text-chart-4",
    },
  ];

  return (
    <div className="rounded-xl border bg-white p-6">
      <div className="mb-5 flex items-center gap-2">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-50">
          <Zap className="h-5 w-5 text-amber-500" />
        </div>
        <div>
          <h2 className="font-semibold text-foreground">
            Processing Performance
          </h2>
          <p className="text-xs text-muted-foreground">
            Average processing times per module
          </p>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {modules.map((m) => (
          <div key={m.label} className="rounded-lg border p-4">
            <div className="mb-3 flex items-center gap-2">
              <div
                className={`flex h-8 w-8 items-center justify-center rounded-lg ${m.color}`}
              >
                <m.icon className="h-4 w-4" />
              </div>
              <span className="text-sm font-medium text-foreground">
                {m.label}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <p className="text-xs text-muted-foreground">Completed</p>
                <p className="text-lg font-bold text-foreground">
                  {m.stats.total_completed}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Avg Time</p>
                <div className="flex items-center gap-1">
                  <Clock className="h-3.5 w-3.5 text-muted-foreground" />
                  <p className="text-lg font-bold text-foreground">
                    {m.stats.avg_processing_seconds.toFixed(1)}s
                  </p>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// --- Main Page ---

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get("/analytics/overview")
      .then((res) => {
        setData(res.data);
      })
      .catch((err) => {
        const message =
          err.response?.data?.detail || "Failed to load analytics data";
        setError(message);
        toast.error(message);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex h-96 flex-col items-center justify-center gap-4">
        <AlertCircle className="h-12 w-12 text-red-400" />
        <p className="text-lg font-medium text-foreground">
          Failed to load analytics
        </p>
        <p className="text-sm text-muted-foreground">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div>
      <Header
        title="Analytics & Insights"
        description="Verification trends, portfolio performance, and processing metrics"
      />

      <div className="space-y-6 p-6">
        {/* Row 1: Verification Trends (full width) */}
        <VerificationTrendsChart trends={data.verification_trends} />

        {/* Row 2: Portfolio Performance (full width) */}
        <PortfolioPerformanceCard data={data.portfolio_performance} />

        {/* Row 3: AI Asset Performance + Alert Summary */}
        <div className="grid gap-6 lg:grid-cols-2">
          <AIAssetPerformanceCard data={data.ai_asset_performance} />
          <AlertSummaryCard data={data.alert_summary} />
        </div>

        {/* Row 4: Asset Type Breakdown + Processing Performance */}
        <div className="grid gap-6 lg:grid-cols-2">
          <AssetTypeBreakdownCard data={data.asset_type_breakdown} />
          <ProcessingPerformanceCard data={data.processing_stats} />
        </div>
      </div>
    </div>
  );
}
