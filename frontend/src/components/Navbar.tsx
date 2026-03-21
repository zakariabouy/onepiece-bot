"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Navbar() {
  const path = usePathname();

  const links = [
    { href: "/chat", label: "Chat" },
    { href: "/theory", label: "Theory Scorer" },
  ];

  return (
    <nav className="sticky top-0 z-50 border-b border-white/[0.06] bg-[#020617]/90 backdrop-blur-xl">
      <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5 group">
          <img
            src="/logo.png"
            alt="Logo"
            className="w-7 h-7 group-hover:scale-105 transition-transform"
          />
          <span className="text-[15px] font-semibold text-gray-100 tracking-tight">
            One Piece Bot
          </span>
        </Link>

        <div className="flex items-center gap-1">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={`px-4 py-1.5 rounded-lg text-[13px] font-medium transition-all duration-150 ${
                path === l.href
                  ? "bg-white/[0.1] text-white"
                  : "text-gray-400 hover:text-gray-200 hover:bg-white/[0.05]"
              }`}
            >
              {l.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}
