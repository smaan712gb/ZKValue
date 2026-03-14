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
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  PieChart as RechartsPie,
  Pie,
  Cell,
  AreaChart,
  Area,
} from "recharts";

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
  const chartData = trends.map((t) => ({
    ...t,
    month: formatMonth(t.date),
    successRate: t.success_rate * 100,
  }));

  return (
    <div className="rounded-xl border bg-card p-6">
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
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartData} barGap={2}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
            <XAxis dataKey="month" tick={{ fontSize: 12, fill: "#888" }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 12, fill: "#888" }} axisLine={false} tickLine={false} allowDecimals={false} />
            <Tooltip
              contentStyle={{ borderRadius: 8, border: "1px solid #e5e7eb", boxShadow: "0 4px 12px rgba(0,0,0,0.08)" }}
              formatter={(value, name) => [String(value), name === "completed" ? "Completed" : "Failed"]}
              labelFormatter={(label) => `Month: ${label}`}
            />
            <Legend
              verticalAlign="top"
              align="right"
              iconType="circle"
              iconSize={8}
              formatter={(value) => <span className="text-xs text-gray-600">{value === "completed" ? "Completed" : "Failed"}</span>}
            />
            <Bar dataKey="completed" stackId="a" fill="#10b981" radius={[0, 0, 0, 0]} name="completed" />
            <Bar dataKey="failed" stackId="a" fill="#ef4444" radius={[4, 4, 0, 0]} name="failed" />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}

const ASSET_PIE_COLORS = ["#6366f1", "#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"];

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
    <div className="rounded-xl border bg-card p-6">
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
  // Backend returns rates already as percentages (e.g. 66.7 for 66.7%), normalize to 0-1
  const ias38 = data.ias38_compliance_rate > 1 ? data.ias38_compliance_rate / 100 : data.ias38_compliance_rate;
  const asc350 = data.asc350_compliance_rate > 1 ? data.asc350_compliance_rate / 100 : data.asc350_compliance_rate;

  const complianceItems = [
    {
      label: "IAS 38 Compliance",
      rate: ias38,
      color: "bg-emerald-500",
    },
    {
      label: "ASC 350 Compliance",
      rate: asc350,
      color: "bg-blue-500",
    },
  ];

  return (
    <div className="rounded-xl border bg-card p-6">
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
    <div className="rounded-xl border bg-card p-6">
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
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center">
          {/* Pie Chart */}
          <div className="flex-shrink-0">
            <ResponsiveContainer width={180} height={180}>
              <RechartsPie>
                <Pie
                  data={data.map((d) => ({ name: d.asset_type.replace(/_/g, " "), value: d.total_value }))}
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={75}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {data.map((_, idx) => (
                    <Cell key={idx} fill={ASSET_PIE_COLORS[idx % ASSET_PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => formatCurrency(Number(value))} />
              </RechartsPie>
            </ResponsiveContainer>
          </div>

          {/* Details */}
          <div className="flex-1 space-y-3">
            {data.map((item, idx) => {
              const pct = (item.count / totalCount) * 100;
              const valuePct = (item.total_value / maxValue) * 100;

              return (
                <div key={item.asset_type}>
                  <div className="mb-1.5 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span
                        className="inline-block h-3 w-3 rounded-sm"
                        style={{ backgroundColor: ASSET_PIE_COLORS[idx % ASSET_PIE_COLORS.length] }}
                      />
                      <span className="text-sm font-medium text-foreground">
                        {item.asset_type.replace(/_/g, " ")}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {item.count} ({pct.toFixed(0)}%)
                      </span>
                    </div>
                    <div className="text-right">
                      <span className="text-sm font-semibold text-foreground">
                        {formatCurrency(item.total_value)}
                      </span>
                      <span className="ml-2 text-xs text-muted-foreground">
                        {formatPercent(item.avg_confidence)}
                      </span>
                    </div>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-secondary">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{ width: `${valuePct}%`, backgroundColor: ASSET_PIE_COLORS[idx % ASSET_PIE_COLORS.length] }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
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
      badgeClass: "bg-red-50 text-red-700 border-red-200 dark:bg-red-950 dark:text-red-400 dark:border-red-800",
      dotClass: "bg-red-500",
    },
    {
      label: "Warning",
      count: data.by_severity.warning,
      icon: AlertTriangle,
      badgeClass: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950 dark:text-amber-400 dark:border-amber-800",
      dotClass: "bg-amber-500",
    },
    {
      label: "Info",
      count: data.by_severity.info,
      icon: Info,
      badgeClass: "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950 dark:text-blue-400 dark:border-blue-800",
      dotClass: "bg-blue-500",
    },
  ];

  return (
    <div className="rounded-xl border bg-card p-6">
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
    <div className="rounded-xl border bg-card p-6">
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
