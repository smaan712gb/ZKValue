"use client";

import { Header } from "@/components/layout/header";
import { useState, useEffect, useCallback } from "react";
import {
  ScrollText,
  Download,
  Search,
  Filter,
  ChevronLeft,
  ChevronRight,
  FileCheck,
  LogIn,
  Settings,
  Eye,
  Upload,
  UserPlus,
  Loader2,
} from "lucide-react";
import api from "@/lib/api";
import { toast } from "sonner";

interface AuditLog {
  id: string;
  timestamp: string;
  user_name: string;
  action: string;
  resource_type: string;
  details: string;
  ip_address: string;
  resource_id: string;
}

interface AuditLogsResponse {
  items: AuditLog[];
  total: number;
}

const actionIcons: Record<string, typeof FileCheck> = {
  verification_created: FileCheck,
  verification_completed: FileCheck,
  user_login: LogIn,
  settings_updated: Settings,
  report_viewed: Eye,
  loan_tape_uploaded: Upload,
  member_invited: UserPlus,
};

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [actionFilter, setActionFilter] = useState("all");
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 15;

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string | number> = {
        page: currentPage,
        page_size: pageSize,
      };
      if (actionFilter !== "all") {
        params.action = actionFilter;
      }
      if (searchQuery.trim()) {
        params.user_id = searchQuery.trim();
      }
      const res = await api.get<AuditLogsResponse>("/audit/logs", { params });
      setLogs(res.data.items);
      setTotal(res.data.total);
    } catch {
      toast.error("Failed to load audit logs");
      setLogs([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [currentPage, actionFilter, searchQuery]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  const handleExport = async () => {
    setExporting(true);
    try {
      const res = await api.get("/audit/export", { responseType: "blob" });
      const blob = new Blob([res.data], { type: "text/csv" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `audit-log-${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success("Audit log exported");
    } catch {
      toast.error("Failed to export audit log");
    } finally {
      setExporting(false);
    }
  };

  return (
    <div>
      <Header
        title="Audit Log"
        description="Complete record of all actions in your organization"
        actions={
          <button
            onClick={handleExport}
            disabled={exporting}
            className="inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium hover:bg-secondary disabled:opacity-50"
          >
            {exporting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Download className="h-4 w-4" />
            )}
            Export CSV
          </button>
        }
      />

      <div className="p-6">
        {/* Filters */}
        <div className="mb-6 flex flex-wrap items-center gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search audit logs..."
              value={searchQuery}
              onChange={(e) => { setSearchQuery(e.target.value); setCurrentPage(1); }}
              className="w-full rounded-lg border bg-white py-2 pl-10 pr-4 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <select
              value={actionFilter}
              onChange={(e) => { setActionFilter(e.target.value); setCurrentPage(1); }}
              className="rounded-lg border bg-white px-3 py-2 text-sm outline-none focus:border-primary"
            >
              <option value="all">All Actions</option>
              <option value="verification_created">Verification Created</option>
              <option value="verification_completed">Verification Completed</option>
              <option value="user_login">User Login</option>
              <option value="settings_updated">Settings Updated</option>
              <option value="report_viewed">Report Viewed</option>
              <option value="loan_tape_uploaded">Loan Tape Uploaded</option>
              <option value="member_invited">Member Invited</option>
            </select>
          </div>
        </div>

        {/* Log Table */}
        <div className="overflow-hidden rounded-xl border bg-white">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : logs.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
              <ScrollText className="mb-3 h-10 w-10" />
              <p className="text-sm font-medium">No audit logs found</p>
              <p className="mt-1 text-xs">Try adjusting your search or filters</p>
            </div>
          ) : (
            <>
              <table className="w-full">
                <thead>
                  <tr className="border-b bg-secondary/50">
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">Timestamp</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">User</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">Action</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">Details</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">IP Address</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {logs.map((log) => {
                    const Icon = actionIcons[log.action] || ScrollText;
                    return (
                      <tr key={log.id} className="transition-colors hover:bg-secondary/30">
                        <td className="whitespace-nowrap px-6 py-3 text-sm text-muted-foreground">
                          {new Date(log.timestamp).toLocaleString()}
                        </td>
                        <td className="px-6 py-3">
                          <span className="text-sm font-medium">{log.user_name}</span>
                        </td>
                        <td className="px-6 py-3">
                          <span className="inline-flex items-center gap-1.5 rounded-md bg-secondary px-2 py-0.5 text-xs font-medium capitalize">
                            <Icon className="h-3 w-3" />
                            {log.action.replace(/_/g, " ")}
                          </span>
                        </td>
                        <td className="px-6 py-3 text-sm text-muted-foreground">{log.details}</td>
                        <td className="px-6 py-3 font-mono text-xs text-muted-foreground">{log.ip_address}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>

              {/* Pagination */}
              <div className="flex items-center justify-between border-t px-6 py-4">
                <p className="text-sm text-muted-foreground">
                  Showing {(currentPage - 1) * pageSize + 1} to {Math.min(currentPage * pageSize, total)} of {total}
                </p>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                    className="rounded-lg border p-2 text-muted-foreground hover:bg-secondary disabled:opacity-50"
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </button>
                  <span className="text-sm">{currentPage} / {totalPages}</span>
                  <button
                    onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                    disabled={currentPage === totalPages}
                    className="rounded-lg border p-2 text-muted-foreground hover:bg-secondary disabled:opacity-50"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
