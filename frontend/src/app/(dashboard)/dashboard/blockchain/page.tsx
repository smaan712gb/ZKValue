"use client";

import { Header } from "@/components/layout/header";
import { useState, useEffect, useCallback } from "react";
import { useAuthStore } from "@/stores/auth";
import {
  Link as LinkIcon,
  Plus,
  ChevronLeft,
  ChevronRight,
  Search,
  CheckCircle2,
  Clock,
  XCircle,
  Loader2,
  ShieldCheck,
  Hash,
  Layers,
} from "lucide-react";
import api from "@/lib/api";
import { toast } from "sonner";

// ─── Types ────────────────────────────────────────────────────────────────────

interface Anchor {
  id: string;
  created_at: string;
  merkle_root: string;
  proof_count: number;
  tx_hash: string;
  status: "confirmed" | "pending" | "failed";
  chain: string;
}

interface AnchorsResponse {
  items: Anchor[];
  total: number;
}

interface VerifyResult {
  anchored: boolean;
  merkle_valid: boolean;
  tx_hash: string;
  block_number: number | null;
  proof_hash: string;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function truncate(str: string, maxLen = 20): string {
  if (!str || str.length <= maxLen) return str;
  return `${str.slice(0, 8)}…${str.slice(-6)}`;
}

function isNullTxHash(hash: string): boolean {
  return !hash || /^0x0+$/.test(hash);
}

function StatusBadge({ status }: { status: Anchor["status"] }) {
  const config = {
    confirmed: {
      label: "Confirmed",
      cls: "bg-emerald-50 text-emerald-700 border-emerald-200",
      icon: CheckCircle2,
    },
    pending: {
      label: "Pending",
      cls: "bg-amber-50 text-amber-700 border-amber-200",
      icon: Clock,
    },
    failed: {
      label: "Failed",
      cls: "bg-red-50 text-red-700 border-red-200",
      icon: XCircle,
    },
  }[status] ?? {
    label: status,
    cls: "bg-secondary text-foreground border",
    icon: Clock,
  };

  const Icon = config.icon;
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium ${config.cls}`}
    >
      <Icon className="h-3 w-3" />
      {config.label}
    </span>
  );
}

// ─── Stats Bar ────────────────────────────────────────────────────────────────

function StatsBar({
  totalAnchors,
  totalProofs,
}: {
  totalAnchors: number;
  totalProofs: number;
}) {
  const stats = [
    {
      label: "Total Anchors",
      value: totalAnchors.toLocaleString(),
      icon: Layers,
      color: "bg-blue-50 text-blue-600",
    },
    {
      label: "Total Proofs Anchored",
      value: totalProofs.toLocaleString(),
      icon: ShieldCheck,
      color: "bg-emerald-50 text-emerald-600",
    },
  ];

  return (
    <div className="mb-6 grid gap-4 sm:grid-cols-2">
      {stats.map((s) => (
        <div
          key={s.label}
          className="flex items-center gap-4 rounded-xl border bg-white p-5"
        >
          <div
            className={`flex h-11 w-11 items-center justify-center rounded-lg ${s.color}`}
          >
            <s.icon className="h-5 w-5" />
          </div>
          <div>
            <p className="text-2xl font-bold text-foreground">{s.value}</p>
            <p className="text-sm text-muted-foreground">{s.label}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function BlockchainPage() {
  const { user } = useAuthStore();
  const isAdminOrOwner =
    user?.role === "admin" || user?.role === "owner";

  const [anchors, setAnchors] = useState<Anchor[]>([]);
  const [total, setTotal] = useState(0);
  const [totalProofs, setTotalProofs] = useState(0);
  const [loadingAnchors, setLoadingAnchors] = useState(true);
  const [creatingAnchor, setCreatingAnchor] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 20;

  const [proofHash, setProofHash] = useState("");
  const [verifying, setVerifying] = useState(false);
  const [verifyResult, setVerifyResult] = useState<VerifyResult | null>(null);

  const fetchAnchors = useCallback(async (page: number) => {
    setLoadingAnchors(true);
    try {
      const res = await api.get<AnchorsResponse>("/blockchain/anchors", {
        params: { page, page_size: pageSize },
      });
      setAnchors(res.data.items);
      setTotal(res.data.total);
      // Derive total proofs from all items loaded
      setTotalProofs((prev) => {
        const sum = res.data.items.reduce((acc, a) => acc + (a.proof_count ?? 0), 0);
        return page === 1 ? sum : prev + sum;
      });
    } catch {
      toast.error("Failed to load blockchain anchors");
    } finally {
      setLoadingAnchors(false);
    }
  }, []);

  useEffect(() => {
    fetchAnchors(currentPage);
  }, [fetchAnchors, currentPage]);

  const handleCreateAnchor = async () => {
    setCreatingAnchor(true);
    try {
      await api.post("/blockchain/anchor");
      toast.success("Daily anchor created successfully");
      setCurrentPage(1);
      fetchAnchors(1);
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(detail || "Failed to create anchor");
    } finally {
      setCreatingAnchor(false);
    }
  };

  const handleVerify = async () => {
    const hash = proofHash.trim();
    if (!hash) {
      toast.error("Please enter a proof hash");
      return;
    }
    setVerifying(true);
    setVerifyResult(null);
    try {
      const res = await api.get<VerifyResult>(`/blockchain/verify/${encodeURIComponent(hash)}`);
      setVerifyResult(res.data);
      toast.success("Verification complete");
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(detail || "Verification failed");
    } finally {
      setVerifying(false);
    }
  };

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  // Compute total proofs from current anchors list (best-effort)
  const currentTotalProofs = anchors.reduce((acc, a) => acc + (a.proof_count ?? 0), 0);

  return (
    <div>
      <Header
        title="Blockchain Anchoring"
        description="On-chain proof anchoring and verification for immutable audit trails"
        actions={
          isAdminOrOwner ? (
            <button
              onClick={handleCreateAnchor}
              disabled={creatingAnchor}
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              {creatingAnchor ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Plus className="h-4 w-4" />
              )}
              {creatingAnchor ? "Creating…" : "Create Daily Anchor"}
            </button>
          ) : undefined
        }
      />

      <div className="p-6 space-y-6">
        {/* Stats */}
        <StatsBar totalAnchors={total} totalProofs={currentTotalProofs} />

        {/* Anchors Table */}
        <div className="overflow-hidden rounded-xl border bg-white">
          <div className="flex items-center gap-2 border-b px-6 py-4">
            <Layers className="h-5 w-5 text-primary" />
            <h2 className="font-semibold text-foreground">Anchors</h2>
            <span className="ml-auto text-xs text-muted-foreground">
              {total} total
            </span>
          </div>

          {loadingAnchors ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : anchors.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
              <Hash className="mb-3 h-10 w-10" />
              <p className="text-sm font-medium">No anchors found</p>
              <p className="mt-1 text-xs">
                {isAdminOrOwner
                  ? "Create your first daily anchor using the button above."
                  : "No blockchain anchors have been created yet."}
              </p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-secondary/50">
                      <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        Date
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        Merkle Root
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        Proofs
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        TX Hash
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        Chain
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {anchors.map((anchor) => (
                      <tr
                        key={anchor.id}
                        className="transition-colors hover:bg-secondary/30"
                      >
                        <td className="whitespace-nowrap px-6 py-3 text-muted-foreground">
                          {new Date(anchor.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-3 font-mono text-xs text-foreground">
                          {truncate(anchor.merkle_root, 26)}
                        </td>
                        <td className="px-6 py-3 text-right font-medium text-foreground">
                          {anchor.proof_count.toLocaleString()}
                        </td>
                        <td className="px-6 py-3 font-mono text-xs">
                          {isNullTxHash(anchor.tx_hash) ? (
                            <span className="text-muted-foreground">
                              {truncate(anchor.tx_hash, 26)}
                            </span>
                          ) : (
                            <a
                              href={`https://etherscan.io/tx/${anchor.tx_hash}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center gap-1 text-primary hover:underline"
                            >
                              {truncate(anchor.tx_hash, 26)}
                              <LinkIcon className="h-3 w-3 flex-shrink-0" />
                            </a>
                          )}
                        </td>
                        <td className="px-6 py-3">
                          <StatusBadge status={anchor.status} />
                        </td>
                        <td className="px-6 py-3 text-muted-foreground capitalize">
                          {anchor.chain}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              <div className="flex items-center justify-between border-t px-6 py-4">
                <p className="text-sm text-muted-foreground">
                  Showing{" "}
                  {Math.min((currentPage - 1) * pageSize + 1, total)}–
                  {Math.min(currentPage * pageSize, total)} of {total}
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
            </>
          )}
        </div>

        {/* Proof Verification */}
        <div className="rounded-xl border bg-white p-6">
          <div className="mb-5 flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
              <ShieldCheck className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h2 className="font-semibold text-foreground">
                Proof Verification
              </h2>
              <p className="text-xs text-muted-foreground">
                Verify any proof hash against on-chain data
              </p>
            </div>
          </div>

          <div className="flex gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input
                type="text"
                value={proofHash}
                onChange={(e) => setProofHash(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleVerify()}
                placeholder="Enter proof hash (e.g. 0xabc…)"
                className="w-full rounded-lg border bg-white py-2 pl-10 pr-4 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
              />
            </div>
            <button
              onClick={handleVerify}
              disabled={verifying}
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              {verifying ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <ShieldCheck className="h-4 w-4" />
              )}
              {verifying ? "Verifying…" : "Verify On-Chain"}
            </button>
          </div>

          {verifyResult && (
            <div className="mt-5 rounded-lg border bg-secondary/20 p-4">
              <p className="mb-3 text-sm font-semibold text-foreground">
                Verification Result
              </p>
              <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <div>
                  <dt className="text-xs font-medium text-muted-foreground">
                    Anchored
                  </dt>
                  <dd className="mt-0.5">
                    {verifyResult.anchored ? (
                      <span className="inline-flex items-center gap-1 text-sm font-semibold text-emerald-600">
                        <CheckCircle2 className="h-4 w-4" /> Yes
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-sm font-semibold text-red-600">
                        <XCircle className="h-4 w-4" /> No
                      </span>
                    )}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs font-medium text-muted-foreground">
                    Merkle Valid
                  </dt>
                  <dd className="mt-0.5">
                    {verifyResult.merkle_valid ? (
                      <span className="inline-flex items-center gap-1 text-sm font-semibold text-emerald-600">
                        <CheckCircle2 className="h-4 w-4" /> Valid
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-sm font-semibold text-red-600">
                        <XCircle className="h-4 w-4" /> Invalid
                      </span>
                    )}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs font-medium text-muted-foreground">
                    TX Hash
                  </dt>
                  <dd className="mt-0.5 font-mono text-xs text-foreground break-all">
                    {isNullTxHash(verifyResult.tx_hash) ? (
                      <span className="text-muted-foreground">
                        {truncate(verifyResult.tx_hash, 26)}
                      </span>
                    ) : (
                      <a
                        href={`https://etherscan.io/tx/${verifyResult.tx_hash}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-primary hover:underline"
                      >
                        {truncate(verifyResult.tx_hash, 26)}
                        <LinkIcon className="h-3 w-3 flex-shrink-0" />
                      </a>
                    )}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs font-medium text-muted-foreground">
                    Block Number
                  </dt>
                  <dd className="mt-0.5 text-sm font-medium text-foreground">
                    {verifyResult.block_number != null
                      ? verifyResult.block_number.toLocaleString()
                      : "—"}
                  </dd>
                </div>
              </dl>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
