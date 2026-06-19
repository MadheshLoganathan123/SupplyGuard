"use client";

import Image from "next/image";
import { useState, useEffect, useCallback } from "react";

const BACKEND_URL = (() => {
  const configured = (process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000/api/v1").replace(/\/+$/, "");
  return configured.endsWith("/api/v1") ? configured : `${configured}/api/v1`;
})();

interface Incident {
  id: string;
  title: string;
  date: string;
  desc: string;
  icon: string;
  iconColor: string;
  iconBg: string;
  tag: string;
  tagColor: string;
  tagBg: string;
  impact: string;
}

interface AgentPerf {
  agent_id: string;
  name: string;
  efficiency_pct: number;
  negotiation_speed_avg_sec: number;
  route_accuracy_pct: number;
  badge?: string;
}

interface ReportsMetrics {
  food_security_gaps_prevented: number;
  food_security_trend_pct: number;
  price_stability_variance_pct: number;
  tons_rerouted: number;
  reroute_capacity_pct: number;
  resilience_index: number;
  last_sync: string;
}

const severityIcon = (severity: string) => {
  switch (severity?.toUpperCase()) {
    case "HIGH": return { icon: "water_drop", iconColor: "text-error", iconBg: "bg-error/15", impact: "High" };
    case "MEDIUM": return { icon: "handshake", iconColor: "text-secondary", iconBg: "bg-secondary/15", impact: "Medium" };
    default: return { icon: "route", iconColor: "text-primary", iconBg: "bg-primary/15", impact: "Daily Optimization" };
  }
};

const formatDate = (iso: string) => {
  const d = new Date(iso);
  return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" }).toUpperCase();
};

const formatSync = (iso: string) => {
  const d = new Date(iso);
  return d.toLocaleString("en-GB", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit", timeZone: "UTC", timeZoneName: "short" }).toUpperCase();
};

const mapIncident = (raw: Record<string, string>): Incident => {
  const meta = severityIcon(raw.severity ?? "LOW");
  const status = raw.status ?? "OPEN";
  return {
    id: raw.id,
    title: `${raw.title}${status === "RESOLVED" ? "" : ""}`,
    date: formatDate(raw.occurred_at),
    desc: raw.description ?? "",
    icon: meta.icon,
    iconColor: meta.iconColor,
    iconBg: meta.iconBg,
    tag: raw.sector ? `Sector: ${raw.severity}` : `Severity: ${raw.severity}`,
    tagColor: status === "RESOLVED" ? "text-primary" : "text-on-surface-variant",
    tagBg: "bg-surface-container border border-outline-variant/30",
    impact: meta.impact,
  };
};

const badgeStyle = (badge?: string) => {
  if (badge === "Top Performer") return "bg-primary text-on-primary";
  if (badge === "Experimental") return "bg-error text-on-error";
  return "inline-block w-[52px] h-[8px] rounded-full bg-secondary/70";
};

export default function Reports() {
  const [exportOpen, setExportOpen] = useState(false);
  const [filterOpen, setFilterOpen] = useState(false);
  const [filterQuery, setFilterQuery] = useState("");
  const [heuristicOpen, setHeuristicOpen] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [negSpeed, setNegSpeed] = useState(60);
  const [routeAcc, setRouteAcc] = useState(80);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [agents, setAgents] = useState<AgentPerf[]>([]);
  const [metrics, setMetrics] = useState<ReportsMetrics | null>(null);

  const fetchReports = useCallback(async () => {
    try {
      const [incRes, metricsRes, perfRes, heurRes] = await Promise.all([
        fetch(`${BACKEND_URL}/incidents/?limit=50`),
        fetch(`${BACKEND_URL}/reports/metrics`),
        fetch(`${BACKEND_URL}/reports/agents/performance?limit=5`),
        fetch(`${BACKEND_URL}/heuristics/`),
      ]);

      if (incRes.ok) {
        const data = await incRes.json();
        if (Array.isArray(data)) setIncidents(data.map(mapIncident));
      }
      if (metricsRes.ok) setMetrics(await metricsRes.json());
      if (perfRes.ok) {
        const data = await perfRes.json();
        if (Array.isArray(data)) setAgents(data);
      }
      if (heurRes.ok) {
        const data = await heurRes.json();
        const active = Array.isArray(data) ? data[0] : null;
        if (active?.payload) {
          setNegSpeed(active.payload.negotiation_speed_bias ?? 60);
          setRouteAcc(active.payload.route_accuracy_bias ?? 80);
        }
      }
    } catch (err) {
      console.warn("Reports fetch failed:", err);
    }
  }, []);

  useEffect(() => {
    void Promise.resolve().then(() => {
      void fetchReports();
    });
  }, [fetchReports]);

  const handleExport = async (fmt: string) => {
    setExportOpen(false);
    const format = fmt.startsWith("PDF") ? "pdf" : fmt.startsWith("XLS") ? "xls" : "json";
    setToast(`Exporting Audit Report as ${format.toUpperCase()}…`);
    try {
      const res = await fetch(`${BACKEND_URL}/reports/export?format=${format}`, { method: "POST" });
      if (!res.ok) throw new Error("Export failed");
      const { job_id } = await res.json();

      const poll = async (attempts = 0): Promise<void> => {
        if (attempts > 20) throw new Error("Export timed out");
        const statusRes = await fetch(`${BACKEND_URL}/reports/export/${job_id}`);
        if (!statusRes.ok) throw new Error("Export status failed");
        const status = await statusRes.json();
        if (status.status === "done") {
          if (format === "json" && status.download) {
            const blob = new Blob([JSON.stringify(status.download, null, 2)], { type: "application/json" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `supplyguard-audit-${Date.now()}.json`;
            a.click();
            URL.revokeObjectURL(url);
          }
          setToast(`Report downloaded in ${format.toUpperCase()} format.`);
          return;
        }
        await new Promise((r) => setTimeout(r, 500));
        return poll(attempts + 1);
      };
      await poll();
    } catch (err) {
      console.warn("Export failed:", err);
      setToast("Export failed — backend may be offline.");
    }
  };

  const handleSaveHeuristics = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch(`${BACKEND_URL}/heuristics/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: "default_calibration",
          payload: { negotiation_speed_bias: negSpeed, route_accuracy_bias: routeAcc },
          active: true,
        }),
      });
      if (!res.ok) throw new Error("Save failed");
      setHeuristicOpen(false);
      setToast("Agent heuristics updated. Recalculating active path priorities.");
    } catch (err) {
      console.warn("Heuristics save failed:", err);
      setToast("Failed to save heuristics.");
    }
  };

  const filtered = incidents.filter(
    (inc) =>
      inc.title.toLowerCase().includes(filterQuery.toLowerCase()) ||
      inc.desc.toLowerCase().includes(filterQuery.toLowerCase())
  );

  const foodSecurity = metrics ? (metrics.food_security_gaps_prevented / 1000).toFixed(1) + "k" : "12.4k";
  const barHeights = [40, 55, 45, 65, 58, 80, 90, 100];

  return (
    <div className="pt-[88px] pb-4 flex-1 flex flex-col px-lg py-md gap-md overflow-y-auto h-full">

      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-md">
        <div>
          <h1 className="text-[26px] font-bold text-on-surface leading-tight tracking-tight">Reports & Strategic Analytics</h1>
          <p className="text-[12px] text-on-surface-variant mt-[3px]">Review agentic interventions and humanitarian impact trends.</p>
        </div>
        <div className="flex items-center gap-[8px] shrink-0 relative">
          <button
            onClick={() => setFilterOpen((p) => !p)}
            className="flex items-center gap-[6px] px-[14px] py-[8px] bg-surface-container border border-outline-variant/40 text-on-surface rounded-lg hover:border-primary/50 hover:text-primary transition-all font-mono text-[11px] font-bold uppercase tracking-wider"
          >
            <span className="material-symbols-outlined text-[16px]">filter_alt</span>
            Filter Data
          </button>

          <div className="relative">
            <button
              onClick={() => setExportOpen((p) => !p)}
              className="flex items-center gap-[6px] px-[14px] py-[8px] bg-secondary text-on-secondary font-bold rounded-lg hover:brightness-110 transition-all font-mono text-[11px] uppercase tracking-wider shadow-lg shadow-secondary/20"
            >
              <span className="material-symbols-outlined text-[16px]">picture_as_pdf</span>
              Export Audit Report
              <span className="material-symbols-outlined text-[16px]">expand_more</span>
            </button>
            {exportOpen && (
              <div className="absolute right-0 mt-[4px] w-52 glass-panel rounded-xl bg-surface-container/98 z-20 shadow-2xl overflow-hidden border border-outline-variant/20 animate-in fade-in duration-150">
                {["PDF (Gov)", "XLS (NGO)", "JSON (Raw)"].map((fmt) => (
                  <button
                    key={fmt}
                    onClick={() => handleExport(fmt)}
                    className="w-full text-left px-md py-[9px] hover:bg-primary/10 text-[13px] text-on-surface font-medium transition-colors"
                  >
                    {fmt}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {filterOpen && (
        <div className="flex items-center gap-sm">
          <input
            type="text"
            placeholder="Search incidents, agents…"
            value={filterQuery}
            onChange={(e) => setFilterQuery(e.target.value)}
            className="w-full max-w-sm bg-surface-container border border-outline-variant/30 rounded-lg py-[7px] px-[12px] text-[13px] focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/40 text-on-surface placeholder:text-on-surface-variant/50"
          />
        </div>
      )}

      {toast && (
        <div className="px-md py-[9px] rounded-lg bg-primary/10 border border-primary/30 text-[12px] text-primary flex justify-between items-center animate-in fade-in duration-300 font-mono">
          <span>{toast}</span>
          <button onClick={() => setToast(null)} className="font-bold ml-md hover:text-on-surface">DISMISS</button>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-md shrink-0">
        <div className="glass-panel p-md rounded-xl flex flex-col justify-between min-h-[220px]">
          <div>
            <span className="text-[9px] font-bold uppercase tracking-[0.2em] text-primary block font-mono">Strategic Mitigation</span>
            <h3 className="text-[18px] font-bold text-on-surface mt-[6px] leading-snug">Food Security Gaps Prevented</h3>
          </div>
          <div className="flex items-baseline gap-[10px] mt-sm">
            <span className="text-[40px] font-bold text-primary font-mono leading-none">{foodSecurity}</span>
            <span className="text-[12px] text-primary font-mono font-bold flex items-center gap-[4px]">
              <span className="material-symbols-outlined text-[14px]">trending_up</span>
              +{metrics?.food_security_trend_pct ?? 8.2}%
            </span>
          </div>
          <div className="flex items-end gap-[5px] h-[68px] mt-sm">
            {barHeights.map((h, i) => (
              <div
                key={i}
                className={`flex-1 rounded-t-sm transition-all ${i === 7 ? "bg-primary shadow-[0_0_8px_#4edea3]" : "bg-primary/25 hover:bg-primary/45"}`}
                style={{ height: `${h}%` }}
              />
            ))}
          </div>
        </div>

        <div className="glass-panel p-md rounded-xl flex flex-col justify-between min-h-[220px]">
          <div>
            <span className="text-[9px] font-bold uppercase tracking-[0.2em] text-tertiary block font-mono">Market Analysis</span>
            <h3 className="text-[18px] font-bold text-on-surface mt-[6px] leading-snug">Price Stability Variance</h3>
          </div>
          <div className="flex items-baseline gap-[10px] mt-sm">
            <span className="text-[40px] font-bold text-tertiary font-mono leading-none">±{metrics?.price_stability_variance_pct ?? 1.4}%</span>
            <span className="text-[12px] text-tertiary font-mono font-bold flex items-center gap-[4px]">
              <span className="material-symbols-outlined text-[14px]">verified</span>Stable
            </span>
          </div>
          <div className="relative flex items-center mt-sm h-[40px]">
            <div className="absolute w-full h-[1px] bg-outline-variant/25"></div>
            <div className="flex w-full justify-around items-center z-10">
              {[false, false, false, true].map((active, i) => (
                <div
                  key={i}
                  className={`rounded-full bg-tertiary transition-all ${active ? "w-[14px] h-[14px] shadow-[0_0_10px_rgba(255,178,183,0.8)]" : "w-[9px] h-[9px] opacity-40"}`}
                />
              ))}
            </div>
          </div>
        </div>

        <div className="glass-panel p-md rounded-xl flex flex-col justify-between min-h-[220px]">
          <div>
            <span className="text-[9px] font-bold uppercase tracking-[0.2em] text-secondary block font-mono">Logistics Volume</span>
            <h3 className="text-[18px] font-bold text-on-surface mt-[6px] leading-snug">Total Tons Re-routed</h3>
          </div>
          <div className="flex items-baseline gap-[10px] mt-sm">
            <span className="text-[40px] font-bold text-secondary font-mono leading-none">{metrics?.tons_rerouted?.toFixed(0) ?? 842}</span>
            <span className="text-[13px] text-on-surface-variant font-mono font-medium">Metric Tons</span>
          </div>
          <div className="mt-sm">
            <div className="w-full h-[6px] bg-surface-container-high rounded-full overflow-hidden">
              <div className="bg-secondary h-full rounded-full shadow-[0_0_6px_#ffb95f]" style={{ width: `${metrics?.reroute_capacity_pct ?? 74}%` }}></div>
            </div>
            <div className="flex justify-between mt-[6px] font-mono text-[10px]">
              <span className="text-on-surface-variant">Cap: 1,200t</span>
              <span className="text-secondary font-bold">{metrics?.reroute_capacity_pct?.toFixed(0) ?? 74}% Target</span>
            </div>
          </div>
        </div>
      </div>

      <div className="flex gap-md min-h-0 flex-1">
        <div className="flex-1 glass-panel rounded-xl p-md flex flex-col min-w-0 overflow-y-auto">
          <div className="flex justify-between items-center mb-md shrink-0">
            <h3 className="text-[18px] font-bold text-on-surface">Historical Incident Report</h3>
            <button className="text-[12px] text-primary font-bold font-mono hover:underline">View Full Archive</button>
          </div>

          <div className="space-y-md">
            {filtered.map((inc) => (
              <div
                key={inc.id}
                className="flex items-start gap-[12px] p-[12px] border border-outline-variant/20 rounded-lg hover:bg-surface-variant/15 transition-colors"
              >
                <div className={`w-[38px] h-[38px] rounded-lg ${inc.iconBg} flex items-center justify-center shrink-0`}>
                  <span className={`material-symbols-outlined text-[20px] ${inc.iconColor}`}>{inc.icon}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex justify-between items-start gap-sm mb-[3px]">
                    <h4 className="text-[13px] font-bold text-on-surface leading-snug">{inc.title}</h4>
                    <span className="text-[10px] font-mono text-on-surface-variant shrink-0 font-medium">{inc.date}</span>
                  </div>
                  <p className="text-[12px] text-on-surface-variant leading-relaxed mb-[8px]">{inc.desc}</p>
                  <div className="flex flex-wrap gap-[6px] font-mono text-[10px] font-bold">
                    <span className={`px-[8px] py-[3px] rounded ${inc.tagBg} ${inc.tagColor}`}>{inc.tag}</span>
                    <span className="px-[8px] py-[3px] rounded bg-surface-container border border-outline-variant/30 text-on-surface-variant">
                      Impact: {inc.impact}
                    </span>
                  </div>
                </div>
              </div>
            ))}
            {filtered.length === 0 && (
              <p className="text-[12px] text-on-surface-variant/70 italic text-center py-lg">No incidents matched your filter.</p>
            )}
          </div>
        </div>

        <div className="w-[300px] shrink-0 glass-panel rounded-xl p-md flex flex-col overflow-y-auto">
          <h3 className="text-[18px] font-bold text-on-surface mb-md shrink-0">Agent Performance Log</h3>

          <div className="space-y-[20px] flex-1">
            {agents.map((agent) => (
              <div key={agent.agent_id}>
                <div className="flex justify-between items-center mb-[8px]">
                  <div className="flex items-center gap-[8px]">
                    <span className="text-[13px] font-bold text-on-surface">{agent.name}</span>
                    {agent.badge && (
                      typeof badgeStyle(agent.badge) === "string" && agent.badge !== "Stable" ? (
                        <span className={`text-[9px] px-[7px] py-[2px] rounded font-mono font-bold tracking-wider uppercase ${badgeStyle(agent.badge)}`}>
                          {agent.badge}
                        </span>
                      ) : (
                        <span className={badgeStyle(agent.badge) as string}></span>
                      )
                    )}
                  </div>
                  <span className="font-mono text-[12px] font-bold text-primary">{agent.efficiency_pct}% Eff</span>
                </div>
                <div className="grid grid-cols-2 gap-[6px]">
                  <div className="bg-surface-container rounded-lg p-[10px] border border-outline-variant/20">
                    <p className="text-[10px] text-on-surface-variant">Negotiation Speed</p>
                    <p className="text-[12px] font-bold text-on-surface font-mono mt-[3px]">{agent.negotiation_speed_avg_sec}s avg</p>
                  </div>
                  <div className="bg-surface-container rounded-lg p-[10px] border border-outline-variant/20">
                    <p className="text-[10px] text-on-surface-variant">Route Opt.</p>
                    <p className="text-[12px] font-bold text-on-surface font-mono mt-[3px]">{agent.route_accuracy_pct}% Acc</p>
                  </div>
                </div>
              </div>
            ))}
            {agents.length === 0 && (
              <p className="text-[12px] text-on-surface-variant/70 italic">No agent performance data available.</p>
            )}
          </div>

          <div className="pt-md border-t border-outline-variant/20 mt-md shrink-0">
            <button
              onClick={() => setHeuristicOpen(true)}
              className="w-full py-[10px] border border-primary/50 text-primary font-bold rounded-lg hover:bg-primary/10 transition-colors font-mono text-[10px] uppercase tracking-widest"
            >
              Configure Agent Heuristics
            </button>
          </div>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-md border-t border-outline-variant/20 pt-md shrink-0">
        <div className="flex items-center gap-[10px]">
          <div className="relative w-10 h-10 rounded-full overflow-hidden border border-primary/20 shrink-0">
            <Image fill className="object-cover" alt="Global index" src="/images/earth_network.jpg" sizes="100vw" />
          </div>
          <div>
            <h4 className="text-[12px] font-bold text-on-surface">Global Resilience Index</h4>
            <p className="text-[11px] text-primary font-semibold font-mono">
              System Health: Optimal ({metrics?.resilience_index?.toFixed(2) ?? "0.92"})
            </p>
          </div>
        </div>
        <div className="flex gap-md font-mono text-[10px] text-right">
          <div className="flex flex-col items-end">
            <span className="text-on-surface-variant uppercase font-semibold tracking-wide text-[9px]">Last Data Sync</span>
            <span className="text-on-surface font-bold mt-[2px]">
              {metrics?.last_sync ? formatSync(metrics.last_sync) : "—"}
            </span>
          </div>
          <div className="w-[1px] h-8 bg-outline-variant/30"></div>
          <div className="flex flex-col items-end">
            <span className="text-on-surface-variant uppercase font-semibold tracking-wide text-[9px]">Security Protocol</span>
            <span className="text-primary font-bold mt-[2px]">SHA-512 ACTIVE</span>
          </div>
        </div>
      </div>

      {heuristicOpen && (
        <div className="fixed inset-0 z-50 bg-[#0b1326]/70 backdrop-blur-sm flex items-center justify-center p-md animate-in fade-in duration-200">
          <div className="glass-panel w-full max-w-md bg-surface-container/98 p-lg rounded-xl shadow-2xl border-primary/20 animate-in zoom-in-95 duration-200">
            <div className="flex justify-between items-start mb-md">
              <div>
                <h3 className="text-[17px] font-bold text-primary flex items-center gap-sm">
                  <span className="material-symbols-outlined text-[20px]">tune</span>
                  Heuristic Tuning
                </h3>
                <p className="text-[12px] text-on-surface-variant mt-[3px]">Calibrate AI pathfinding decision weights.</p>
              </div>
              <button onClick={() => setHeuristicOpen(false)} className="text-on-surface-variant hover:text-on-surface transition-colors">
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>
            <form onSubmit={handleSaveHeuristics} className="space-y-lg">
              {[
                { label: "NEGOTIATION SPEED BIAS", val: negSpeed, set: setNegSpeed, hint: "Higher weight forces faster consensus but reduces route cost-effectiveness." },
                { label: "ROUTE ACCURACY BIAS", val: routeAcc, set: setRouteAcc, hint: "Higher weight forces threat-free paths but increases search latency." },
              ].map(({ label, val, set, hint }) => (
                <div key={label} className="space-y-[6px]">
                  <div className="flex justify-between font-mono text-[11px] font-bold text-on-surface-variant">
                    <span>{label}</span>
                    <span className="text-primary">{val}%</span>
                  </div>
                  <input
                    type="range" min="10" max="100"
                    value={val}
                    onChange={(e) => set(Number(e.target.value))}
                    className="w-full accent-primary h-1 bg-surface-variant rounded-full outline-none"
                  />
                  <p className="text-[10px] text-on-surface-variant/70 leading-snug">{hint}</p>
                </div>
              ))}
              <button
                type="submit"
                className="w-full mt-sm bg-primary text-on-primary py-[10px] rounded-lg font-bold hover:brightness-110 transition-all flex justify-center items-center gap-xs font-mono text-[11px] uppercase tracking-widest shadow-lg shadow-primary/20"
              >
                <span className="material-symbols-outlined text-[18px]">save</span>
                Commit Calibration
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
