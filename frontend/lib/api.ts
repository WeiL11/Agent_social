// Typed REST client for the backend. This is the ONLY place that talks to the
// backend — build any UI on top of these functions. Same client works for a
// future Expo/RN app (only the auth header source changes).
//
// Auth: dev uses X-Dev-User; swap `authHeaders()` to Supabase Bearer in prod.

import type {
  Character, CharacterChat, CharacterChatSummary, CharacterFriendResult, Conversation,
  DirectMessage, DispatchResult, Encounter, Friend, GenerateResult, Match, Me, Scenario,
  SelfExtractProfile, ShareResult, SharedCharacter, WaveResult,
} from "./types";

export const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// Friendly-beta auth: the player picks a handle once (stored locally) and it is
// sent as X-Dev-User. Swap authHeaders() to a Supabase Bearer token for real auth.
export function getHandle(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("persona_handle");
}
export function setHandle(h: string) {
  localStorage.setItem("persona_handle", h.trim().toLowerCase().replace(/[^a-z0-9_-]/g, ""));
}
export function clearHandle() { localStorage.removeItem("persona_handle"); }

function authHeaders(): Record<string, string> {
  const h = getHandle();
  return h ? { "X-Dev-User": h } : {};
}

async function req<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...authHeaders(), ...(init.headers || {}) },
  });
  if (!res.ok) throw new Error(`${res.status} ${path}: ${await res.text()}`);
  return res.status === 204 ? (undefined as T) : res.json();
}

// ---- health ----
export const getHealth = () => req<{ status: string; db: boolean }>("/health");

// ---- characters ----
export const listCharacters = () => req<Character[]>("/characters");
export const getCharacter = (id: string) => req<Character>(`/characters/${id}`);
export const updateCharacter = (id: string, body: { name?: string; appearance?: Record<string, string> }) =>
  req<Character>(`/characters/${id}`, { method: "PUT", body: JSON.stringify(body) });

export const generateFromProfile = (
  profile: SelfExtractProfile,
  opts: { source?: string; apply_mode?: "create_new" | "enrich_existing"; enrich_character_id?: string } = {},
) =>
  req<GenerateResult>("/profiles", {
    method: "POST",
    body: JSON.stringify({
      source: opts.source ?? "self_extract",
      apply_mode: opts.apply_mode ?? "create_new",
      enrich_character_id: opts.enrich_character_id ?? null,
      profile,
    }),
  });

// ---- dispatch (#3) ----
export const listScenarios = () => req<Scenario[]>("/scenarios");
export const createDispatch = (scenarioId: string, characterIds: string[], seed?: number) =>
  req<DispatchResult>("/dispatches", {
    method: "POST",
    body: JSON.stringify({ scenario_id: scenarioId, character_ids: characterIds, seed }),
  });

// ---- real extraction: paste conversation TEXT -> characters ----
export const extractFromText = (text: string, applyMode: "create_new" | "enrich_existing" = "create_new",
                                enrichCharacterId?: string) =>
  req<GenerateResult & { engine: string }>("/profiles/extract", {
    method: "POST",
    body: JSON.stringify({ text, apply_mode: applyMode, enrich_character_id: enrichCharacterId ?? null }),
  });

// ---- 邂逅 explore: sprite meets compatible strangers ----
export const explore = (characterId: string) =>
  req<{ encounter: Encounter | null; remaining_today: number; message: string }>(
    `/characters/${characterId}/explore`, { method: "POST" });
export const myEncounters = () => req<Encounter[]>("/me/encounters");

// ---- matchmaking (model A: persona as matchmaker) ----
export const getMatches = (limit = 10) => req<Match[]>(`/matches?limit=${limit}`);
export const wave = (theirCharacterId: string, fromCharacterId?: string) =>
  req<WaveResult>(`/matches/${theirCharacterId}/wave`, {
    method: "POST",
    body: JSON.stringify(fromCharacterId ? { from_character_id: fromCharacterId } : {}),
  });
export const getMe = () => req<Me>("/me");
export const setDiscoverable = (discoverable: boolean) =>
  req<Me>("/me", { method: "PUT", body: JSON.stringify({ discoverable }) });

// ---- direct messages (owner-friends only) ----
export const getConversations = () => req<Conversation[]>("/conversations");
export const getMessages = (friendUserId: string) =>
  req<DirectMessage[]>(`/friends/${friendUserId}/messages`);
export const sendMessage = (friendUserId: string, body: string) =>
  req<DirectMessage>(`/friends/${friendUserId}/messages`, {
    method: "POST", body: JSON.stringify({ body }),
  });

// ---- friends ----
export const listFriends = () => req<Friend[]>("/friends");
export const sendFriendRequest = (handle: string) =>
  req<Friend>("/friends/requests", { method: "POST", body: JSON.stringify({ handle }) });
export const acceptFriend = (friendshipId: string) =>
  req<Friend>(`/friends/requests/${friendshipId}/accept`, { method: "POST" });
export const removeFriend = (friendshipId: string) =>
  req<{ deleted: string }>(`/friends/requests/${friendshipId}`, { method: "DELETE" });
// Owner-friend perk: see all characters a friend manages.
export const friendCharacters = (friendUserId: string) =>
  req<Character[]>(`/friends/${friendUserId}/characters`);

// ---- character-level friends (creature <-> creature, 2/day) ----
export const befriendCharacter = (characterId: string, targetCharacterId: string) =>
  req<CharacterFriendResult>(`/characters/${characterId}/friends`, {
    method: "POST", body: JSON.stringify({ target_character_id: targetCharacterId }),
  });
export const listCharacterFriends = (characterId: string) =>
  req<Character[]>(`/characters/${characterId}/friends`);  // only the other creature
export const unfriendCharacter = (characterId: string, otherCharacterId: string) =>
  req<{ deleted: string }>(`/characters/${characterId}/friends/${otherCharacterId}`, { method: "DELETE" });

// ---- character <-> character chat (short auto-conversation + summary) ----
export const startCharacterChat = (characterId: string, withCharacterId: string) =>
  req<CharacterChat>(`/characters/${characterId}/chats`, {
    method: "POST", body: JSON.stringify({ with_character_id: withCharacterId }),
  });
export const listCharacterChats = (characterId: string) =>
  req<CharacterChatSummary[]>(`/characters/${characterId}/chats`);
export const getCharacterChat = (chatId: string) =>
  req<CharacterChat>(`/character-chats/${chatId}`);

// ---- sharing ----
export const shareCharacter = (id: string, target: "public" | string) =>
  req<ShareResult>(`/characters/${id}/share`, { method: "POST", body: JSON.stringify({ target }) });
export const sharedWithMe = () => req<SharedCharacter[]>("/shared");
export const getSharedByToken = (token: string) =>
  fetch(`${API}/shared/${token}`).then((r) => (r.ok ? (r.json() as Promise<SharedCharacter>) : Promise.reject(new Error("invalid share"))));

// ---- image URLs (public, drop straight into <img src>) ----
export const avatarUrl = (id: string) => `${API}/render/characters/${id}/avatar.svg`;
export const radarUrl = (id: string) => `${API}/render/characters/${id}/radar.svg`;
export const cardUrl = (id: string) => `${API}/render/characters/${id}/card.svg`;
export const sharedCardUrl = (token: string) => `${API}/shared/${token}/card.svg`;
