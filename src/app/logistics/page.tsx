"use client";

import { useState, useEffect, useCallback } from "react";
import { supabase } from "../../lib/supabaseClient";

interface Shipment {
  id: string;          // shipment_code displayed in the table
  _dbId: string;       // actual UUID from DB used for API calls
  origin: string;
  destination: string;
  status: "IN-TRANSIT" | "REROUTED" | "PERIMETER DROP" | "DELIVERED" | "DELAYED";
  agent: string;
}

const BACKEND_URL = (() => {
  const configured = (process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000").replace(/\/+$/, "");
  return configured.endsWith("/api/v1") ? configured : `${configured}/api/v1`;
})();

interface Path {
  name: string;
  dist: string;
  desc: string;
  efficiency: number;
  color: "primary" | "secondary";
}

const STATIC_PATHS: Path[] = [
  { name: 'PATH A: EXPRESS', dist: '8.2km', desc: 'Prioritizes speed via Perimeter Bypass.', efficiency: 85, color: 'primary' },
  { name: 'PATH B: SECURE', dist: '12.4km', desc: 'Maximum threat avoidance. 0 risk zone.', efficiency: 98, color: 'secondary' },
];

export default function Logistics() {
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [paths, setPaths] = useState<Path[]>(STATIC_PATHS);
  const [agents, setAgents] = useState<string[]>([]);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const loadShipments = useCallback(async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/shipments/?limit=50`, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
      });

      if (!res.ok) {
        console.error("Logistics API error:", await res.text());
        return;
      }

      const data = await res.json();
      setShipments((data ?? []).map((s: Record<string, unknown>) => ({
        id: (s.shipment_code as string) || (s.id as string),
        _dbId: s.id as string,
        origin: s.origin as string,
        destination: s.destination as string,
        status: s.status as Shipment["status"],
        agent: (s.agent as { name?: string } | null)?.name || "Unassigned",
      })));
    } catch (err) {
      console.error("Failed to load shipments:", err);
    }
  }, []);

  const loadAgents = useCallback(async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/agents/?limit=100`);
      if (res.ok) {
        const data = await res.json();
        setAgents((data ?? []).map((a: { name: string }) => a.name));
      }
    } catch (err) {
      console.warn("Failed to load agents:", err);
    }
  }, []);

  useEffect(() => {
    void Promise.resolve().then(() => {
      void loadShipments();
      void loadAgents();
    });

    // Supabase Realtime Subscription
    const channel = supabase
      .channel('shipments-realtime')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'shipments' }, () => {
        loadShipments();
      })
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [loadShipments, loadAgents]);
  const [simulating, setSimulating] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Add shipment form
  const [newOrigin, setNewOrigin] = useState("");
  const [newDest, setNewDest] = useState("");
  const [newAgent, setNewAgent] = useState("");
  const [newStatus, setNewStatus] = useState<Shipment["status"]>("IN-TRANSIT");

  const getAuthHeaders = async () => {
    const { data, error } = await supabase.auth.getSession();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (error) {
      console.warn("Unable to get session token:", error.message);
      return headers;
    }
    const token = data?.session?.access_token;
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
    return headers;
  };

  const parseAgentId = (candidate: string) => {
    const uuidRegex = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;
    return uuidRegex.test(candidate.trim()) ? candidate.trim() : undefined;
  };

  const handleSimulateNew = async () => {
    if (simulating) return;
    setSimulating(true);
    try {
      const res = await fetch(`${BACKEND_URL}/routing/ai/reroute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ area: "Sector 12" }),
      });
      if (res.ok) {
        const data = await res.json();
        setPaths((prev) => [...prev, ...data.paths]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSimulating(false);
    }
  };

  const handleAddShipment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newOrigin || !newDest || !newAgent) return;

    setSubmitError(null);
    setIsSubmitting(true);

    const payload: Record<string, unknown> = {
      shipment_code: `#SS-${Math.floor(Math.random() * 9000 + 1000)}`,
      origin: newOrigin,
      destination: newDest,
      status: newStatus,
      agent_name: newAgent.trim(),
    };

    const agentId = parseAgentId(newAgent);
    if (agentId) {
      payload.agent_id = agentId;
      delete payload.agent_name;
    }

    const headers = await getAuthHeaders();

    try {
      const res = await fetch(`${BACKEND_URL}/shipments/`, {
        method: "POST",
        headers,
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        setIsModalOpen(false);
        setNewOrigin("");
        setNewDest("");
        setNewAgent("");
        await loadShipments();
        return;
      }

      const errText = await res.text();
      if (res.status === 401) {
        console.warn("Backend auth required, falling back to direct Supabase insert.");
      } else {
        setSubmitError(errText || `Failed to create shipment (${res.status})`);
        return;
      }
    } catch (err) {
      console.error("Shipment creation failed:", err);
      setSubmitError("Could not reach backend. Trying Supabase fallback...");
    } finally {
      setIsSubmitting(false);
    }

    const { error } = await supabase.from('shipments').insert({
      shipment_code: payload.shipment_code,
      origin: payload.origin,
      destination: payload.destination,
      status: payload.status,
      agent_id: agentId ?? null,
    });

    if (error) {
      setSubmitError(error.message);
    } else {
      setIsModalOpen(false);
      setNewOrigin('');
      setNewDest('');
      setNewAgent('');
      await loadShipments();
    }
  };

  const handleTriggerReroute = async (dbId: string) => {
    const headers = await getAuthHeaders();
    let success = false;

    try {
      const res = await fetch(`${BACKEND_URL}/shipments/${dbId}/trigger-reroute`, {
        method: "POST",
        headers,
      });

      if (res.ok) {
        success = true;
      } else {
        console.warn("Reroute API returned", res.status, await res.text());
      }
    } catch (err) {
      console.error('Reroute API error:', err);
    }

    if (!success) {
      const { error } = await supabase
        .from('shipments')
        .update({ status: 'REROUTED' })
        .eq('id', dbId);
      if (error) {
        console.error('Reroute fallback failed:', error.message);
      }
    }

    loadShipments();
  };

  const statusStyle = (s: Shipment["status"]) => {
    if (s === "IN-TRANSIT") return "bg-primary/15 text-primary border-primary/25";
    if (s === "REROUTED") return "bg-secondary/15 text-secondary border-secondary/25";
    return "bg-surface-variant text-on-surface-variant border-outline-variant/40";
  };

  return (
    <div className="pt-[88px] pb-4 flex-1 flex flex-col px-lg py-md gap-md overflow-y-auto h-full">

      {/* ── Page Header ── */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-sm shrink-0">
        <div>
          <h1 className="text-[26px] font-bold text-on-surface leading-tight tracking-tight">Logistics Orchestration</h1>
          <p className="text-[12px] text-on-surface-variant mt-[3px]">Real-time status of multi-modal delivery agents and supply chains.</p>
        </div>
        <div className="flex gap-[8px] shrink-0">
          <span className="inline-flex items-center gap-[6px] px-[12px] py-[6px] bg-surface-container border border-outline-variant/30 rounded-full text-[11px] text-on-surface font-medium">
            <span className="w-[7px] h-[7px] rounded-full bg-primary pulse-emerald shrink-0"></span>
            1,242 Active Agents
          </span>
          <span className="inline-flex items-center gap-[6px] px-[12px] py-[6px] bg-surface-container border border-outline-variant/30 rounded-full text-[11px] text-on-surface font-medium">
            <span className="w-[7px] h-[7px] rounded-full bg-secondary shrink-0"></span>
            14 Reroutes Pending
          </span>
        </div>
      </div>

      {/* ── Main Layout ── */}
      <div className="flex gap-md flex-1 min-h-0">

        {/* ── Left Column: Fleet Overview + Map ── */}
        <div className="w-[260px] shrink-0 flex flex-col gap-md overflow-y-auto">
          <p className="text-[9px] font-bold uppercase tracking-[0.22em] text-primary/70 font-mono shrink-0">Fleet Overview</p>

          {/* Gig-Drivers */}
          <div className="bg-surface-container border border-outline-variant/25 rounded-xl p-[14px] hover:border-primary/40 transition-colors shrink-0">
            <div className="flex justify-between items-start mb-[10px]">
              <div className="flex items-center gap-[10px]">
                <div className="w-9 h-9 rounded-lg bg-surface-container-high flex items-center justify-center text-primary shrink-0">
                  <span className="material-symbols-outlined text-[20px]">directions_car</span>
                </div>
                <div>
                  <p className="text-[13px] font-bold text-on-surface leading-tight">Gig-Drivers</p>
                  <p className="text-[11px] text-on-surface-variant">Last Mile Delivery</p>
                </div>
              </div>
              <span className="text-[24px] font-bold text-primary font-mono leading-none">842</span>
            </div>
            <div className="w-full h-[3px] bg-surface-container-highest rounded-full overflow-hidden">
              <div className="bg-primary h-full w-[92%] rounded-full"></div>
            </div>
            <div className="flex justify-between mt-[6px] font-mono text-[10px]">
              <span className="text-on-surface-variant">92% Utilization</span>
              <span className="text-primary font-bold">+4.2%</span>
            </div>
          </div>

          {/* Trucking Co-ops */}
          <div className="bg-surface-container border border-outline-variant/25 rounded-xl p-[14px] hover:border-secondary/40 transition-colors shrink-0">
            <div className="flex justify-between items-start mb-[10px]">
              <div className="flex items-center gap-[10px]">
                <div className="w-9 h-9 rounded-lg bg-surface-container-high flex items-center justify-center text-secondary shrink-0">
                  <span className="material-symbols-outlined text-[20px]">local_shipping</span>
                </div>
                <div>
                  <p className="text-[13px] font-bold text-on-surface leading-tight">Trucking Co-ops</p>
                  <p className="text-[11px] text-on-surface-variant">Wholesale Transport</p>
                </div>
              </div>
              <span className="text-[24px] font-bold text-secondary font-mono leading-none">156</span>
            </div>
            <div className="w-full h-[3px] bg-surface-container-highest rounded-full overflow-hidden">
              <div className="bg-secondary h-full w-[78%] rounded-full"></div>
            </div>
            <div className="flex justify-between mt-[6px] font-mono text-[10px]">
              <span className="text-on-surface-variant">78% Utilization</span>
              <span className="text-secondary font-bold">At Capacity</span>
            </div>
          </div>

          {/* Cargo Bike Units */}
          <div className="bg-surface-container border border-outline-variant/25 rounded-xl p-[14px] hover:border-primary/40 transition-colors shrink-0">
            <div className="flex justify-between items-start mb-[10px]">
              <div className="flex items-center gap-[10px]">
                <div className="w-9 h-9 rounded-lg bg-surface-container-high flex items-center justify-center text-primary shrink-0">
                  <span className="material-symbols-outlined text-[20px]">pedal_bike</span>
                </div>
                <div>
                  <p className="text-[13px] font-bold text-on-surface leading-tight">Cargo Bike Units</p>
                  <p className="text-[11px] text-on-surface-variant">Urban Density Core</p>
                </div>
              </div>
              <span className="text-[24px] font-bold text-primary font-mono leading-none">244</span>
            </div>
            <div className="w-full h-[3px] bg-surface-container-highest rounded-full overflow-hidden">
              <div className="bg-primary h-full w-[65%] rounded-full"></div>
            </div>
            <div className="flex justify-between mt-[6px] font-mono text-[10px]">
              <span className="text-on-surface-variant">65% Utilization</span>
              <span className="text-primary font-bold">Available</span>
            </div>
          </div>

          {/* L-Grid Map Widget */}
          <div className="flex-1 min-h-[180px] bg-surface-container border border-outline-variant/25 rounded-xl overflow-hidden relative">
            {/* Dark map base */}
            <div className="absolute inset-0 bg-[#0b1326] z-0"></div>
            <div
              className="absolute inset-0 opacity-30 z-0"
              style={{
                background:
                  "radial-gradient(circle at 50% 50%, rgba(78,222,163,0.2), transparent 60%), linear-gradient(180deg, #0b1326 0%, #152238 100%)",
              }}
            />
            {/* Network node SVG */}
            <svg className="absolute inset-0 w-full h-full z-10 pointer-events-none" viewBox="0 0 260 200" preserveAspectRatio="xMidYMid slice">
              <g stroke="rgba(255,255,255,0.12)" strokeWidth="0.8" fill="none">
                <line x1="40"  y1="60"  x2="100" y2="40"/>
                <line x1="100" y1="40"  x2="160" y2="70"/>
                <line x1="160" y1="70"  x2="220" y2="50"/>
                <line x1="40"  y1="60"  x2="80"  y2="110"/>
                <line x1="80"  y1="110" x2="140" y2="130"/>
                <line x1="140" y1="130" x2="200" y2="110"/>
                <line x1="200" y1="110" x2="220" y2="50"/>
                <line x1="100" y1="40"  x2="80"  y2="110"/>
                <line x1="160" y1="70"  x2="140" y2="130"/>
                <line x1="80"  y1="110" x2="60"  y2="160"/>
                <line x1="140" y1="130" x2="130" y2="170"/>
                <line x1="200" y1="110" x2="210" y2="160"/>
                <line x1="40"  y1="60"  x2="30"  y2="120"/>
                <line x1="30"  y1="120" x2="60"  y2="160"/>
              </g>
              <g fill="rgba(255,255,255,0.25)">
                {[[40,60],[100,40],[160,70],[220,50],[80,110],[140,130],[200,110],[60,160],[130,170],[210,160],[30,120]].map(([x,y],i) => (
                  <circle key={i} cx={x} cy={y} r="2.5"/>
                ))}
              </g>
            </svg>
            {/* Overlay */}
            <div className="absolute inset-0 z-20 flex flex-col p-[10px]">
              <div className="flex justify-between items-start">
                <span className="bg-surface/80 backdrop-blur-sm px-[8px] py-[4px] rounded text-[10px] font-bold border border-outline-variant/30 font-mono text-on-surface">L-GRID ACTIVE</span>
                <button className="bg-surface-container-high/80 p-[5px] rounded-lg backdrop-blur-sm border border-outline-variant/30 text-on-surface-variant hover:text-on-surface transition-colors">
                  <span className="material-symbols-outlined text-[14px]">fullscreen</span>
                </button>
              </div>
              <div className="mt-auto">
                <p className="text-[11px] font-bold text-primary uppercase font-mono tracking-wide">Sector 07: High Traffic</p>
                <p className="text-[10px] text-on-surface-variant">42 Agents currently in sector</p>
              </div>
            </div>
          </div>
        </div>

        {/* ── Right Column: Reroute Panel + Shipments Table ── */}
        <div className="flex-1 flex flex-col gap-md min-w-0 overflow-y-auto">

          {/* AI Reroute Analysis */}
          <div className="glass-panel rounded-xl p-md relative overflow-hidden shrink-0 border-primary/15">
            <div className="absolute -right-10 -top-10 w-40 h-40 bg-primary/5 blur-3xl rounded-full pointer-events-none"></div>

            {/* Header row */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-start gap-md mb-md">
              <div>
                <h3 className="text-[17px] font-bold text-on-surface flex items-center gap-[8px] leading-tight">
                  <span className="material-symbols-outlined text-primary text-[20px]">psychology</span>
                  AI Reroute Analysis
                </h3>
                <p className="text-[11px] text-on-surface-variant mt-[3px]">Alternative Paths Calculated for Sector 12 Disruptions</p>
              </div>
              <div className="flex gap-[24px] font-mono shrink-0">
                <div className="text-right">
                  <p className="text-[9px] text-on-surface-variant uppercase tracking-widest font-semibold">Efficiency<br/>Gain</p>
                  <p className="text-[20px] font-bold text-primary leading-tight mt-[2px]">+18.5%</p>
                </div>
                <div className="text-right">
                  <p className="text-[9px] text-on-surface-variant uppercase tracking-widest font-semibold">Threat<br/>Avoided</p>
                  <p className="text-[20px] font-bold text-secondary leading-tight mt-[2px]">High</p>
                </div>
              </div>
            </div>

            {/* Path cards */}
            <div className="flex gap-md flex-wrap">
              {paths.map((p, idx) => (
                <div key={idx} className="flex-1 min-w-[160px] bg-surface-container-lowest/60 border border-outline-variant/20 rounded-lg p-[12px]">
                  <div className="flex justify-between items-center mb-[6px]">
                    <span className={`text-[10px] font-bold font-mono ${p.color === "primary" ? "text-primary" : "text-secondary"}`}>{p.name}</span>
                    <span className="text-[10px] text-on-surface-variant font-mono">{p.dist}</span>
                  </div>
                  <p className="text-[12px] text-on-surface leading-relaxed mb-[10px]">{p.desc}</p>
                  <div className="flex items-center gap-[6px]">
                    <div className="flex-1 h-[3px] bg-surface-variant rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${p.color === "primary" ? "bg-primary" : "bg-secondary"}`}
                        style={{ width: `${p.efficiency}%` }}
                      ></div>
                    </div>
                    <span className="text-[10px] font-mono font-bold text-on-surface-variant">{p.efficiency}%</span>
                  </div>
                </div>
              ))}

              {/* Simulate New */}
              <button
                onClick={handleSimulateNew}
                disabled={simulating}
                className="flex-none w-[100px] bg-surface-container-lowest/60 border border-dashed border-outline-variant/40 rounded-lg p-[12px] flex flex-col items-center justify-center gap-[6px] text-on-surface-variant hover:text-primary hover:border-primary/50 transition-all disabled:opacity-60"
              >
                <span className={`material-symbols-outlined text-[22px] ${simulating ? "animate-spin text-primary" : ""}`}>
                  {simulating ? "autorenew" : "add_circle"}
                </span>
                <span className="text-[9px] font-bold font-mono uppercase tracking-widest text-center leading-tight">
                  {simulating ? "Calculating..." : "Simulate New"}
                </span>
              </button>
            </div>
          </div>

          {/* Active Shipments Table */}
          <div className="glass-panel rounded-xl overflow-hidden flex-1 flex flex-col min-h-0">
            {/* Table header */}
            <div className="px-md py-[10px] border-b border-outline-variant/25 flex justify-between items-center shrink-0">
              <h3 className="text-[14px] font-bold text-on-surface">Active Shipments</h3>
              <div className="flex gap-[6px]">
                <button className="text-on-surface-variant hover:text-on-surface transition-colors p-[4px]">
                  <span className="material-symbols-outlined text-[18px]">filter_alt</span>
                </button>
                <button className="text-on-surface-variant hover:text-on-surface transition-colors p-[4px]">
                  <span className="material-symbols-outlined text-[18px]">download</span>
                </button>
              </div>
            </div>

            {/* Table */}
            <div className="overflow-x-auto flex-1">
              <table className="w-full text-left border-collapse">
                <thead className="border-b border-outline-variant/20">
                  <tr>
                    {["Shipment ID", "Origin", "Destination", "Status", "Agent", "Action"].map((h) => (
                      <th key={h} className="px-md py-[9px] text-[9px] font-bold uppercase tracking-[0.15em] text-on-surface-variant whitespace-nowrap">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-outline-variant/10">
                  {shipments.map((ship) => (
                    <tr key={ship.id} className="hover:bg-surface-variant/15 transition-colors">
                      <td className="px-md py-[12px] font-mono text-[13px] text-primary font-bold whitespace-nowrap">{ship.id}</td>
                      <td className="px-md py-[12px] text-[13px] text-on-surface">{ship.origin}</td>
                      <td className="px-md py-[12px] text-[13px] text-on-surface">{ship.destination}</td>
                      <td className="px-md py-[12px]">
                        <span className={`inline-flex items-center px-[8px] py-[3px] rounded text-[9px] font-bold border font-mono tracking-wide ${statusStyle(ship.status)}`}>
                          {ship.status}
                        </span>
                      </td>
                      <td className="px-md py-[12px] text-[12px] text-on-surface-variant font-mono whitespace-nowrap">{ship.agent}</td>
                      <td className="px-md py-[12px]">
                        <button 
                          onClick={() => handleTriggerReroute(ship._dbId)}
                          title="Trigger AI Reroute"
                          className="text-on-surface-variant hover:text-primary transition-colors flex items-center justify-center text-[10px] border border-outline-variant/30 px-2 py-1 rounded font-bold"
                        >
                          REROUTE
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* View Full Manifest */}
            <div className="px-md py-[10px] border-t border-outline-variant/20 text-center shrink-0">
              <button className="text-[12px] font-bold text-primary hover:underline underline-offset-4 font-mono">
                View Full Manifest ({shipments.length + 44} Active)
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* FAB */}
      <div className="fixed bottom-[24px] right-[24px] z-40">
        <button
          onClick={() => setIsModalOpen(true)}
          className="w-[52px] h-[52px] bg-primary text-on-primary rounded-full shadow-2xl shadow-primary/30 flex items-center justify-center hover:scale-110 active:scale-95 transition-all"
        >
          <span className="material-symbols-outlined text-[24px] font-bold">add</span>
        </button>
      </div>

      {/* Add Shipment Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-[#0b1326]/80 backdrop-blur-md flex items-center justify-center p-md animate-in fade-in duration-300">
          <div className="glass-panel w-[440px] max-w-[95vw] p-xl rounded-3xl shadow-[0_0_40px_-10px_rgba(78,222,163,0.3)] border border-primary/20 animate-in zoom-in-95 duration-300 relative overflow-hidden">
            {/* Decorative background glow */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-primary/10 blur-3xl rounded-full pointer-events-none -translate-y-1/2 translate-x-1/3"></div>
            
            <div className="flex justify-between items-start mb-lg relative z-10">
              <div>
                <h3 className="text-[19px] font-bold text-on-surface flex items-center gap-[8px] leading-tight">
                  <div className="w-8 h-8 rounded-lg bg-primary/15 flex items-center justify-center">
                    <span className="material-symbols-outlined text-[18px] text-primary">add_box</span>
                  </div>
                  New Shipment
                </h3>
                <p className="text-[12px] text-on-surface-variant mt-[6px]">Register dynamic cargo routing in the logistics network.</p>
              </div>
              <button onClick={() => setIsModalOpen(false)} className="w-8 h-8 rounded-full bg-surface-container hover:bg-surface-container-high flex items-center justify-center text-on-surface-variant hover:text-on-surface transition-colors">
                <span className="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>
            
            <form onSubmit={handleAddShipment} className="space-y-md relative z-10">
              {[
                { label: "Cargo Origin", val: newOrigin, set: setNewOrigin, ph: "e.g. Sector 7 Greenhouse", icon: "location_on" },
                { label: "Cargo Destination", val: newDest, set: setNewDest, ph: "e.g. Node Delta Clinic", icon: "flag" },
              ].map(({ label, val, set, ph, icon }) => (
                <div key={label}>
                  <label className="block text-[10px] font-bold text-on-surface-variant uppercase tracking-widest mb-[6px]">{label}</label>
                  <div className="relative">
                    <span className="absolute left-[12px] top-1/2 -translate-y-1/2 material-symbols-outlined text-[18px] text-on-surface-variant/60">{icon}</span>
                    <input
                      type="text" required placeholder={ph}
                      className="w-full bg-surface-container-low border border-outline-variant/30 rounded-xl pl-[38px] pr-[12px] py-[10px] text-[13px] focus:ring-2 focus:ring-primary/50 focus:border-primary outline-none text-on-surface transition-all placeholder:text-on-surface-variant/40"
                      value={val} onChange={(e) => set(e.target.value)}
                    />
                  </div>
                </div>
              ))}
              <div className="grid grid-cols-2 gap-md">
                <div>
                  <label className="block text-[10px] font-bold text-on-surface-variant uppercase tracking-widest mb-[6px]">Assigned Agent</label>
                  <div className="relative">
                    <span className="absolute left-[12px] top-1/2 -translate-y-1/2 material-symbols-outlined text-[18px] text-on-surface-variant/60">smart_toy</span>
                    <input
                      type="text" required placeholder="e.g. Gig-D22" list="agent-options"
                      className="w-full bg-surface-container-low border border-outline-variant/30 rounded-xl pl-[38px] pr-[12px] py-[10px] text-[13px] focus:ring-2 focus:ring-primary/50 focus:border-primary outline-none text-on-surface font-mono transition-all placeholder:text-on-surface-variant/40"
                      value={newAgent} onChange={(e) => setNewAgent(e.target.value)}
                    />
                    <datalist id="agent-options">
                      {agents.map((name) => (
                        <option key={name} value={name} />
                      ))}
                    </datalist>
                  </div>
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-on-surface-variant uppercase tracking-widest mb-[6px]">Status</label>
                  <div className="relative">
                    <select
                      className="w-full bg-surface-container-low border border-outline-variant/30 rounded-xl pl-[12px] pr-[30px] py-[10px] text-[13px] focus:ring-2 focus:ring-primary/50 focus:border-primary outline-none text-on-surface font-mono transition-all appearance-none cursor-pointer"
                      value={newStatus} onChange={(e) => setNewStatus(e.target.value as Shipment["status"])}
                    >
                      <option value="IN-TRANSIT" className="bg-surface-container text-on-surface">IN-TRANSIT</option>
                      <option value="REROUTED" className="bg-surface-container text-on-surface">REROUTED</option>
                      <option value="PERIMETER DROP" className="bg-surface-container text-on-surface">PERIMETER DROP</option>
                    </select>
                    <span className="absolute right-[10px] top-1/2 -translate-y-1/2 material-symbols-outlined text-[18px] text-on-surface-variant/60 pointer-events-none">expand_more</span>
                  </div>
                </div>
              </div>
              {submitError && (
                <p className="text-[12px] text-error font-mono">{submitError}</p>
              )}
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full mt-2 bg-primary text-on-primary py-[12px] rounded-xl font-bold hover:brightness-110 active:scale-[0.98] transition-all flex justify-center items-center gap-[8px] font-mono text-[12px] uppercase tracking-widest shadow-lg shadow-primary/20 disabled:opacity-60"
              >
                <span className="material-symbols-outlined text-[20px]">send</span>
                {isSubmitting ? "Dispatching..." : "Dispatch Shipment"}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
