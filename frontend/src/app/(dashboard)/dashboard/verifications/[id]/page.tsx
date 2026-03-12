"use client";

import { Header } from "@/components/layout/header";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useState, useEffect, useCallback } from "react";
import {
  ArrowLeft,
  Shield,
  CheckCircle2,
  Download,
  Copy,
  ExternalLink,
  Clock,
  Landmark,
  Brain,
  FileText,
  Lock,
  Hash,
  Loader2,
  XCircle,
  AlertCircle,
} from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";

interface CovenantItem {
  required: number;
  actual: number;
  compliant: boolean;
}

interface PipelineStep {
  step: string;
  desc: string;
  time: string;
  status: string;
}

interface Verification {
  id: string;
  module: string;
  status: string;
  created_at: string;
  completed_at: string;
  proof_hash: string;
  metadata: Record<string, string>;
  result_data: {
    nav_value: number;
    total_principal: number;
    weighted_avg_rate: number;
    avg_ltv_ratio: number;
    loan_count: number;
    interest_accrual_verified: boolean;
    ltv_compliance: boolean;
    covenant_compliance: Record<string, CovenantItem>;
  };
  proof_certificate: {
    algorithm: string;
    inputs_hash: string;
    outputs_hash: string;
    computation_hash: string;
    timestamp: string;
    block_attestation: string;
  };
  pipeline_steps?: PipelineStep[];
}

export default function VerificationDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const [activeTab, setActiveTab] = useState<"overview" | "proof" | "report">("overview");
  const [verification, setVerification] = useState<Verification | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [verifyingProof, setVerifyingProof] = useState(false);

  const fetchVerification = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.get(`/verifications/${id}`);
      setVerification(data);
    } catch (err: any) {
      const message = err.response?.data?.detail || err.message || "Failed to load verification";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (id) {
      fetchVerification();
    }
  }, [id, fetchVerification]);

  const handleVerifyProof = async () => {
    setVerifyingProof(true);
    try {
      await api.post(`/verifications/${id}/verify-proof`);
      toast.success("Proof verified successfully");
      fetchVerification();
    } catch (err: any) {
      const message = err.response?.data?.detail || err.message || "Proof verification failed";
      toast.error(message);
    } finally {
      setVerifyingProof(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success("Copied to clipboard");
  };

  const formatCurrency = (val: number) => {
    if (val >= 1e9) return `$${(val / 1e9).toFixed(2)}B`;
    if (val >= 1e6) return `$${(val / 1e6).toFixed(1)}M`;
    return `$${val.toLocaleString()}`;
  };

  const getDuration = (start: string, end: string) => {
    const ms = new Date(end).getTime() - new Date(start).getTime();
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes}m ${seconds.toString().padStart(2, "0")}s`;
  };

  const getStatusBanner = (status: string) => {
    switch (status) {
      case "completed":
        return {
          icon: CheckCircle2,
          borderClass: "border-emerald-200 bg-emerald-50 dark:border-emerald-800 dark:bg-emerald-950",
          iconBg: "bg-emerald-100",
          iconColor: "text-emerald-600",
          titleColor: "text-emerald-900",
          descColor: "text-emerald-700",
          metaColor: "text-emerald-600",
          title: "Verification Completed",
          desc: "All computations verified. Proof certificate generated and on-chain attestation recorded.",
        };
      case "running":
        return {
          icon: Loader2,
          borderClass: "border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-950",
          iconBg: "bg-blue-100",
          iconColor: "text-blue-600 animate-spin",
          titleColor: "text-blue-900",
          descColor: "text-blue-700",
          metaColor: "text-blue-600",
          title: "Verification In Progress",
          desc: "Computations are being verified. This may take a few minutes.",
        };
      case "failed":
        return {
          icon: XCircle,
          borderClass: "border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950",
          iconBg: "bg-red-100",
          iconColor: "text-red-600",
          titleColor: "text-red-900",
          descColor: "text-red-700",
          metaColor: "text-red-600",
          title: "Verification Failed",
          desc: "An error occurred during verification. Please review and retry.",
        };
      default:
        return {
          icon: AlertCircle,
          borderClass: "border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-950",
          iconBg: "bg-amber-100",
          iconColor: "text-amber-600",
          titleColor: "text-amber-900",
          descColor: "text-amber-700",
          metaColor: "text-amber-600",
          title: `Verification ${status.charAt(0).toUpperCase() + status.slice(1)}`,
          desc: "Verification is pending or in a transitional state.",
        };
    }
  };

  if (loading) {
    return (
      <div>
        <Header title="Verification Details" />
        <div className="flex h-[60vh] items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">Loading verification...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !verification) {
    return (
      <div>
        <Header title="Verification Details" />
        <div className="p-6">
          <Link
            href="/dashboard/verifications"
            className="mb-6 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Verifications
          </Link>
          <div className="flex h-[50vh] items-center justify-center">
            <div className="flex flex-col items-center gap-4 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-red-100">
                <XCircle className="h-6 w-6 text-red-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-foreground">Failed to Load Verification</h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  {error || "Verification not found"}
                </p>
              </div>
              <button
                onClick={fetchVerification}
                className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90"
              >
                Retry
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const v = verification;
  const banner = getStatusBanner(v.status);
  const BannerIcon = banner.icon;

  const moduleLabel =
    v.module === "private_credit"
      ? "Private Credit"
      : v.module.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <div>
      <Header
        title="Verification Details"
        actions={
          <div className="flex items-center gap-2">
            <button className="inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium hover:bg-secondary">
              <Download className="h-4 w-4" />
              Download Report
            </button>
            <button className="inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium hover:bg-secondary">
              <ExternalLink className="h-4 w-4" />
              Share Proof
            </button>
          </div>
        }
      />

      <div className="p-6">
        <Link
          href="/dashboard/verifications"
          className="mb-6 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Verifications
        </Link>

        {/* Status Banner */}
        <div className={`mb-6 flex items-center gap-4 rounded-xl border p-4 ${banner.borderClass}`}>
          <div className={`flex h-12 w-12 items-center justify-center rounded-full ${banner.iconBg}`}>
            <BannerIcon className={`h-6 w-6 ${banner.iconColor}`} />
          </div>
          <div>
            <h2 className={`text-lg font-semibold ${banner.titleColor}`}>
              {banner.title}
            </h2>
            <p className={`text-sm ${banner.descColor}`}>
              {banner.desc}
            </p>
          </div>
          {v.completed_at && (
            <div className="ml-auto text-right">
              <div className={`text-sm font-medium ${banner.titleColor}`}>
                {new Date(v.completed_at).toLocaleString()}
              </div>
              <div className={`text-xs ${banner.metaColor}`}>
                Duration: {getDuration(v.created_at, v.completed_at)}
              </div>
            </div>
          )}
        </div>

        {/* Tabs */}
        <div className="mb-6 flex gap-1 rounded-lg bg-secondary p-1">
          {(["overview", "proof", "report"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === tab
                  ? "bg-card text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {activeTab === "overview" && (
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Basic Info */}
            <div className="rounded-xl border bg-card p-6">
              <h3 className="mb-4 font-semibold text-foreground">Verification Info</h3>
              <dl className="space-y-3">
                {[
                  { label: "ID", value: v.id },
                  { label: "Name", value: v.metadata?.portfolio_name || v.metadata?.name || "-" },
                  { label: "Module", value: moduleLabel },
                  { label: "Status", value: v.status.charAt(0).toUpperCase() + v.status.slice(1) },
                  { label: "Created", value: new Date(v.created_at).toLocaleString() },
                  ...(v.completed_at
                    ? [{ label: "Completed", value: new Date(v.completed_at).toLocaleString() }]
                    : []),
                ].map((item) => (
                  <div key={item.label} className="flex items-center justify-between">
                    <dt className="text-sm text-muted-foreground">{item.label}</dt>
                    <dd className="text-sm font-medium text-foreground">
                      {item.value}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>

            {/* Key Metrics */}
            {v.result_data && (
              <div className="rounded-xl border bg-card p-6">
                <h3 className="mb-4 font-semibold text-foreground">Key Metrics</h3>
                <div className="grid grid-cols-2 gap-4">
                  {[
                    ...(v.result_data.nav_value != null
                      ? [{ label: "NAV", value: formatCurrency(v.result_data.nav_value) }]
                      : []),
                    ...(v.result_data.total_principal != null
                      ? [{ label: "Total Principal", value: formatCurrency(v.result_data.total_principal) }]
                      : []),
                    ...(v.result_data.weighted_avg_rate != null
                      ? [{ label: "Weighted Avg Rate", value: `${(v.result_data.weighted_avg_rate * 100).toFixed(2)}%` }]
                      : []),
                    ...(v.result_data.avg_ltv_ratio != null
                      ? [{ label: "Avg LTV Ratio", value: `${(v.result_data.avg_ltv_ratio * 100).toFixed(1)}%` }]
                      : []),
                    ...(v.result_data.loan_count != null
                      ? [{ label: "Loan Count", value: v.result_data.loan_count.toString() }]
                      : []),
                    ...(v.result_data.interest_accrual_verified != null
                      ? [{ label: "Interest Verified", value: v.result_data.interest_accrual_verified ? "Yes" : "No" }]
                      : []),
                  ].map((m) => (
                    <div key={m.label} className="rounded-lg bg-secondary/50 p-3">
                      <div className="text-xs text-muted-foreground">{m.label}</div>
                      <div className="mt-1 text-lg font-semibold text-foreground">{m.value}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Covenant Compliance */}
            {v.result_data?.covenant_compliance && Object.keys(v.result_data.covenant_compliance).length > 0 && (
              <div className="rounded-xl border bg-card p-6 lg:col-span-2">
                <h3 className="mb-4 font-semibold text-foreground">Covenant Compliance</h3>
                <div className="grid gap-4 md:grid-cols-3">
                  {Object.entries(v.result_data.covenant_compliance).map(([key, covenant]) => (
                    <div
                      key={key}
                      className={`rounded-lg border p-4 ${
                        covenant.compliant
                          ? "border-emerald-200 bg-emerald-50 dark:border-emerald-800 dark:bg-emerald-950"
                          : "border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950"
                      }`}
                    >
                      <div className="mb-2 flex items-center justify-between">
                        <span className="text-sm font-medium capitalize text-foreground">
                          {key.replace(/_/g, " ")}
                        </span>
                        <CheckCircle2
                          className={`h-4 w-4 ${
                            covenant.compliant ? "text-emerald-600" : "text-red-600"
                          }`}
                        />
                      </div>
                      <div className="flex items-end justify-between">
                        <div>
                          <div className="text-xs text-muted-foreground">Required</div>
                          <div className="text-sm font-semibold">{covenant.required}</div>
                        </div>
                        <div className="text-right">
                          <div className="text-xs text-muted-foreground">Actual</div>
                          <div className="text-sm font-semibold">{covenant.actual}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === "proof" && (
          <div className="space-y-6">
            {/* Proof Hash */}
            <div className="rounded-xl border bg-card p-6">
              <div className="mb-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Lock className="h-5 w-5 text-primary" />
                  <h3 className="font-semibold text-foreground">Cryptographic Proof</h3>
                </div>
                <button
                  onClick={handleVerifyProof}
                  disabled={verifyingProof}
                  className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90 disabled:opacity-50"
                >
                  {verifyingProof ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Shield className="h-4 w-4" />
                  )}
                  {verifyingProof ? "Verifying..." : "Verify Proof"}
                </button>
              </div>
              <div className="space-y-4">
                {v.proof_hash && (
                  <div>
                    <div className="mb-1 text-sm text-muted-foreground">Proof Hash</div>
                    <div className="flex items-center gap-2 rounded-lg bg-secondary p-3 font-mono text-sm">
                      <Hash className="h-4 w-4 shrink-0 text-muted-foreground" />
                      <span className="flex-1 truncate">{v.proof_hash}</span>
                      <button
                        onClick={() => copyToClipboard(v.proof_hash)}
                        className="shrink-0 text-muted-foreground hover:text-foreground"
                      >
                        <Copy className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                )}

                {v.proof_certificate && Object.entries(v.proof_certificate).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between border-b pb-3 last:border-0">
                    <span className="text-sm capitalize text-muted-foreground">
                      {key.replace(/_/g, " ")}
                    </span>
                    <span className="font-mono text-sm text-foreground">{value as string}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Verification Steps */}
            <div className="rounded-xl border bg-card p-6">
              <h3 className="mb-4 font-semibold text-foreground">Verification Pipeline</h3>
              <div className="space-y-4">
                {(v.pipeline_steps || []).map((step, i, arr) => (
                  <div key={step.step} className="flex items-start gap-4">
                    <div className="flex flex-col items-center">
                      <div
                        className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-medium ${
                          step.status === "done"
                            ? "bg-emerald-100 text-emerald-700"
                            : step.status === "running"
                            ? "bg-blue-100 text-blue-700"
                            : "bg-gray-100 text-gray-500"
                        }`}
                      >
                        {step.status === "running" ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          i + 1
                        )}
                      </div>
                      {i < arr.length - 1 && (
                        <div
                          className={`h-8 w-px ${
                            step.status === "done" ? "bg-emerald-200" : "bg-gray-200"
                          }`}
                        />
                      )}
                    </div>
                    <div className="flex-1 pb-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-foreground">{step.step}</span>
                        <span className="flex items-center gap-1 text-xs text-muted-foreground">
                          <Clock className="h-3 w-3" />
                          {step.time}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground">{step.desc}</p>
                    </div>
                  </div>
                ))}
                {(!v.pipeline_steps || v.pipeline_steps.length === 0) && (
                  <p className="text-sm text-muted-foreground">
                    No pipeline step details available for this verification.
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === "report" && (
          <div className="rounded-xl border bg-card p-6">
            <div className="mb-6 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <FileText className="h-5 w-5 text-primary" />
                <h3 className="font-semibold text-foreground">Verification Report</h3>
              </div>
              <button className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90">
                <Download className="h-4 w-4" />
                Download PDF
              </button>
            </div>

            <div className="rounded-lg border bg-secondary/30 p-8">
              <div className="mx-auto max-w-2xl space-y-6">
                <div className="text-center">
                  <div className="mb-2 flex items-center justify-center gap-2">
                    <Shield className="h-6 w-6 text-primary" />
                    <span className="text-xl font-bold">VerifAI</span>
                  </div>
                  <h2 className="text-lg font-semibold">Portfolio Verification Report</h2>
                  <p className="text-sm text-muted-foreground">
                    {v.metadata?.portfolio_name || v.metadata?.name || v.id}
                    {v.completed_at && ` | Generated ${new Date(v.completed_at).toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}`}
                  </p>
                </div>
                <hr />
                <div>
                  <h4 className="mb-2 font-semibold">Executive Summary</h4>
                  <p className="text-sm text-muted-foreground">
                    This report certifies that the Net Asset Value (NAV) of{" "}
                    {v.metadata?.portfolio_name || v.metadata?.name || "the portfolio"}{" "}
                    has been independently verified using zero-knowledge computation.
                    All loan-level calculations including interest accrual, LTV ratios,
                    and covenant compliance have been verified without exposing
                    underlying borrower data.
                  </p>
                </div>
                {v.result_data && (
                  <div>
                    <h4 className="mb-2 font-semibold">Verified Metrics</h4>
                    <table className="w-full text-sm">
                      <tbody>
                        {v.result_data.nav_value != null && (
                          <tr className="border-b">
                            <td className="py-2 text-muted-foreground">NAV</td>
                            <td className="py-2 text-right font-medium">{formatCurrency(v.result_data.nav_value)}</td>
                          </tr>
                        )}
                        {v.result_data.total_principal != null && (
                          <tr className="border-b">
                            <td className="py-2 text-muted-foreground">Total Principal</td>
                            <td className="py-2 text-right font-medium">{formatCurrency(v.result_data.total_principal)}</td>
                          </tr>
                        )}
                        {v.result_data.loan_count != null && (
                          <tr className="border-b">
                            <td className="py-2 text-muted-foreground">Loan Count</td>
                            <td className="py-2 text-right font-medium">{v.result_data.loan_count}</td>
                          </tr>
                        )}
                        {v.result_data.weighted_avg_rate != null && (
                          <tr className="border-b">
                            <td className="py-2 text-muted-foreground">Weighted Avg Rate</td>
                            <td className="py-2 text-right font-medium">{(v.result_data.weighted_avg_rate * 100).toFixed(2)}%</td>
                          </tr>
                        )}
                        {v.result_data.avg_ltv_ratio != null && (
                          <tr>
                            <td className="py-2 text-muted-foreground">Average LTV</td>
                            <td className="py-2 text-right font-medium">{(v.result_data.avg_ltv_ratio * 100).toFixed(1)}%</td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                )}
                {v.proof_certificate && (
                  <div>
                    <h4 className="mb-2 font-semibold">Proof Certificate</h4>
                    <div className="rounded-lg bg-card p-4 font-mono text-xs">
                      <p>Algorithm: {v.proof_certificate.algorithm}</p>
                      <p>Proof Hash: {v.proof_hash}</p>
                      <p>On-Chain: {v.proof_certificate.block_attestation}</p>
                      <p>Timestamp: {v.proof_certificate.timestamp}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
