"use client";

import { useEffect, useState } from "react";
import type { EvidenceSummary } from "@/lib/evidence/types";

let cache: Promise<EvidenceSummary> | null = null;

function load(): Promise<EvidenceSummary> {
  if (!cache) {
    cache = fetch("/evidence/summary.json", { cache: "force-cache" }).then((r) => {
      if (!r.ok) throw new Error(`Evidence summary unavailable (${r.status})`);
      return r.json() as Promise<EvidenceSummary>;
    });
    cache.catch(() => {
      cache = null;
    });
  }
  return cache;
}

export function useEvidence(): { data: EvidenceSummary | null; error: string | null } {
  const [state, setState] = useState<{ data: EvidenceSummary | null; error: string | null }>({ data: null, error: null });
  useEffect(() => {
    let live = true;
    load()
      .then((data) => live && setState({ data, error: null }))
      .catch((e: Error) => live && setState({ data: null, error: e.message }));
    return () => {
      live = false;
    };
  }, []);
  return state;
}
