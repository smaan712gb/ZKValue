"use client";

import { useAuthStore } from "@/stores/auth";
import api from "@/lib/api";
import { toast } from "sonner";
import { Bell, Search } from "lucide-react";
import { useState, useEffect, useRef, useCallback } from "react";
import { ThemeToggle } from "@/components/shared/theme-toggle";

interface Notification {
  id: string;
  title: string;
  message: string;
  read: boolean;
  created_at: string;
}

interface HeaderProps {
  title: string;
  description?: string;
  actions?: React.ReactNode;
}

export function Header({ title, description, actions }: HeaderProps) {
  const { user } = useAuthStore();
  const [searchOpen, setSearchOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const fetchUnreadCount = useCallback(async () => {
    try {
      const res = await api.get("/notifications/unread");
      setUnreadCount(res.data.count ?? 0);
      setNotifications(res.data.notifications?.slice(0, 5) ?? []);
    } catch {
      // silently ignore
    }
  }, []);

  useEffect(() => {
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 30000);
    return () => clearInterval(interval);
  }, [fetchUnreadCount]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleMarkAllRead = async () => {
    try {
      await api.post("/notifications/read-all");
      setUnreadCount(0);
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
      toast.success("All notifications marked as read");
    } catch {
      toast.error("Failed to mark notifications as read");
    }
  };

  return (
    <header className="flex h-16 items-center justify-between border-b bg-card px-6">
      <div>
        <h1 className="text-lg font-semibold text-foreground">{title}</h1>
        {description && (
          <p className="text-sm text-muted-foreground">{description}</p>
        )}
      </div>

      <div className="flex items-center gap-3">
        {actions}

        {/* Search */}
        <div className="relative">
          {searchOpen ? (
            <input
              autoFocus
              type="text"
              placeholder="Search verifications..."
              className="w-64 rounded-lg border bg-card px-4 py-1.5 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
              onBlur={() => setSearchOpen(false)}
            />
          ) : (
            <button
              onClick={() => setSearchOpen(true)}
              className="flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
            >
              <Search className="h-4 w-4" />
            </button>
          )}
        </div>

        {/* Notifications */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="relative flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
          >
            <Bell className="h-4 w-4" />
            {unreadCount > 0 && (
              <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-[16px] items-center justify-center rounded-full bg-destructive px-1 text-[10px] font-medium text-white">
                {unreadCount > 99 ? "99+" : unreadCount}
              </span>
            )}
          </button>

          {dropdownOpen && (
            <div className="absolute right-0 top-full z-50 mt-2 w-80 rounded-lg border bg-card shadow-lg">
              <div className="flex items-center justify-between border-b px-4 py-3">
                <span className="text-sm font-semibold text-foreground">Notifications</span>
                {unreadCount > 0 && (
                  <button
                    onClick={handleMarkAllRead}
                    className="text-xs font-medium text-primary hover:underline"
                  >
                    Mark all read
                  </button>
                )}
              </div>
              <ul className="max-h-80 overflow-y-auto">
                {notifications.length === 0 ? (
                  <li className="px-4 py-6 text-center text-sm text-muted-foreground">
                    No notifications
                  </li>
                ) : (
                  notifications.map((n) => (
                    <li
                      key={n.id}
                      className={`border-b px-4 py-3 last:border-b-0 ${
                        !n.read ? "bg-primary/5" : ""
                      }`}
                    >
                      <p className="text-sm font-medium text-foreground">{n.title}</p>
                      <p className="mt-0.5 text-xs text-muted-foreground line-clamp-2">
                        {n.message}
                      </p>
                    </li>
                  ))
                )}
              </ul>
            </div>
          )}
        </div>

        {/* Theme Toggle */}
        <ThemeToggle />

        {/* User avatar */}
        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
          {user?.full_name
            ?.split(" ")
            .map((n) => n[0])
            .join("")
            .toUpperCase() || "U"}
        </div>
      </div>
    </header>
  );
}
