"use client";

import Link from "next/link";
import { useState } from "react";
import { supabase, withRetry } from "../../../lib/supabaseClient";
import AuthBackground from "../_components/AuthBackground";
import AuthCard from "../_components/AuthCard";
import AuthInput from "../_components/AuthInput";
import SocialButton from "../_components/SocialButton";

const ROLES = [
  { value: "Farmer",          icon: "agriculture",    label: "Farmer" },
  { value: "Driver",          icon: "local_shipping", label: "Driver" },
  { value: "Store Owner",     icon: "storefront",     label: "Store Owner" },
  { value: "Pantry Manager",  icon: "inventory_2",    label: "Pantry Mgr" },
  { value: "Admin",           icon: "admin_panel_settings", label: "Admin" },
];

export default function SignUpPage() {
  const [fullName, setFullName] = useState("");
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole]         = useState("Farmer");

  const [error, setError]     = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);

  /* Password strength */
  const strength = (() => {
    if (!password) return 0;
    let s = 0;
    if (password.length >= 8)        s++;
    if (/[A-Z]/.test(password))      s++;
    if (/[0-9]/.test(password))      s++;
    if (/[^A-Za-z0-9]/.test(password)) s++;
    return s;
  })();
  const strengthLabel = ["", "Weak", "Fair", "Good", "Strong"][strength];
  const strengthColor = ["", "bg-error", "bg-secondary", "bg-primary/70", "bg-primary"][strength];

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (strength < 2) { setError("Please choose a stronger password."); return; }
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const { error: err } = await withRetry(() =>
        supabase.auth.signUp({
          email,
          password,
          options: { data: { full_name: fullName, role } },
        })
      );
      if (err) throw new Error(err.message);
      setSuccess("Account created! Check your email to confirm, then sign in.");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  const handleGoogle = async () => {
    setGoogleLoading(true);
    setError(null);
    try {
      const { data, error: err } = await withRetry(() =>
        supabase.auth.signInWithOAuth({
          provider: "google",
          options: { redirectTo: `${window.location.origin}/` },
        })
      );
      if (err) throw new Error(err.message);
      if (data?.url) window.location.assign(data.url);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setGoogleLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center px-4 py-10 overflow-auto">
      <AuthBackground />

      <div className="w-full max-w-[440px] flex flex-col gap-6">
        {/* Logo */}
        <div className="flex flex-col items-center gap-2 text-center">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-primary text-[32px]">shield</span>
            <span className="text-[22px] font-bold text-primary tracking-tight">SupplyGuard</span>
          </div>
          <p className="text-[12px] text-on-surface-variant/70 uppercase tracking-widest font-mono">
            AI Crisis Logistics Platform
          </p>
        </div>

        <AuthCard>
          {/* Header */}
          <div className="mb-5">
            <h1 className="text-[22px] font-bold text-on-surface leading-tight">Create account</h1>
            <p className="text-[13px] text-on-surface-variant mt-1">
              Join SupplyGuard and start monitoring your supply chain.
            </p>
          </div>

          {/* Google OAuth */}
          <SocialButton onClick={handleGoogle} loading={googleLoading}>
            <svg className="w-[18px] h-[18px] shrink-0" viewBox="0 0 24 24">
              <path fill="#EA4335" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            <span>{googleLoading ? "Redirecting…" : "Sign up with Google"}</span>
          </SocialButton>

          {/* Divider */}
          <div className="flex items-center gap-3 my-5">
            <div className="flex-1 h-[1px] bg-outline-variant/30" />
            <span className="text-[11px] text-on-surface-variant/50 uppercase tracking-widest font-mono">or</span>
            <div className="flex-1 h-[1px] bg-outline-variant/30" />
          </div>

          <form onSubmit={handleSignUp} noValidate className="flex flex-col gap-4">
            {/* Full name */}
            <AuthInput
              id="fullName"
              label="Full name"
              value={fullName}
              onChange={setFullName}
              autoComplete="name"
              required
              icon="person"
            />

            {/* Email */}
            <AuthInput
              id="email"
              label="Email address"
              type="email"
              value={email}
              onChange={setEmail}
              autoComplete="email"
              required
              icon="mail"
            />

            {/* Password */}
            <div className="flex flex-col gap-[6px]">
              <AuthInput
                id="password"
                label="Password"
                type="password"
                value={password}
                onChange={setPassword}
                autoComplete="new-password"
                required
                icon="lock"
              />
              {/* Strength meter */}
              {password.length > 0 && (
                <div className="flex items-center gap-2 px-1">
                  <div className="flex gap-1 flex-1">
                    {[1, 2, 3, 4].map((i) => (
                      <div
                        key={i}
                        className={`h-[3px] flex-1 rounded-full transition-all duration-300 ${
                          i <= strength ? strengthColor : "bg-outline-variant/30"
                        }`}
                      />
                    ))}
                  </div>
                  <span className={`text-[10px] font-mono font-bold ${
                    strength <= 1 ? "text-error" :
                    strength === 2 ? "text-secondary" :
                    "text-primary"
                  }`}>
                    {strengthLabel}
                  </span>
                </div>
              )}
            </div>

            {/* Role selector */}
            <div>
              <p className="text-[11px] text-on-surface-variant/70 uppercase tracking-widest mb-2 font-medium font-mono">
                Your role
              </p>
              <div className="grid grid-cols-5 gap-[6px]">
                {ROLES.map((r) => (
                  <button
                    key={r.value}
                    type="button"
                    onClick={() => setRole(r.value)}
                    className={`flex flex-col items-center gap-[4px] py-[10px] px-[6px] rounded-xl border text-[10px] font-medium transition-all duration-150 ${
                      role === r.value
                        ? "border-primary bg-primary/10 text-primary"
                        : "border-outline-variant/30 bg-surface-container text-on-surface-variant hover:border-primary/40 hover:text-on-surface"
                    }`}
                  >
                    <span className="material-symbols-outlined text-[18px]">{r.icon}</span>
                    <span className="leading-tight text-center">{r.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="relative w-full py-[13px] rounded-xl bg-primary text-on-primary text-[14px] font-bold tracking-wide hover:brightness-110 active:scale-[0.98] transition-all duration-150 disabled:opacity-60 disabled:cursor-not-allowed overflow-hidden mt-1"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-on-primary/30 border-t-on-primary rounded-full animate-spin" />
                  Creating account…
                </span>
              ) : (
                "Create Account"
              )}
            </button>
          </form>

          {/* Feedback */}
          {(error || success) && (
            <div
              className={`mt-4 flex items-start gap-2 px-4 py-3 rounded-xl text-[13px] border ${
                error
                  ? "bg-error/8 border-error/20 text-error"
                  : "bg-primary/8 border-primary/20 text-primary"
              }`}
            >
              <span className="material-symbols-outlined text-[16px] mt-[1px] shrink-0">
                {error ? "error" : "check_circle"}
              </span>
              <span>{error || success}</span>
            </div>
          )}

          {/* Switch to sign-in */}
          <p className="mt-5 text-center text-[13px] text-on-surface-variant">
            Already have an account?{" "}
            <Link
              href="/auth/signin"
              className="text-primary font-semibold hover:underline underline-offset-2"
            >
              Sign in
            </Link>
          </p>
        </AuthCard>

        {/* Footer */}
        <p className="text-center text-[11px] text-on-surface-variant/40 font-mono">
          © {new Date().getFullYear()} SupplyGuard · All rights reserved
        </p>
      </div>
    </div>
  );
}
