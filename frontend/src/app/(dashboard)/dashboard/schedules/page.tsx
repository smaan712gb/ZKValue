"use client";

import { Header } from "@/components/layout/header";
import { useState, useEffect, useCallback } from "react";
import api from "@/lib/api";
import { toast } from "sonner";
import {
  CalendarClock,
  Plus,
  Play,
  Pause,
  Trash2,
  Loader2,
  AlertCircle,
  AlertTriangle,
  Info,
  ChevronLeft,
  ChevronRight,
  Clock,
  Landmark,
  Brain,
  Bell,
  CheckCircle2,
  X,
  RotateCcw,
  ShieldCheck,
  Filter,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Schedule {
  id: string;
  name: string;
  module: string;
  frequency: string;
  next_run_at: string;
  run_count: number;
  is_active: boolean;
  drift_threshold: number;
  input_data: Record<string, unknown>;
  created_at: string;
}

interface DriftAlert {
  id: string;
  alert_type: string;
  severity: "critical" | "warning" | "info";
  message: string;
  drift_percentage: number;
  status: "new" | "acknowledged" | "resolved";
  created_at: string;
}

interface AlertsResponse {
  items: DriftAlert[];
  total: number;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function ModuleBadge({ module }: { module: string }) {
  if (module === "private_credit") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-emerald-200 bg-emerald-50 dark:border-emerald-800 dark:bg-emerald-950 px-2.5 py-0.5 text-xs font-medium text-emerald-700 dark:text-emerald-400">
        <Landmark className="h-3 w-3" />
        Credit
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-violet-200 bg-violet-50 px-2.5 py-0.5 text-xs font-medium text-violet-700">
      <Brain className="h-3 w-3" />
      AI-IP
    </span>
  );
}

function SeverityBadge({ severity }: { severity: string }) {
  const styles: Record<string, string> = {
    critical: "bg-red-50 text-red-700 border-red-200 dark:bg-red-950 dark:text-red-400 dark:border-red-800",
    warning: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950 dark:text-amber-400 dark:border-amber-800",
    info: "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950 dark:text-blue-400 dark:border-blue-800",
  };
  const icons: Record<string, typeof AlertCircle> = {
    critical: AlertCircle,
    warning: AlertTriangle,
    info: Info,
  };
  const Icon = icons[severity] || Info;
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium ${styles[severity] || styles.info}`}
    >
      <Icon className="h-3 w-3" />
      {severity.charAt(0).toUpperCase() + severity.slice(1)}
    </span>
  );
}

function AlertStatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    new: "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950 dark:text-blue-400 dark:border-blue-800",
    acknowledged: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950 dark:text-amber-400 dark:border-amber-800",
    resolved: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950 dark:text-emerald-400 dark:border-emerald-800",
  };
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium ${styles[status] || styles.new}`}
    >
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function SchedulesPage() {
  const [activeTab, setActiveTab] = useState<"schedules" | "alerts">(
    "schedules",
  );

  return (
    <div>
      <Header
        title="Verification Schedules"
        description="Manage recurring verifications and drift alerts"
      />

      <div className="p-6">
        {/* Tabs */}
        <div className="mb-6 flex gap-1 rounded-lg bg-secondary/60 p-1">
          <button
            onClick={() => setActiveTab("schedules")}
            className={`flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === "schedules"
                ? "bg-card text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <CalendarClock className="h-4 w-4" />
            Schedules
          </button>
          <button
            onClick={() => setActiveTab("alerts")}
            className={`flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === "alerts"
                ? "bg-card text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Bell className="h-4 w-4" />
            Drift Alerts
          </button>
        </div>

        {activeTab === "schedules" ? <SchedulesTab /> : <AlertsTab />}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Schedules Tab
// ---------------------------------------------------------------------------

function SchedulesTab() {
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const fetchSchedules = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get("/schedules");
      setSchedules(res.data?.items ?? res.data ?? []);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to load schedules";
      setError(message);
      toast.error("Failed to load schedules");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSchedules();
  }, [fetchSchedules]);

  const handleToggle = async (schedule: Schedule) => {
    setActionLoading(schedule.id);
    try {
      await api.put(`/schedules/${schedule.id}`, {
        is_active: !schedule.is_active,
      });
      setSchedules((prev) =>
        prev.map((s) =>
          s.id === schedule.id ? { ...s, is_active: !s.is_active } : s,
        ),
      );
      toast.success(
        schedule.is_active ? "Schedule paused" : "Schedule activated",
      );
    } catch {
      toast.error("Failed to update schedule");
    } finally {
      setActionLoading(null);
    }
  };

  const handleRunNow = async (id: string) => {
    setActionLoading(id);
    try {
      await api.post(`/schedules/${id}/run`);
      toast.success("Verification run triggered");
      fetchSchedules();
    } catch {
      toast.error("Failed to trigger run");
    } finally {
      setActionLoading(null);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this schedule?")) return;
    setActionLoading(id);
    try {
      await api.delete(`/schedules/${id}`);
      setSchedules((prev) => prev.filter((s) => s.id !== id));
      toast.success("Schedule deleted");
    } catch {
      toast.error("Failed to delete schedule");
    } finally {
      setActionLoading(null);
    }
  };

  const formatDate = (d: string) =>
    new Date(d).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });

  return (
    <>
      {/* Action bar */}
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {schedules.length} schedule{schedules.length !== 1 && "s"}
        </p>
        <button
          onClick={() => setShowModal(true)}
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" />
          New Schedule
        </button>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex flex-col items-center justify-center rounded-xl border bg-card py-20">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="mt-3 text-sm text-muted-foreground">
            Loading schedules...
          </p>
        </div>
      )}

      {/* Error */}
      {!loading && error && (
        <div className="flex flex-col items-center justify-center rounded-xl border bg-card py-20">
          <AlertCircle className="h-8 w-8 text-red-500" />
          <p className="mt-3 text-sm font-medium text-foreground">
            Failed to load schedules
          </p>
          <p className="mt-1 text-xs text-muted-foreground">{error}</p>
          <button
            onClick={fetchSchedules}
            className="mt-4 inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90"
          >
            Retry
          </button>
        </div>
      )}

      {/* Empty */}
      {!loading && !error && schedules.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-xl border bg-card py-20">
          <CalendarClock className="h-8 w-8 text-muted-foreground" />
          <p className="mt-3 text-sm font-medium text-foreground">
            No schedules yet
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            Create your first recurring verification schedule
          </p>
          <button
            onClick={() => setShowModal(true)}
            className="mt-4 inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" />
            New Schedule
          </button>
        </div>
      )}

      {/* Schedule cards */}
      {!loading && !error && schedules.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {schedules.map((s) => (
            <div
              key={s.id}
              className="flex flex-col justify-between rounded-xl border bg-card p-5 transition-shadow hover:shadow-md"
            >
              {/* Header */}
              <div>
                <div className="flex items-start justify-between">
                  <div className="min-w-0 flex-1">
                    <h3 className="truncate text-sm font-semibold text-foreground">
                      {s.name}
                    </h3>
                    <div className="mt-1.5 flex flex-wrap items-center gap-2">
                      <ModuleBadge module={s.module} />
                      <span className="inline-flex items-center gap-1 rounded-full border bg-secondary/50 px-2.5 py-0.5 text-xs font-medium text-muted-foreground">
                        <RotateCcw className="h-3 w-3" />
                        {s.frequency.charAt(0).toUpperCase() +
                          s.frequency.slice(1)}
                      </span>
                    </div>
                  </div>
                  {/* Active / Paused pill */}
                  <button
                    onClick={() => handleToggle(s)}
                    disabled={actionLoading === s.id}
                    className={`ml-2 flex-shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors ${
                      s.is_active
                        ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400 hover:bg-emerald-100"
                        : "bg-gray-100 text-gray-500 hover:bg-gray-200"
                    }`}
                  >
                    {s.is_active ? "Active" : "Paused"}
                  </button>
                </div>

                {/* Details */}
                <div className="mt-4 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">Next run</span>
                    <span className="font-medium text-foreground">
                      {s.next_run_at ? formatDate(s.next_run_at) : "\u2014"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">Total runs</span>
                    <span className="font-medium text-foreground">
                      {s.run_count}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">
                      Drift threshold
                    </span>
                    <span className="font-medium text-foreground">
                      {s.drift_threshold}%
                    </span>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="mt-4 flex items-center gap-2 border-t pt-4">
                <button
                  onClick={() => handleRunNow(s.id)}
                  disabled={actionLoading === s.id}
                  className="inline-flex flex-1 items-center justify-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-secondary disabled:opacity-50"
                >
                  {actionLoading === s.id ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Play className="h-3.5 w-3.5" />
                  )}
                  Run Now
                </button>
                <button
                  onClick={() => handleToggle(s)}
                  disabled={actionLoading === s.id}
                  className="inline-flex items-center justify-center rounded-lg border p-1.5 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground disabled:opacity-50"
                  title={s.is_active ? "Pause" : "Resume"}
                >
                  {s.is_active ? (
                    <Pause className="h-3.5 w-3.5" />
                  ) : (
                    <Play className="h-3.5 w-3.5" />
                  )}
                </button>
                <button
                  onClick={() => handleDelete(s.id)}
                  disabled={actionLoading === s.id}
                  className="inline-flex items-center justify-center rounded-lg border p-1.5 text-muted-foreground transition-colors hover:bg-red-50 hover:text-red-600 disabled:opacity-50"
                  title="Delete"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* New Schedule Modal */}
      {showModal && (
        <NewScheduleModal
          onClose={() => setShowModal(false)}
          onCreated={() => {
            setShowModal(false);
            fetchSchedules();
          }}
        />
      )}
    </>
  );
}

// ---------------------------------------------------------------------------
// New Schedule Modal
// ---------------------------------------------------------------------------

function NewScheduleModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: () => void;
}) {
  const [name, setName] = useState("");
  const [module, setModule] = useState("private_credit");
  const [frequency, setFrequency] = useState("daily");
  const [driftThreshold, setDriftThreshold] = useState("5");
  const [inputData, setInputData] = useState("{}");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      toast.error("Schedule name is required");
      return;
    }

    let parsedInput: Record<string, unknown>;
    try {
      parsedInput = JSON.parse(inputData);
    } catch {
      toast.error("Input data must be valid JSON");
      return;
    }

    setSubmitting(true);
    try {
      await api.post("/schedules", {
        name: name.trim(),
        module,
        frequency,
        drift_threshold: parseFloat(driftThreshold),
        input_data: parsedInput,
      });
      toast.success("Schedule created");
      onCreated();
    } catch {
      toast.error("Failed to create schedule");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-lg rounded-xl bg-card shadow-xl">
        {/* Modal header */}
        <div className="flex items-center justify-between border-b px-6 py-4">
          <h2 className="text-base font-semibold text-foreground">
            New Verification Schedule
          </h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-muted-foreground hover:bg-secondary hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4 px-6 py-5">
          {/* Name */}
          <div>
            <label className="mb-1 block text-sm font-medium text-foreground">
              Schedule Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Monthly Credit Portfolio Review"
              className="w-full rounded-lg border bg-card px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
            />
          </div>

          {/* Module */}
          <div>
            <label className="mb-1 block text-sm font-medium text-foreground">
              Module
            </label>
            <select
              value={module}
              onChange={(e) => setModule(e.target.value)}
              className="w-full rounded-lg border bg-card px-3 py-2 text-sm outline-none focus:border-primary"
            >
              <option value="private_credit">Private Credit</option>
              <option value="ai_ip_valuation">AI-IP Valuation</option>
            </select>
          </div>

          {/* Frequency */}
          <div>
            <label className="mb-1 block text-sm font-medium text-foreground">
              Frequency
            </label>
            <select
              value={frequency}
              onChange={(e) => setFrequency(e.target.value)}
              className="w-full rounded-lg border bg-card px-3 py-2 text-sm outline-none focus:border-primary"
            >
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
              <option value="quarterly">Quarterly</option>
            </select>
          </div>

          {/* Drift threshold */}
          <div>
            <label className="mb-1 block text-sm font-medium text-foreground">
              Drift Threshold (%)
            </label>
            <input
              type="number"
              min="0"
              max="100"
              step="0.1"
              value={driftThreshold}
              onChange={(e) => setDriftThreshold(e.target.value)}
              className="w-full rounded-lg border bg-card px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
            />
          </div>

          {/* Input data */}
          <div>
            <label className="mb-1 block text-sm font-medium text-foreground">
              Input Data (JSON)
            </label>
            <textarea
              rows={4}
              value={inputData}
              onChange={(e) => setInputData(e.target.value)}
              placeholder='{"portfolio_id": "...", "parameters": {}}'
              className="w-full rounded-lg border bg-card px-3 py-2 font-mono text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
            />
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 border-t pt-4">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border px-4 py-2 text-sm font-medium text-muted-foreground hover:bg-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90 disabled:opacity-50"
            >
              {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
              Create Schedule
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Drift Alerts Tab
// ---------------------------------------------------------------------------

function AlertsTab() {
  const [alerts, setAlerts] = useState<DriftAlert[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [severityFilter, setSeverityFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [currentPage, setCurrentPage] = useState(1);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const pageSize = 10;

  const fetchAlerts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string | number> = {
        page: currentPage,
        page_size: pageSize,
      };
      if (severityFilter !== "all") params.severity = severityFilter;
      if (statusFilter !== "all") params.status = statusFilter;

      const res = await api.get<AlertsResponse>("/schedules/alerts", {
        params,
      });
      setAlerts(res.data?.items ?? []);
      setTotal(res.data?.total ?? 0);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to load alerts";
      setError(message);
      toast.error("Failed to load drift alerts");
    } finally {
      setLoading(false);
    }
  }, [currentPage, severityFilter, statusFilter]);

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  const handleAcknowledge = async (id: string) => {
    setActionLoading(id);
    try {
      await api.post(`/schedules/alerts/${id}/acknowledge`);
      setAlerts((prev) =>
        prev.map((a) =>
          a.id === id ? { ...a, status: "acknowledged" as const } : a,
        ),
      );
      toast.success("Alert acknowledged");
    } catch {
      toast.error("Failed to acknowledge alert");
    } finally {
      setActionLoading(null);
    }
  };

  const handleResolve = async (id: string) => {
    setActionLoading(id);
    try {
      await api.post(`/schedules/alerts/${id}/resolve`);
      setAlerts((prev) =>
        prev.map((a) =>
          a.id === id ? { ...a, status: "resolved" as const } : a,
        ),
      );
      toast.success("Alert resolved");
    } catch {
      toast.error("Failed to resolve alert");
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <>
      {/* Filters */}
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <select
            value={severityFilter}
            onChange={(e) => {
              setSeverityFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="rounded-lg border bg-card px-3 py-2 text-sm outline-none focus:border-primary"
          >
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="warning">Warning</option>
            <option value="info">Info</option>
          </select>
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="rounded-lg border bg-card px-3 py-2 text-sm outline-none focus:border-primary"
          >
            <option value="all">All Statuses</option>
            <option value="new">New</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="resolved">Resolved</option>
          </select>
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex flex-col items-center justify-center rounded-xl border bg-card py-20">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="mt-3 text-sm text-muted-foreground">
            Loading alerts...
          </p>
        </div>
      )}

      {/* Error */}
      {!loading && error && (
        <div className="flex flex-col items-center justify-center rounded-xl border bg-card py-20">
          <AlertCircle className="h-8 w-8 text-red-500" />
          <p className="mt-3 text-sm font-medium text-foreground">
            Failed to load alerts
          </p>
          <p className="mt-1 text-xs text-muted-foreground">{error}</p>
          <button
            onClick={fetchAlerts}
            className="mt-4 inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90"
          >
            Retry
          </button>
        </div>
      )}

      {/* Empty */}
      {!loading && !error && alerts.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-xl border bg-card py-20">
          <ShieldCheck className="h-8 w-8 text-muted-foreground" />
          <p className="mt-3 text-sm font-medium text-foreground">
            No drift alerts
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            {severityFilter !== "all" || statusFilter !== "all"
              ? "Try adjusting your filters"
              : "All verifications are within expected thresholds"}
          </p>
        </div>
      )}

      {/* Table */}
      {!loading && !error && alerts.length > 0 && (
        <div className="overflow-hidden rounded-xl border bg-card">
          <table className="w-full">
            <thead>
              <tr className="border-b bg-secondary/50">
                <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Severity
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Alert Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Message
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Drift
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Timestamp
                </th>
                <th className="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {alerts.map((alert) => (
                <tr
                  key={alert.id}
                  className="transition-colors hover:bg-secondary/30"
                >
                  <td className="px-6 py-3">
                    <SeverityBadge severity={alert.severity} />
                  </td>
                  <td className="px-6 py-3">
                    <span className="text-sm font-medium text-foreground">
                      {alert.alert_type.replace(/_/g, " ")}
                    </span>
                  </td>
                  <td className="max-w-xs truncate px-6 py-3 text-sm text-muted-foreground">
                    {alert.message}
                  </td>
                  <td className="px-6 py-3">
                    <span className="font-mono text-sm font-semibold text-foreground">
                      {alert.drift_percentage.toFixed(1)}%
                    </span>
                  </td>
                  <td className="px-6 py-3">
                    <AlertStatusBadge status={alert.status} />
                  </td>
                  <td className="whitespace-nowrap px-6 py-3 text-sm text-muted-foreground">
                    <span className="inline-flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {new Date(alert.created_at).toLocaleString()}
                    </span>
                  </td>
                  <td className="px-6 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      {alert.status === "new" && (
                        <button
                          onClick={() => handleAcknowledge(alert.id)}
                          disabled={actionLoading === alert.id}
                          className="inline-flex items-center gap-1 rounded-md border px-2.5 py-1 text-xs font-medium text-muted-foreground transition-colors hover:bg-amber-50 hover:text-amber-700 disabled:opacity-50"
                        >
                          {actionLoading === alert.id ? (
                            <Loader2 className="h-3 w-3 animate-spin" />
                          ) : (
                            <CheckCircle2 className="h-3 w-3" />
                          )}
                          Acknowledge
                        </button>
                      )}
                      {alert.status !== "resolved" && (
                        <button
                          onClick={() => handleResolve(alert.id)}
                          disabled={actionLoading === alert.id}
                          className="inline-flex items-center gap-1 rounded-md border px-2.5 py-1 text-xs font-medium text-muted-foreground transition-colors hover:bg-emerald-50 hover:text-emerald-700 disabled:opacity-50"
                        >
                          {actionLoading === alert.id ? (
                            <Loader2 className="h-3 w-3 animate-spin" />
                          ) : (
                            <ShieldCheck className="h-3 w-3" />
                          )}
                          Resolve
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Pagination */}
          <div className="flex items-center justify-between border-t px-6 py-4">
            <p className="text-sm text-muted-foreground">
              Showing {(currentPage - 1) * pageSize + 1} to{" "}
              {Math.min(currentPage * pageSize, total)} of {total} alerts
            </p>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="rounded-lg border p-2 text-muted-foreground hover:bg-secondary disabled:opacity-50"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <span className="text-sm">
                {currentPage} / {totalPages}
              </span>
              <button
                onClick={() =>
                  setCurrentPage((p) => Math.min(totalPages, p + 1))
                }
                disabled={currentPage === totalPages}
                className="rounded-lg border p-2 text-muted-foreground hover:bg-secondary disabled:opacity-50"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
