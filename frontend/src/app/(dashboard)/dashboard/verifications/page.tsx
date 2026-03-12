"use client";

import { Header } from "@/components/layout/header";
import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import api from "@/lib/api";
import { toast } from "sonner";
import type { Verification, VerificationModule, VerificationStatus } from "@/types";
import {
  FileCheck,
  Search,
  Filter,
  Download,
  ChevronLeft,
  ChevronRight,
  CheckCircle2,
  Clock,
  AlertCircle,
  Landmark,
  Brain,
  Shield,
  Plus,
  ExternalLink,
  Loader2,
} from "lucide-react";

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    completed: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950 dark:text-emerald-400 dark:border-emerald-800",
    processing: "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950 dark:text-blue-400 dark:border-blue-800",
    pending: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950 dark:text-amber-400 dark:border-amber-800",
    failed: "bg-red-50 text-red-700 border-red-200 dark:bg-red-950 dark:text-red-400 dark:border-red-800",
  };
  const icons: Record<string, typeof CheckCircle2> = {
    completed: CheckCircle2,
    processing: Clock,
    pending: Clock,
    failed: AlertCircle,
  };
  const Icon = icons[status] || Clock;
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium ${styles[status] || styles.pending}`}>
      <Icon className="h-3 w-3" />
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

export default function VerificationsPage() {
  const [verifications, setVerifications] = useState<Verification[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [moduleFilter, setModuleFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  const fetchVerifications = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string | number> = {
        page: currentPage,
        page_size: pageSize,
      };
      if (moduleFilter !== "all") params.module = moduleFilter;
      if (statusFilter !== "all") params.status = statusFilter;

      const res = await api.get("/verifications", { params });
      setVerifications(res.data?.items ?? []);
      setTotalCount(res.data?.total ?? res.data?.items?.length ?? 0);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to load verifications";
      setError(message);
      toast.error("Failed to load verifications");
    } finally {
      setLoading(false);
    }
  }, [currentPage, moduleFilter, statusFilter]);

  useEffect(() => {
    fetchVerifications();
  }, [fetchVerifications]);

  // Client-side search filter (search is applied on top of server-filtered results)
  const filtered = verifications.filter((v) => {
    if (!searchQuery) return true;
    const meta = v.metadata as Record<string, string>;
    const name = meta?.portfolio_name || meta?.asset_name || v.id;
    return name.toLowerCase().includes(searchQuery.toLowerCase());
  });

  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));

  const formatDate = (d: string) => new Date(d).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  const formatCurrency = (v: number) => {
    if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
    if (v >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
    if (v >= 1e3) return `$${(v / 1e3).toFixed(0)}K`;
    return `$${v}`;
  };

  return (
    <div>
      <Header
        title="Verifications"
        description="Manage and track all your verification requests"
        actions={
          <Link
            href="/dashboard/credit"
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" />
            New Verification
          </Link>
        }
      />

      <div className="p-6">
        {/* Filters */}
        <div className="mb-6 flex flex-wrap items-center gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search verifications..."
              value={searchQuery}
              onChange={(e) => { setSearchQuery(e.target.value); setCurrentPage(1); }}
              className="w-full rounded-lg border bg-card py-2 pl-10 pr-4 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <select
              value={moduleFilter}
              onChange={(e) => { setModuleFilter(e.target.value); setCurrentPage(1); }}
              className="rounded-lg border bg-card px-3 py-2 text-sm outline-none focus:border-primary"
            >
              <option value="all">All Modules</option>
              <option value="private_credit">Private Credit</option>
              <option value="ai_ip_valuation">AI-IP Valuation</option>
            </select>
            <select
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setCurrentPage(1); }}
              className="rounded-lg border bg-card px-3 py-2 text-sm outline-none focus:border-primary"
            >
              <option value="all">All Statuses</option>
              <option value="completed">Completed</option>
              <option value="processing">Processing</option>
              <option value="pending">Pending</option>
              <option value="failed">Failed</option>
            </select>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex flex-col items-center justify-center rounded-xl border bg-card py-20">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="mt-3 text-sm text-muted-foreground">Loading verifications...</p>
          </div>
        )}

        {/* Error State */}
        {!loading && error && (
          <div className="flex flex-col items-center justify-center rounded-xl border bg-card py-20">
            <AlertCircle className="h-8 w-8 text-red-500" />
            <p className="mt-3 text-sm font-medium text-foreground">Failed to load verifications</p>
            <p className="mt-1 text-xs text-muted-foreground">{error}</p>
            <button
              onClick={fetchVerifications}
              className="mt-4 inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90"
            >
              Retry
            </button>
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center rounded-xl border bg-card py-20">
            <FileCheck className="h-8 w-8 text-muted-foreground" />
            <p className="mt-3 text-sm font-medium text-foreground">No verifications found</p>
            <p className="mt-1 text-xs text-muted-foreground">
              {searchQuery || moduleFilter !== "all" || statusFilter !== "all"
                ? "Try adjusting your search or filters"
                : "Create your first verification to get started"}
            </p>
            {!searchQuery && moduleFilter === "all" && statusFilter === "all" && (
              <Link
                href="/dashboard/credit"
                className="mt-4 inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90"
              >
                <Plus className="h-4 w-4" />
                New Verification
              </Link>
            )}
          </div>
        )}

        {/* Table */}
        {!loading && !error && filtered.length > 0 && (
          <div className="overflow-hidden rounded-xl border bg-card">
            <table className="w-full">
              <thead>
                <tr className="border-b bg-secondary/50">
                  <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">Verification</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">Module</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">Value</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">Date</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">Proof</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {filtered.map((v) => {
                  const meta = v.metadata as Record<string, string>;
                  const name = meta?.portfolio_name || meta?.asset_name || v.id;
                  const value = (v.result_data as Record<string, number>)?.nav_value;
                  return (
                    <tr key={v.id} className="transition-colors hover:bg-secondary/30">
                      <td className="px-6 py-4">
                        <Link href={`/dashboard/verifications/${v.id}`} className="group flex items-center gap-3">
                          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-secondary">
                            <Shield className="h-4 w-4 text-primary" />
                          </div>
                          <div>
                            <div className="text-sm font-medium text-foreground group-hover:text-primary">{name}</div>
                            <div className="text-xs text-muted-foreground font-mono">{v.id}</div>
                          </div>
                        </Link>
                      </td>
                      <td className="px-6 py-4">
                        {v.module === "private_credit" ? (
                          <span className="inline-flex items-center gap-1 text-xs font-medium text-chart-2">
                            <Landmark className="h-3 w-3" /> Credit
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-xs font-medium text-chart-4">
                            <Brain className="h-3 w-3" /> AI-IP
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4"><StatusBadge status={v.status} /></td>
                      <td className="px-6 py-4 text-sm font-medium text-foreground">
                        {value ? formatCurrency(value) : "\u2014"}
                      </td>
                      <td className="px-6 py-4 text-sm text-muted-foreground">{formatDate(v.created_at)}</td>
                      <td className="px-6 py-4">
                        {v.proof_hash ? (
                          <span className="inline-flex items-center gap-1 rounded-md bg-emerald-50 dark:bg-emerald-950 px-2 py-0.5 font-mono text-xs text-emerald-700 dark:text-emerald-400">
                            <CheckCircle2 className="h-3 w-3" />
                            {v.proof_hash.slice(0, 10)}...
                          </span>
                        ) : (
                          <span className="text-xs text-muted-foreground">{"\u2014"}</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          {v.report_url && (
                            <button className="rounded-md p-1.5 text-muted-foreground hover:bg-secondary hover:text-foreground" title="Download Report">
                              <Download className="h-4 w-4" />
                            </button>
                          )}
                          <Link href={`/dashboard/verifications/${v.id}`} className="rounded-md p-1.5 text-muted-foreground hover:bg-secondary hover:text-foreground" title="View Details">
                            <ExternalLink className="h-4 w-4" />
                          </Link>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            {/* Pagination */}
            <div className="flex items-center justify-between border-t px-6 py-4">
              <p className="text-sm text-muted-foreground">
                Showing {(currentPage - 1) * pageSize + 1} to{" "}
                {Math.min(currentPage * pageSize, totalCount)} of {totalCount} results
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="rounded-lg border p-2 text-muted-foreground hover:bg-secondary disabled:opacity-50"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                {Array.from({ length: totalPages }, (_, i) => (
                  <button
                    key={i}
                    onClick={() => setCurrentPage(i + 1)}
                    className={`flex h-8 w-8 items-center justify-center rounded-lg text-sm ${
                      currentPage === i + 1
                        ? "bg-primary text-white"
                        : "text-muted-foreground hover:bg-secondary"
                    }`}
                  >
                    {i + 1}
                  </button>
                ))}
                <button
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  className="rounded-lg border p-2 text-muted-foreground hover:bg-secondary disabled:opacity-50"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
