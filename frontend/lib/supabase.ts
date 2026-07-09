// Supabase client (auth only — data always goes through the FastAPI backend).
// When NEXT_PUBLIC_SUPABASE_URL is unset (local dev), the app falls back to the
// X-Dev-User handle mode and this module exports null.

import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const url = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";
const anon = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "";

export const supabase: SupabaseClient | null =
  url && anon ? createClient(url, anon) : null;

export const authEnabled = Boolean(supabase);

// Synchronous token cache so the API client doesn't need async header plumbing.
let _token: string | null = null;

if (supabase && typeof window !== "undefined") {
  supabase.auth.getSession().then(({ data }) => {
    _token = data.session?.access_token ?? null;
    window.dispatchEvent(new Event("auth-changed"));
  });
  supabase.auth.onAuthStateChange((_e, session) => {
    _token = session?.access_token ?? null;
    window.dispatchEvent(new Event("auth-changed"));
  });
}

export const getToken = () => _token;

export async function signInWithGoogle() {
  if (!supabase) return;
  await supabase.auth.signInWithOAuth({
    provider: "google",
    options: { redirectTo: typeof window !== "undefined" ? window.location.origin : undefined },
  });
}

export async function signOut() {
  if (!supabase) return;
  await supabase.auth.signOut();
}
