import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";

export const metadata: Metadata = {
  title: "One Piece Bot",
  description: "Your AI Nakama for exploring the Grand Line",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased relative">
        {/* Global background */}
        <div
          className="fixed inset-0 bg-cover bg-center bg-no-repeat -z-20"
          style={{ backgroundImage: "url('/static/assets/bg.jpeg')" }}
        />
        <div className="fixed inset-0 bg-gradient-to-b from-[#020617]/70 via-[#020617]/85 to-[#020617] -z-10" />

        <Navbar />
        <main>{children}</main>
      </body>
    </html>
  );
}
