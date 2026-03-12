"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  Shield,
  Brain,
  ArrowRight,
  CheckCircle,
  Lock,
  BarChart3,
  Layers,
  FileCheck,
  Zap,
  Building2,
} from "lucide-react";

export default function LandingPage() {
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav
        className={`fixed top-0 z-50 w-full transition-all duration-300 ${
          scrollY > 20
            ? "bg-white/80 shadow-sm backdrop-blur-lg"
            : "bg-transparent"
        }`}
      >
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary">
              <Shield className="h-5 w-5 text-white" />
            </div>
            <span className="text-xl font-bold tracking-tight text-foreground">
              ZKValue
            </span>
          </div>
          <div className="hidden items-center gap-8 md:flex">
            <a
              href="#features"
              className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              Features
            </a>
            <a
              href="#modules"
              className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              Modules
            </a>
            <a
              href="#pricing"
              className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              Pricing
            </a>
            <a
              href="#compliance"
              className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              Compliance
            </a>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              Sign In
            </Link>
            <Link
              href="/register"
              className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden px-6 pt-32 pb-20">
        <div className="absolute inset-0 -z-10">
          <div className="absolute left-1/2 top-0 h-[600px] w-[800px] -translate-x-1/2 rounded-full bg-primary/5 blur-3xl" />
        </div>
        <div className="mx-auto max-w-4xl text-center">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-4 py-1.5 text-sm font-medium text-primary">
            <Lock className="h-3.5 w-3.5" />
            Cryptographic Proof Layer for Opaque Assets
          </div>
          <h1 className="mb-6 text-5xl font-bold leading-tight tracking-tight text-foreground md:text-6xl lg:text-7xl">
            Prove the value.
            <br />
            <span className="text-primary">Protect the data.</span>
          </h1>
          <p className="mx-auto mb-10 max-w-2xl text-lg leading-relaxed text-muted-foreground md:text-xl">
            Verifiable computation for alternative asset valuation. Zero-knowledge
            proofs ensure your calculations are correct without exposing sensitive
            data. Trusted by funds, auditors, and enterprises.
          </p>
          <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link
              href="/register"
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-8 py-3.5 text-base font-semibold text-white shadow-lg shadow-primary/25 transition-all hover:bg-primary/90 hover:shadow-xl"
            >
              Start Free Trial
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="#modules"
              className="inline-flex items-center gap-2 rounded-lg border border-border px-8 py-3.5 text-base font-semibold text-foreground transition-colors hover:bg-secondary"
            >
              See How It Works
            </Link>
          </div>
          <div className="mt-12 flex items-center justify-center gap-8 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-chart-2" />
              SOC 2 Ready
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-chart-2" />
              IAS 38 Compliant
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-chart-2" />
              On-Chain Attestation
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="border-t bg-secondary/30 px-6 py-20">
        <div className="mx-auto max-w-6xl">
          <div className="mb-12 text-center">
            <h2 className="mb-4 text-3xl font-bold tracking-tight text-foreground">
              Enterprise-grade verification infrastructure
            </h2>
            <p className="mx-auto max-w-2xl text-muted-foreground">
              Built for Big 4 auditors, private credit funds, and AI companies
              that need cryptographic proof of asset valuations.
            </p>
          </div>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {[
              {
                icon: Lock,
                title: "Zero-Knowledge Proofs",
                desc: "Prove computation correctness without revealing raw data. Your loan tapes and model weights stay private.",
              },
              {
                icon: Brain,
                title: "AI-Powered Analysis",
                desc: "DeepSeek-V3 reasoning engine classifies assets, runs valuations, and generates compliance reports.",
              },
              {
                icon: Building2,
                title: "Multi-Tenant Architecture",
                desc: "Enterprise isolation with per-organization LLM configuration, RBAC, and data segregation.",
              },
              {
                icon: FileCheck,
                title: "Compliance Ready",
                desc: "IAS 38, ASC 350, and IFRS compliant reports. Full audit trail for every verification.",
              },
              {
                icon: BarChart3,
                title: "Real-Time Dashboard",
                desc: "Monitor verification status, portfolio health, and valuation trends across your organization.",
              },
              {
                icon: Zap,
                title: "Automated Workflows",
                desc: "Upload loan tapes or connect cloud accounts. Automated verification with webhook notifications.",
              },
            ].map((feature) => (
              <div
                key={feature.title}
                className="rounded-xl border bg-white p-6 transition-shadow hover:shadow-md"
              >
                <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                  <feature.icon className="h-5 w-5 text-primary" />
                </div>
                <h3 className="mb-2 text-lg font-semibold text-foreground">
                  {feature.title}
                </h3>
                <p className="text-sm leading-relaxed text-muted-foreground">
                  {feature.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Modules Section */}
      <section id="modules" className="px-6 py-20">
        <div className="mx-auto max-w-6xl">
          <div className="mb-16 text-center">
            <h2 className="mb-4 text-3xl font-bold tracking-tight text-foreground">
              Two modules. One platform.
            </h2>
            <p className="mx-auto max-w-2xl text-muted-foreground">
              Whether you manage private credit portfolios or need to prove
              AI-IP value, ZKValue has you covered.
            </p>
          </div>

          {/* Module 1: Private Credit */}
          <div className="mb-16 grid items-center gap-12 lg:grid-cols-2">
            <div>
              <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-chart-2/10 px-3 py-1 text-sm font-medium text-chart-2">
                <Shield className="h-3.5 w-3.5" />
                ZK Private Credit
              </div>
              <h3 className="mb-4 text-2xl font-bold text-foreground">
                Verify loan portfolios without exposing borrower data
              </h3>
              <p className="mb-6 text-muted-foreground">
                Private credit funds can prove NAV calculations, LTV ratios, and
                covenant compliance to LPs and auditors — cryptographically.
              </p>
              <ul className="space-y-3">
                {[
                  "Interest accrual verification",
                  "Collateral ratio (LTV) calculation",
                  "Covenant compliance checking",
                  "NAV attestation with proof certificate",
                ].map((item) => (
                  <li key={item} className="flex items-center gap-3 text-sm">
                    <CheckCircle className="h-4 w-4 shrink-0 text-chart-2" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-xl border bg-secondary/50 p-8">
              <div className="space-y-4 font-mono text-sm">
                <div className="text-muted-foreground">
                  {"// Upload encrypted loan tape"}
                </div>
                <div>
                  <span className="text-chart-4">POST</span>{" "}
                  <span className="text-primary">/api/v1/credit/verify</span>
                </div>
                <div className="rounded-lg bg-white p-4 text-xs">
                  <pre className="text-muted-foreground">
{`{
  "portfolio_name": "Fund III - Q4 2025",
  "loan_count": 247,
  "total_principal": 892000000,
  "verification_type": "full_portfolio"
}`}
                  </pre>
                </div>
                <div className="text-muted-foreground">
                  {"// Response: ZK proof + certificate"}
                </div>
                <div className="rounded-lg bg-white p-4 text-xs">
                  <pre className="text-chart-2">
{`{
  "status": "completed",
  "proof_hash": "0x7a3f...e91c",
  "nav_verified": true,
  "certificate_url": "/proofs/abc123.pdf"
}`}
                  </pre>
                </div>
              </div>
            </div>
          </div>

          {/* Module 2: AI-IP Valuation */}
          <div className="grid items-center gap-12 lg:grid-cols-2">
            <div className="order-2 lg:order-1">
              <div className="rounded-xl border bg-secondary/50 p-8">
                <div className="space-y-3">
                  {[
                    {
                      type: "Training Data",
                      value: "$12.4M",
                      method: "Cost Approach",
                      confidence: "94%",
                    },
                    {
                      type: "Model Weights",
                      value: "$8.7M",
                      method: "Cost + Market",
                      confidence: "89%",
                    },
                    {
                      type: "Inference Infra",
                      value: "$3.2M",
                      method: "Income Approach",
                      confidence: "91%",
                    },
                    {
                      type: "Deployed App",
                      value: "$18.5M",
                      method: "Income Approach",
                      confidence: "87%",
                    },
                  ].map((asset) => (
                    <div
                      key={asset.type}
                      className="flex items-center justify-between rounded-lg bg-white p-4"
                    >
                      <div>
                        <div className="font-medium text-foreground">
                          {asset.type}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {asset.method}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-semibold text-foreground">
                          {asset.value}
                        </div>
                        <div className="text-xs text-chart-2">
                          {asset.confidence} confidence
                        </div>
                      </div>
                    </div>
                  ))}
                  <div className="flex items-center justify-between border-t pt-3">
                    <span className="font-semibold text-foreground">
                      Total AI-IP Value
                    </span>
                    <span className="text-lg font-bold text-primary">
                      $42.8M
                    </span>
                  </div>
                </div>
              </div>
            </div>
            <div className="order-1 lg:order-2">
              <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-chart-4/10 px-3 py-1 text-sm font-medium text-chart-4">
                <Brain className="h-3.5 w-3.5" />
                AI-IP Valuation
              </div>
              <h3 className="mb-4 text-2xl font-bold text-foreground">
                Prove your AI assets are worth what you claim
              </h3>
              <p className="mb-6 text-muted-foreground">
                Automated valuation of training data, model weights, inference
                infrastructure, and deployed applications per IAS 38 / ASC 350.
              </p>
              <ul className="space-y-3">
                {[
                  "Automated asset classification with AI",
                  "Multi-method valuation (cost, market, income)",
                  "IAS 38 / ASC 350 compliance checks",
                  "Balance-sheet-ready reports with ZK proofs",
                ].map((item) => (
                  <li key={item} className="flex items-center gap-3 text-sm">
                    <CheckCircle className="h-4 w-4 shrink-0 text-chart-4" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="border-t bg-secondary/30 px-6 py-20">
        <div className="mx-auto max-w-5xl">
          <div className="mb-12 text-center">
            <h2 className="mb-4 text-3xl font-bold tracking-tight text-foreground">
              Simple, transparent pricing
            </h2>
            <p className="text-muted-foreground">
              Start with Starter. Scale to Enterprise. No hidden fees.
            </p>
          </div>
          <div className="grid gap-6 md:grid-cols-3">
            {[
              {
                name: "Starter",
                price: "$499",
                period: "/month",
                desc: "For teams getting started with verified valuations",
                features: [
                  "10 verifications/month",
                  "PDF proof certificates",
                  "Email support",
                  "1 module (Credit or AI-IP)",
                  "Up to 5 team members",
                ],
                cta: "Start Free Trial",
                highlighted: false,
              },
              {
                name: "Professional",
                price: "$1,999",
                period: "/month",
                desc: "For growing funds and AI companies",
                features: [
                  "50 verifications/month",
                  "API access + webhooks",
                  "White-label reports",
                  "Both modules included",
                  "Up to 25 team members",
                  "Priority support",
                  "Custom LLM provider",
                ],
                cta: "Start Free Trial",
                highlighted: true,
              },
              {
                name: "Enterprise",
                price: "Custom",
                period: "",
                desc: "For large institutions and Big 4 firms",
                features: [
                  "Unlimited verifications",
                  "On-premise deployment",
                  "Custom ZK circuits",
                  "SSO / SAML",
                  "Dedicated support",
                  "SLA guarantee",
                  "Audit integration",
                ],
                cta: "Contact Sales",
                highlighted: false,
              },
            ].map((plan) => (
              <div
                key={plan.name}
                className={`rounded-xl border p-8 ${
                  plan.highlighted
                    ? "border-primary bg-white shadow-lg shadow-primary/10"
                    : "bg-white"
                }`}
              >
                {plan.highlighted && (
                  <div className="mb-4 inline-block rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
                    Most Popular
                  </div>
                )}
                <h3 className="text-lg font-semibold text-foreground">
                  {plan.name}
                </h3>
                <div className="my-4">
                  <span className="text-4xl font-bold text-foreground">
                    {plan.price}
                  </span>
                  <span className="text-muted-foreground">{plan.period}</span>
                </div>
                <p className="mb-6 text-sm text-muted-foreground">
                  {plan.desc}
                </p>
                <Link
                  href="/register"
                  className={`mb-6 block w-full rounded-lg py-2.5 text-center text-sm font-medium transition-colors ${
                    plan.highlighted
                      ? "bg-primary text-white hover:bg-primary/90"
                      : "border bg-secondary text-foreground hover:bg-secondary/80"
                  }`}
                >
                  {plan.cta}
                </Link>
                <ul className="space-y-3">
                  {plan.features.map((f) => (
                    <li
                      key={f}
                      className="flex items-center gap-2 text-sm text-muted-foreground"
                    >
                      <CheckCircle className="h-3.5 w-3.5 shrink-0 text-chart-2" />
                      {f}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Compliance Section */}
      <section id="compliance" className="px-6 py-20">
        <div className="mx-auto max-w-4xl text-center">
          <h2 className="mb-4 text-3xl font-bold tracking-tight text-foreground">
            Built for compliance from day one
          </h2>
          <p className="mx-auto mb-12 max-w-2xl text-muted-foreground">
            Every verification produces a cryptographic proof certificate and a
            complete audit trail. Ready for regulators, auditors, and LPs.
          </p>
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { label: "IAS 38", desc: "Intangible Asset Standard" },
              { label: "ASC 350", desc: "US GAAP Goodwill & Intangibles" },
              { label: "SOC 2", desc: "Type II Ready Architecture" },
              { label: "GDPR", desc: "Data Privacy by Design" },
            ].map((item) => (
              <div
                key={item.label}
                className="rounded-xl border bg-secondary/30 p-6"
              >
                <div className="mb-2 text-2xl font-bold text-primary">
                  {item.label}
                </div>
                <div className="text-sm text-muted-foreground">{item.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="border-t bg-primary px-6 py-16">
        <div className="mx-auto max-w-3xl text-center">
          <h2 className="mb-4 text-3xl font-bold tracking-tight text-white">
            Ready to prove your assets&apos; value?
          </h2>
          <p className="mb-8 text-lg text-primary-foreground/80">
            Join leading funds and AI companies using cryptographic proofs for
            asset verification.
          </p>
          <Link
            href="/register"
            className="inline-flex items-center gap-2 rounded-lg bg-white px-8 py-3.5 text-base font-semibold text-primary shadow-lg transition-all hover:bg-gray-50"
          >
            Start Your Free Trial
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t bg-white px-6 py-12">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-6 md:flex-row">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
              <Shield className="h-4 w-4 text-white" />
            </div>
            <span className="text-lg font-bold text-foreground">ZKValue</span>
          </div>
          <div className="flex gap-8 text-sm text-muted-foreground">
            <a href="#" className="hover:text-foreground">Privacy</a>
            <a href="#" className="hover:text-foreground">Terms</a>
            <a href="#" className="hover:text-foreground">Security</a>
            <a href="#" className="hover:text-foreground">Docs</a>
          </div>
          <div className="text-sm text-muted-foreground">
            &copy; {new Date().getFullYear()} ZKValue. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}
