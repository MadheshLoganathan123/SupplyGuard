"use client";

import Link from "next/link";
import { useState } from "react";
import { supabase, withRetry } from "../../../lib/supabaseClient";
import AuthBackground from "../_components/AuthBackground";
import AuthCard from "../_components/AuthCard";
import AuthInput from "../_components/AuthInput";
import SocialButton from "../_components/SocialButton";

export default function SignInPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const { data, error: err } = await withRetry(() =>
        supabase.auth.signInWithPassword({ email, password })
      );
      if (err) throw new Error(err.message);
      if (!data.session?.access_token) throw new Error("Unable to sign in. Please try again.");
      setSuccess("Signed in successfully. Redirecting…");
      setTimeout(() => { window.location.href = "/"; }, 800);
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

      <div className="w-full max-w-[420px] flex flex-col gap-6">
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
          <div className="mb-6">
            <h1 className="text-[22px] font-bold text-on-surface leading-tight">Welcome back</h1>
            <p className="text-[13px] text-on-surface-variant mt-1">
              Sign in to access your command center.
            </p>
          </div>

          {/* Google OAuth */}
          <SocialButton onClick={handleGoogle} loading={googleLoading}>
            {/* Google SVG */}
            <svg className="w-[18px] h-[18px] shrink-0" viewBox="0 0 24 24">
              <path fill="#EA4335" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            <span>{googleLoading ? "Redirecting…" : "Continue with Google"}</span>
          </SocialButton>

          {/* Divider */}
          <div className="flex items-center gap-3 my-5">
            <div className="flex-1 h-[1px] bg-outline-variant/30" />
            <span className="text-[11px] text-on-surface-variant/50 uppercase tracking-widest font-mono">or</span>
            <div className="flex-1 h-[1px] bg-outline-variant/30" />
          </div>

          {/* Email + Password form */}
          <form onSubmit={handleSignIn} noValidate className="flex flex-col gap-4">
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
            <AuthInput
              id="password"
              label="Password"
              type="password"
              value={password}
              onChange={setPassword}
              autoComplete="current-password"
              required
              icon="lock"
            />

            {/* Forgot password */}
            <div className="flex justify-end -mt-1">
              <button
                type="button"
                className="text-[12px] text-primary/80 hover:text-primary transition-colors font-medium"
              >
                Forgot password?
              </button>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="relative w-full py-[13px] rounded-xl bg-primary text-on-primary text-[14px] font-bold tracking-wide hover:brightness-110 active:scale-[0.98] transition-all duration-150 disabled:opacity-60 disabled:cursor-not-allowed overflow-hidden"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-on-primary/30 border-t-on-primary rounded-full animate-spin" />
                  Signing in…
                </span>
              ) : (
                "Sign In"
              )}
              {/* Shimmer */}
              {!loading && (
                <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full hover:translate-x-full transition-transform duration-700 pointer-events-none" />
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

          {/* Switch to sign-up */}
          <p className="mt-5 text-center text-[13px] text-on-surface-variant">
            Don&apos;t have an account?{" "}
            <Link
              href="/auth/signup"
              className="text-primary font-semibold hover:underline underline-offset-2"
            >
              Create one
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
