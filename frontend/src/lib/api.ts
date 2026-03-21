import { CharacterInfo, Passage, TheoryResult } from "./types";

const BASE = "";

export async function sendChat(
  message: string,
  history: { role: string; content: string }[],
  k = 5,
  temperature = 0.5
): Promise<{ reply: string; passages: Passage[]; character: CharacterInfo | null }> {
  const res = await fetch(`${BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history, k, temperature }),
  });
  if (!res.ok) throw new Error("Chat request failed");
  return res.json();
}

export async function evaluateTheory(
  theory: string,
  evidence: string
): Promise<TheoryResult> {
  const res = await fetch(`${BASE}/api/theory/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ theory, evidence }),
  });
  if (!res.ok) throw new Error("Theory evaluation failed");
  return res.json();
}
