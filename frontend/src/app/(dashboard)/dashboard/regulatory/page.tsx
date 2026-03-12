"use client";

import { Header } from "@/components/layout/header";
import { useState, useCallback } from "react";
import {
  FileText,
  Globe,
  ChevronDown,
  ChevronUp,
  Loader2,
  BookOpen,
  AlertCircle,
  Sparkles,
} from "lucide-react";
import api from "@/lib/api";
import { toast } from "sonner";

// ─── Types ────────────────────────────────────────────────────────────────────

interface ReportSection {
  title: string;
  data: Record<string, unknown>;
}

interface Report {
  report_type: string;
  generated_at: string;
  sections: ReportSection[];
}

interface Narrative {
  filing_summary: string;
  risk_disclosure: string;
  compliance_attestation: string;
  recommendations: string;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatValue(val: unknown): string {
  if (val === null || val === undefined) return "—";
  if (typeof val === "boolean") return val ? "Yes" : "No";
  if (typeof val === "number") return val.toLocaleString();
  if (typeof val === "object") return JSON.stringify(val, null, 2);
  return String(val);
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function SectionAccordion({ section }: { section: ReportSection }) {
  const [open, setOpen] = useState(false);
  const entries = Object.entries(section.data);

  return (
    <div className="rounded-lg border">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between px-4 py-3 text-left hover:bg-secondary/40 transition-colors"
      >
        <span className="text-sm font-medium text-foreground">{section.title}</span>
        {open ? (
          <ChevronUp className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        )}
      </button>
      {open && (
        <div className="border-t px-4 py-3">
          {entries.length === 0 ? (
            <p className="text-xs text-muted-foreground">No data available.</p>
          ) : (
            <dl className="grid gap-2 sm:grid-cols-2">
              {entries.map(([k, v]) => (
                <div key={k} className="flex flex-col gap-0.5">
                  <dt className="text-xs font-medium text-muted-foreground capitalize">
                    {k.replace(/_/g, " ")}
                  </dt>
                  <dd className="text-sm text-foreground font-mono break-words">
                    {formatValue(v)}
                  </dd>
                </div>
              ))}
            </dl>
          )}
        </div>
      )}
    </div>
  );
}

function NarrativeDisplay({ narrative }: { narrative: Narrative }) {
  const fields: { key: keyof Narrative; label: string }[] = [
    { key: "filing_summary", label: "Filing Summary" },
    { key: "risk_disclosure", label: "Risk Disclosure" },
    { key: "compliance_attestation", label: "Compliance Attestation" },
    { key: "recommendations", label: "Recommendations" },
  ];

  return (
    <div className="mt-4 space-y-3">
      {fields.map(({ key, label }) => (
        <div key={key} className="rounded-lg border bg-secondary/20 p-4">
          <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            {label}
          </p>
          <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">
            {narrative[key] || "—"}
          </p>
        </div>
      ))}
    </div>
  );
}

// ─── Report Card ──────────────────────────────────────────────────────────────

interface ReportCardProps {
  title: string;
  description: string;
  icon: React.ElementType;
  iconBg: string;
  reportType: "form-pf" | "aifmd";
  endpoint: string;
}

function ReportCard({
  title,
  description,
  icon: Icon,
  iconBg,
  reportType,
  endpoint,
}: ReportCardProps) {
  const [report, setReport] = useState<Report | null>(null);
  const [narrative, setNarrative] = useState<Narrative | null>(null);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [generatingNarrative, setGeneratingNarrative] = useState(false);

  const handleGenerateReport = useCallback(async () => {
    setGeneratingReport(true);
    try {
      const res = await api.get<Report>(endpoint);
      setReport(res.data);
      setNarrative(null);
      toast.success(`${title} generated successfully`);
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(detail || `Failed to generate ${title}`);
    } finally {
      setGeneratingReport(false);
    }
  }, [endpoint, title]);

  const handleGenerateNarrative = useCallback(async () => {
    setGeneratingNarrative(true);
    try {
      const res = await api.post<Narrative>(
        `/regulatory/narrative/${reportType}`
      );
      setNarrative(res.data);
      toast.success("Narrative generated successfully");
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(detail || "Failed to generate narrative");
    } finally {
      setGeneratingNarrative(false);
    }
  }, [reportType]);

  return (
    <div className="rounded-xl border bg-white flex flex-col">
      {/* Card header */}
      <div className="p-6 border-b">
        <div className="flex items-start gap-4">
          <div
            className={`flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-lg ${iconBg}`}
          >
            <Icon className="h-6 w-6" />
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="font-semibold text-foreground text-base">{title}</h2>
            <p className="mt-1 text-sm text-muted-foreground">{description}</p>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <button
            onClick={handleGenerateReport}
            disabled={generatingReport}
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90 disabled:opacity-50 transition-colors"
          >
            {generatingReport ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <FileText className="h-4 w-4" />
            )}
            {generatingReport ? "Generating…" : "Generate Report"}
          </button>
          {report && (
            <button
              onClick={handleGenerateNarrative}
              disabled={generatingNarrative}
              className="inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium hover:bg-secondary disabled:opacity-50 transition-colors"
            >
              {generatingNarrative ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4" />
              )}
              {generatingNarrative ? "Generating…" : "Generate Narrative"}
            </button>
          )}
        </div>
      </div>

      {/* Report sections */}
      {report && (
        <div className="p-6 space-y-3 flex-1">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BookOpen className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium text-foreground">
                Report Sections
              </span>
            </div>
            <span className="text-xs text-muted-foreground">
              Generated{" "}
              {new Date(report.generated_at).toLocaleString()}
            </span>
          </div>

          {report.sections.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
              <AlertCircle className="mb-2 h-8 w-8" />
              <p className="text-sm">No sections returned in this report.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {report.sections.map((section, idx) => (
                <SectionAccordion key={idx} section={section} />
              ))}
            </div>
          )}

          {/* Narrative */}
          {narrative && <NarrativeDisplay narrative={narrative} />}
        </div>
      )}
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function RegulatoryPage() {
  return (
    <div>
      <Header
        title="Regulatory Reports"
        description="Generate SEC Form PF and AIFMD Annex IV compliance reports with AI-powered narratives"
      />

      <div className="p-6">
        <div className="grid gap-6 lg:grid-cols-2">
          <ReportCard
            title="SEC Form PF"
            description="Quarterly reporting form for registered investment advisers that manage private funds, providing systemic risk data to the SEC."
            icon={FileText}
            iconBg="bg-blue-50 text-blue-600"
            reportType="form-pf"
            endpoint="/regulatory/form-pf"
          />
          <ReportCard
            title="AIFMD Annex IV"
            description="Alternative Investment Fund Managers Directive Annex IV reporting for EU regulatory transparency and systemic risk monitoring."
            icon={Globe}
            iconBg="bg-violet-50 text-violet-600"
            reportType="aifmd"
            endpoint="/regulatory/aifmd"
          />
        </div>
      </div>
    </div>
  );
}
