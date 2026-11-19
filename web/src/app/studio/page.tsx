import type { Metadata } from "next";
import { Suspense } from "react";
import { Studio } from "@/components/studio/Studio";

export const metadata: Metadata = { title: "Studio · ModelFlow" };

export default function StudioPage() {
  return (
    <Suspense fallback={<p className="p-8 text-soft">Loading studio…</p>}>
      <Studio />
    </Suspense>
  );
}
