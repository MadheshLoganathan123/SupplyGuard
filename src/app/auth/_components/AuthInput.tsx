"use client";

import { useState } from "react";

interface AuthInputProps {
  id: string;
  label: string;
  type?: string;
  value: string;
  onChange: (v: string) => void;
  autoComplete?: string;
  required?: boolean;
  icon?: string; // material symbol name
}

export default function AuthInput({
  id,
  label,
  type = "text",
  value,
  onChange,
  autoComplete,
  required,
  icon,
}: AuthInputProps) {
  const [showPassword, setShowPassword] = useState(false);
  const isPassword = type === "password";
  const inputType = isPassword ? (showPassword ? "text" : "password") : type;
  const filled = value.length > 0;

  return (
    <div className="relative group">
      {/* Icon prefix */}
      {icon && (
        <span className="material-symbols-outlined absolute left-[14px] top-1/2 -translate-y-1/2 text-[18px] text-on-surface-variant/60 group-focus-within:text-primary transition-colors pointer-events-none z-10">
          {icon}
        </span>
      )}

      <input
        id={id}
        type={inputType}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        autoComplete={autoComplete}
        required={required}
        placeholder=" "
        className={`
          peer w-full bg-surface-container border border-outline-variant/40 rounded-xl
          text-[14px] text-on-surface outline-none transition-all duration-200
          focus:border-primary focus:ring-2 focus:ring-primary/20
          placeholder-transparent
          ${icon ? "pl-[42px]" : "pl-[16px]"}
          ${isPassword ? "pr-[44px]" : "pr-[16px]"}
          pt-[22px] pb-[8px]
        `}
      />

      {/* Floating label */}
      <label
        htmlFor={id}
        className={`
          absolute left-0 transition-all duration-200 pointer-events-none
          ${icon ? "left-[42px]" : "left-[16px]"}
          peer-placeholder-shown:top-[50%] peer-placeholder-shown:-translate-y-1/2
          peer-placeholder-shown:text-[14px] peer-placeholder-shown:text-on-surface-variant/60
          peer-focus:top-[8px] peer-focus:translate-y-0
          peer-focus:text-[11px] peer-focus:text-primary
          ${filled
            ? "top-[8px] translate-y-0 text-[11px] text-on-surface-variant/70"
            : ""
          }
          font-medium tracking-wide
        `}
      >
        {label}
      </label>

      {/* Password toggle */}
      {isPassword && (
        <button
          type="button"
          tabIndex={-1}
          onClick={() => setShowPassword((p) => !p)}
          className="absolute right-[14px] top-1/2 -translate-y-1/2 text-on-surface-variant/50 hover:text-primary transition-colors"
          aria-label={showPassword ? "Hide password" : "Show password"}
        >
          <span className="material-symbols-outlined text-[18px]">
            {showPassword ? "visibility_off" : "visibility"}
          </span>
        </button>
      )}
    </div>
  );
}
