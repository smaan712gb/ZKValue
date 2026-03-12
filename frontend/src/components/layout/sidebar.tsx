"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Shield,
  LayoutDashboard,
  FileCheck,
  Landmark,
  Brain,
  Settings,
  CreditCard,
  ScrollText,
  LogOut,
  ChevronLeft,
  Users,
  CalendarClock,
  BarChart3,
  FileText,
  Activity,
  MessageSquare,
  Link2,
  Database,
  FileBarChart,
} from "lucide-react";
import { useAuthStore } from "@/stores/auth";
import { useState } from "react";

const navigation = [
  {
    name: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    name: "Verifications",
    href: "/dashboard/verifications",
    icon: FileCheck,
  },
  {
    name: "Private Credit",
    href: "/dashboard/credit",
    icon: Landmark,
  },
  {
    name: "AI-IP Valuation",
    href: "/dashboard/ai-ip",
    icon: Brain,
  },
  {
    name: "Document AI",
    href: "/dashboard/document-ai",
    icon: FileText,
  },
  { type: "separator" as const },
  {
    name: "Stress Testing",
    href: "/dashboard/stress-testing",
    icon: Activity,
  },
  {
    name: "NL Query",
    href: "/dashboard/nl-query",
    icon: MessageSquare,
  },
  {
    name: "Regulatory",
    href: "/dashboard/regulatory",
    icon: FileBarChart,
  },
  {
    name: "Blockchain",
    href: "/dashboard/blockchain",
    icon: Link2,
  },
  {
    name: "Model Registry",
    href: "/dashboard/model-registry",
    icon: Database,
  },
  { type: "separator" as const },
  {
    name: "Schedules",
    href: "/dashboard/schedules",
    icon: CalendarClock,
  },
  {
    name: "Analytics",
    href: "/dashboard/analytics",
    icon: BarChart3,
  },
  {
    name: "Audit Log",
    href: "/dashboard/audit",
    icon: ScrollText,
  },
  {
    name: "Team",
    href: "/dashboard/settings?tab=team",
    icon: Users,
  },
  {
    name: "Billing",
    href: "/dashboard/billing",
    icon: CreditCard,
  },
  {
    name: "Settings",
    href: "/dashboard/settings",
    icon: Settings,
  },
];

export function AppSidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuthStore();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={`flex h-screen flex-col border-r bg-sidebar-background transition-all duration-300 ${
        collapsed ? "w-[68px]" : "w-[260px]"
      }`}
    >
      {/* Logo */}
      <div className="flex h-16 items-center justify-between border-b px-4">
        <Link href="/dashboard" className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary">
            <Shield className="h-4 w-4 text-white" />
          </div>
          {!collapsed && (
            <span className="text-lg font-bold tracking-tight text-foreground">
              ZKValue
            </span>
          )}
        </Link>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-sidebar-accent hover:text-foreground"
        >
          <ChevronLeft
            className={`h-4 w-4 transition-transform ${
              collapsed ? "rotate-180" : ""
            }`}
          />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-4">
        <ul className="space-y-1">
          {navigation.map((item, i) => {
            if ("type" in item && item.type === "separator") {
              return (
                <li key={`sep-${i}`} className="my-3 border-t border-sidebar-border" />
              );
            }
            const navItem = item as { name: string; href: string; icon: typeof LayoutDashboard };
            const isActive =
              pathname === navItem.href ||
              (navItem.href !== "/dashboard" && pathname.startsWith(navItem.href.split("?")[0]));

            return (
              <li key={navItem.name}>
                <Link
                  href={navItem.href}
                  className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-sidebar-primary/10 text-sidebar-primary"
                      : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                  }`}
                  title={collapsed ? navItem.name : undefined}
                >
                  <navItem.icon className="h-4.5 w-4.5 shrink-0" />
                  {!collapsed && <span>{navItem.name}</span>}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* User Section */}
      <div className="border-t p-3">
        <div
          className={`flex items-center gap-3 rounded-lg px-3 py-2 ${
            collapsed ? "justify-center" : ""
          }`}
        >
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
            {user?.full_name
              ?.split(" ")
              .map((n) => n[0])
              .join("")
              .toUpperCase() || "U"}
          </div>
          {!collapsed && (
            <div className="flex-1 overflow-hidden">
              <div className="truncate text-sm font-medium text-foreground">
                {user?.full_name}
              </div>
              <div className="truncate text-xs text-muted-foreground">
                {user?.organization?.name}
              </div>
            </div>
          )}
          {!collapsed && (
            <button
              onClick={logout}
              className="text-muted-foreground transition-colors hover:text-destructive"
              title="Sign out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
    </aside>
  );
}
