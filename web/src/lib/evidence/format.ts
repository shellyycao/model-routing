/** Display formatting only. Never rounds away the denominator. */

export const fmtRate = (x: number) => x.toFixed(3);
export const fmtUsd = (x: number | null | undefined) => (x === null || x === undefined ? "not estimable" : `$${x < 0.01 ? x.toFixed(5) : x.toFixed(4)}`);
export const fmtSeconds = (ms: number | null) => (ms === null ? "—" : `${(ms / 1000).toFixed(2)} s`);
export const fmtFrac = (k: number, n: number) => `${k}/${n}`;

export const METRIC_LABELS: Record<string, string> = {
  functional_correct: "functional correct",
  content_correct: "content correct",
  // price-matched-v2 A3 primary is strict (invalid ranking scored as zero); see docs/FINAL_REPORT.md.
  ndcg_at_5: "strict nDCG@5",
};

export const metricLabel = (m: string) => METRIC_LABELS[m] ?? m.replace(/_/g, " ");
