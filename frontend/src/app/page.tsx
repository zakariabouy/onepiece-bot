"use client";

import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-[calc(100vh-3.5rem)]">
      <div className="flex flex-col items-center justify-center min-h-[calc(100vh-3.5rem)] px-6">
        <div className="text-center max-w-xl mx-auto">
          <img
            src="/logo.png"
            alt="Straw Hat Logo"
            className="w-24 h-24 mx-auto mb-8 drop-shadow-2xl"
          />

          <h1 className="text-5xl md:text-6xl font-bold text-white mb-3 tracking-tight">
            One Piece Bot
          </h1>

          <p className="text-amber-400/70 text-sm tracking-[0.2em] uppercase font-medium mb-6">
            Your AI Nakama on the Grand Line
          </p>

          <p className="text-gray-400 text-[15px] max-w-md mx-auto leading-relaxed mb-10">
            Chat about the story, explore lore from 1000+ chapters, or submit
            your wildest theories and see how they hold up against canon.
          </p>

          <div className="flex flex-col sm:flex-row gap-3 justify-center mb-20">
            <Link
              href="/chat"
              className="px-7 py-3 rounded-lg bg-indigo-600 hover:bg-indigo-500 font-medium text-sm text-white transition-colors"
            >
              Start Chatting
            </Link>
            <Link
              href="/theory"
              className="px-7 py-3 rounded-lg border border-white/[0.12] hover:bg-white/[0.06] font-medium text-sm text-gray-300 transition-colors"
            >
              Score a Theory
            </Link>
          </div>
        </div>

        {/* Feature cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-3xl w-full">
          <FeatureCard
            title="Canon Knowledge"
            desc="RAG-powered search across 2,000+ notes covering every arc, character, and mystery."
          />
          <FeatureCard
            title="Theory Analysis"
            desc="5-dimension scoring with NLI contradiction detection and foreshadowing matching."
          />
          <FeatureCard
            title="Dual-LLM"
            desc="Fast chat responses with Groq, deep 235B theory analysis with Cerebras."
          />
        </div>
      </div>
    </div>
  );
}

function FeatureCard({ title, desc }: { title: string; desc: string }) {
  return (
    <div className="glass rounded-xl p-5 hover:bg-white/[0.04] transition-colors">
      <h3 className="font-semibold text-white text-sm mb-2">{title}</h3>
      <p className="text-[13px] text-gray-400 leading-relaxed">{desc}</p>
    </div>
  );
}
