"use client";

import Link from "next/link";
import { useEffect, useState, useRef } from "react";
import { motion, useInView } from "framer-motion";
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
  ChevronRight,
  Sparkles,
  Globe,
} from "lucide-react";
import { ThemeToggle } from "@/components/shared/theme-toggle";

/* ── Animated counter ── */
function AnimatedNumber({ value, prefix = "" }: { value: number; prefix?: string }) {
  const [count, setCount] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true });

  useEffect(() => {
    if (!inView) return;
    let start = 0;
    const duration = 1200;
    const step = (ts: number) => {
      if (!start) start = ts;
      const progress = Math.min((ts - start) / duration, 1);
      setCount(Math.floor(progress * value));
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [inView, value]);

  return <span ref={ref}>{prefix}{count.toLocaleString()}</span>;
}

/* ── Section wrapper with fade-in ── */
function Section({
  children,
  className = "",
  id,
}: {
  children: React.ReactNode;
  className?: string;
  id?: string;
}) {
  return (
    <motion.section
      id={id}
      className={className}
      initial={{ opacity: 0, y: 32 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.6, ease: "easeOut" }}
    >
      {children}
    </motion.section>
  );
}

export default function LandingPage() {
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* ═══════════ Navigation ═══════════ */}
      <nav
        className={`fixed top-0 z-50 w-full transition-all duration-500 ${
          scrollY > 20
            ? "border-b border-border/50 bg-background/70 shadow-sm backdrop-blur-xl"
            : "bg-transparent"
        }`}
      >
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-primary/80 shadow-lg shadow-primary/25">
              <Shield className="h-5 w-5 text-white" />
            </div>
            <span className="text-xl font-bold tracking-tight">
              ZKValue
            </span>
          </div>
          <div className="hidden items-center gap-8 md:flex">
            {["Features", "Modules", "Pricing", "Compliance"].map((item) => (
              <a
                key={item}
                href={`#${item.toLowerCase()}`}
                className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
              >
                {item}
              </a>
            ))}
          </div>
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <Link
              href="/login"
              className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              Sign In
            </Link>
            <Link
              href="/register"
              className="rounded-xl bg-primary px-5 py-2 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/25 transition-all hover:bg-primary/90 hover:shadow-xl"
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* ═══════════ Hero ═══════════ */}
      <section className="relative overflow-hidden px-6 pt-36 pb-24">
        {/* Animated gradient orbs */}
        <div className="absolute inset-0 -z-10 overflow-hidden">
          <div className="animate-pulse-glow absolute -left-32 top-20 h-[500px] w-[500px] rounded-full bg-primary/10 blur-[120px]" />
          <div className="animate-pulse-glow absolute -right-32 top-40 h-[400px] w-[400px] rounded-full bg-chart-4/10 blur-[120px]" style={{ animationDelay: "2s" }} />
          <div className="animate-pulse-glow absolute left-1/2 bottom-0 h-[300px] w-[600px] -translate-x-1/2 rounded-full bg-chart-2/8 blur-[100px]" style={{ animationDelay: "4s" }} />
          <div className="bg-grid-pattern absolute inset-0 text-foreground" />
        </div>

        <motion.div
          className="mx-auto max-w-4xl text-center"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        >
          <motion.div
            className="mb-6 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-4 py-1.5 text-sm font-medium text-primary backdrop-blur-sm"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
          >
            <Sparkles className="h-3.5 w-3.5" />
            Cryptographic Proof Layer for Opaque Assets
          </motion.div>

          <h1 className="mb-6 text-5xl font-extrabold leading-[1.1] tracking-tight md:text-6xl lg:text-7xl">
            Prove the value.
            <br />
            <span className="bg-gradient-to-r from-primary via-chart-4 to-chart-2 bg-clip-text text-transparent">
              Protect the data.
            </span>
          </h1>

          <p className="mx-auto mb-10 max-w-2xl text-lg leading-relaxed text-muted-foreground md:text-xl">
            Verifiable computation for alternative asset valuation. Zero-knowledge
            proofs ensure your calculations are correct without exposing sensitive
            data. Trusted by funds, auditors, and enterprises.
          </p>

          <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link
              href="/register"
              className="group inline-flex items-center gap-2 rounded-xl bg-primary px-8 py-3.5 text-base font-semibold text-white shadow-xl shadow-primary/25 transition-all hover:bg-primary/90 hover:shadow-2xl hover:shadow-primary/30"
            >
              Start Free Trial
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </Link>
            <Link
              href="#modules"
              className="inline-flex items-center gap-2 rounded-xl border border-border bg-background/50 px-8 py-3.5 text-base font-semibold backdrop-blur-sm transition-colors hover:bg-secondary"
            >
              See How It Works
            </Link>
          </div>

          {/* Trust badges */}
          <div className="mt-14 flex flex-wrap items-center justify-center gap-x-8 gap-y-3 text-sm text-muted-foreground">
            {[
              { icon: CheckCircle, label: "SOC 2 Ready" },
              { icon: CheckCircle, label: "IAS 38 Compliant" },
              { icon: CheckCircle, label: "On-Chain Attestation" },
              { icon: Globe, label: "Multi-Jurisdiction" },
            ].map((item) => (
              <div key={item.label} className="flex items-center gap-2">
                <item.icon className="h-4 w-4 text-chart-2" />
                {item.label}
              </div>
            ))}
          </div>
        </motion.div>

        {/* Stats bar */}
        <motion.div
          className="mx-auto mt-20 grid max-w-4xl grid-cols-2 gap-4 md:grid-cols-4"
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.6 }}
        >
          {[
            { value: 892, prefix: "$", suffix: "M+", label: "Assets Verified" },
            { value: 247, prefix: "", suffix: "+", label: "Portfolios Analyzed" },
            { value: 99, prefix: "", suffix: ".9%", label: "Proof Accuracy" },
            { value: 12, prefix: "", suffix: "+", label: "Compliance Frameworks" },
          ].map((stat) => (
            <div
              key={stat.label}
              className="rounded-xl border border-border/50 bg-background/50 p-5 text-center backdrop-blur-sm"
            >
              <div className="text-2xl font-bold text-foreground md:text-3xl">
                <AnimatedNumber value={stat.value} prefix={stat.prefix} />
                {stat.suffix}
              </div>
              <div className="mt-1 text-xs text-muted-foreground">{stat.label}</div>
            </div>
          ))}
        </motion.div>
      </section>

      {/* ═══════════ Features Grid ═══════════ */}
      <Section id="features" className="border-t border-border/50 bg-secondary/30 px-6 py-24">
        <div className="mx-auto max-w-6xl">
          <div className="mb-14 text-center">
            <p className="mb-3 text-sm font-semibold uppercase tracking-widest text-primary">
              Platform Capabilities
            </p>
            <h2 className="mb-4 text-3xl font-bold tracking-tight md:text-4xl">
              Enterprise-grade verification infrastructure
            </h2>
            <p className="mx-auto max-w-2xl text-muted-foreground">
              Built for Big 4 auditors, private credit funds, and AI companies
              that need cryptographic proof of asset valuations.
            </p>
          </div>
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {[
              {
                icon: Lock,
                title: "Zero-Knowledge Proofs",
                desc: "Prove computation correctness without revealing raw data. Your loan tapes and model weights stay private.",
                gradient: "from-primary/10 to-primary/5",
              },
              {
                icon: Brain,
                title: "AI-Powered Analysis",
                desc: "Multi-provider LLM engine classifies assets, runs valuations, and generates compliance reports.",
                gradient: "from-chart-4/10 to-chart-4/5",
              },
              {
                icon: Building2,
                title: "Multi-Tenant Architecture",
                desc: "Enterprise isolation with per-organization LLM configuration, RBAC, and data segregation.",
                gradient: "from-chart-3/10 to-chart-3/5",
              },
              {
                icon: FileCheck,
                title: "Compliance Ready",
                desc: "IAS 38, ASC 350, SEC Form PF, AIFMD compliant reports. Full audit trail for every verification.",
                gradient: "from-chart-2/10 to-chart-2/5",
              },
              {
                icon: BarChart3,
                title: "Real-Time Dashboard",
                desc: "Monitor verification status, portfolio health, and valuation trends with professional visualizations.",
                gradient: "from-chart-5/10 to-chart-5/5",
              },
              {
                icon: Zap,
                title: "Automated Workflows",
                desc: "Upload loan tapes or describe AI assets. Automated verification with async task processing.",
                gradient: "from-chart-1/10 to-chart-1/5",
              },
            ].map((feature, i) => (
              <motion.div
                key={feature.title}
                className="group relative overflow-hidden rounded-2xl border border-border/50 bg-card p-7 transition-all hover:border-primary/30 hover:shadow-lg hover:shadow-primary/5"
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08, duration: 0.5 }}
              >
                <div className={`absolute inset-0 -z-10 bg-gradient-to-br ${feature.gradient} opacity-0 transition-opacity group-hover:opacity-100`} />
                <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10">
                  <feature.icon className="h-5 w-5 text-primary" />
                </div>
                <h3 className="mb-2 text-lg font-semibold">
                  {feature.title}
                </h3>
                <p className="text-sm leading-relaxed text-muted-foreground">
                  {feature.desc}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </Section>

      {/* ═══════════ Modules ═══════════ */}
      <Section id="modules" className="px-6 py-24">
        <div className="mx-auto max-w-6xl">
          <div className="mb-16 text-center">
            <p className="mb-3 text-sm font-semibold uppercase tracking-widest text-chart-2">
              Verification Modules
            </p>
            <h2 className="mb-4 text-3xl font-bold tracking-tight md:text-4xl">
              Two modules. One platform.
            </h2>
            <p className="mx-auto max-w-2xl text-muted-foreground">
              Whether you manage private credit portfolios or need to prove
              AI-IP value, ZKValue has you covered.
            </p>
          </div>

          {/* Module 1: Private Credit */}
          <div className="mb-20 grid items-center gap-12 lg:grid-cols-2">
            <div>
              <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-chart-2/10 px-3 py-1 text-sm font-medium text-chart-2">
                <Shield className="h-3.5 w-3.5" />
                ZK Private Credit
              </div>
              <h3 className="mb-4 text-2xl font-bold">
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
                  "Covenant compliance checking (DSCR, leverage)",
                  "NAV attestation with proof certificate",
                  "Stress testing across macro scenarios",
                  "SEC Form PF & AIFMD regulatory reports",
                ].map((item) => (
                  <li key={item} className="flex items-center gap-3 text-sm">
                    <CheckCircle className="h-4 w-4 shrink-0 text-chart-2" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-2xl border border-border/50 bg-card p-8 shadow-sm">
              <div className="space-y-4 font-mono text-sm">
                <div className="text-muted-foreground">
                  {"// Upload encrypted loan tape"}
                </div>
                <div>
                  <span className="text-chart-4">POST</span>{" "}
                  <span className="text-primary">/api/v1/credit/verify</span>
                </div>
                <div className="rounded-xl bg-secondary/50 p-4 text-xs">
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
                <div className="rounded-xl bg-secondary/50 p-4 text-xs">
                  <pre className="text-chart-2">
{`{
  "status": "completed",
  "proof_hash": "0x7a3f...e91c",
  "nav_verified": true,
  "health_rating": 8,
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
              <div className="rounded-2xl border border-border/50 bg-card p-8 shadow-sm">
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
                      className="flex items-center justify-between rounded-xl bg-secondary/50 p-4 transition-colors hover:bg-secondary"
                    >
                      <div>
                        <div className="font-medium">
                          {asset.type}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {asset.method}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-semibold">
                          {asset.value}
                        </div>
                        <div className="text-xs text-chart-2">
                          {asset.confidence} confidence
                        </div>
                      </div>
                    </div>
                  ))}
                  <div className="flex items-center justify-between border-t border-border pt-3">
                    <span className="font-semibold">
                      Total AI-IP Value
                    </span>
                    <span className="text-lg font-bold bg-gradient-to-r from-primary to-chart-4 bg-clip-text text-transparent">
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
              <h3 className="mb-4 text-2xl font-bold">
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
                  "Sensitivity analysis (Bull/Base/Bear)",
                  "Executive reports with visualizations",
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
      </Section>

      {/* ═══════════ Pricing ═══════════ */}
      <Section id="pricing" className="border-t border-border/50 bg-secondary/30 px-6 py-24">
        <div className="mx-auto max-w-5xl">
          <div className="mb-14 text-center">
            <p className="mb-3 text-sm font-semibold uppercase tracking-widest text-primary">
              Plans
            </p>
            <h2 className="mb-4 text-3xl font-bold tracking-tight md:text-4xl">
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
            ].map((plan, i) => (
              <motion.div
                key={plan.name}
                className={`relative rounded-2xl border p-8 transition-shadow ${
                  plan.highlighted
                    ? "border-primary bg-card shadow-xl shadow-primary/10"
                    : "border-border/50 bg-card hover:shadow-md"
                }`}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1, duration: 0.5 }}
              >
                {plan.highlighted && (
                  <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 rounded-full bg-gradient-to-r from-primary to-chart-4 px-4 py-1 text-xs font-semibold text-white shadow-lg">
                    Most Popular
                  </div>
                )}
                <h3 className="text-lg font-semibold">
                  {plan.name}
                </h3>
                <div className="my-4">
                  <span className="text-4xl font-bold">
                    {plan.price}
                  </span>
                  <span className="text-muted-foreground">{plan.period}</span>
                </div>
                <p className="mb-6 text-sm text-muted-foreground">
                  {plan.desc}
                </p>
                <Link
                  href="/register"
                  className={`mb-6 block w-full rounded-xl py-2.5 text-center text-sm font-medium transition-all ${
                    plan.highlighted
                      ? "bg-primary text-white shadow-lg shadow-primary/25 hover:bg-primary/90"
                      : "border border-border bg-secondary hover:bg-secondary/80"
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
              </motion.div>
            ))}
          </div>
        </div>
      </Section>

      {/* ═══════════ Compliance ═══════════ */}
      <Section id="compliance" className="px-6 py-24">
        <div className="mx-auto max-w-4xl text-center">
          <p className="mb-3 text-sm font-semibold uppercase tracking-widest text-chart-2">
            Regulatory Compliance
          </p>
          <h2 className="mb-4 text-3xl font-bold tracking-tight md:text-4xl">
            Built for compliance from day one
          </h2>
          <p className="mx-auto mb-14 max-w-2xl text-muted-foreground">
            Every verification produces a cryptographic proof certificate and a
            complete audit trail. Ready for regulators, auditors, and LPs.
          </p>
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { label: "IAS 38", desc: "Intangible Asset Standard" },
              { label: "ASC 350", desc: "US GAAP Goodwill & Intangibles" },
              { label: "SEC Form PF", desc: "Private Fund Reporting" },
              { label: "AIFMD", desc: "EU Fund Manager Directive" },
            ].map((item, i) => (
              <motion.div
                key={item.label}
                className="rounded-2xl border border-border/50 bg-card p-6 transition-all hover:border-primary/30 hover:shadow-md"
                initial={{ opacity: 0, scale: 0.95 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08, duration: 0.4 }}
              >
                <div className="mb-2 text-2xl font-bold bg-gradient-to-r from-primary to-chart-2 bg-clip-text text-transparent">
                  {item.label}
                </div>
                <div className="text-sm text-muted-foreground">{item.desc}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </Section>

      {/* ═══════════ CTA ═══════════ */}
      <section className="relative overflow-hidden border-t border-border/50 px-6 py-20">
        <div className="absolute inset-0 -z-10 bg-gradient-to-br from-primary via-primary/90 to-chart-4/80" />
        <div className="absolute inset-0 -z-10 bg-grid-pattern text-white" />
        <div className="mx-auto max-w-3xl text-center">
          <h2 className="mb-4 text-3xl font-bold tracking-tight text-white md:text-4xl">
            Ready to prove your assets&apos; value?
          </h2>
          <p className="mb-8 text-lg text-white/70">
            Join leading funds and AI companies using cryptographic proofs for
            asset verification.
          </p>
          <Link
            href="/register"
            className="group inline-flex items-center gap-2 rounded-xl bg-white px-8 py-3.5 text-base font-semibold text-primary shadow-xl transition-all hover:bg-gray-50 hover:shadow-2xl"
          >
            Start Your Free Trial
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
          </Link>
        </div>
      </section>

      {/* ═══════════ Footer ═══════════ */}
      <footer className="border-t border-border/50 bg-card px-6 py-12">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-6 md:flex-row">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-primary/80">
              <Shield className="h-4 w-4 text-white" />
            </div>
            <span className="text-lg font-bold">ZKValue</span>
          </div>
          <div className="flex gap-8 text-sm text-muted-foreground">
            <a href="#" className="transition-colors hover:text-foreground">Privacy</a>
            <a href="#" className="transition-colors hover:text-foreground">Terms</a>
            <a href="#" className="transition-colors hover:text-foreground">Security</a>
            <a href="#" className="transition-colors hover:text-foreground">Docs</a>
          </div>
          <div className="text-sm text-muted-foreground">
            &copy; {new Date().getFullYear()} ZKValue. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}
