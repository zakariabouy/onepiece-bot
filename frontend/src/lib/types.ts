export interface CharacterInfo {
  name: string;
  image: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  passages?: Passage[];
  character?: CharacterInfo | null;
}

export interface Passage {
  id: string;
  title: string;
  arc: string;
  text: string;
  score: number;
  rerank_score?: number;
}

export interface TheoryResult {
  score: number;
  max_score: number;
  verdict: string;
  breakdown: Record<string, string | number>;
  dimensions: Record<string, number>;
  analysis: string;
  supporting_evidence: { type: string; summary: string; relevance: number }[];
  canon_evidence: { title: string; relation: string; reasoning: string }[];
  foreshadowing_matches: string[];
  warnings: string[];
}
