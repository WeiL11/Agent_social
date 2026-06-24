import type { SelfExtractProfile } from "./types";

// Handy fixture for testing generation without a real export.
export const SAMPLE_PROFILE: SelfExtractProfile = {
  version: "1.0",
  facets: [
    {
      facet: "coding",
      weight: 80,
      radar: { logic: 85, creativity: 60, knowledge: 70, curiosity: 75, empathy: 40, humor: 50, grit: 65, structure: 80 },
      trait_tags: ["systematic", "analytical"],
      species_hint: "robot",
      summary: "喜歡拆解問題、追求嚴謹解法的人。",
    },
    {
      facet: "creative",
      weight: 55,
      radar: { logic: 50, creativity: 90, knowledge: 55, curiosity: 80, empathy: 65, humor: 75, grit: 45, structure: 40 },
      trait_tags: ["imaginative", "playful"],
      species_hint: "sprite",
      summary: "天馬行空、愛玩點子的人。",
    },
  ],
  overall_summary: "邏輯與創意兼具的探索者。",
};
