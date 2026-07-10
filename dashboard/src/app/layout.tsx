import type { Metadata } from "next";
import Link from "next/link";
import { Geist, Geist_Mono } from "next/font/google";
import { History } from "lucide-react";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AgentReplay",
  description:
    "Flight recorder and time-travel debugger for AI agents — record, detect, analyze, fork.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="flex min-h-full flex-col">
        <header className="sticky top-0 z-40 border-b border-white/[0.06] bg-[#08080d]/70 backdrop-blur-xl">
          <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-6">
            <Link href="/" className="flex items-center gap-2.5">
              <span className="flex size-7 items-center justify-center rounded-lg bg-violet-500/15 ring-1 ring-violet-400/30">
                <History className="size-4 text-violet-300" />
              </span>
              <span className="text-sm font-semibold tracking-tight text-zinc-100">
                AgentReplay
              </span>
            </Link>
            <span className="text-[11px] font-medium uppercase tracking-widest text-zinc-600">
              Flight recorder for AI agents
            </span>
          </div>
        </header>
        <main className="flex-1">{children}</main>
        <footer className="border-t border-white/[0.06] py-5">
          <p className="text-center text-[11px] text-zinc-600">
            Record · Detect · Analyze · Fork — verify fixes against the exact
            conversation that failed.
          </p>
        </footer>
      </body>
    </html>
  );
}
