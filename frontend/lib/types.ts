// Types mirroring the backend contract (see API.md / openapi.json).
// Keep in sync with ../backend/app/schemas. Do NOT change backend to match UI;
// request additions from the backend owner instead.

export type AxisId =
  | "logic" | "creativity" | "knowledge" | "curiosity"
  | "empathy" | "humor" | "grit" | "structure";

export const AXES: { id: AxisId; label: string }[] = [
  { id: "logic", label: "邏輯" },
  { id: "creativity", label: "創意" },
  { id: "knowledge", label: "知識" },
  { id: "curiosity", label: "好奇心" },
  { id: "empathy", label: "同理" },
  { id: "humor", label: "幽默" },
  { id: "grit", label: "毅力" },
  { id: "structure", label: "條理" },
];

export type Facet = "coding" | "analytical" | "creative" | "social" | "learning" | "planning";

export type Radar = Partial<Record<AxisId, number>>;

export interface Character {
  id: string;
  slot: number;
  name: string | null;
  species: string | null;
  archetype: string | null;
  facet: string | null;
  radar: Radar;
  trait_tags: string[];
  persona: string | null;
  appearance: Record<string, string>;
  level: number;
  xp: number;
  status: "active" | "retired";
}

export interface GenerateResult {
  created: Character[];
  skipped_facets: string[];
  slot_cap: number;
}

export interface FacetIn {
  facet: Facet | string;
  weight: number;
  radar: Radar;
  trait_tags: string[];
  species_hint?: string | null;
  summary?: string | null;
}

export interface SelfExtractProfile {
  version: string;
  facets: FacetIn[];
  overall_summary?: string | null;
}

export interface DirectMessage {
  id: string;
  from_me: boolean;
  body: string;
  created_at: string;
  read: boolean;
}

export interface Conversation {
  friend_user_id: string;
  handle: string;
  last_message: string | null;
  last_at: string | null;
  unread: number;
}

export interface CharacterChatLine {
  speaker: string;
  character_id: string | null;
  text: string;
}
export interface CharacterChat {
  id: string;
  transcript: CharacterChatLine[];
  summary: string | null;
  created_at: string;
}
export interface CharacterChatSummary {
  id: string;
  summary: string | null;
  created_at: string;
}

export interface Encounter {
  chat_id: string;
  my_character: Character;
  other_character: Character;   // stranger sprite's public profile (owner hidden)
  compatibility: number;
  reasons: string[];
  transcript: CharacterChatLine[];
  summary: string | null;
  created_at: string;
  waved: boolean;
}

export interface Match {
  their_character: Character;  // persona shown; human identity hidden until mutual wave
  my_character_id: string;
  score: number;              // 0..100 compatibility
  reasons: string[];
  waved: boolean;
}

export interface WaveResult {
  matched: boolean;           // both waved -> now owner-friends
  friendship_id: string | null;
}

export interface Me {
  handle: string;
  discoverable: boolean;
}

export interface CharacterFriendResult {
  friend: Character;        // only the other creature is revealed (no owner info)
  remaining_today: number;  // character-level befriend quota left today
}

export type FriendDirection = "incoming" | "outgoing" | "friends";
export interface Friend {
  friendship_id: string;
  user_id: string;
  handle: string;
  status: "pending" | "accepted";
  direction: FriendDirection;
}

export interface ShareResult {
  token: string;
  is_public: boolean;
  url: string;       // frontend path e.g. /shared/<token>
  card_url: string;  // absolute SVG image url
}

export interface Scenario {
  id: string;
  key: string | null;   // stable slug — use to map your own quest illustration
  title: string;
  type: string;         // "solo" | "shared"
  art: string | null;   // art hint (e.g. "library"); frontend picks the actual image
  requirements: Record<string, any>;
  rewards: Record<string, any>;
}

export interface DispatchResult {
  dispatch_id: string;
  outcome: "success" | "fail";
  log: { steps: any[]; text?: string; margin?: number; roll?: number; reason?: string };
  rewards: Record<string, any>;
  characters: Character[]; // post-progression state (xp/level updated)
}

export interface SharedCharacter {
  name: string | null;
  species: string | null;
  archetype: string | null;
  radar: Radar;
  trait_tags: string[];
  persona: string | null;
  level: number;
  owner_handle: string;
}
