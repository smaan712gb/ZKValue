"use client";

import { Header } from "@/components/layout/header";
import { useState, useEffect, useCallback } from "react";
import {
  Search,
  AlertCircle,
  Loader2,
  ChevronDown,
  ChevronUp,
  Lightbulb,
  MessageSquare,
  Code2,
  Table2,
} from "lucide-react";
import api from "@/lib/api";
import { toast } from "sonner";

// ─── Types ────────────────────────────────────────────────────────────────────

interface QueryResult {
  answer: string;
  sql: string;
  rows: Record<string, unknown>[];
  row_count: number;
  columns?: string[];
}

interface SuggestionsResponse {
  suggestions: string[];
}

// ─── SQL Code Block ───────────────────────────────────────────────────────────

function CollapsibleSQL({ sql }: { sql: string }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="rounded-xl border bg-card overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between px-5 py-4 text-left hover:bg-secondary/30 transition-colors"
      >
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-violet-100">
            <Code2 className="h-4 w-4 text-violet-600" />
          </div>
          <span className="text-sm font-semibold text-foreground">
            Generated SQL
          </span>
        </div>
        {open ? (
          <ChevronUp className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        )}
      </button>

      {open && (
        <div className="border-t bg-gray-950 px-5 py-4">
          <pre className="overflow-x-auto text-xs leading-relaxed text-emerald-400 font-mono whitespace-pre-wrap break-words">
            {sql}
          </pre>
        </div>
      )}
    </div>
  );
}

// ─── Results Table ────────────────────────────────────────────────────────────

function ResultsTable({
  rows,
  columns,
  rowCount,
}: {
  rows: Record<string, unknown>[];
  columns: string[];
  rowCount: number;
}) {
  if (rows.length === 0) {
    return (
      <div className="rounded-xl border bg-card p-8 text-center">
        <Table2 className="mx-auto mb-3 h-8 w-8 text-muted-foreground" />
        <p className="text-sm text-muted-foreground">No rows returned.</p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border bg-card">
      <div className="flex items-center gap-2 border-b px-5 py-4">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-blue-100">
          <Table2 className="h-4 w-4 text-blue-600" />
        </div>
        <span className="text-sm font-semibold text-foreground">Results</span>
        <span className="ml-auto rounded-full bg-secondary px-2.5 py-0.5 text-xs font-medium text-muted-foreground">
          {rowCount.toLocaleString()} row{rowCount !== 1 ? "s" : ""}
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-max">
          <thead>
            <tr className="border-b bg-secondary/50">
              {columns.map((col) => (
                <th
                  key={col}
                  className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground whitespace-nowrap"
                >
                  {col.replace(/_/g, " ")}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y">
            {rows.map((row, idx) => (
              <tr key={idx} className="transition-colors hover:bg-secondary/30">
                {columns.map((col) => {
                  const val = row[col];
                  return (
                    <td
                      key={col}
                      className="px-5 py-3 text-sm text-foreground whitespace-nowrap"
                    >
                      {val === null || val === undefined ? (
                        <span className="text-muted-foreground">—</span>
                      ) : typeof val === "number" ? (
                        val.toLocaleString()
                      ) : (
                        String(val)
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {rowCount > rows.length && (
        <div className="border-t px-5 py-3">
          <p className="text-xs text-muted-foreground">
            Showing {rows.length} of {rowCount.toLocaleString()} rows.
          </p>
        </div>
      )}
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function NLQueryPage() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [suggestionsLoading, setSuggestionsLoading] = useState(true);

  const fetchSuggestions = useCallback(async () => {
    setSuggestionsLoading(true);
    try {
      const res = await api.get<SuggestionsResponse>("/nl-query/suggestions");
      setSuggestions(res.data?.suggestions ?? []);
    } catch {
      // Silently fail — suggestions are non-critical
      setSuggestions([]);
    } finally {
      setSuggestionsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSuggestions();
  }, [fetchSuggestions]);

  const handleAsk = useCallback(async () => {
    const q = question.trim();
    if (!q) {
      toast.error("Please enter a question.");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await api.post<QueryResult>("/nl-query/query", {
        question: q,
      });
      const data = res.data;

      // Derive columns from first row if not provided
      let cols = data.columns ?? [];
      if (cols.length === 0 && data.rows && data.rows.length > 0) {
        cols = Object.keys(data.rows[0]);
      }

      setResult({ ...data, columns: cols });
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ??
        (err instanceof Error ? err.message : "Query failed.");
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }, [question]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleAsk();
    }
  };

  const columns = result?.columns ?? [];

  return (
    <div>
      <Header
        title="Natural Language Query"
        description="Ask questions about your portfolio data in plain English"
      />

      <div className="space-y-6 p-6">
        {/* Query Input */}
        <div className="rounded-xl border bg-card p-6">
          <div className="mb-4 flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
              <MessageSquare className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h2 className="font-semibold text-foreground">Ask a Question</h2>
              <p className="text-xs text-muted-foreground">
                Press Ctrl+Enter to submit
              </p>
            </div>
          </div>

          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="e.g. What is the total NAV of loans with LTV above 80%?"
            rows={4}
            className="w-full resize-none rounded-lg border bg-secondary/20 px-4 py-3 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-primary focus:bg-card focus:ring-2 focus:ring-primary/20"
          />

          <div className="mt-3 flex items-center justify-end gap-3">
            {question.trim() && (
              <button
                onClick={() => {
                  setQuestion("");
                  setResult(null);
                  setError(null);
                }}
                className="rounded-lg border px-4 py-2 text-sm font-medium text-muted-foreground hover:bg-secondary hover:text-foreground"
              >
                Clear
              </button>
            )}
            <button
              onClick={handleAsk}
              disabled={loading || !question.trim()}
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2 text-sm font-medium text-white hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Search className="h-4 w-4" />
              )}
              Ask
            </button>
          </div>
        </div>

        {/* Suggested Questions */}
        {(suggestionsLoading || suggestions.length > 0) && !result && !loading && (
          <div className="rounded-xl border bg-card p-5">
            <div className="mb-3 flex items-center gap-2">
              <Lightbulb className="h-4 w-4 text-amber-500" />
              <span className="text-sm font-semibold text-foreground">
                Suggested Questions
              </span>
            </div>

            {suggestionsLoading ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading suggestions...
              </div>
            ) : (
              <div className="flex flex-wrap gap-2">
                {suggestions.map((s, i) => (
                  <button
                    key={i}
                    onClick={() => setQuestion(s)}
                    className="rounded-full border border-border bg-secondary/50 px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:border-primary hover:bg-primary/5 hover:text-primary"
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex flex-col items-center justify-center rounded-xl border bg-card py-16">
            <Loader2 className="mb-4 h-10 w-10 animate-spin text-primary" />
            <p className="text-sm font-medium text-foreground">
              Processing your query...
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              Translating to SQL and fetching results.
            </p>
          </div>
        )}

        {/* Error State */}
        {!loading && error && (
          <div className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-5">
            <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-red-500" />
            <div>
              <p className="text-sm font-semibold text-red-700">Query Failed</p>
              <p className="mt-1 text-xs text-red-600">{error}</p>
            </div>
          </div>
        )}

        {/* Results */}
        {!loading && result && (
          <div className="space-y-4">
            {/* Natural Language Answer */}
            <div className="rounded-xl border border-primary/20 bg-primary/5 p-6">
              <div className="mb-3 flex items-center gap-2">
                <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary/10">
                  <MessageSquare className="h-4 w-4 text-primary" />
                </div>
                <span className="text-sm font-semibold text-foreground">
                  Answer
                </span>
              </div>
              <p className="text-sm leading-relaxed text-foreground">
                {result.answer}
              </p>
            </div>

            {/* Generated SQL */}
            {result.sql && <CollapsibleSQL sql={result.sql} />}

            {/* Results Table */}
            {result.rows && (
              <ResultsTable
                rows={result.rows}
                columns={columns}
                rowCount={result.row_count ?? result.rows.length}
              />
            )}
          </div>
        )}
      </div>
    </div>
  );
}
