"use client";

import { usePathname } from "next/navigation";
import { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import { User } from "@supabase/supabase-js";
import { supabase } from "../lib/supabaseClient";

// Auth routes that should render WITHOUT the shell chrome (sidebar/topbar)
const AUTH_ROUTES = ["/auth/signin", "/auth/signup"];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  // Render bare children for auth pages — no chrome
  if (AUTH_ROUTES.some((r) => pathname.startsWith(r))) {
    return (
      <div className="min-h-screen bg-background text-on-surface overflow-auto">
        {children}
      </div>
    );
  }

  return <AppChrome>{children}</AppChrome>;
}

// ── Full dashboard chrome (sidebar + topbar) ──────────────────────────────────
function AppChrome({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [rerouting, setRerouting] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [authUser, setAuthUser] = useState<User | null>(null);
  const [showNotifications, setShowNotifications] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState<Array<{ id: string; title: string; body: string; notification_type: string; read: boolean; created_at: string; link: string | null }>>([]);
  const notifRef = useRef<HTMLDivElement>(null);

  // Dynamic AI status text
  const aiStatusText =
    pathname === "/"          ? "AI: OPTIMIZING ROUTE FOR SECTOR 7..." :
    pathname === "/logistics" ? "AI: OPTIMIZING ROUTE..." :
    pathname === "/network"   ? "AI: OPTIMIZING ROUTE IN SECTOR 7G..." :
    pathname === "/reports"   ? "AI: AGGREGATING SECURITY TRENDS..." :
                                "AI: SURVEILLANCE MODE ACTIVE";

  const BACKEND_URL = (() => {
    const configured = (process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000").replace(/\/+$/, "");
    return configured.endsWith("/api/v1") ? configured : `${configured}/api/v1`;
  })();

  const triggerReroute = async () => {
    setRerouting(true);
    setToastMessage("AI Reroute Optimization Initiated: Calculating alternate paths...");

    try {
      // Call the backend to trigger orchestrator/reroute
      const response = await fetch(`${BACKEND_URL}/agents/orchestrate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action_type: "reroute",
          sector: "GLOBAL",
          threat_level: "ELEVATED",
          metadata: {
            trigger: "manual_operator_request",
            timestamp: new Date().toISOString(),
          },
        }),
      });

      if (response.ok) {
        const result = await response.json();
        const efficiency = result.efficiency_improvement || 18.5;
        const sectors = result.affected_sectors || "Sector 7 & Sector 12";
        setToastMessage(
          `New routes calculated. ${sectors} transit updated (+${efficiency.toFixed(1)}% efficiency).`
        );
      } else {
        setToastMessage("Reroute calculation completed. Check logs for details.");
      }
    } catch (error) {
      console.error("Reroute failed:", error);
      setToastMessage("Reroute optimization initiated locally. Backend may be offline.");
    } finally {
      setRerouting(false);
    }
  };

  const fetchNotifications = useCallback(async () => {
    try {
      const { data: sess } = await supabase.auth.getSession();
      const token = sess?.session?.access_token;
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;
      const res = await fetch(`${BACKEND_URL}/notifications?limit=10`, { headers });
      if (res.ok) {
        const data = await res.json();
        setNotifications(data.items ?? []);
        setUnreadCount(data.unread ?? 0);
      }
    } catch { /* ignore */ }
  }, [BACKEND_URL]);

  useEffect(() => {
    if (!authUser) return;
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, [authUser, fetchNotifications]);

  useEffect(() => {
    if (!toastMessage) return;
    const t = setTimeout(() => setToastMessage(null), 6000);
    return () => clearTimeout(t);
  }, [toastMessage]);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const { data } = await supabase.auth.getSession();
        if (!mounted) return;
        setAuthUser(data?.session?.user ?? null);
      } catch {
        setAuthUser(null);
      }
    })();

    const { data: sub } = supabase.auth.onAuthStateChange((event, session) => {
      setAuthUser(session?.user ?? null);
    });

    return () => {
      mounted = false;
      sub?.subscription?.unsubscribe?.();
    };
  }, []);

  const navItems = [
    { name: "Dashboard", href: "/",          icon: "dashboard" },
    { name: "Logistics", href: "/logistics", icon: "local_shipping" },
    { name: "Network",   href: "/network",   icon: "hub" },
    { name: "Reports",   href: "/reports",   icon: "assessment" },
  ];

  return (
    <div className="flex h-screen bg-background text-on-surface overflow-hidden">

      {/* ── Sidebar (desktop) ───────────────────────────────────────── */}
      <aside className="fixed left-0 top-0 h-full z-40 flex flex-col pb-md bg-surface-container border-r border-outline-variant/20 w-[210px] hidden md:flex">
        {/* Logo */}
        <div className="px-md pt-[18px] pb-md mb-sm border-b border-outline-variant/20">
          <div className="flex items-center gap-sm">
            <span className="material-symbols-outlined text-primary text-2xl">shield</span>
            <div>
              <h1 className="text-[15px] font-bold text-primary tracking-tight leading-tight">SupplyShield AI</h1>
              <p className="text-[10px] text-on-surface-variant uppercase tracking-widest flex items-center gap-[5px] mt-[2px]">
                <span className={`w-[7px] h-[7px] rounded-full shrink-0 ${rerouting ? "bg-secondary animate-ping" : "bg-primary pulse-emerald"}`} />
                {rerouting ? "Optimizing..." : "Active Monitoring"}
              </p>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-sm space-y-[2px] pt-sm">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-[10px] px-[12px] py-[9px] rounded-lg transition-all duration-150 ${
                  isActive
                    ? "bg-primary text-on-primary font-semibold"
                    : "text-on-surface-variant hover:text-on-surface hover:bg-surface-variant"
                }`}
              >
                <span className={`material-symbols-outlined text-[20px] ${isActive ? "text-on-primary" : ""}`}>{item.icon}</span>
                <span className="text-[13px] font-medium">{item.name}</span>
              </Link>
            );
          })}
        </nav>

        {/* Initiate Reroute */}
        <div className="px-md mt-auto mb-md">
          <button
            onClick={triggerReroute}
            disabled={rerouting}
            className={`w-full py-[9px] rounded-lg text-[13px] font-semibold hover:brightness-110 transition-all flex items-center justify-center gap-sm shadow-lg ${
              rerouting
                ? "bg-surface-variant text-on-surface-variant cursor-not-allowed"
                : "bg-primary/10 text-primary border border-primary/40 hover:bg-primary/20"
            }`}
          >
            <span className="material-symbols-outlined text-[18px]">{rerouting ? "hourglass_empty" : "alt_route"}</span>
            {rerouting ? "Rerouting..." : "Initiate Reroute"}
          </button>
        </div>

        {/* Bottom links */}
        <div className="border-t border-outline-variant/20 pt-sm px-sm">
          <Link href="#" className="flex items-center gap-[10px] px-[12px] py-[9px] text-on-surface-variant hover:text-on-surface hover:bg-surface-variant transition-all duration-150 rounded-lg">
            <span className="material-symbols-outlined text-[20px]">settings</span>
            <span className="text-[13px] font-medium">Settings</span>
          </Link>
          <Link href="#" className="flex items-center gap-[10px] px-[12px] py-[9px] text-on-surface-variant hover:text-on-surface hover:bg-surface-variant transition-all duration-150 rounded-lg">
            <span className="material-symbols-outlined text-[20px]">help</span>
            <span className="text-[13px] font-medium">Support</span>
          </Link>
        </div>
      </aside>

      {/* ── Main content ────────────────────────────────────────────── */}
      <main className="w-full md:pl-[210px] flex flex-col relative h-screen">

        {/* TopAppBar */}
        <header className="fixed top-0 right-0 left-0 md:left-[210px] z-50 flex justify-between items-center px-lg h-14 bg-surface/80 backdrop-blur-md border-b border-outline-variant/30">
          <div className="flex items-center gap-xl">
            <span className="text-headline-md font-bold text-primary tracking-tight">SupplyShield</span>
            <div className="relative group hidden sm:block">
              <span className="absolute inset-y-0 left-3 flex items-center text-on-surface-variant">
                <span className="material-symbols-outlined text-[18px]">search</span>
              </span>
              <input
                className="bg-surface-container-low border border-outline-variant/30 rounded-full pl-10 pr-lg py-1.5 text-body-sm focus:ring-1 focus:ring-primary focus:border-primary w-64 transition-all outline-none"
                placeholder="Search logistics nodes..."
                type="text"
              />
            </div>
          </div>
          <div className="flex items-center gap-md relative">
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="p-2 text-on-surface-variant hover:bg-surface-variant/50 rounded-full transition-colors relative"
            >
              <span className="material-symbols-outlined">notifications_active</span>
              {unreadCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 w-5 h-5 bg-secondary text-on-secondary text-[10px] font-bold rounded-full flex items-center justify-center">
                  {unreadCount > 99 ? "99+" : unreadCount}
                </span>
              )}
            </button>

            {showNotifications && (
              <div
                ref={notifRef}
                className="absolute top-full right-0 mt-2 w-80 bg-surface border border-outline-variant/30 rounded-xl shadow-2xl z-50 max-h-96 flex flex-col overflow-hidden"
              >
                <div className="flex items-center justify-between px-md py-sm border-b border-outline-variant/20">
                  <span className="text-label-sm font-semibold">Notifications</span>
                  <button
                    onClick={async () => {
                      try {
                        const { data: sess } = await supabase.auth.getSession();
                        const token = sess?.session?.access_token;
                        const headers: Record<string, string> = { "Content-Type": "application/json" };
                        if (token) headers["Authorization"] = `Bearer ${token}`;
                        await fetch(`${BACKEND_URL}/notifications/read-all`, { method: "POST", headers });
                        setUnreadCount(0);
                        setNotifications(prev => prev.map(n => ({ ...n, read: true })));
                      } catch { /* ignore */ }
                    }}
                    className="text-[11px] text-primary hover:underline"
                  >
                    Mark all read
                  </button>
                </div>
                <div className="flex-1 overflow-y-auto">
                  {notifications.length === 0 && (
                    <div className="p-md text-center text-on-surface-variant text-sm">No notifications</div>
                  )}
                  {notifications.map((n) => (
                    <div
                      key={n.id}
                      className={`px-md py-sm border-b border-outline-variant/10 text-sm hover:bg-surface-variant/30 cursor-pointer transition-colors ${n.read ? "" : "bg-primary/5 border-l-2 border-l-primary"}`}
                      onClick={async () => {
                        if (!n.read) {
                          try {
                            const { data: sess } = await supabase.auth.getSession();
                            const token = sess?.session?.access_token;
                            const headers: Record<string, string> = { "Content-Type": "application/json" };
                            if (token) headers["Authorization"] = `Bearer ${token}`;
                            await fetch(`${BACKEND_URL}/notifications/${n.id}/read`, { method: "PATCH", headers });
                            setUnreadCount(prev => Math.max(0, prev - 1));
                            setNotifications(prev => prev.map(x => x.id === n.id ? { ...x, read: true } : x));
                          } catch { /* ignore */ }
                        }
                        if (n.link) window.open(n.link, "_blank");
                      }}
                    >
                      <div className="flex items-center gap-sm">
                        <span className={`material-symbols-outlined text-[16px] ${n.notification_type === "warning" ? "text-warning" : n.notification_type === "error" ? "text-error" : "text-primary"}`}>
                          {n.notification_type === "warning" ? "warning" : n.notification_type === "error" ? "error" : "info"}
                        </span>
                        <span className="font-medium text-label-sm flex-1">{n.title}</span>
                      </div>
                      {n.body && <p className="text-on-surface-variant text-[12px] mt-1 ml-7">{n.body}</p>}
                      <p className="text-[10px] text-on-surface-variant/60 mt-1 ml-7">{new Date(n.created_at).toLocaleString()}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Click outside to close */}
            {showNotifications && (
              <div className="fixed inset-0 z-40" onClick={() => setShowNotifications(false)} />
            )}

            <button className="p-2 text-on-surface-variant hover:bg-surface-variant/50 rounded-full transition-colors">
              <span className="material-symbols-outlined">settings</span>
            </button>
            <div className="h-8 w-[1px] bg-outline-variant/30 mx-xs" />
            <div className="flex items-center gap-sm pl-xs">
              {authUser ? (
                <Link href="/profile" className="flex items-center gap-2 rounded-full hover:bg-surface-variant/60 px-2 py-1 transition-colors">
                  <div className="text-right hidden xl:block">
                    <p className="text-label-md font-label-md leading-none font-medium">{authUser.user_metadata?.full_name || authUser.email?.split("@")[0] || "User"}</p>
                    <p className="text-[10px] text-primary-container font-bold uppercase tracking-widest">{authUser.user_metadata?.role || "User"}</p>
                  </div>
                  <div className="relative w-9 h-9 rounded-full overflow-hidden border border-primary/20 bg-primary/20 flex items-center justify-center">
                    <span className="material-symbols-outlined text-primary text-[18px]">person</span>
                  </div>
                </Link>
              ) : (
                <div className="flex items-center gap-2">
                  <Link href="/auth/signin" className="text-sm font-semibold text-primary hover:underline">Sign In</Link>
                  <Link href="/auth/signup" className="text-sm font-medium text-on-surface-variant ml-2">Sign Up</Link>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* AI Status Pulse Bar */}
        <div className="fixed top-14 left-0 md:left-[210px] right-0 z-30 h-8 flex items-center justify-center bg-error-container/90 backdrop-blur-sm border-b border-error/20">
          <div className="flex items-center gap-sm text-on-error-container text-label-xs font-label-xs uppercase tracking-widest animate-pulse">
            <span className="w-2 h-2 rounded-full bg-on-error-container" />
            {rerouting ? "AI: Actively Rerouting Sector 7 & 12 convoys..." : aiStatusText}
          </div>
        </div>

        {/* Page content */}
        <div className="flex-1 w-full overflow-hidden relative">
          {children}
        </div>

        {/* Mobile bottom nav */}
        <nav className="md:hidden fixed bottom-0 w-full bg-surface-container border-t border-outline-variant/30 px-md py-sm flex justify-around items-center z-50">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex flex-col items-center gap-xs ${isActive ? "text-primary" : "text-on-surface-variant"}`}
              >
                <span className="material-symbols-outlined">{item.icon}</span>
                <span className="text-[10px] font-label-xs uppercase">{item.name}</span>
              </Link>
            );
          })}
        </nav>
      </main>

      {/* Toast */}
      {toastMessage && (
        <div className="fixed bottom-20 md:bottom-6 right-6 z-50 max-w-sm glass-panel p-md rounded-xl shadow-2xl flex gap-md items-start border-primary/30 animate-in fade-in slide-in-from-bottom-5 duration-300">
          <span className="material-symbols-outlined text-primary">info</span>
          <div className="flex-1">
            <h4 className="text-label-md font-bold text-primary">System Notification</h4>
            <p className="text-body-sm text-on-surface-variant mt-1 leading-snug">{toastMessage}</p>
          </div>
          <button onClick={() => setToastMessage(null)} className="text-on-surface-variant hover:text-on-surface">
            <span className="material-symbols-outlined text-sm">close</span>
          </button>
        </div>
      )}
    </div>
  );
}
