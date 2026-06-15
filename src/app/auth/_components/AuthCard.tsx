"use client";

interface AuthCardProps {
  children: React.ReactNode;
}

/**
 * Glassmorphism card wrapper used by both sign-in and sign-up pages.
 */
export default function AuthCard({ children }: AuthCardProps) {
  return (
    <div className="w-full max-w-[420px] bg-surface-container/80 backdrop-blur-2xl border border-outline-variant/30 rounded-2xl shadow-2xl shadow-black/40 p-8 relative overflow-hidden">
      {/* Subtle top-left glow accent */}
      <div className="absolute -top-16 -left-16 w-48 h-48 bg-primary/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-10 -right-10 w-36 h-36 bg-secondary/8 rounded-full blur-2xl pointer-events-none" />
      <div className="relative z-10">{children}</div>
    </div>
  );
}
