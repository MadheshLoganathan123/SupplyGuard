"use client";

interface SocialButtonProps {
  onClick: () => void;
  loading?: boolean;
  children: React.ReactNode;
}

export default function SocialButton({ onClick, loading, children }: SocialButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={loading}
      className="w-full flex items-center justify-center gap-3 px-4 py-[11px] bg-surface-container border border-outline-variant/40 rounded-xl text-[13px] font-medium text-on-surface hover:border-primary/50 hover:bg-surface-container-high transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
    >
      {children}
    </button>
  );
}
