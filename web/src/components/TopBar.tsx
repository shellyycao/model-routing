"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const TABS = [
  { href: "/", label: "Home" },
  { href: "/library", label: "My Workflows" },
  { href: "/studio", label: "Studio" },
  { href: "/evidence", label: "Evidence" },
];

export function TopBar() {
  const path = usePathname();
  return (
    <header className="flex h-16 items-center justify-between gap-4 border-b border-line px-4 sm:px-6">
      <Link href="/" className="flex items-center gap-3 whitespace-nowrap text-lg font-bold tracking-tight" aria-label="ModelFlow home">
        <span aria-hidden className="grid h-7 w-7 place-items-center rounded-[9px] bg-gradient-to-br from-[#d5caff] to-[#7863d8] text-[#161420]">
          ◇
        </span>
        <span>ModelFlow</span>
      </Link>
      <nav aria-label="Primary" className="flex gap-1 overflow-x-auto">
        {TABS.map((t) => {
          const active = t.href === "/" ? path === "/" : path.startsWith(t.href);
          return (
            <Link
              key={t.href}
              href={t.href}
              aria-current={active ? "page" : undefined}
              className={`whitespace-nowrap rounded-[9px] px-3 py-2 text-sm ${active ? "bg-[#272337] text-[#ded7ff]" : "text-muted hover:text-ink"}`}
            >
              {t.label}
            </Link>
          );
        })}
      </nav>
      <span className="pill hidden md:inline-flex" title="Workflows are stored in this browser only. No AI model is called yet.">
        Prototype · local only · no AI calls
      </span>
    </header>
  );
}
