"use client";

import Image from "next/image";
import { useState, useEffect } from "react";

interface NodeDetail {
  name: string;
  type: "Farm" | "Warehouse" | "Retail" | "Shipping";
  status: "OPERATIONAL" | "AT-RISK" | "BLOCKED" | "INACTIVE";
  agent: string;
  image: string;
  inventory: string;
  inventoryColor: string;
  threat: string;
  threatColor: string;
  throughput: string;
  connections: {
    name: string;
    type: "drone" | "flight" | "truck";
    status: "active" | "pending";
    eta: string;
    iconBg: string;
    iconColor: string;
  }[];
}

const nodeDataList: Record<string, NodeDetail> = {
  "Farm #204": {
    name: "Farm #204",
    type: "Farm",
    status: "OPERATIONAL",
    agent: "Sourcing Agent: Alpha-9",
    image: "/images/vertical_farm.jpg",
    inventory: "82% (High)",
    inventoryColor: "text-primary",
    threat: "Low (Minor Delay)",
    threatColor: "text-primary",
    throughput: "1.2k units/hr",
    connections: [
      { name: "Drone Fleet Beta", type: "drone", status: "active", eta: "12 mins", iconBg: "bg-primary/15", iconColor: "text-primary" },
      { name: "Aerial Transport 04", type: "flight", status: "pending", eta: "Loading", iconBg: "bg-secondary/15", iconColor: "text-secondary" },
    ],
  },
  "Warehouse B": {
    name: "Warehouse B",
    type: "Warehouse",
    status: "OPERATIONAL",
    agent: "Sourcing Agent: Omega-4",
    image: "/images/earth_network.jpg",
    inventory: "94% (Full)",
    inventoryColor: "text-primary",
    threat: "None",
    threatColor: "text-primary",
    throughput: "4.8k units/hr",
    connections: [
      { name: "Truck Convoy Sector 7", type: "truck", status: "active", eta: "45 mins", iconBg: "bg-primary/15", iconColor: "text-primary" },
      { name: "Drone Fleet Alpha", type: "drone", status: "active", eta: "5 mins", iconBg: "bg-primary/15", iconColor: "text-primary" },
    ],
  },
  "Retail Store Delta": {
    name: "Retail Store Delta",
    type: "Retail",
    status: "AT-RISK",
    agent: "Recipient Agent: Delta-3",
    image: "/images/map_logistics.jpg",
    inventory: "21% (Critical Low)",
    inventoryColor: "text-error",
    threat: "High (Sector 7 Flood)",
    threatColor: "text-error",
    throughput: "450 units/hr",
    connections: [
      { name: "Emergency Courier 9", type: "drone", status: "pending", eta: "Delayed", iconBg: "bg-secondary/15", iconColor: "text-secondary" },
    ],
  },
  "Shipping Node 71": {
    name: "Shipping Node 71",
    type: "Shipping",
    status: "BLOCKED",
    agent: "Logistics Agent: Sigma-12",
    image: "/images/map_command_center.jpg",
    inventory: "55% (Static)",
    inventoryColor: "text-secondary",
    threat: "Critical (Road Closed)",
    threatColor: "text-error",
    throughput: "0 units/hr",
    connections: [],
  },
};

// Topology node layout — 2 rows × ~12 cols = 24 slots
// First few slots are the named interactive nodes; rest are filler
const TOPOLOGY_ROWS = 2;
const TOPOLOGY_COLS = 12;

const namedNodes = Object.keys(nodeDataList);

// Filler node icons cycling
const fillerIcons = ["agriculture", "warehouse", "storefront", "local_shipping"];

export default function Network() {
  const [selectedNode, setSelectedNode] = useState<NodeDetail>(nodeDataList["Farm #204"]);
  const [showDetail, setShowDetail] = useState(true);
  const [latency, setLatency] = useState(24);
  const [successRate, setSuccessRate] = useState(97.7);
  const [projecting, setProjecting] = useState(false);
  const [projectionDone, setProjectionDone] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => {
      setLatency(Math.floor(20 + Math.random() * 10));
      setSuccessRate(parseFloat((96.5 + Math.random() * 2.5).toFixed(1)));
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleRunProjection = () => {
    setProjecting(true);
    setProjectionDone(false);
    setTimeout(() => {
      setProjecting(false);
      setProjectionDone(true);
    }, 2000);
  };

  const getStatusDot = (status: NodeDetail["status"]) => {
    switch (status) {
      case "OPERATIONAL": return "bg-primary";
      case "AT-RISK": return "bg-secondary";
      case "BLOCKED": return "bg-error";
      default: return "bg-outline-variant";
    }
  };

  const getNodeIcon = (type: NodeDetail["type"]) => {
    switch (type) {
      case "Farm": return "agriculture";
      case "Warehouse": return "warehouse";
      case "Retail": return "storefront";
      case "Shipping": return "local_shipping";
    }
  };

  const getNodeIconColor = (status: NodeDetail["status"]) => {
    switch (status) {
      case "OPERATIONAL": return "text-primary";
      case "AT-RISK": return "text-secondary";
      case "BLOCKED": return "text-error";
      default: return "text-on-surface-variant/30";
    }
  };

  return (
    <div className="pt-[88px] pb-4 flex-1 flex flex-col px-lg py-md gap-md overflow-y-auto h-full">
      <div className="flex gap-md h-full min-h-0">

        {/* ── Left column ── */}
        <div className="flex-1 flex flex-col gap-md min-w-0 overflow-y-auto pr-xs">

          {/* Page header row */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-sm">
            <div>
              <h1 className="text-[26px] font-bold text-on-surface leading-tight tracking-tight">Global Supply Network</h1>
              <p className="text-[12px] text-on-surface-variant mt-[2px] leading-snug">
                Live visual telemetry of all active supply nodes<br className="hidden sm:block" /> and edge connections.
              </p>
            </div>
            {/* Status badges */}
            <div className="flex gap-[6px] shrink-0 font-mono text-[11px] font-bold tracking-wider">
              <div className="bg-surface-container border border-outline-variant/30 rounded px-[10px] py-[6px] flex flex-col items-start">
                <span className="text-on-surface-variant font-normal text-[9px] uppercase tracking-widest">Operational:</span>
                <span className="text-primary text-[13px]">142</span>
              </div>
              <div className="bg-surface-container border border-outline-variant/30 rounded px-[10px] py-[6px] flex flex-col items-start">
                <span className="text-on-surface-variant font-normal text-[9px] uppercase tracking-widest">At-Risk:</span>
                <span className="text-secondary text-[13px]">14</span>
              </div>
              <div className="bg-surface-container border border-outline-variant/30 rounded px-[10px] py-[6px] flex flex-col items-start">
                <span className="text-on-surface-variant font-normal text-[9px] uppercase tracking-widest">Blocked:</span>
                <span className="text-error text-[13px]">3</span>
              </div>
            </div>
          </div>

          {/* Metric cards row */}
          <div className="grid grid-cols-3 gap-md">
            {/* Network Latency */}
            <div className="glass-panel px-md py-[10px] rounded-xl flex flex-col justify-between min-h-[80px]">
              <div className="flex justify-between items-center">
                <span className="text-[11px] text-on-surface-variant font-medium">Network Latency</span>
                <span className="material-symbols-outlined text-primary text-[17px]">wifi_tethering</span>
              </div>
              <div>
                <span className="text-[26px] font-bold text-primary font-mono leading-none">{latency}ms</span>
                <div className="w-full h-[3px] bg-surface-variant rounded-full mt-[6px] overflow-hidden">
                  <div className="bg-primary h-full rounded-full transition-all duration-700" style={{ width: `${(latency / 40) * 100}%` }}></div>
                </div>
              </div>
            </div>

            {/* Negotiation Success */}
            <div className="glass-panel px-md py-[10px] rounded-xl flex flex-col justify-between min-h-[80px]">
              <div className="flex justify-between items-center">
                <span className="text-[11px] text-on-surface-variant font-medium">Negotiation Success</span>
                <span className="material-symbols-outlined text-secondary text-[17px]">handshake</span>
              </div>
              <div>
                <span className="text-[26px] font-bold text-secondary font-mono leading-none">{successRate}%</span>
                <div className="w-full h-[3px] bg-surface-variant rounded-full mt-[6px] overflow-hidden">
                  <div className="bg-secondary h-full rounded-full transition-all duration-700" style={{ width: `${successRate}%` }}></div>
                </div>
              </div>
            </div>

            {/* Supply-Demand Gap */}
            <div className="glass-panel px-md py-[10px] rounded-xl flex flex-col justify-between min-h-[80px]">
              <div className="flex justify-between items-center">
                <span className="text-[11px] text-on-surface-variant font-medium">Supply-Demand Gap</span>
                <span className="material-symbols-outlined text-error text-[17px]">query_stats</span>
              </div>
              <div>
                <span className="text-[26px] font-bold text-error font-mono leading-none">4.2%</span>
                <div className="w-full h-[3px] bg-surface-variant rounded-full mt-[6px] overflow-hidden">
                  <div className="bg-error h-full rounded-full w-[15%]"></div>
                </div>
              </div>
            </div>
          </div>

          {/* Active Topology panel */}
          <div className="glass-panel rounded-xl p-md flex flex-col">
            <div className="flex items-center justify-between mb-md">
              <h3 className="text-[10px] font-bold uppercase tracking-[0.18em] text-on-surface-variant font-mono">Active Topology</h3>
              <div className="flex gap-md font-mono text-[10px] font-medium text-on-surface-variant">
                <span className="flex items-center gap-[5px]"><span className="w-[7px] h-[7px] rounded-full bg-primary inline-block"></span>Farms</span>
                <span className="flex items-center gap-[5px]"><span className="w-[7px] h-[7px] rounded-full bg-secondary inline-block"></span>Hubs</span>
                <span className="flex items-center gap-[5px]"><span className="w-[7px] h-[7px] rounded-full bg-on-surface-variant/40 inline-block"></span>Retail</span>
              </div>
            </div>

            {/* Node grid — row 1 */}
            <div className="space-y-[6px]">
              {[0, 1].map((row) => (
                <div key={row} className="flex gap-[6px]">
                  {Array.from({ length: TOPOLOGY_COLS }).map((_, col) => {
                    const nodeIdx = row * TOPOLOGY_COLS + col;
                    const namedKey = namedNodes[nodeIdx];
                    if (namedKey) {
                      const node = nodeDataList[namedKey];
                      const isSelected = selectedNode.name === namedKey;
                      return (
                        <button
                          key={namedKey}
                          onClick={() => { setSelectedNode(node); setShowDetail(true); setProjectionDone(false); }}
                          className={`relative flex-1 aspect-square glass-panel flex items-center justify-center rounded transition-all border ${
                            isSelected
                              ? "border-primary bg-primary/10"
                              : "border-outline-variant/25 hover:border-primary/50"
                          }`}
                        >
                          <span className={`material-symbols-outlined text-[16px] ${getNodeIconColor(node.status)}`}>
                            {getNodeIcon(node.type)}
                          </span>
                          <span className={`absolute -top-[3px] -right-[3px] w-[8px] h-[8px] rounded-full ${getStatusDot(node.status)}`}></span>
                        </button>
                      );
                    }
                    // Filler node
                    return (
                      <div
                        key={`filler-${row}-${col}`}
                        className="relative flex-1 aspect-square glass-panel flex items-center justify-center rounded border border-outline-variant/15 opacity-35"
                      >
                        <span className="material-symbols-outlined text-on-surface-variant/60 text-[15px]">
                          {fillerIcons[(nodeIdx) % 4]}
                        </span>
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          </div>

          {/* Sourcing Flow Graph */}
          <div className="glass-panel rounded-xl p-md flex flex-col" style={{ minHeight: "220px" }}>
            <div className="flex justify-between items-center mb-sm">
              <h3 className="text-[10px] font-bold uppercase tracking-[0.18em] text-on-surface-variant font-mono">Sourcing Flow Graph</h3>
              <span className="text-[10px] text-primary bg-primary/10 border border-primary/25 px-[10px] py-[4px] rounded font-mono font-bold">
                Real-time Optimization
              </span>
            </div>
            <div className="flex-1 relative flex items-center justify-center">
              {/* SVG flow lines */}
              <svg className="absolute inset-0 w-full h-full" viewBox="0 0 600 160" preserveAspectRatio="xMidYMid meet">
                {/* Cross lines */}
                <path d="M 140 42 Q 300 42 460 42" fill="none" stroke="rgba(78,222,163,0.25)" strokeDasharray="6 4" strokeWidth="1.5" />
                <path d="M 140 42 Q 300 120 460 118" fill="none" stroke="rgba(78,222,163,0.5)" strokeWidth="1.5" />
                <path d="M 140 118 Q 300 42 460 42" fill="none" stroke="rgba(78,222,163,0.5)" strokeWidth="1.5" />
                <path d="M 140 118 Q 300 118 460 118" fill="none" stroke="rgba(78,222,163,0.25)" strokeDasharray="6 4" strokeWidth="1.5" />
              </svg>
              {/* Source nodes */}
              <div className="absolute left-[18%] flex flex-col gap-[40px]">
                {[0, 1].map((i) => (
                  <div key={i} className="w-9 h-9 rounded-full border border-primary/50 bg-surface-container flex items-center justify-center">
                    <span className="material-symbols-outlined text-primary text-[17px]">psychology</span>
                  </div>
                ))}
              </div>
              {/* Recipient nodes */}
              <div className="absolute right-[18%] flex flex-col gap-[40px]">
                {[0, 1].map((i) => (
                  <div key={i} className="w-9 h-9 rounded-full border border-primary/40 bg-surface-container flex items-center justify-center">
                    <span className="material-symbols-outlined text-primary/70 text-[17px]">person</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* ── Right column: Node detail card ── */}
        {showDetail && (
          <div className="w-[260px] shrink-0 flex flex-col">
            <div className="glass-panel rounded-xl flex flex-col overflow-hidden border-outline-variant/20 h-full">
              {/* Card header */}
              <div className="px-md pt-md pb-sm flex items-start justify-between">
                <div>
                  <h2 className="text-[18px] font-bold text-on-surface leading-tight">{selectedNode.name}</h2>
                  <span className="inline-block mt-[5px] text-[10px] bg-primary/15 text-primary border border-primary/25 px-[8px] py-[3px] rounded font-mono font-semibold tracking-wide">
                    {selectedNode.agent}
                  </span>
                </div>
                <button
                  onClick={() => setShowDetail(false)}
                  className="text-on-surface-variant hover:text-on-surface transition-colors mt-1"
                  aria-label="Close"
                >
                  <span className="material-symbols-outlined text-[18px]">close</span>
                </button>
              </div>

              {/* Node image */}
              <div className="px-md">
                <div className="relative w-full rounded-lg overflow-hidden border border-outline-variant/20" style={{ aspectRatio: "16/9" }}>
                  <Image fill className="object-cover" alt={selectedNode.name} src={selectedNode.image} sizes="100vw" />
                </div>
              </div>

              {/* Telemetry rows */}
              <div className="px-md pt-md pb-sm space-y-[10px] font-mono text-[12px]">
                <div className="flex justify-between items-center">
                  <span className="text-on-surface-variant">Inventory Level</span>
                  <span className={`font-bold ${selectedNode.inventoryColor}`}>{selectedNode.inventory}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-on-surface-variant">Local Threat Level</span>
                  <span className={`font-bold ${selectedNode.threatColor}`}>{selectedNode.threat}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-on-surface-variant">Agent Throughput</span>
                  <span className="font-bold text-on-surface">{selectedNode.throughput}</span>
                </div>
              </div>

              {/* Connected Logistics */}
              <div className="px-md pb-sm">
                <h3 className="text-[9px] font-bold uppercase tracking-[0.18em] text-on-surface-variant mb-[8px] font-mono">Connected Logistics</h3>
                <div className="space-y-[6px]">
                  {selectedNode.connections.length > 0 ? (
                    selectedNode.connections.map((c, idx) => (
                      <div
                        key={idx}
                        className="flex items-center gap-[10px] p-[8px] bg-surface-container rounded-lg border border-outline-variant/15 hover:border-outline-variant/30 transition-colors"
                      >
                        <div className={`w-8 h-8 rounded flex items-center justify-center shrink-0 ${c.iconBg}`}>
                          <span className={`material-symbols-outlined text-[16px] ${c.iconColor}`}>
                            {c.type === "drone" ? "flight" : c.type === "flight" ? "flight_takeoff" : "local_shipping"}
                          </span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-[12px] font-semibold text-on-surface leading-tight truncate">{c.name}</p>
                          <p className="text-[10px] text-on-surface-variant font-mono">
                            {c.status === "active" ? `ETA: ${c.eta}` : `Status: ${c.eta}`}
                          </p>
                        </div>
                        <span className={`material-symbols-outlined text-[17px] shrink-0 ${c.status === "active" ? "text-primary" : "text-secondary"}`}>
                          {c.status === "active" ? "check_circle" : "pending"}
                        </span>
                      </div>
                    ))
                  ) : (
                    <p className="text-[11px] text-on-surface-variant/70 italic">No active connections.</p>
                  )}
                </div>
              </div>

              {/* Spacer */}
              <div className="flex-1"></div>

              {/* Run Demand Projection */}
              <div className="px-md pb-md pt-sm border-t border-outline-variant/20">
                {projectionDone && (
                  <p className="text-[10px] text-primary font-mono mb-[8px] leading-snug">
                    Projection complete: supply matches demand (+4.2% margin).
                  </p>
                )}
                <button
                  onClick={handleRunProjection}
                  disabled={projecting}
                  className="w-full py-[11px] border border-primary/50 text-primary font-bold rounded-lg hover:bg-primary hover:text-on-primary transition-all flex items-center justify-center gap-sm font-mono text-[11px] uppercase tracking-widest disabled:opacity-60"
                >
                  <span className={`material-symbols-outlined text-[18px] ${projecting ? "animate-spin" : ""}`}>
                    {projecting ? "autorenew" : "bar_chart"}
                  </span>
                  {projecting ? "Analyzing..." : "Run Demand Projection"}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
