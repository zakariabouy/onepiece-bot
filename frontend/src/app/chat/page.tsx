"use client";

import { useState, useRef, useEffect } from "react";
import { sendChat } from "@/lib/api";
import { ChatMessage, Passage } from "@/lib/types";

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: ChatMessage = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const history = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }));
      const data = await sendChat(text, history);
      const botMsg: ChatMessage = {
        role: "assistant",
        content: data.reply,
        passages: data.passages,
        character: data.character,
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Something went wrong. Please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)]">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto py-6 px-4">
        <div className="max-w-2xl mx-auto space-y-5">
          {/* Empty state */}
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center min-h-[55vh] text-center gap-4">
              <img src="/logo.png" alt="Logo" className="w-16 h-16 opacity-60 mb-2" />
              <h2 className="text-xl font-semibold text-white">
                Ask anything about One Piece
              </h2>
              <p className="text-gray-500 text-sm max-w-sm">
                Characters, arcs, devil fruits, mysteries — I have 2,000+ notes
                to draw from.
              </p>
              <div className="flex flex-wrap gap-2 justify-center max-w-md mt-2">
                {[
                  "Who is Joy Boy?",
                  "Explain the Void Century",
                  "What are the Ancient Weapons?",
                  "Tell me about Shanks",
                ].map((q) => (
                  <button
                    key={q}
                    onClick={() => setInput(q)}
                    className="px-3 py-1.5 text-[13px] rounded-lg border border-white/[0.08] hover:bg-white/[0.05] transition-colors text-gray-400 hover:text-gray-300"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Messages */}
          {messages.map((msg, i) => (
            <div key={i} className="animate-in">
              {/* User message */}
              {msg.role === "user" ? (
                <div className="flex justify-end">
                  <div className="max-w-[75%] bg-indigo-600 text-white px-4 py-2.5 rounded-lg text-sm leading-relaxed">
                    {msg.content}
                  </div>
                </div>
              ) : (
                /* Assistant message */
                <div className="space-y-2">
                  {/* Character image */}
                  {msg.character && (
                    <div className="flex items-center gap-3 mb-1">
                      <img
                        src={msg.character.image}
                        alt={msg.character.name}
                        className="w-10 h-10 rounded-lg object-cover border border-white/[0.08]"
                      />
                      <span className="text-sm font-medium text-gray-300">
                        {msg.character.name}
                      </span>
                    </div>
                  )}
                  <div className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">
                    {msg.content}
                  </div>

                  {/* Sources */}
                  {msg.passages && msg.passages.length > 0 && (
                    <div className="pt-1">
                      <button
                        onClick={() => setExpandedIdx(expandedIdx === i ? null : i)}
                        className="text-xs text-gray-500 hover:text-gray-400 transition-colors"
                      >
                        {expandedIdx === i ? "Hide" : "Show"} {msg.passages.length} source{msg.passages.length > 1 ? "s" : ""}
                      </button>
                      {expandedIdx === i && (
                        <div className="mt-2 space-y-1.5 animate-in">
                          {msg.passages.map((p: Passage, j: number) => (
                            <div
                              key={j}
                              className="text-xs bg-white/[0.03] border border-white/[0.05] rounded-lg p-3"
                            >
                              <div className="flex items-baseline gap-2 mb-1">
                                <span className="font-medium text-gray-300">
                                  {p.title}
                                </span>
                                {p.arc && (
                                  <span className="text-gray-600">{p.arc}</span>
                                )}
                                <span className="ml-auto text-gray-600 font-mono text-[11px]">
                                  {(p.score * 100).toFixed(0)}%
                                </span>
                              </div>
                              <p className="text-gray-500 leading-relaxed">{p.text}</p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}

          {/* Typing indicator */}
          {loading && (
            <div className="animate-in flex gap-1.5 items-center py-2">
              <div className="w-1.5 h-1.5 bg-gray-500 rounded-full typing-dot" />
              <div className="w-1.5 h-1.5 bg-gray-500 rounded-full typing-dot" />
              <div className="w-1.5 h-1.5 bg-gray-500 rounded-full typing-dot" />
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-white/[0.06] p-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="max-w-2xl mx-auto flex gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about One Piece..."
            className="flex-1 bg-white/[0.04] border border-white/[0.08] rounded-lg px-4 py-2.5 text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-white/[0.15] transition-colors"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-30 rounded-lg font-medium text-sm transition-colors"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
