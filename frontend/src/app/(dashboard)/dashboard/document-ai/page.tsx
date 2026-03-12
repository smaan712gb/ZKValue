"use client";

import { Header } from "@/components/layout/header";
import { useState, useRef, useCallback } from "react";
import {
  Upload,
  FileText,
  AlertCircle,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  X,
  FileSpreadsheet,
  Cpu,
} from "lucide-react";
import api from "@/lib/api";
import { toast } from "sonner";

interface ExtractedLoan {
  loan_id?: string;
  principal?: number;
  balance?: number;
  rate?: number;
  ltv?: number;
  status?: string;
  [key: string]: unknown;
}

interface ParseResult {
  filename: string;
  extraction_method: string;
  loan_count: number;
  warnings: string[];
  loans: ExtractedLoan[];
  verification_id?: string;
  verification_status?: string;
}

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
const ACCEPTED_TYPES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "application/vnd.ms-excel",
  "text/csv",
];
const ACCEPTED_EXTENSIONS = ".pdf,.xlsx,.xls,.csv";

function formatCurrency(v: number | undefined) {
  if (v === undefined || v === null) return "—";
  if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
  if (v >= 1e3) return `$${(v / 1e3).toFixed(0)}K`;
  return `$${v.toLocaleString()}`;
}

function formatPercent(v: number | undefined) {
  if (v === undefined || v === null) return "—";
  return `${(v * 100).toFixed(2)}%`;
}

export default function DocumentAIPage() {
  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ParseResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): string | null => {
    if (file.size > MAX_FILE_SIZE) {
      return "File exceeds 50MB limit.";
    }
    const ext = file.name.split(".").pop()?.toLowerCase();
    if (!["pdf", "xlsx", "xls", "csv"].includes(ext ?? "")) {
      return "Only PDF, XLSX, XLS, and CSV files are accepted.";
    }
    return null;
  };

  const handleFileSelect = (file: File) => {
    const err = validateFile(file);
    if (err) {
      toast.error(err);
      return;
    }
    setSelectedFile(file);
    setResult(null);
    setError(null);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFileSelect(file);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFileSelect(file);
    e.target.value = "";
  };

  const runAction = useCallback(
    async (endpoint: string, actionLabel: string) => {
      if (!selectedFile) {
        toast.error("Please select a file first.");
        return;
      }
      setLoading(true);
      setError(null);
      setResult(null);

      try {
        const formData = new FormData();
        formData.append("file", selectedFile);

        const res = await api.post(endpoint, formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });

        setResult(res.data);
        toast.success(`${actionLabel} completed successfully.`);
      } catch (err: unknown) {
        const msg =
          (err as { response?: { data?: { detail?: string } } })?.response
            ?.data?.detail ??
          (err instanceof Error ? err.message : `${actionLabel} failed.`);
        setError(msg);
        toast.error(msg);
      } finally {
        setLoading(false);
      }
    },
    [selectedFile]
  );

  const previewLoans = result?.loans?.slice(0, 5) ?? [];

  return (
    <div>
      <Header
        title="Document AI"
        description="Parse PDF and Excel loan tapes with AI-powered extraction"
      />

      <div className="space-y-6 p-6">
        {/* Upload Zone */}
        <div className="rounded-xl border bg-white p-6">
          <div className="mb-4 flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
              <Cpu className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h2 className="font-semibold text-foreground">Upload Document</h2>
              <p className="text-xs text-muted-foreground">
                PDF, XLSX, XLS, or CSV — max 50MB
              </p>
            </div>
          </div>

          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => !loading && fileInputRef.current?.click()}
            className={`relative flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-12 transition-colors ${
              dragOver
                ? "border-primary bg-primary/5"
                : selectedFile
                ? "border-emerald-400 bg-emerald-50"
                : "border-border hover:border-primary/50 hover:bg-secondary/30"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              accept={ACCEPTED_EXTENSIONS}
              onChange={handleInputChange}
            />

            {selectedFile ? (
              <>
                {selectedFile.name.endsWith(".pdf") ? (
                  <FileText className="mb-3 h-10 w-10 text-emerald-500" />
                ) : (
                  <FileSpreadsheet className="mb-3 h-10 w-10 text-emerald-500" />
                )}
                <p className="text-sm font-semibold text-foreground">
                  {selectedFile.name}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                </p>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedFile(null);
                    setResult(null);
                    setError(null);
                  }}
                  className="mt-3 inline-flex items-center gap-1 rounded-full border border-red-200 bg-red-50 px-3 py-1 text-xs font-medium text-red-600 hover:bg-red-100"
                >
                  <X className="h-3 w-3" />
                  Remove
                </button>
              </>
            ) : (
              <>
                <Upload className="mb-3 h-10 w-10 text-muted-foreground" />
                <p className="mb-1 text-sm font-medium text-foreground">
                  Drag and drop your loan tape here
                </p>
                <p className="text-xs text-muted-foreground">
                  or click to browse files
                </p>
                <p className="mt-2 text-[11px] text-muted-foreground">
                  Supported: PDF, XLSX, XLS, CSV — up to 50MB
                </p>
              </>
            )}
          </div>

          {/* Action Buttons */}
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <button
              disabled={!selectedFile || loading}
              onClick={() => runAction("/document-ai/parse", "Parse")}
              className="inline-flex items-center gap-2 rounded-lg border border-border bg-white px-5 py-2 text-sm font-medium text-foreground transition-colors hover:bg-secondary disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <FileText className="h-4 w-4" />
              )}
              Parse Only
            </button>
            <button
              disabled={!selectedFile || loading}
              onClick={() =>
                runAction(
                  "/document-ai/parse-and-verify",
                  "Parse & Verify"
                )
              }
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <CheckCircle2 className="h-4 w-4" />
              )}
              Parse &amp; Verify
            </button>
          </div>
        </div>

        {/* Loading Overlay */}
        {loading && (
          <div className="flex flex-col items-center justify-center rounded-xl border bg-white py-16">
            <Loader2 className="mb-4 h-10 w-10 animate-spin text-primary" />
            <p className="text-sm font-medium text-foreground">
              Processing document...
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              AI extraction in progress. This may take a moment.
            </p>
          </div>
        )}

        {/* Error State */}
        {!loading && error && (
          <div className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-5">
            <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-red-500" />
            <div>
              <p className="text-sm font-semibold text-red-700">
                Extraction Failed
              </p>
              <p className="mt-1 text-xs text-red-600">{error}</p>
            </div>
          </div>
        )}

        {/* Results */}
        {!loading && result && (
          <div className="space-y-4">
            {/* Summary Card */}
            <div className="rounded-xl border bg-white p-6">
              <div className="mb-4 flex items-center gap-2">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-50">
                  <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                </div>
                <div>
                  <h2 className="font-semibold text-foreground">
                    Extraction Results
                  </h2>
                  <p className="text-xs text-muted-foreground">
                    {result.filename}
                  </p>
                </div>
                {result.verification_id && (
                  <span className="ml-auto inline-flex items-center gap-1 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-700">
                    <CheckCircle2 className="h-3 w-3" />
                    Verification Started
                  </span>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
                <div className="rounded-lg bg-secondary/50 p-4">
                  <p className="text-xs text-muted-foreground">
                    Extraction Method
                  </p>
                  <p className="mt-1 text-base font-semibold capitalize text-foreground">
                    {result.extraction_method ?? "—"}
                  </p>
                </div>
                <div className="rounded-lg bg-secondary/50 p-4">
                  <p className="text-xs text-muted-foreground">Loans Extracted</p>
                  <p className="mt-1 text-base font-semibold text-foreground">
                    {result.loan_count?.toLocaleString() ?? "—"}
                  </p>
                </div>
                <div className="rounded-lg bg-secondary/50 p-4">
                  <p className="text-xs text-muted-foreground">Warnings</p>
                  <p className="mt-1 text-base font-semibold text-foreground">
                    {result.warnings?.length ?? 0}
                  </p>
                </div>
              </div>

              {/* Warnings */}
              {result.warnings && result.warnings.length > 0 && (
                <div className="mt-4 space-y-2">
                  {result.warnings.map((w, i) => (
                    <div
                      key={i}
                      className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3"
                    >
                      <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-amber-500" />
                      <p className="text-xs text-amber-700">{w}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Preview Table */}
            {previewLoans.length > 0 && (
              <div className="overflow-hidden rounded-xl border bg-white">
                <div className="border-b px-6 py-4">
                  <h3 className="font-semibold text-foreground">
                    Loan Preview
                  </h3>
                  <p className="text-xs text-muted-foreground">
                    First {previewLoans.length} of {result.loan_count} loans
                  </p>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[600px]">
                    <thead>
                      <tr className="border-b bg-secondary/50">
                        {[
                          "Loan ID",
                          "Principal",
                          "Balance",
                          "Rate",
                          "LTV",
                          "Status",
                        ].map((col) => (
                          <th
                            key={col}
                            className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground"
                          >
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {previewLoans.map((loan, idx) => (
                        <tr
                          key={loan.loan_id ?? idx}
                          className="transition-colors hover:bg-secondary/30"
                        >
                          <td className="px-6 py-3 font-mono text-xs text-foreground">
                            {loan.loan_id ?? `#${idx + 1}`}
                          </td>
                          <td className="px-6 py-3 text-sm text-foreground">
                            {formatCurrency(loan.principal as number)}
                          </td>
                          <td className="px-6 py-3 text-sm text-foreground">
                            {formatCurrency(loan.balance as number)}
                          </td>
                          <td className="px-6 py-3 text-sm text-foreground">
                            {formatPercent(loan.rate as number)}
                          </td>
                          <td className="px-6 py-3 text-sm text-foreground">
                            {formatPercent(loan.ltv as number)}
                          </td>
                          <td className="px-6 py-3">
                            {loan.status ? (
                              <span
                                className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                                  loan.status === "current"
                                    ? "bg-emerald-50 text-emerald-700"
                                    : loan.status === "delinquent"
                                    ? "bg-amber-50 text-amber-700"
                                    : loan.status === "default"
                                    ? "bg-red-50 text-red-700"
                                    : "bg-secondary text-muted-foreground"
                                }`}
                              >
                                {loan.status}
                              </span>
                            ) : (
                              <span className="text-xs text-muted-foreground">
                                —
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {result.loan_count > 5 && (
                  <div className="border-t px-6 py-3">
                    <p className="text-xs text-muted-foreground">
                      Showing 5 of {result.loan_count} loans. Run a full
                      verification to process all records.
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
