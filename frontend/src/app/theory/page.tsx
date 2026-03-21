"use client";

import { useState } from "react";
import { evaluateTheory } from "@/lib/api";
import { TheoryResult } from "@/lib/types";

const VERDICT_STYLE: Record<string, { color: string; bg: string }> = {
  "Pirate King-Tier": { color: "text-yellow-400", bg: "from-yellow-500/10 to-transparent" },
  "Yonko-Level": { color: "text-red-400", bg: "from-red-500/10 to-transparent" },
  Solid: { color: "text-green-400", bg: "from-green-500/10 to-transparent" },
  "Needs Work": { color: "text-orange-400", bg: "from-orange-500/10 to-transparent" },
  "Walk the Plank": { color: "text-gray-400", bg: "from-gray-500/10 to-transparent" },
};

const DIMENSION_LABELS: Record<string, string> = {
  THEMATIC_FIT: "Thematic Fit",
  NARRATIVE_STYLE: "Narrative Style",
  POWER_CONSISTENCY: "Power Consistency",
  EVIDENCE_QUALITY: "Evidence Quality",
  ORIGINALITY: "Originality",
};

const NLI_STYLE: Record<string, { color: string; border: string; bg: string; label: string }> = {
  SUPPORTS: { color: "text-emerald-400", border: "border-emerald-500/20", bg: "bg-emerald-500/[0.04]", label: "Supports" },
  CONTRADICTS: { color: "text-red-400", border: "border-red-500/20", bg: "bg-red-500/[0.04]", label: "Contradicts" },
  NEUTRAL: { color: "text-gray-400", border: "border-white/[0.06]", bg: "bg-white/[0.02]", label: "Neutral" },
};

export default function TheoryPage() {
  const [theory, setTheory] = useState("");
  const [evidence, setEvidence] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TheoryResult | null>(null);
  const [error, setError] = useState("");

  async function handleSubmit() {
    if (!theory.trim() || loading) return;
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const data = await evaluateTheory(theory, evidence);
      setResult(data);
    } catch {
      setError("Evaluation failed. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  }

  const scorePercent = result ? (result.score / result.max_score) * 100 : 0;
  const verdictStyle = result ? VERDICT_STYLE[result.verdict] : null;

  return (
    <div className="max-w-2xl mx-auto px-4 py-8 space-y-6">
      {/* Form */}
      <div className="glass rounded-xl p-6 space-y-5">
        <div>
          <h1 className="text-xl font-semibold text-white mb-1">Theory Scorer</h1>
          <p className="text-gray-500 text-sm">
            Evaluate your theory against canon evidence and foreshadowing.
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1.5">
            Your Theory
          </label>
          <textarea
            value={theory}
            onChange={(e) => setTheory(e.target.value)}
            rows={4}
            placeholder="e.g. Shanks is actually a Celestial Dragon who chose to become a pirate..."
            className="w-full bg-white/[0.03] border border-white/[0.08] rounded-lg px-4 py-3 text-sm text-gray-100 placeholder-gray-600 focus:outline-none focus:border-white/[0.15] transition-colors resize-none"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1.5">
            Supporting Evidence
            <span className="text-gray-600 font-normal ml-1">optional</span>
          </label>
          <textarea
            value={evidence}
            onChange={(e) => setEvidence(e.target.value)}
            rows={3}
            placeholder="Cite chapters, SBS answers, or manga panels..."
            className="w-full bg-white/[0.03] border border-white/[0.08] rounded-lg px-4 py-3 text-sm text-gray-100 placeholder-gray-600 focus:outline-none focus:border-white/[0.15] transition-colors resize-none"
          />
        </div>

        <button
          onClick={handleSubmit}
          disabled={loading || !theory.trim()}
          className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-30 rounded-lg font-medium text-sm transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Evaluating...
            </>
          ) : (
            "Evaluate Theory"
          )}
        </button>

        {error && (
          <p className="text-red-400 text-sm text-center">{error}</p>
        )}
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-4 animate-in">
          {/* Score + Verdict */}
          <div className={`glass rounded-xl p-6 bg-gradient-to-br ${verdictStyle?.bg ?? ""}`}>
            <div className="flex items-end justify-between mb-5">
              <div>
                <div className="text-xs uppercase tracking-wider text-gray-500 mb-1">
                  Score
                </div>
                <div className="text-4xl font-bold text-white tabular-nums">
                  {result.score}
                  <span className="text-base text-gray-500 font-normal ml-1">
                    / {result.max_score}
                  </span>
                </div>
              </div>
              <div className="text-right">
                <div className="text-xs uppercase tracking-wider text-gray-500 mb-1">
                  Verdict
                </div>
                <div className={`text-xl font-semibold ${verdictStyle?.color ?? "text-gray-300"}`}>
                  {result.verdict}
                </div>
              </div>
            </div>

            <div className="w-full h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-1000 ease-out"
                style={{
                  width: `${scorePercent}%`,
                  background:
                    scorePercent > 66
                      ? "#22c55e"
                      : scorePercent > 33
                      ? "#eab308"
                      : "#ef4444",
                }}
              />
            </div>
          </div>

          {/* Dimensions */}
          {result.dimensions && Object.keys(result.dimensions).length > 0 && (
            <div className="glass rounded-xl p-6">
              <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">
                Dimensions
              </h2>
              <div className="space-y-3">
                {Object.entries(result.dimensions).map(([key, value]) => {
                  const pct = (value / 5) * 100;
                  const color = value >= 4 ? "#22c55e" : value >= 3 ? "#eab308" : "#ef4444";
                  return (
                    <div key={key}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-400">
                          {DIMENSION_LABELS[key] ?? key}
                        </span>
                        <span className="text-gray-500 font-mono text-xs" style={{ color }}>
                          {value}/5
                        </span>
                      </div>
                      <div className="w-full h-1 bg-white/[0.06] rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-700"
                          style={{ width: `${pct}%`, background: color }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Analysis */}
          {result.analysis && (
            <div className="glass rounded-xl p-6">
              <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">
                Analysis
              </h2>
              <p className="text-sm text-gray-400 leading-relaxed whitespace-pre-wrap">
                {result.analysis}
              </p>
            </div>
          )}

          {/* Canon Evidence */}
          {result.canon_evidence && result.canon_evidence.length > 0 && (
            <div className="glass rounded-xl p-6">
              <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">
                Canon Evidence
              </h2>
              <div className="space-y-2.5">
                {result.canon_evidence.map((ev, i) => {
                  const style = NLI_STYLE[ev.relation] ?? NLI_STYLE.NEUTRAL;
                  return (
                    <div
                      key={i}
                      className={`${style.bg} ${style.border} border rounded-lg p-3.5`}
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="font-medium text-sm text-gray-200">
                          {ev.title}
                        </span>
                        <span className={`text-[11px] font-medium uppercase tracking-wider ${style.color}`}>
                          {style.label}
                        </span>
                      </div>
                      <p className="text-sm text-gray-500 leading-relaxed">
                        {ev.reasoning}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Supporting Evidence */}
          {result.supporting_evidence && result.supporting_evidence.length > 0 && (
            <div className="glass rounded-xl p-6">
              <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">
                Related Data
              </h2>
              <div className="space-y-1.5">
                {result.supporting_evidence.map((ev, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-3 text-sm py-2 border-b border-white/[0.04] last:border-0"
                  >
                    <span className="text-[11px] font-mono text-indigo-400/70 uppercase tracking-wider mt-0.5 shrink-0 w-20">
                      {ev.type}
                    </span>
                    <span className="text-gray-400 flex-1">{ev.summary}</span>
                    <span className="text-gray-600 shrink-0 font-mono text-xs">
                      {(ev.relevance * 100).toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Foreshadowing */}
          {result.foreshadowing_matches && result.foreshadowing_matches.length > 0 && (
            <div className="glass rounded-xl p-6">
              <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">
                Foreshadowing Matches
              </h2>
              <ul className="space-y-2">
                {result.foreshadowing_matches.map((f, i) => (
                  <li
                    key={i}
                    className="text-sm text-gray-400 pl-3 border-l-2 border-amber-500/30 py-0.5"
                  >
                    {f}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Warnings */}
          {result.warnings && result.warnings.length > 0 && (
            <div className="border border-red-500/15 bg-red-500/[0.03] rounded-xl p-6">
              <h2 className="text-sm font-semibold text-red-400 uppercase tracking-wider mb-3">
                Warnings
              </h2>
              <ul className="space-y-1.5">
                {result.warnings.map((w, i) => (
                  <li key={i} className="text-sm text-red-300/70">
                    {w}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
