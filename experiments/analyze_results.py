"""M6 analysis: saved raw records -> processed tables + figures (offline; no AWS, no model code).

Usage:
  .venv/bin/python -m experiments.analyze_results [--config configs/analysis.yaml] [--out DIR]
      [--status pilot_only] [--generated-at ISO] [--records F ...] [--routing-dir DIR]

SYNTHETIC_FIXTURE-derived output is refused under results/. Mixed experiment_ids are refused unless
listed in the config's experiment_group. Schema: docs/analysis_schema.md.
"""

from __future__ import annotations

import argparse
import json

from src.analysis.pipeline import DEFAULT_CONFIG_PATH, load_config, run_analysis


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    ap.add_argument("--out", dest="out_dir")
    ap.add_argument("--status", dest="status_override", choices=["pilot_only"])
    ap.add_argument("--generated-at", dest="generated_at")
    ap.add_argument("--records", dest="workflow_records", nargs="+")
    ap.add_argument("--routing-dir", dest="routing_dir")
    a = vars(ap.parse_args(argv))
    cfg = load_config(a.pop("config"), **a)
    m = run_analysis(cfg)
    print(json.dumps({"out_dir": cfg.out_dir, "tables": m["tables"]}, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
