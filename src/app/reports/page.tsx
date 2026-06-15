"use client";

import Image from "next/image";
import { useState } from "react";

interface Incident {
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

const incidents: Incident[] = [
  {
    title: "Sector 7 Flash Flood - Resolved",
    date: "24 OCT 2023",
    desc: "AI Agent detected rising water levels 4 hours before crest. Automated rerouting of 14 grain convoys saved $2.1M in spoilage.",
    icon: "water_drop",
    iconColor: "text-error",
    iconBg: "bg-error/15",
    tag: "Saved: 14 Convoys",
    tagColor: "text-primary",
    tagBg: "bg-surface-container border border-outline-variant/30",
    impact: "High",
  },
  {
    title: "Local Labor Strike - Mitigated",
    date: "18 OCT 2023",
    desc: "Negotiation agent initiated fair-market rate adjustments for carrier sub-contractors, avoiding a 48-hour port shutdown.",
    icon: "handshake",
    iconColor: "text-secondary",
    iconBg: "bg-secondary/15",
    tag: "Negotiation Level: L3",
    tagColor: "text-on-surface-variant",
    tagBg: "bg-surface-container border border-outline-variant/30",
    impact: "Medium",
  },
  {
    title: "Border Congestion Peak",
    date: "12 OCT 2023",
    desc: "Dynamic multi-point routing bypassed Grade A checkpoint, reducing border dwell time by 12% across 400+ shipments.",
    icon: "route",
    iconColor: "text-primary",
    iconBg: "bg-primary/15",
    tag: "Efficiency: +12%",
    tagColor: "text-primary",
    tagBg: "bg-surface-container border border-outline-variant/30",
    impact: "Daily Optimization",
  },
];

export default function Reports() {
  const [exportOpen, setExportOpen] = useState(false);
  const [filterOpen, setFilterOpen] = useState(false);
  const [filterQuery, setFilterQuery] = useState("");
  const [heuristicOpen, setHeuristicOpen] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [negSpeed, setNegSpeed] = useState(60);
  const [routeAcc, setRouteAcc] = useState(80);

  const handleExport = (fmt: string) => {
    setExportOpen(false);
    setToast(`Exporting Audit Report as ${fmt}…`);
    setTimeout(() => setToast(`Report downloaded in ${fmt} format.`), 2000);
  };

  const handleSaveHeuristics = (e: React.FormEvent) => {
    e.preventDefault();
    setHeuristicOpen(false);
    setToast("Agent heuristics updated. Recalculating active path priorities.");
  };

  const filtered = incidents.filter(
    (inc) =>
      inc.title.toLowerCase().includes(filterQuery.toLowerCase()) ||
      inc.desc.toLowerCase().includes(filterQuery.toLowerCase())
  );

  return (
    <div className="pt-[88px] pb-4 flex-1 flex flex-col px-lg py-md gap-md overflow-y-auto h-full">

      {/* ── Page Header ── */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-md">
        <div>
          <h1 className="text-[26px] font-bold text-on-surface leading-tight tracking-tight">Reports & Strategic Analytics</h1>
          <p className="text-[12px] text-on-surface-variant mt-[3px]">Review agentic interventions and humanitarian impact trends.</p>
        </div>
        <div className="flex items-center gap-[8px] shrink-0 relative">
          {/* Filter Data */}
          <button
            onClick={() => setFilterOpen((p) => !p)}
            className="flex items-center gap-[6px] px-[14px] py-[8px] bg-surface-container border border-outline-variant/40 text-on-surface rounded-lg hover:border-primary/50 hover:text-primary transition-all font-mono text-[11px] font-bold uppercase tracking-wider"
          >
            <span className="material-symbols-outlined text-[16px]">filter_alt</span>
            Filter Data
          </button>

          {/* Export Audit Report */}
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

      {/* Filter bar */}
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

      {/* Toast */}
      {toast && (
        <div className="px-md py-[9px] rounded-lg bg-primary/10 border border-primary/30 text-[12px] text-primary flex justify-between items-center animate-in fade-in duration-300 font-mono">
          <span>{toast}</span>
          <button onClick={() => setToast(null)} className="font-bold ml-md hover:text-on-surface">DISMISS</button>
        </div>
      )}

      {/* ── Bento Metric Cards ── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-md shrink-0">

        {/* Card 1 — Food Security Gaps Prevented */}
        <div className="glass-panel p-md rounded-xl flex flex-col justify-between min-h-[220px]">
          <div>
            <span className="text-[9px] font-bold uppercase tracking-[0.2em] text-primary block font-mono">Strategic Mitigation</span>
            <h3 className="text-[18px] font-bold text-on-surface mt-[6px] leading-snug">Food Security Gaps Prevented</h3>
          </div>
          <div className="flex items-baseline gap-[10px] mt-sm">
            <span className="text-[40px] font-bold text-primary font-mono leading-none">12.4k</span>
            <span className="text-[12px] text-primary font-mono font-bold flex items-center gap-[4px]">
              <span className="material-symbols-outlined text-[14px]">trending_up</span>+8.2%
            </span>
          </div>
          {/* Bar chart */}
          <div className="flex items-end gap-[5px] h-[68px] mt-sm">
            {[40, 55, 45, 65, 58, 80, 90, 100].map((h, i) => (
              <div
                key={i}
                className={`flex-1 rounded-t-sm transition-all ${i === 7 ? "bg-primary shadow-[0_0_8px_#4edea3]" : "bg-primary/25 hover:bg-primary/45"}`}
                style={{ height: `${h}%` }}
              />
            ))}
          </div>
        </div>

        {/* Card 2 — Price Stability Variance */}
        <div className="glass-panel p-md rounded-xl flex flex-col justify-between min-h-[220px]">
          <div>
            <span className="text-[9px] font-bold uppercase tracking-[0.2em] text-tertiary block font-mono">Market Analysis</span>
            <h3 className="text-[18px] font-bold text-on-surface mt-[6px] leading-snug">Price Stability Variance</h3>
          </div>
          <div className="flex items-baseline gap-[10px] mt-sm">
            <span className="text-[40px] font-bold text-tertiary font-mono leading-none">±1.4%</span>
            <span className="text-[12px] text-tertiary font-mono font-bold flex items-center gap-[4px]">
              <span className="material-symbols-outlined text-[14px]">verified</span>Stable
            </span>
          </div>
          {/* Dot indicator row */}
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

        {/* Card 3 — Total Tons Re-routed */}
        <div className="glass-panel p-md rounded-xl flex flex-col justify-between min-h-[220px]">
          <div>
            <span className="text-[9px] font-bold uppercase tracking-[0.2em] text-secondary block font-mono">Logistics Volume</span>
            <h3 className="text-[18px] font-bold text-on-surface mt-[6px] leading-snug">Total Tons Re-routed</h3>
          </div>
          <div className="flex items-baseline gap-[10px] mt-sm">
            <span className="text-[40px] font-bold text-secondary font-mono leading-none">842</span>
            <span className="text-[13px] text-on-surface-variant font-mono font-medium">Metric Tons</span>
          </div>
          <div className="mt-sm">
            <div className="w-full h-[6px] bg-surface-container-high rounded-full overflow-hidden">
              <div className="bg-secondary h-full rounded-full shadow-[0_0_6px_#ffb95f]" style={{ width: "74%" }}></div>
            </div>
            <div className="flex justify-between mt-[6px] font-mono text-[10px]">
              <span className="text-on-surface-variant">Cap: 1,200t</span>
              <span className="text-secondary font-bold">74% Target</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Bottom Two-Column Section ── */}
      <div className="flex gap-md min-h-0 flex-1">

        {/* Historical Incident Report */}
        <div className="flex-1 glass-panel rounded-xl p-md flex flex-col min-w-0 overflow-y-auto">
          <div className="flex justify-between items-center mb-md shrink-0">
            <h3 className="text-[18px] font-bold text-on-surface">Historical Incident Report</h3>
            <button className="text-[12px] text-primary font-bold font-mono hover:underline">View Full Archive</button>
          </div>

          <div className="space-y-md">
            {filtered.map((inc, idx) => (
              <div
                key={idx}
                className="flex items-start gap-[12px] p-[12px] border border-outline-variant/20 rounded-lg hover:bg-surface-variant/15 transition-colors"
              >
                {/* Icon */}
                <div className={`w-[38px] h-[38px] rounded-lg ${inc.iconBg} flex items-center justify-center shrink-0`}>
                  <span className={`material-symbols-outlined text-[20px] ${inc.iconColor}`}>{inc.icon}</span>
                </div>
                {/* Content */}
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

        {/* Agent Performance Log */}
        <div className="w-[300px] shrink-0 glass-panel rounded-xl p-md flex flex-col overflow-y-auto">
          <h3 className="text-[18px] font-bold text-on-surface mb-md shrink-0">Agent Performance Log</h3>

          <div className="space-y-[20px] flex-1">
            {/* Optimax-9 Core */}
            <div>
              <div className="flex justify-between items-center mb-[8px]">
                <div className="flex items-center gap-[8px]">
                  <span className="text-[13px] font-bold text-on-surface">Optimax-9 Core</span>
                  <span className="text-[9px] bg-primary text-on-primary px-[7px] py-[2px] rounded font-mono font-bold tracking-wider uppercase">
                    Top Performer
                  </span>
                </div>
                <span className="font-mono text-[12px] font-bold text-primary">98.4% Eff</span>
              </div>
              <div className="grid grid-cols-2 gap-[6px]">
                <div className="bg-surface-container rounded-lg p-[10px] border border-outline-variant/20">
                  <p className="text-[10px] text-on-surface-variant">Negotiation Speed</p>
                  <p className="text-[12px] font-bold text-on-surface font-mono mt-[3px]">1.2s avg</p>
                </div>
                <div className="bg-surface-container rounded-lg p-[10px] border border-outline-variant/20">
                  <p className="text-[10px] text-on-surface-variant">Route Opt.</p>
                  <p className="text-[12px] font-bold text-on-surface font-mono mt-[3px]">99.1% Acc</p>
                </div>
              </div>
            </div>

            {/* Vanguard-Beta */}
            <div>
              <div className="flex justify-between items-center mb-[8px]">
                <div className="flex items-center gap-[8px]">
                  <span className="text-[13px] font-bold text-on-surface">Vanguard-Beta</span>
                  <span className="text-[9px] bg-error text-on-error px-[7px] py-[2px] rounded font-mono font-bold tracking-wider uppercase">
                    Experimental
                  </span>
                </div>
                <span className="font-mono text-[12px] font-bold text-tertiary">91.2% Eff</span>
              </div>
              <div className="grid grid-cols-2 gap-[6px]">
                <div className="bg-surface-container rounded-lg p-[10px] border border-outline-variant/20">
                  <p className="text-[10px] text-on-surface-variant">Negotiation Speed</p>
                  <p className="text-[12px] font-bold text-on-surface font-mono mt-[3px]">0.8s avg</p>
                </div>
                <div className="bg-surface-container rounded-lg p-[10px] border border-outline-variant/20">
                  <p className="text-[10px] text-on-surface-variant">Route Opt.</p>
                  <p className="text-[12px] font-bold text-on-surface font-mono mt-[3px]">88.5% Acc</p>
                </div>
              </div>
            </div>

            {/* Sentinel-Shield */}
            <div>
              <div className="flex justify-between items-center mb-[8px]">
                <div className="flex items-center gap-[8px]">
                  <span className="text-[13px] font-bold text-on-surface">Sentinel-Shield</span>
                  {/* Amber bar badge like in screenshot */}
                  <span className="inline-block w-[52px] h-[8px] rounded-full bg-secondary/70"></span>
                </div>
                <span className="font-mono text-[12px] font-bold text-secondary">94.7% Eff</span>
              </div>
              <div className="grid grid-cols-2 gap-[6px]">
                <div className="bg-surface-container rounded-lg p-[10px] border border-outline-variant/20">
                  <p className="text-[10px] text-on-surface-variant">Negotiation Speed</p>
                  <p className="text-[12px] font-bold text-on-surface font-mono mt-[3px]">2.4s avg</p>
                </div>
                <div className="bg-surface-container rounded-lg p-[10px] border border-outline-variant/20">
                  <p className="text-[10px] text-on-surface-variant">Route Opt.</p>
                  <p className="text-[12px] font-bold text-on-surface font-mono mt-[3px]">95.4% Acc</p>
                </div>
              </div>
            </div>
          </div>

          {/* Configure Heuristics */}
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

      {/* ── Footer: Global Resilience Index ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-md border-t border-outline-variant/20 pt-md shrink-0">
        <div className="flex items-center gap-[10px]">
          <div className="relative w-10 h-10 rounded-full overflow-hidden border border-primary/20 shrink-0">
            <Image fill className="object-cover" alt="Global index" src="/images/earth_network.jpg" sizes="100vw" />
          </div>
          <div>
            <h4 className="text-[12px] font-bold text-on-surface">Global Resilience Index</h4>
            <p className="text-[11px] text-primary font-semibold font-mono">System Health: Optimal (0.92)</p>
          </div>
        </div>
        <div className="flex gap-md font-mono text-[10px] text-right">
          <div className="flex flex-col items-end">
            <span className="text-on-surface-variant uppercase font-semibold tracking-wide text-[9px]">Last Data Sync</span>
            <span className="text-on-surface font-bold mt-[2px]">OCT 27, 2023 — 14:32:01 UTC</span>
          </div>
          <div className="w-[1px] h-8 bg-outline-variant/30"></div>
          <div className="flex flex-col items-end">
            <span className="text-on-surface-variant uppercase font-semibold tracking-wide text-[9px]">Security Protocol</span>
            <span className="text-primary font-bold mt-[2px]">SHA-512 ACTIVE</span>
          </div>
        </div>
      </div>

      {/* ── Heuristic Modal ── */}
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
