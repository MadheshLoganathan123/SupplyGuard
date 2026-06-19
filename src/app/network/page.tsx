"use client";

import Image from "next/image";
import { useState, useEffect, useCallback } from "react";

const BACKEND_URL = (() => {
  const configured = (process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000/api/v1").replace(/\/+$/, "");
  return configured.endsWith("/api/v1") ? configured : `${configured}/api/v1`;
})();

interface NodeConnection {
  name: string;
  type: "drone" | "flight" | "truck";
  status: "active" | "pending";
  eta: string;
  iconBg: string;
  iconColor: string;
}

interface NodeDetail {
  id: string;
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
  connections: NodeConnection[];
}

interface ApiNode {
  id: string;
  name: string;
  node_type: string;
  status: string;
  agent_name?: string;
  image_url?: string;
  inventory_label?: string;
  inventory_level?: number;
  threat_level?: string;
  throughput?: string;
  position_index: number;
  connections?: { name: string; type: string; status: string; eta: string }[];
}

const TOPOLOGY_ROWS = 2;
const TOPOLOGY_COLS = 12;
const DEFAULT_IMAGE = "/images/earth_network.jpg";

const mapNodeType = (t: string): NodeDetail["type"] => {
  switch (t) {
    case "FARM": return "Farm";
    case "WAREHOUSE": return "Warehouse";
    case "RETAIL": return "Retail";
    default: return "Shipping";
  }
};

const mapStatus = (s: string): NodeDetail["status"] => {
  if (s === "AT_RISK") return "AT-RISK";
  if (s === "BLOCKED") return "BLOCKED";
  if (s === "INACTIVE") return "INACTIVE";
  return "OPERATIONAL";
};

const inventoryColor = (level?: number, label?: string) => {
  if (label?.toLowerCase().includes("critical") || (level !== undefined && level < 25)) return "text-error";
  if (level !== undefined && level < 50) return "text-secondary";
  return "text-primary";
};

const threatColor = (threat?: string) => {
  const t = (threat ?? "").toLowerCase();
  if (t.includes("critical") || t.includes("high")) return "text-error";
  if (t.includes("minor") || t.includes("low")) return "text-primary";
  return "text-secondary";
};

const mapApiNode = (n: ApiNode): NodeDetail => ({
  id: n.id,
  name: n.name,
  type: mapNodeType(n.node_type),
  status: mapStatus(n.status),
  agent: n.agent_name ?? "Unassigned Agent",
  image: n.image_url ?? DEFAULT_IMAGE,
  inventory: n.inventory_label ?? "—",
  inventoryColor: inventoryColor(n.inventory_level, n.inventory_label),
  threat: n.threat_level ?? "Unknown",
  threatColor: threatColor(n.threat_level),
  throughput: n.throughput ?? "—",
  connections: (n.connections ?? []).map((c) => ({
    name: c.name,
    type: c.type as NodeConnection["type"],
    status: c.status as NodeConnection["status"],
    eta: c.eta,
    iconBg: c.status === "active" ? "bg-primary/15" : "bg-secondary/15",
    iconColor: c.status === "active" ? "text-primary" : "text-secondary",
  })),
});

export default function Network() {
  const [nodes, setNodes] = useState<NodeDetail[]>([]);
  const [statusCounts, setStatusCounts] = useState({ operational: 0, at_risk: 0, blocked: 0 });
  const [selectedNode, setSelectedNode] = useState<NodeDetail | null>(null);
  const [showDetail, setShowDetail] = useState(true);
  const [latency, setLatency] = useState(24);
  const [successRate, setSuccessRate] = useState(97.7);
  const [supplyGap, setSupplyGap] = useState(4.2);
  const [projecting, setProjecting] = useState(false);
  const [projectionDone, setProjectionDone] = useState(false);
  const [projectionMessage, setProjectionMessage] = useState("");

  const fetchNodes = useCallback(async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/nodes/`);
      if (!res.ok) return;
      const data = await res.json();
      const mapped = (data.nodes ?? []).map((n: ApiNode) => mapApiNode(n));
      setNodes(mapped);
      if (data.status_counts) {
        setStatusCounts({
          operational: data.status_counts.operational ?? 0,
          at_risk: data.status_counts.at_risk ?? 0,
          blocked: data.status_counts.blocked ?? 0,
        });
      }
      if (data.metrics) {
        setLatency(Math.round(data.metrics.latency_ms ?? 24));
        setSuccessRate(parseFloat((data.metrics.negotiation_success_pct ?? 97.7).toFixed(1)));
        setSupplyGap(data.metrics.supply_demand_gap_pct ?? 4.2);
      }
      if (mapped.length > 0) {
        setSelectedNode((prev) => prev ?? mapped[0]);
      }
    } catch (err) {
      console.warn("Network nodes fetch failed:", err);
    }
  }, []);

  const fetchNodeDetail = useCallback(async (nodeId: string) => {
    try {
      const res = await fetch(`${BACKEND_URL}/nodes/${nodeId}`);
      if (!res.ok) return;
      const data = await res.json();
      setSelectedNode(mapApiNode(data));
    } catch (err) {
      console.warn("Node detail fetch failed:", err);
    }
  }, []);

  useEffect(() => {
    void Promise.resolve().then(() => {
      void fetchNodes();
    });
    const interval = setInterval(fetchNodes, 15000);
    return () => clearInterval(interval);
  }, [fetchNodes]);

  const handleSelectNode = (node: NodeDetail) => {
    setSelectedNode(node);
    setShowDetail(true);
    setProjectionDone(false);
    fetchNodeDetail(node.id);
  };

  const handleRunProjection = async () => {
    if (!selectedNode) return;
    setProjecting(true);
    setProjectionDone(false);
    setProjectionMessage("");
    try {
      const res = await fetch(`${BACKEND_URL}/projections/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ node_ids: [selectedNode.id], horizon_days: 7 }),
      });
      if (!res.ok) throw new Error("Projection request failed");
      const { job_id } = await res.json();

      const poll = async (attempts = 0): Promise<void> => {
        if (attempts > 20) throw new Error("Projection timed out");
        const statusRes = await fetch(`${BACKEND_URL}/projections/${job_id}`);
        if (!statusRes.ok) throw new Error("Projection status failed");
        const status = await statusRes.json();
        if (status.status === "done" && status.result) {
          setProjectionMessage(status.result.summary ?? "Projection complete.");
          setProjectionDone(true);
          setProjecting(false);
          return;
        }
        if (status.status === "failed") throw new Error("Projection failed");
        await new Promise((r) => setTimeout(r, 500));
        return poll(attempts + 1);
      };
      await poll();
    } catch (err) {
      console.warn("Projection failed:", err);
      setProjecting(false);
    }
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

  const gridNodes = nodes.slice(0, TOPOLOGY_ROWS * TOPOLOGY_COLS);
  const fillerIcons = ["agriculture", "warehouse", "storefront", "local_shipping"];

  return (
    <div className="pt-[88px] pb-4 flex-1 flex flex-col px-lg py-md gap-md overflow-y-auto h-full">
      <div className="flex gap-md h-full min-h-0">

        <div className="flex-1 flex flex-col gap-md min-w-0 overflow-y-auto pr-xs">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-sm">
            <div>
              <h1 className="text-[26px] font-bold text-on-surface leading-tight tracking-tight">Global Supply Network</h1>
              <p className="text-[12px] text-on-surface-variant mt-[2px] leading-snug">
                Live visual telemetry of all active supply nodes<br className="hidden sm:block" /> and edge connections.
              </p>
            </div>
            <div className="flex gap-[6px] shrink-0 font-mono text-[11px] font-bold tracking-wider">
              <div className="bg-surface-container border border-outline-variant/30 rounded px-[10px] py-[6px] flex flex-col items-start">
                <span className="text-on-surface-variant font-normal text-[9px] uppercase tracking-widest">Operational:</span>
                <span className="text-primary text-[13px]">{statusCounts.operational}</span>
              </div>
              <div className="bg-surface-container border border-outline-variant/30 rounded px-[10px] py-[6px] flex flex-col items-start">
                <span className="text-on-surface-variant font-normal text-[9px] uppercase tracking-widest">At-Risk:</span>
                <span className="text-secondary text-[13px]">{statusCounts.at_risk}</span>
              </div>
              <div className="bg-surface-container border border-outline-variant/30 rounded px-[10px] py-[6px] flex flex-col items-start">
                <span className="text-on-surface-variant font-normal text-[9px] uppercase tracking-widest">Blocked:</span>
                <span className="text-error text-[13px]">{statusCounts.blocked}</span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-md">
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

            <div className="glass-panel px-md py-[10px] rounded-xl flex flex-col justify-between min-h-[80px]">
              <div className="flex justify-between items-center">
                <span className="text-[11px] text-on-surface-variant font-medium">Supply-Demand Gap</span>
                <span className="material-symbols-outlined text-error text-[17px]">query_stats</span>
              </div>
              <div>
                <span className="text-[26px] font-bold text-error font-mono leading-none">{supplyGap}%</span>
                <div className="w-full h-[3px] bg-surface-variant rounded-full mt-[6px] overflow-hidden">
                  <div className="bg-error h-full rounded-full" style={{ width: `${Math.min(supplyGap * 3, 100)}%` }}></div>
                </div>
              </div>
            </div>
          </div>

          <div className="glass-panel rounded-xl p-md flex flex-col">
            <div className="flex items-center justify-between mb-md">
              <h3 className="text-[10px] font-bold uppercase tracking-[0.18em] text-on-surface-variant font-mono">Active Topology</h3>
              <div className="flex gap-md font-mono text-[10px] font-medium text-on-surface-variant">
                <span className="flex items-center gap-[5px]"><span className="w-[7px] h-[7px] rounded-full bg-primary inline-block"></span>Farms</span>
                <span className="flex items-center gap-[5px]"><span className="w-[7px] h-[7px] rounded-full bg-secondary inline-block"></span>Hubs</span>
                <span className="flex items-center gap-[5px]"><span className="w-[7px] h-[7px] rounded-full bg-on-surface-variant/40 inline-block"></span>Retail</span>
              </div>
            </div>

            <div className="space-y-[6px]">
              {[0, 1].map((row) => (
                <div key={row} className="flex gap-[6px]">
                  {Array.from({ length: TOPOLOGY_COLS }).map((_, col) => {
                    const nodeIdx = row * TOPOLOGY_COLS + col;
                    const node = gridNodes[nodeIdx];
                    if (node && nodeIdx < 4) {
                      const isSelected = selectedNode?.id === node.id;
                      return (
                        <button
                          key={node.id}
                          onClick={() => handleSelectNode(node)}
                          className={`relative flex-1 aspect-square glass-panel flex items-center justify-center rounded transition-all border ${
                            isSelected ? "border-primary bg-primary/10" : "border-outline-variant/25 hover:border-primary/50"
                          }`}
                        >
                          <span className={`material-symbols-outlined text-[16px] ${getNodeIconColor(node.status)}`}>
                            {getNodeIcon(node.type)}
                          </span>
                          <span className={`absolute -top-[3px] -right-[3px] w-[8px] h-[8px] rounded-full ${getStatusDot(node.status)}`}></span>
                        </button>
                      );
                    }
                    return (
                      <div
                        key={`filler-${row}-${col}`}
                        className="relative flex-1 aspect-square glass-panel flex items-center justify-center rounded border border-outline-variant/15 opacity-35"
                      >
                        <span className="material-symbols-outlined text-on-surface-variant/60 text-[15px]">
                          {fillerIcons[nodeIdx % 4]}
                        </span>
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          </div>

          <div className="glass-panel rounded-xl p-md flex flex-col" style={{ minHeight: "220px" }}>
            <div className="flex justify-between items-center mb-sm">
              <h3 className="text-[10px] font-bold uppercase tracking-[0.18em] text-on-surface-variant font-mono">Sourcing Flow Graph</h3>
              <span className="text-[10px] text-primary bg-primary/10 border border-primary/25 px-[10px] py-[4px] rounded font-mono font-bold">
                Real-time Optimization
              </span>
            </div>
            <div className="flex-1 relative flex items-center justify-center">
              <svg className="absolute inset-0 w-full h-full" viewBox="0 0 600 160" preserveAspectRatio="xMidYMid meet">
                <path d="M 140 42 Q 300 42 460 42" fill="none" stroke="rgba(78,222,163,0.25)" strokeDasharray="6 4" strokeWidth="1.5" />
                <path d="M 140 42 Q 300 120 460 118" fill="none" stroke="rgba(78,222,163,0.5)" strokeWidth="1.5" />
                <path d="M 140 118 Q 300 42 460 42" fill="none" stroke="rgba(78,222,163,0.5)" strokeWidth="1.5" />
                <path d="M 140 118 Q 300 118 460 118" fill="none" stroke="rgba(78,222,163,0.25)" strokeDasharray="6 4" strokeWidth="1.5" />
              </svg>
              <div className="absolute left-[18%] flex flex-col gap-[40px]">
                {[0, 1].map((i) => (
                  <div key={i} className="w-9 h-9 rounded-full border border-primary/50 bg-surface-container flex items-center justify-center">
                    <span className="material-symbols-outlined text-primary text-[17px]">psychology</span>
                  </div>
                ))}
              </div>
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

        {showDetail && selectedNode && (
          <div className="w-[260px] shrink-0 flex flex-col">
            <div className="glass-panel rounded-xl flex flex-col overflow-hidden border-outline-variant/20 h-full">
              <div className="px-md pt-md pb-sm flex items-start justify-between">
                <div>
                  <h2 className="text-[18px] font-bold text-on-surface leading-tight">{selectedNode.name}</h2>
                  <span className="inline-block mt-[5px] text-[10px] bg-primary/15 text-primary border border-primary/25 px-[8px] py-[3px] rounded font-mono font-semibold tracking-wide">
                    {selectedNode.agent}
                  </span>
                </div>
                <button onClick={() => setShowDetail(false)} className="text-on-surface-variant hover:text-on-surface transition-colors mt-1" aria-label="Close">
                  <span className="material-symbols-outlined text-[18px]">close</span>
                </button>
              </div>

              <div className="px-md">
                <div className="relative w-full rounded-lg overflow-hidden border border-outline-variant/20" style={{ aspectRatio: "16/9" }}>
                  <Image fill className="object-cover" alt={selectedNode.name} src={selectedNode.image} sizes="100vw" />
                </div>
              </div>

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

              <div className="px-md pb-sm">
                <h3 className="text-[9px] font-bold uppercase tracking-[0.18em] text-on-surface-variant mb-[8px] font-mono">Connected Logistics</h3>
                <div className="space-y-[6px]">
                  {selectedNode.connections.length > 0 ? (
                    selectedNode.connections.map((c, idx) => (
                      <div key={idx} className="flex items-center gap-[10px] p-[8px] bg-surface-container rounded-lg border border-outline-variant/15 hover:border-outline-variant/30 transition-colors">
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

              <div className="flex-1"></div>

              <div className="px-md pb-md pt-sm border-t border-outline-variant/20">
                {projectionDone && projectionMessage && (
                  <p className="text-[10px] text-primary font-mono mb-[8px] leading-snug">{projectionMessage}</p>
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
