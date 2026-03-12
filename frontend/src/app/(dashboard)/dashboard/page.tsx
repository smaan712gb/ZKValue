"use client";

import { Header } from "@/components/layout/header";
import {
  FileCheck,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  Clock,
  ArrowUpRight,
  Landmark,
  Brain,
  Shield,
  Loader2,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import api from "@/lib/api";
import type { DashboardStats, Verification } from "@/types";

function StatCard({
  title,
  value,
  icon: Icon,
  color,
}: {
  title: string;
  value: string | number;
  icon: typeof FileCheck;
  color: string;
}) {
  return (
    <div className="rounded-xl border bg-white p-6 transition-shadow hover:shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <p className="mt-2 text-3xl font-bold text-foreground">{value}</p>
        </div>
        <div
          className={`flex h-10 w-10 items-center justify-center rounded-lg ${color}`}
        >
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    completed: "bg-emerald-50 text-emerald-700 border-emerald-200",
    processing: "bg-blue-50 text-blue-700 border-blue-200",
    pending: "bg-amber-50 text-amber-700 border-amber-200",
    failed: "bg-red-50 text-red-700 border-red-200",
  };
  const icons: Record<string, typeof CheckCircle2> = {
    completed: CheckCircle2,
    processing: Clock,
    pending: Clock,
    failed: AlertCircle,
  };
  const Icon = icons[status] || Clock;

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium ${
        styles[status] || styles.pending
      }`}
    >
      <Icon className="h-3 w-3" />
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

function ModuleBadge({ module }: { module: string }) {
  if (module === "private_credit") {
    return (
      <span className="inline-flex items-center gap-1 rounded-md bg-chart-2/10 px-2 py-0.5 text-xs font-medium text-chart-2">
        <Landmark className="h-3 w-3" />
        Credit
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-md bg-chart-4/10 px-2 py-0.5 text-xs font-medium text-chart-4">
      <Brain className="h-3 w-3" />
      AI-IP
    </span>
  );
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentVerifications, setRecentVerifications] = useState<Verification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get("/dashboard/stats")
      .then((res) => {
        setStats(res.data);
        setRecentVerifications(res.data.recent_verifications || []);
      })
      .catch((err) => {
        setError(err.response?.data?.detail || "Failed to load dashboard data");
      })
      .finally(() => setLoading(false));
  }, []);

  const formatCurrency = (value: number) => {
    if (value >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(1)}B`;
    if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
    if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`;
    return `$${value}`;
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / 3600000);
    if (hours < 1) return "Just now";
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    if (days < 7) return `${days}d ago`;
    return date.toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="flex h-96 flex-col items-center justify-center gap-4">
        <AlertCircle className="h-12 w-12 text-red-400" />
        <p className="text-lg font-medium text-foreground">Failed to load dashboard</p>
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
        title="Dashboard"
        description="Overview of your verification activity and asset valuations"
        actions={
          <Link
            href="/dashboard/verifications"
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary/90"
          >
            <FileCheck className="h-4 w-4" />
            New Verification
          </Link>
        }
      />

      <div className="p-6">
        {/* Stats Grid */}
        <div className="mb-8 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="Total Verifications"
            value={stats.total_verifications}
            icon={FileCheck}
            color="bg-primary/10 text-primary"
          />
          <StatCard
            title="Total Asset Value"
            value={formatCurrency(stats.total_asset_value)}
            icon={TrendingUp}
            color="bg-chart-2/10 text-chart-2"
          />
          <StatCard
            title="Credit Portfolios"
            value={stats.credit_portfolios}
            icon={Landmark}
            color="bg-chart-3/10 text-chart-3"
          />
          <StatCard
            title="AI Assets Valued"
            value={stats.ai_assets}
            icon={Brain}
            color="bg-chart-4/10 text-chart-4"
          />
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Recent Verifications */}
          <div className="lg:col-span-2">
            <div className="rounded-xl border bg-white">
              <div className="flex items-center justify-between border-b px-6 py-4">
                <h2 className="font-semibold text-foreground">
                  Recent Verifications
                </h2>
                <Link
                  href="/dashboard/verifications"
                  className="flex items-center gap-1 text-sm font-medium text-primary hover:text-primary/80"
                >
                  View all
                  <ArrowUpRight className="h-3.5 w-3.5" />
                </Link>
              </div>
              <div className="divide-y">
                {recentVerifications.length === 0 ? (
                  <div className="px-6 py-12 text-center text-sm text-muted-foreground">
                    No verifications yet. Create your first verification to get started.
                  </div>
                ) : (
                  recentVerifications.map((v) => (
                    <Link
                      key={v.id}
                      href={`/dashboard/verifications/${v.id}`}
                      className="flex items-center justify-between px-6 py-4 transition-colors hover:bg-secondary/50"
                    >
                      <div className="flex items-center gap-4">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-secondary">
                          <Shield className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                          <div className="text-sm font-medium text-foreground">
                            {(v.metadata as Record<string, string>)
                              ?.portfolio_name ||
                              (v.metadata as Record<string, string>)
                                ?.asset_name ||
                              v.id}
                          </div>
                          <div className="mt-0.5 flex items-center gap-2">
                            <ModuleBadge module={v.module} />
                            <span className="text-xs text-muted-foreground">
                              {formatDate(v.created_at)}
                            </span>
                          </div>
                        </div>
                      </div>
                      <StatusBadge status={v.status} />
                    </Link>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Usage & Quick Actions */}
          <div className="space-y-6">
            {/* Usage */}
            <div className="rounded-xl border bg-white p-6">
              <h2 className="mb-4 font-semibold text-foreground">
                Monthly Usage
              </h2>
              <div className="mb-2 flex items-end justify-between">
                <span className="text-3xl font-bold text-foreground">
                  {stats.monthly_usage}
                </span>
                <span className="text-sm text-muted-foreground">
                  / {stats.monthly_limit} verifications
                </span>
              </div>
              <div className="mb-4 h-2 overflow-hidden rounded-full bg-secondary">
                <div
                  className="h-full rounded-full bg-primary transition-all"
                  style={{
                    width: `${Math.min(
                      (stats.monthly_usage / stats.monthly_limit) * 100,
                      100
                    )}%`,
                  }}
                />
              </div>
              <p className="text-xs text-muted-foreground">
                {stats.monthly_limit - stats.monthly_usage} verifications
                remaining this month
              </p>
            </div>

            {/* Verification by Module */}
            <div className="rounded-xl border bg-white p-6">
              <h2 className="mb-4 font-semibold text-foreground">
                Value by Module
              </h2>
              <div className="space-y-4">
                {stats.value_by_module.map((item) => (
                  <div key={item.module}>
                    <div className="mb-1 flex items-center justify-between text-sm">
                      <span className="font-medium text-foreground">
                        {item.module}
                      </span>
                      <span className="text-muted-foreground">
                        {formatCurrency(item.value)}
                      </span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-secondary">
                      <div
                        className={`h-full rounded-full ${
                          item.module.includes("Credit")
                            ? "bg-chart-2"
                            : "bg-chart-4"
                        }`}
                        style={{
                          width: `${
                            stats.total_asset_value > 0
                              ? (item.value / stats.total_asset_value) * 100
                              : 0
                          }%`,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Quick Actions */}
            <div className="rounded-xl border bg-white p-6">
              <h2 className="mb-4 font-semibold text-foreground">
                Quick Actions
              </h2>
              <div className="space-y-2">
                <Link
                  href="/dashboard/credit"
                  className="flex items-center gap-3 rounded-lg border px-4 py-3 text-sm font-medium transition-colors hover:bg-secondary"
                >
                  <Landmark className="h-4 w-4 text-chart-2" />
                  Upload Loan Tape
                </Link>
                <Link
                  href="/dashboard/ai-ip"
                  className="flex items-center gap-3 rounded-lg border px-4 py-3 text-sm font-medium transition-colors hover:bg-secondary"
                >
                  <Brain className="h-4 w-4 text-chart-4" />
                  New AI-IP Valuation
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
