import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

function getSupabaseConfig() {
  if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error(
      "Missing NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY. Add them to .env.local."
    );
  }
  return { supabaseUrl, supabaseAnonKey };
}

const { supabaseUrl: url, supabaseAnonKey: anonKey } = getSupabaseConfig();

export const supabase = createClient(url, anonKey, {
  auth: {
    // Persist session in localStorage so the token is reused
    // across page reloads instead of triggering new sign-in requests.
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
  },
});

// ── Retry helper ──────────────────────────────────────────────────────────────
// Wraps any async call with exponential back-off so transient
// "Too many requests" (429) errors are retried automatically.

const RATE_LIMIT_MESSAGES = [
  "too many requests",
  "rate limit",
  "request id:",      // Supabase includes "Request ID:" in 429 bodies
  "429",
];

function isRateLimitError(err: unknown): boolean {
  const msg = (err instanceof Error ? err.message : String(err)).toLowerCase();
  return RATE_LIMIT_MESSAGES.some((m) => msg.includes(m));
}

/**
 * Retry `fn` up to `maxAttempts` times with exponential back-off.
 *
 * @param fn          — async function to call
 * @param maxAttempts — total attempts (default 3)
 * @param baseDelayMs — initial delay in ms, doubles each retry (default 1500)
 */
export async function withRetry<T>(
  fn: () => Promise<T>,
  maxAttempts = 3,
  baseDelayMs = 1500
): Promise<T> {
  let lastError: unknown;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (err) {
      lastError = err;

      if (!isRateLimitError(err) || attempt === maxAttempts) {
        throw err;
      }

      const delay = baseDelayMs * Math.pow(2, attempt - 1); // 1.5s, 3s, 6s
      console.warn(
        `Supabase rate limit hit. Retrying in ${delay}ms (attempt ${attempt}/${maxAttempts})…`
      );
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }

  throw lastError;
}

export function ensureSupabaseConfig() {
  getSupabaseConfig();
}
