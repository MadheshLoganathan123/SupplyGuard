"use client";

/**
 * Full-screen animated background — dot grid + floating orbs.
 * Rendered behind the card on both auth pages.
 */
export default function AuthBackground() {
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden bg-background">
      {/* Dot grid */}
      <div
        className="absolute inset-0 opacity-40"
        style={{
          backgroundImage:
            "radial-gradient(rgba(78,222,163,0.15) 1px, transparent 1px)",
          backgroundSize: "28px 28px",
        }}
      />
      {/* Glow orbs */}
      <div className="absolute -top-32 -left-32 w-[480px] h-[480px] bg-primary/10 rounded-full blur-[120px] animate-pulse" />
      <div className="absolute top-1/2 -right-40 w-[360px] h-[360px] bg-secondary/8 rounded-full blur-[100px] animate-pulse [animation-delay:2s]" />
      <div className="absolute -bottom-40 left-1/4 w-[320px] h-[320px] bg-primary/6 rounded-full blur-[90px] animate-pulse [animation-delay:4s]" />
      {/* Faint horizontal scan line */}
      <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-primary/20 to-transparent" />
    </div>
  );
}
