"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth";
import { AppSidebar } from "@/components/layout/sidebar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { isAuthenticated, fetchUser } = useAuthStore();

  useEffect(() => {
    const token = localStorage.getItem("zkvalue_token");
    if (!token) {
      router.push("/login");
      return;
    }
    if (!isAuthenticated) {
      fetchUser().catch(() => router.push("/login"));
    }
  }, [isAuthenticated, fetchUser, router]);

  return (
    <div className="flex h-screen overflow-hidden bg-secondary/30">
      <AppSidebar />
      <main className="flex-1 overflow-y-auto">{children}</main>
    </div>
  );
}
