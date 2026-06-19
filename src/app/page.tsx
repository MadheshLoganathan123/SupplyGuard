"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { supabase } from "../lib/supabaseClient";

interface Message {
  agent: string;
  color: string;
  text: string;
}

const BACKEND_URL = (() => {
  const configured = (process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000/api/v1").replace(/\/+$/, "");
  return configured.endsWith("/api/v1") ? configured : `${configured}/api/v1`;
})();

export default function Dashboard() {
  const [threatLevel, setThreatLevel] = useState(35);
  const [threatText, setThreatText] = useState("MODERATE");
  const [activeDisruptions, setActiveDisruptions] = useState(0);
  const [supplyMatchPct, setSupplyMatchPct] = useState(0);
  const [activeUnits, setActiveUnits] = useState(0);
  
  // Negotiation Hub Logs state
  const [logs, setLogs] = useState<Message[]>([]);
  
  const [inputValue, setInputValue] = useState("");
  const feedEndRef = useRef<HTMLDivElement>(null);

  const fetchDashboard = useCallback(async () => {
    try {
      const metricsRes = await fetch(`${BACKEND_URL}/dashboard/metrics`);
      if (metricsRes.ok) {
        const payload = await metricsRes.json();
        setThreatText(payload.threatLevel ?? "MODERATE");
        setActiveDisruptions(payload.activeDisruptions ?? 0);
        setSupplyMatchPct(payload.supplyMatchPct ?? 94);
        setActiveUnits(payload.fleetCounts ?? 0);
        const threatPercent =
          payload.threatLevel === "CRITICAL" ? 95 :
          payload.threatLevel === "ELEVATED" ? 65 : 35;
        setThreatLevel(threatPercent);
      } else {
        console.warn("Dashboard metrics unavailable:", metricsRes.status);
      }
    } catch (err) {
      console.warn("Dashboard fetch failed — backend may be offline:", err);
    }
  }, []);

  const fetchLogs = useCallback(async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/agent-logs?limit=15`);
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) {
          setLogs(data.reverse().map((l: Record<string, string>) => ({
            agent: l.agent_name || "Agent",
            color: "text-primary",
            text: l.message || "Action executed",
          })));
          return;
        }
      }
    } catch {
      // fall through to Supabase
    }

    const { data, error } = await supabase
      .from("agent_logs")
      .select("agent_name, message, executed_at")
      .order("executed_at", { ascending: false })
      .limit(15);

    if (error) {
      console.warn("Agent logs fetch failed:", error.message);
      return;
    }
    if (data && data.length > 0) {
      setLogs(
        [...data].reverse().map((l: Record<string, string>) => ({
          agent: l.agent_name || "Agent",
          color: "text-primary",
          text: l.message || "Action executed",
        }))
      );
    }
  }, []);

  // Fetch metrics and agent logs from the backend
  useEffect(() => {
    void Promise.resolve().then(() => {
      void fetchDashboard();
      void fetchLogs();
    });

    const metricsInterval = setInterval(fetchDashboard, 15000);

    const channel = supabase
      .channel('dashboard-realtime')
      .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'agent_logs' }, (payload) => {
        const l = payload.new as Record<string, string>;
        setLogs(prev => [...prev, {
          agent: l.agent_name || 'Agent',
          color: 'text-primary',
          text: l.message || 'Action executed'
        }].slice(-15));
        fetchDashboard();
      })
      .on('postgres_changes', { event: '*', schema: 'public', table: 'shipments' }, () => {
        fetchDashboard();
      })
      .subscribe();

    return () => {
      clearInterval(metricsInterval);
      supabase.removeChannel(channel);
    };
  }, [fetchDashboard, fetchLogs]);

  // Scroll to bottom of agent logs whenever log updates
  useEffect(() => {
    feedEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const handleInterventionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userText = inputValue.trim();
    const userMsg = {
      agent: "Operator Intervene",
      color: "text-secondary font-bold underline",
      text: userText
    };

    setLogs(prev => [...prev, userMsg].slice(-15));
    setInputValue("");

    try {
      await fetch(`${BACKEND_URL}/interventions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: userText }),
      });
    } catch (err) {
      console.warn("Intervention save failed:", err);
    }

    setTimeout(() => {
      const aiResponse = {
        agent: "Core AI",
        color: "text-primary-container",
        text: `Acknowledged operator feedback: "${userText}". Adapting routing criteria.`
      };
      setLogs(prev => [...prev, aiResponse].slice(-15));
    }, 1200);
  };

  const tickerItems = [
    "NDMA: Localized curfew in East Side effective 2200h",
    "Wholesale: Wheat price spike +12% in District Central",
    "Community: 4 reports of price gouging near Sector 7",
    "Fuel Logistics: Transit cost optimization trend downward 3%",
    "Health Alert: Clean water supply reaching critical threshold in Node Delta"
  ];

  return (
    <div className="pt-[88px] pb-20 md:pb-4 flex-1 flex flex-col px-lg py-md gap-md overflow-y-auto h-full">
      {/* 1. Top Section: Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-gutter shrink-0">
        {/* Global Threat Level */}
        <div className="glass-panel p-md rounded-xl flex flex-col gap-xs group hover:border-secondary/40 transition-all cursor-default">
          <div className="flex justify-between items-center">
            <span className="text-label-xs font-label-xs text-on-surface-variant uppercase font-medium tracking-wider">Global Threat Level</span>
            <span className="material-symbols-outlined text-secondary text-xl">warning</span>
          </div>
          <div className="flex flex-col mt-sm">
            <span className="text-display-lg font-bold text-secondary leading-none tracking-tight uppercase">{threatText}</span>
            <div className="w-full h-[3px] bg-surface-variant rounded-full mt-sm overflow-hidden">
              <div className="bg-secondary h-full rounded-full transition-all duration-700" style={{ width: `${threatLevel}%` }}></div>
            </div>
          </div>
        </div>

        {/* Active Disruptions */}
        <div className="glass-panel p-md rounded-xl flex flex-col gap-xs group hover:border-error/40 transition-all cursor-default">
          <div className="flex justify-between items-center">
            <span className="text-label-xs font-label-xs text-on-surface-variant uppercase font-medium tracking-wider">Active Disruptions</span>
            <span className="material-symbols-outlined text-error text-xl">emergency</span>
          </div>
          <div className="flex items-baseline gap-sm mt-sm">
            <span className="text-display-lg font-bold text-error leading-none font-mono">{activeDisruptions.toString().padStart(2, '0')}</span>
            <span className="text-label-md text-on-surface-variant">Events Detected</span>
          </div>
          <p className="text-[10px] text-error/80 uppercase tracking-widest font-mono mt-xs">Sector 7, Sector 12, Node Delta</p>
        </div>

        {/* Supply Match */}
        <div className="glass-panel p-md rounded-xl flex flex-col gap-xs group hover:border-primary/40 transition-all cursor-default">
          <div className="flex justify-between items-center">
            <span className="text-label-xs font-label-xs text-on-surface-variant uppercase font-medium tracking-wider">Supply Match</span>
            <span className="material-symbols-outlined text-primary text-xl">inventory_2</span>
          </div>
          <div className="flex items-baseline gap-sm mt-sm">
            <span className="text-display-lg font-bold text-primary leading-none font-mono">{supplyMatchPct}%</span>
            <span className="text-label-md text-on-surface-variant">Optimal</span>
          </div>
          <div className="flex gap-[3px] mt-xs">
            <div className="h-[3px] flex-1 bg-primary rounded-full"></div>
            <div className="h-[3px] flex-1 bg-primary rounded-full"></div>
            <div className="h-[3px] flex-1 bg-primary rounded-full"></div>
            <div className="h-[3px] flex-1 bg-surface-variant rounded-full"></div>
          </div>
        </div>

        {/* Network Fleet */}
        <div className="glass-panel p-md rounded-xl flex flex-col gap-xs group hover:border-primary-fixed-dim/40 transition-all cursor-default">
          <div className="flex justify-between items-center">
            <span className="text-label-xs font-label-xs text-on-surface-variant uppercase font-medium tracking-wider">Network Fleet</span>
            <span className="material-symbols-outlined text-primary-fixed-dim text-xl">person_pin_circle</span>
          </div>
          <div className="flex items-baseline gap-sm mt-sm">
            <span className="text-display-lg font-bold text-primary-fixed-dim leading-none font-mono">{activeUnits}</span>
            <span className="text-label-md text-on-surface-variant">Active Units</span>
          </div>
          <p className="text-[10px] text-primary-fixed-dim/80 uppercase tracking-widest font-mono mt-xs">89 Logistics | 53 Emergency</p>
        </div>
      </div>

      {/* 2 & 3. Center Section: Map and Negotiation Hub */}
      <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-12 gap-gutter">
        {/* Map Canvas */}
        <div className="lg:col-span-8 glass-panel rounded-xl relative overflow-hidden min-h-[300px]">
          {/* Dark base + grid overlay */}
          <div className="absolute inset-0 bg-[#0b1326] z-0"></div>
          <div className="absolute inset-0 map-grid-overlay z-10 opacity-60"></div>
          {/* Faint background map gradient (no external image required) */}
          <div
            className="absolute inset-0 w-full h-full opacity-20 z-0"
            style={{
              background:
                "radial-gradient(circle at 30% 40%, rgba(78,222,163,0.15), transparent 50%), radial-gradient(circle at 70% 60%, rgba(255,100,80,0.12), transparent 45%), linear-gradient(135deg, #0b1326 0%, #111827 100%)",
            }}
          />
          {/* SVG network nodes + routes */}
          <svg className="absolute inset-0 w-full h-full pointer-events-none z-20" viewBox="0 0 800 500" preserveAspectRatio="xMidYMid slice">
            {/* Background network node lines (faint white spider-web) */}
            <g stroke="rgba(255,255,255,0.08)" strokeWidth="1" fill="none">
              <line x1="400" y1="50"  x2="600" y2="150"/>
              <line x1="600" y1="150" x2="700" y2="320"/>
              <line x1="700" y1="320" x2="580" y2="460"/>
              <line x1="400" y1="50"  x2="300" y2="200"/>
              <line x1="300" y1="200" x2="420" y2="350"/>
              <line x1="420" y1="350" x2="580" y2="460"/>
              <line x1="300" y1="200" x2="160" y2="300"/>
              <line x1="160" y1="300" x2="200" y2="450"/>
              <line x1="600" y1="150" x2="420" y2="350"/>
              <line x1="160" y1="300" x2="420" y2="350"/>
              <line x1="400" y1="50"  x2="500" y2="250"/>
              <line x1="500" y1="250" x2="700" y2="320"/>
              <line x1="500" y1="250" x2="420" y2="350"/>
            </g>
            {/* Small node dots */}
            <g fill="rgba(255,255,255,0.15)">
              <circle cx="400" cy="50"  r="3"/>
              <circle cx="600" cy="150" r="3"/>
              <circle cx="700" cy="320" r="3"/>
              <circle cx="580" cy="460" r="3"/>
              <circle cx="300" cy="200" r="3"/>
              <circle cx="420" cy="350" r="3"/>
              <circle cx="160" cy="300" r="3"/>
              <circle cx="200" cy="450" r="3"/>
              <circle cx="500" cy="250" r="3"/>
            </g>

            {/* Disruption Zone — rotated quadrilateral (Sector 7) */}
            <polygon
              points="200,280 330,240 370,380 230,400"
              fill="rgba(255,100,80,0.15)"
              stroke="rgba(255,100,80,0.55)"
              strokeWidth="1.5"
              className="animate-pulse"
            />
            <text
              x="243"
              y="340"
              fill="#ff6450"
              fontSize="9"
              fontFamily="monospace"
              fontWeight="bold"
              letterSpacing="1"
              textAnchor="middle"
            >
              SECTOR 7: FLASH FLOOD
            </text>

            {/* Green reroute path — smooth S-curve bottom-left to upper-right */}
            <path
              d="M 80 430 C 200 390, 320 470, 450 420 S 620 320, 740 260"
              fill="none"
              stroke="#4edea3"
              strokeWidth="2"
              strokeDasharray="8 5"
              style={{ animation: "dash 20s linear infinite" }}
            />
            {/* Start node */}
            <circle cx="80" cy="430" r="5" fill="#4edea3"/>
            <circle cx="80" cy="430" r="9" fill="none" stroke="#4edea3" strokeWidth="1.5" opacity="0.5" className="animate-ping"/>
            {/* End node */}
            <circle cx="740" cy="260" r="5" fill="#4edea3"/>
            <circle cx="740" cy="260" r="9" fill="none" stroke="#4edea3" strokeWidth="1.5" opacity="0.5" className="animate-ping"/>
          </svg>

          {/* AI Active Routing badge — top left */}
          <div className="absolute top-md left-md z-30">
            <div className="glass-panel bg-surface/80 px-md py-[6px] rounded-lg flex items-center gap-sm border-primary/20">
              <span className="w-[10px] h-[10px] rounded-full bg-primary pulse-emerald shrink-0"></span>
              <span className="text-[11px] text-primary font-medium tracking-tight">AI Active Routing Enabled</span>
            </div>
          </div>

          {/* Node Telemetry — top right */}
          <div className="absolute top-md right-md z-30">
            <div className="glass-panel bg-surface/90 p-md rounded-lg w-52 border-outline-variant/20">
              <p className="text-[10px] text-on-surface-variant uppercase tracking-widest mb-sm border-b border-outline-variant/20 pb-xs font-semibold">Node Telemetry</p>
              <div className="space-y-xs font-mono">
                <div className="flex justify-between items-center text-[11px]">
                  <span className="text-on-surface-variant">Signal Stability</span>
                  <span className="text-primary font-bold">99.8%</span>
                </div>
                <div className="flex justify-between items-center text-[11px]">
                  <span className="text-on-surface-variant">Reroute Efficiency</span>
                  <span className="text-secondary font-bold">+12.4%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Map control buttons — bottom left */}
          <div className="absolute bottom-md left-md flex gap-sm z-30">
            <button className="bg-surface/95 backdrop-blur-md p-[7px] rounded-lg border border-outline-variant/30 hover:border-primary/50 text-on-surface-variant hover:text-on-surface transition-colors flex items-center justify-center">
              <span className="material-symbols-outlined text-[20px]">layers</span>
            </button>
            <button className="bg-surface/95 backdrop-blur-md p-[7px] rounded-lg border border-outline-variant/30 hover:border-primary/50 text-on-surface-variant hover:text-on-surface transition-colors flex items-center justify-center">
              <span className="material-symbols-outlined text-[20px]">gps_fixed</span>
            </button>
          </div>
        </div>

        {/* Agentic Negotiation Hub */}
        <div className="lg:col-span-4 glass-panel rounded-xl flex flex-col overflow-hidden border-primary/10 min-h-[300px]">
          <div className="px-md py-[10px] border-b border-outline-variant/30 bg-surface-container-high/50 flex justify-between items-center shrink-0">
            <div className="flex items-center gap-sm">
              <span className="material-symbols-outlined text-primary text-xl">smart_toy</span>
              <h2 className="text-[11px] uppercase tracking-widest font-semibold text-on-surface">Agentic Negotiation Hub</h2>
            </div>
            <span className="text-[10px] font-mono text-on-surface-variant tracking-widest">v4.0.2-BETA</span>
          </div>

          <div className="flex-1 overflow-y-auto p-md space-y-[10px] font-mono text-[12px] leading-relaxed">
            {logs.map((log, index) => (
              <div key={index} className="flex gap-xs items-start animate-in fade-in slide-in-from-left-2 duration-300">
                <span className={`${log.color} font-bold shrink-0 leading-relaxed`}>[{log.agent}]</span>
                <span className="text-on-surface-variant break-words leading-relaxed">{log.text}</span>
              </div>
            ))}
            <div ref={feedEndRef} />
          </div>

          <form onSubmit={handleInterventionSubmit} className="p-sm bg-surface-container-low border-t border-outline-variant/30 shrink-0">
            <div className="flex gap-xs">
              <input
                className="flex-1 bg-background border border-outline-variant/30 rounded px-sm py-[7px] text-[12px] focus:ring-1 focus:ring-primary focus:border-primary outline-none text-on-surface placeholder:text-on-surface-variant/50"
                placeholder="Intervene in negotiation..."
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
              />
              <button type="submit" className="bg-surface-variant hover:bg-surface-container-highest px-sm py-1 rounded transition-colors text-on-surface flex items-center justify-center">
                <span className="material-symbols-outlined text-[18px]">send</span>
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* 4. Bottom: Live Intel Ticker */}
      <div className="h-10 glass-panel rounded-lg flex items-center overflow-hidden border-outline-variant/20 shrink-0">
        <div className="bg-secondary px-md h-full flex items-center gap-sm shrink-0 z-10 border-r border-secondary/30">
          <span className="material-symbols-outlined text-[18px] text-on-secondary">rss_feed</span>
          <span className="text-on-secondary text-[10px] uppercase font-bold tracking-widest font-mono">Live Intel</span>
        </div>
        <div className="flex-1 relative overflow-hidden h-full flex items-center">
          <div className="flex items-center gap-12 whitespace-nowrap animate-ticker text-on-surface-variant text-[10px] uppercase tracking-widest font-medium font-mono">
            {[...tickerItems, ...tickerItems].map((item, index) => (
              <span key={index} className="flex items-center gap-sm">
                <span className="text-secondary">•</span> {item}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
