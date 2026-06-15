import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

function getSupabaseConfig() {
  if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error(
      "Missing NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY environment variables. Add them to .env.local."
    );
  }

  return { supabaseUrl, supabaseAnonKey };
}

const { supabaseUrl: url, supabaseAnonKey: anonKey } = getSupabaseConfig();
export const supabase = createClient(url, anonKey);

export function ensureSupabaseConfig() {
  getSupabaseConfig();
}
