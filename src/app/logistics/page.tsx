"use client";

import Image from "next/image";
import { useState } from "react";

interface Shipment {
  id: string;
  origin: string;
  destination: string;
  status: "IN-TRANSIT" | "REROUTED" | "PERIMETER DROP";
  agent: string;
}

interface Path {
  name: string;
  dist: string;
  desc: string;
  efficiency: number;
  color: "primary" | "secondary";
}

const initialShipments: Shipment[] = [
  { id: "#SS-4921", origin: "Valley Farms Hub", destination: "Midtown Pantry", status: "IN-TRANSIT", agent: "Unit: 49-Alpha" },
  { id: "#SS-4922", origin: "Central Wholesale", destination: "Independent Grocer 4", status: "REROUTED", agent: "Logi-Truck-9" },
  { id: "#SS-4925", origin: "Vertical Fields G3", destination: "Perimeter Drop-A", status: "PERIMETER DROP", agent: "Gig-X71" },
  { id: "#SS-4928", origin: "Hydro-Collective", destination: "Pantry Hub South", status: "IN-TRANSIT", agent: "Cycle-Unit-12" },
];

const initialPaths: Path[] = [
  { name: "PATH A: EXPRESS", dist: "8.2km", desc: "Prioritizes speed via Perimeter Bypass.", efficiency: 85, color: "primary" },
  { name: "PATH B: SECURE", dist: "12.4km", desc: "Maximum threat avoidance. 0 risk.", efficiency: 98, color: "secondary" },
];

export default function Logistics() {
  const [shipments, setShipments] = useState<Shipment[]>(initialShipments);
  const [paths, setPaths] = useState<Path[]>(initialPaths);
  const [simulating, setSimulating] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Add shipment form
  const [newOrigin, setNewOrigin] = useState("");
  const [newDest, setNewDest] = useState("");
  const [newAgent, setNewAgent] = useState("");
  const [newStatus, setNewStatus] = useState<Shipment["status"]>("IN-TRANSIT");

  const handleSimulateNew = () => {
    if (simulating) return;
    setSimulating(true);
    setTimeout(() => {
      const letters = "CDEFGHIJKLMNOP";
      const newPath: Path = {
        name: `PATH ${letters[paths.length - 2]}: DYNAMIC`,
        dist: `${(Math.random() * 8 + 5).toFixed(1)}km`,
        desc: "AI computed alternate route via secondary grid lanes.",
        efficiency: Math.floor(Math.random() * 15 + 82),
        color: "primary",
      };
      setPaths((prev) => [...prev, newPath]);
      setSimulating(false);
    }, 1500);
  };

  const handleAddShipment = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newOrigin || !newDest || !newAgent) return;
    setShipments((prev) => [
      {
        id: `#SS-${Math.floor(Math.random() * 9000 + 1000)}`,
        origin: newOrigin,
        destination: newDest,
        status: newStatus,
        agent: newAgent,
      },
      ...prev,
    ]);
    setIsModalOpen(false);
    setNewOrigin(""); setNewDest(""); setNewAgent("");
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
            <Image
              fill
              className="absolute inset-0 object-cover opacity-15 grayscale z-0"
              alt="Logistics Map"
              src="/images/map_logistics.jpg"
              sizes="100vw"
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
                        <button className="text-on-surface-variant hover:text-on-surface transition-colors flex items-center justify-center">
                          <span className="material-symbols-outlined text-[18px]">more_horiz</span>
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
        <div className="fixed inset-0 z-50 bg-[#0b1326]/70 backdrop-blur-sm flex items-center justify-center p-md animate-in fade-in duration-200">
          <div className="glass-panel w-full max-w-md bg-surface-container/98 p-lg rounded-xl shadow-2xl border-primary/20 animate-in zoom-in-95 duration-200">
            <div className="flex justify-between items-start mb-md">
              <div>
                <h3 className="text-[17px] font-bold text-primary flex items-center gap-sm">
                  <span className="material-symbols-outlined text-[20px]">local_shipping</span>
                  Add New Shipment
                </h3>
                <p className="text-[12px] text-on-surface-variant mt-[3px]">Register dynamic cargo routing in system database.</p>
              </div>
              <button onClick={() => setIsModalOpen(false)} className="text-on-surface-variant hover:text-on-surface transition-colors">
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>
            <form onSubmit={handleAddShipment} className="space-y-md">
              {[
                { label: "Cargo Origin", val: newOrigin, set: setNewOrigin, ph: "e.g. Sector 7 Greenhouse" },
                { label: "Cargo Destination", val: newDest, set: setNewDest, ph: "e.g. Node Delta Clinic" },
              ].map(({ label, val, set, ph }) => (
                <div key={label}>
                  <label className="block text-[10px] font-bold text-on-surface-variant uppercase tracking-wider mb-[4px]">{label}</label>
                  <input
                    type="text" required placeholder={ph}
                    className="w-full bg-background border border-outline-variant/30 rounded-lg px-[12px] py-[8px] text-[13px] focus:ring-1 focus:ring-primary focus:border-primary outline-none text-on-surface"
                    value={val} onChange={(e) => set(e.target.value)}
                  />
                </div>
              ))}
              <div className="grid grid-cols-2 gap-sm">
                <div>
                  <label className="block text-[10px] font-bold text-on-surface-variant uppercase tracking-wider mb-[4px]">Assigned Agent</label>
                  <input
                    type="text" required placeholder="e.g. Gig-D22"
                    className="w-full bg-background border border-outline-variant/30 rounded-lg px-[12px] py-[8px] text-[13px] focus:ring-1 focus:ring-primary focus:border-primary outline-none text-on-surface font-mono"
                    value={newAgent} onChange={(e) => setNewAgent(e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-on-surface-variant uppercase tracking-wider mb-[4px]">Status</label>
                  <select
                    className="w-full bg-background border border-outline-variant/30 rounded-lg px-[10px] py-[8px] text-[13px] focus:ring-1 focus:ring-primary focus:border-primary outline-none text-on-surface font-mono"
                    value={newStatus} onChange={(e) => setNewStatus(e.target.value as Shipment["status"])}
                  >
                    <option value="IN-TRANSIT">IN-TRANSIT</option>
                    <option value="REROUTED">REROUTED</option>
                    <option value="PERIMETER DROP">PERIMETER DROP</option>
                  </select>
                </div>
              </div>
              <button
                type="submit"
                className="w-full bg-primary text-on-primary py-[10px] rounded-lg font-bold hover:brightness-110 transition-all flex justify-center items-center gap-xs font-mono text-[11px] uppercase tracking-widest shadow-lg shadow-primary/20"
              >
                <span className="material-symbols-outlined text-[18px]">add_task</span>
                Register Shipment
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
