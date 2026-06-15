"use client";

import Image from "next/image";
import { useState, useEffect, useRef } from "react";

interface Message {
  agent: string;
  color: string;
  text: string;
}

const randomMessages: Message[] = [
  { agent: "Logistics Agent", color: "text-primary", text: "Rerouting Unit #421 to avoid rising water levels." },
  { agent: "Sourcing Agent", color: "text-primary-fixed-dim", text: "Alternative supplier found for essential medicine." },
  { agent: "Recipient Agent", color: "text-secondary", text: "Validation token received for sector delivery." },
  { agent: "Core AI", color: "text-primary-container", text: "Resource balancing complete for current hour." },
  { agent: "Logistics Agent", color: "text-primary", text: "Drone swarm route optimized for high wind corridors." },
  { agent: "Sourcing Agent", color: "text-primary-fixed-dim", text: "Wheat reserves at warehouse Delta checked and certified." }
];

export default function Dashboard() {
  // Threat Level State (simulating random noise fluctuation)
  const [threatLevel, setThreatLevel] = useState(65);
  
  // Negotiation Hub Logs state
  const [logs, setLogs] = useState<Message[]>([
    { agent: "Logistics Agent", color: "text-primary", text: "Bypassing Sector 7 via Perimeter Node B." },
    { agent: "Sourcing Agent", color: "text-primary-fixed-dim", text: "Surplus grains allocated from Warehouse Delta." },
    { agent: "Recipient Agent", color: "text-secondary", text: "ETA adjustment confirmed. Community notified." },
    { agent: "Logistics Agent", color: "text-primary", text: "Analyzing secondary blockages in Sector 3..." },
    { agent: "Core AI", color: "text-primary-container", text: "Calculating optimal re-entry points. Please standby." }
  ]);
  
  const [inputValue, setInputValue] = useState("");
  const feedEndRef = useRef<HTMLDivElement>(null);

  // Simulating live telemetry updates
  useEffect(() => {
    const logInterval = setInterval(() => {
      const randomMsg = randomMessages[Math.floor(Math.random() * randomMessages.length)];
      setLogs(prev => [...prev, randomMsg].slice(-15)); // Cap logs at 15 messages
    }, 5000);

    const threatInterval = setInterval(() => {
      const noise = (Math.random() - 0.5) * 4;
      setThreatLevel(prev => Math.max(60, Math.min(72, prev + noise)));
    }, 3500);

    return () => {
      clearInterval(logInterval);
      clearInterval(threatInterval);
    };
  }, []);

  // Scroll to bottom of agent logs whenever log updates
  useEffect(() => {
    feedEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const handleInterventionSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    // Append user input as "Operator Intervene"
    const userMsg = {
      agent: "Operator Intervene",
      color: "text-secondary font-bold underline",
      text: inputValue
    };

    setLogs(prev => [...prev, userMsg].slice(-15));
    setInputValue("");

    // Simulate quick AI response to user input
    setTimeout(() => {
      const aiResponse = {
        agent: "Core AI",
        color: "text-primary-container",
        text: `Acknowledged operator feedback: "${inputValue}". Adapting routing criteria.`
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
            <span className="text-display-lg font-bold text-secondary leading-none tracking-tight">ELEVATED</span>
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
            <span className="text-display-lg font-bold text-error leading-none font-mono">03</span>
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
            <span className="text-display-lg font-bold text-primary leading-none font-mono">94%</span>
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
            <span className="text-display-lg font-bold text-primary-fixed-dim leading-none font-mono">142</span>
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
          {/* Faint background map image */}
          <Image
            fill
            className="absolute inset-0 w-full h-full object-cover grayscale opacity-10 z-0"
            alt="Karachi Map Background"
            src="/images/map_command_center.jpg"
            sizes="100vw"
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
