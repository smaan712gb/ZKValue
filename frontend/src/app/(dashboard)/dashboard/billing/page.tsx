"use client";

import { Header } from "@/components/layout/header";
import {
  CheckCircle,
  CreditCard,
  Download,
  ExternalLink,
  Loader2,
  Zap,
} from "lucide-react";
import { useEffect, useState } from "react";
import api from "@/lib/api";
import { toast } from "sonner";

interface CurrentPlan {
  name: string;
  price: number | null;
  nextBillingDate: string | null;
  usageCount: number;
  usageLimit: number;
  paymentMethod?: {
    brand: string;
    last4: string;
    expMonth: number;
    expYear: number;
  } | null;
  invoices?: Invoice[];
}

interface Invoice {
  id: string;
  date: string;
  amount: number;
  status: string;
  downloadUrl?: string;
}

const plans = [
  {
    id: "starter",
    name: "Starter",
    price: 499,
    features: ["10 verifications/month", "PDF proof certificates", "Email support", "1 module", "5 team members"],
  },
  {
    id: "professional",
    name: "Professional",
    price: 1999,
    features: ["50 verifications/month", "API access + webhooks", "White-label reports", "Both modules", "25 team members", "Priority support", "Custom LLM provider"],
  },
  {
    id: "enterprise",
    name: "Enterprise",
    price: null,
    features: ["Unlimited verifications", "On-premise deployment", "Custom ZK circuits", "SSO / SAML", "Dedicated support", "SLA guarantee", "Audit integration"],
  },
];

export default function BillingPage() {
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [currentPlan, setCurrentPlan] = useState<CurrentPlan | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCurrentPlan();
  }, []);

  const fetchCurrentPlan = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get("/billing/current-plan");
      setCurrentPlan(res.data);
    } catch {
      setError("Failed to load billing information.");
      toast.error("Failed to load billing information.");
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = async (plan: string) => {
    setActionLoading(plan);
    try {
      const res = await api.post("/billing/create-checkout-session", { plan });
      if (res.data?.url) {
        window.location.href = res.data.url;
      } else {
        toast.error("Failed to create checkout session. No redirect URL received.");
      }
    } catch {
      toast.error(`Failed to initiate upgrade to ${plan}. Please try again.`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleManageBilling = async () => {
    setActionLoading("portal");
    try {
      const res = await api.post("/billing/portal-session");
      if (res.data?.url) {
        window.location.href = res.data.url;
      } else {
        toast.error("Failed to open billing portal. No redirect URL received.");
      }
    } catch {
      toast.error("Failed to open billing portal. Please try again.");
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) {
    return (
      <div>
        <Header title="Billing" description="Manage your subscription and billing" />
        <div className="flex items-center justify-center p-24">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  if (error && !currentPlan) {
    return (
      <div>
        <Header title="Billing" description="Manage your subscription and billing" />
        <div className="flex flex-col items-center justify-center gap-4 p-24">
          <p className="text-sm text-muted-foreground">{error}</p>
          <button
            onClick={fetchCurrentPlan}
            className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const currentPlanName = currentPlan?.name?.toLowerCase() ?? "";
  const usagePercent = currentPlan && currentPlan.usageLimit > 0
    ? Math.round((currentPlan.usageCount / currentPlan.usageLimit) * 100)
    : 0;
  const invoices = currentPlan?.invoices ?? [];
  const paymentMethod = currentPlan?.paymentMethod;

  return (
    <div>
      <Header title="Billing" description="Manage your subscription and billing" />

      <div className="p-6">
        {/* Current Plan */}
        <div className="mb-8 rounded-xl border bg-white p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-primary" />
                <h2 className="text-lg font-semibold">{currentPlan?.name ?? "—"} Plan</h2>
              </div>
              <p className="mt-1 text-sm text-muted-foreground">
                {currentPlan?.price != null
                  ? `$${currentPlan.price.toLocaleString()}/month`
                  : "Custom pricing"}
                {currentPlan?.nextBillingDate && (
                  <> &middot; Next billing date: {new Date(currentPlan.nextBillingDate).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}</>
                )}
              </p>
            </div>
            <div className="text-right">
              <div className="text-sm text-muted-foreground">Usage this month</div>
              <div className="text-2xl font-bold text-foreground">
                {currentPlan?.usageCount ?? 0} / {currentPlan?.usageLimit ?? 0}
              </div>
              <div className="mt-1 h-2 w-32 overflow-hidden rounded-full bg-secondary">
                <div
                  className="h-full rounded-full bg-primary"
                  style={{ width: `${Math.min(usagePercent, 100)}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Plans */}
        <div className="mb-8 grid gap-6 md:grid-cols-3">
          {plans.map((plan) => {
            const isCurrent = plan.id === currentPlanName;
            return (
              <div
                key={plan.name}
                className={`rounded-xl border p-6 ${
                  isCurrent ? "border-primary bg-primary/5 shadow-sm" : "bg-white"
                }`}
              >
                {isCurrent && (
                  <div className="mb-3 inline-block rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
                    Current Plan
                  </div>
                )}
                <h3 className="text-lg font-semibold">{plan.name}</h3>
                <div className="my-3">
                  {plan.price ? (
                    <>
                      <span className="text-3xl font-bold">${plan.price.toLocaleString()}</span>
                      <span className="text-muted-foreground">/mo</span>
                    </>
                  ) : (
                    <span className="text-3xl font-bold">Custom</span>
                  )}
                </div>
                <ul className="mb-6 space-y-2">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-center gap-2 text-sm text-muted-foreground">
                      <CheckCircle className="h-3.5 w-3.5 shrink-0 text-chart-2" />
                      {f}
                    </li>
                  ))}
                </ul>
                {isCurrent ? (
                  <button disabled className="w-full rounded-lg border bg-secondary py-2 text-sm font-medium text-muted-foreground">
                    Current Plan
                  </button>
                ) : (
                  <button
                    onClick={() => handleUpgrade(plan.id)}
                    disabled={actionLoading === plan.id}
                    className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary py-2 text-sm font-medium text-white hover:bg-primary/90 disabled:opacity-50"
                  >
                    {actionLoading === plan.id && <Loader2 className="h-4 w-4 animate-spin" />}
                    {plan.price ? "Upgrade" : "Contact Sales"}
                  </button>
                )}
              </div>
            );
          })}
        </div>

        {/* Payment Method */}
        <div className="mb-8 rounded-xl border bg-white p-6">
          <h2 className="mb-4 font-semibold">Payment Method</h2>
          {paymentMethod ? (
            <div className="flex items-center justify-between rounded-lg border p-4">
              <div className="flex items-center gap-3">
                <CreditCard className="h-5 w-5 text-muted-foreground" />
                <div>
                  <div className="text-sm font-medium capitalize">{paymentMethod.brand} ending in {paymentMethod.last4}</div>
                  <div className="text-xs text-muted-foreground">Expires {String(paymentMethod.expMonth).padStart(2, "0")}/{paymentMethod.expYear}</div>
                </div>
              </div>
              <button
                onClick={handleManageBilling}
                disabled={actionLoading === "portal"}
                className="flex items-center gap-1 text-sm font-medium text-primary hover:underline disabled:opacity-50"
              >
                {actionLoading === "portal" && <Loader2 className="h-3 w-3 animate-spin" />}
                Update
              </button>
            </div>
          ) : (
            <div className="flex items-center justify-between rounded-lg border border-dashed p-4">
              <div className="flex items-center gap-3">
                <CreditCard className="h-5 w-5 text-muted-foreground" />
                <div className="text-sm text-muted-foreground">No payment method on file</div>
              </div>
              <button
                onClick={handleManageBilling}
                disabled={actionLoading === "portal"}
                className="flex items-center gap-1 text-sm font-medium text-primary hover:underline disabled:opacity-50"
              >
                {actionLoading === "portal" && <Loader2 className="h-3 w-3 animate-spin" />}
                Add
              </button>
            </div>
          )}
        </div>

        {/* Invoices */}
        <div className="rounded-xl border bg-white">
          <div className="border-b px-6 py-4">
            <h2 className="font-semibold">Invoice History</h2>
          </div>
          <div className="divide-y">
            {invoices.length === 0 ? (
              <div className="px-6 py-8 text-center text-sm text-muted-foreground">
                No invoices yet.
              </div>
            ) : (
              invoices.map((inv) => (
                <div key={inv.id} className="flex items-center justify-between px-6 py-4">
                  <div className="flex items-center gap-4">
                    <div className="text-sm font-medium">{new Date(inv.date).toLocaleDateString("en-US", { month: "long", year: "numeric" })}</div>
                    <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium capitalize text-emerald-700">{inv.status}</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-sm font-medium">${inv.amount.toLocaleString()}.00</span>
                    {inv.downloadUrl && (
                      <a href={inv.downloadUrl} target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-foreground">
                        <Download className="h-4 w-4" />
                      </a>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
