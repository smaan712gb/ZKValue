"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Shield, Eye, EyeOff, Loader2, CheckCircle } from "lucide-react";
import { useAuthStore } from "@/stores/auth";
import { toast } from "sonner";

export default function RegisterPage() {
  const router = useRouter();
  const { register, isLoading } = useAuthStore();
  const [formData, setFormData] = useState({
    full_name: "",
    email: "",
    password: "",
    org_name: "",
  });
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.password.length < 8) {
      toast.error("Password must be at least 8 characters");
      return;
    }
    try {
      await register(formData);
      toast.success("Account created successfully!");
      router.push("/dashboard");
    } catch {
      toast.error("Registration failed. Please try again.");
    }
  };

  const updateField = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="flex min-h-screen">
      {/* Left Panel */}
      <div className="hidden w-1/2 flex-col justify-between bg-primary p-12 lg:flex">
        <div className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/20">
            <Shield className="h-5 w-5 text-white" />
          </div>
          <span className="text-xl font-bold text-white">ZKValue</span>
        </div>
        <div>
          <h2 className="mb-6 text-3xl font-bold text-white">
            Start verifying in minutes
          </h2>
          <ul className="space-y-4">
            {[
              "Upload loan tapes or connect cloud accounts",
              "AI classifies and values your assets automatically",
              "Receive cryptographic proof certificates",
              "Share verified reports with LPs, auditors, and investors",
            ].map((item) => (
              <li
                key={item}
                className="flex items-start gap-3 text-primary-foreground/80"
              >
                <CheckCircle className="mt-0.5 h-5 w-5 shrink-0 text-white/60" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="text-sm text-primary-foreground/50">
          &copy; {new Date().getFullYear()} ZKValue
        </div>
      </div>

      {/* Right Panel */}
      <div className="flex w-full items-center justify-center px-6 lg:w-1/2">
        <div className="w-full max-w-md">
          <div className="mb-8 lg:hidden">
            <div className="flex items-center gap-2">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary">
                <Shield className="h-5 w-5 text-white" />
              </div>
              <span className="text-xl font-bold text-foreground">ZKValue</span>
            </div>
          </div>

          <h1 className="mb-2 text-2xl font-bold text-foreground">
            Create your account
          </h1>
          <p className="mb-8 text-muted-foreground">
            Start your 14-day free trial. No credit card required.
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                htmlFor="org_name"
                className="mb-1.5 block text-sm font-medium text-foreground"
              >
                Organization Name
              </label>
              <input
                id="org_name"
                type="text"
                value={formData.org_name}
                onChange={(e) => updateField("org_name", e.target.value)}
                placeholder="Acme Capital Partners"
                required
                className="w-full rounded-lg border bg-white px-4 py-2.5 text-sm outline-none transition-colors placeholder:text-muted-foreground focus:border-primary focus:ring-2 focus:ring-primary/20"
              />
            </div>

            <div>
              <label
                htmlFor="full_name"
                className="mb-1.5 block text-sm font-medium text-foreground"
              >
                Full Name
              </label>
              <input
                id="full_name"
                type="text"
                value={formData.full_name}
                onChange={(e) => updateField("full_name", e.target.value)}
                placeholder="Jane Smith"
                required
                className="w-full rounded-lg border bg-white px-4 py-2.5 text-sm outline-none transition-colors placeholder:text-muted-foreground focus:border-primary focus:ring-2 focus:ring-primary/20"
              />
            </div>

            <div>
              <label
                htmlFor="email"
                className="mb-1.5 block text-sm font-medium text-foreground"
              >
                Work Email
              </label>
              <input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => updateField("email", e.target.value)}
                placeholder="jane@acmecapital.com"
                required
                className="w-full rounded-lg border bg-white px-4 py-2.5 text-sm outline-none transition-colors placeholder:text-muted-foreground focus:border-primary focus:ring-2 focus:ring-primary/20"
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="mb-1.5 block text-sm font-medium text-foreground"
              >
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={formData.password}
                  onChange={(e) => updateField("password", e.target.value)}
                  placeholder="Min. 8 characters"
                  required
                  minLength={8}
                  className="w-full rounded-lg border bg-white px-4 py-2.5 pr-10 text-sm outline-none transition-colors placeholder:text-muted-foreground focus:border-primary focus:ring-2 focus:ring-primary/20"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary py-2.5 text-sm font-semibold text-white transition-colors hover:bg-primary/90 disabled:opacity-50"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Creating account...
                </>
              ) : (
                "Create Account"
              )}
            </button>

            <p className="text-center text-xs text-muted-foreground">
              By creating an account, you agree to our{" "}
              <a href="#" className="text-primary hover:underline">
                Terms of Service
              </a>{" "}
              and{" "}
              <a href="#" className="text-primary hover:underline">
                Privacy Policy
              </a>
            </p>
          </form>

          <p className="mt-6 text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link
              href="/login"
              className="font-medium text-primary hover:text-primary/80"
            >
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
