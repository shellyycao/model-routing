"""Routing (XAI Researcher): leakage-safe data access, transparent estimators, S1-S4 strategies,
recorded constraint/Pareto/lexicographic selection, and hash-chained counterfactual logging.

See docs/methodology.md. Modules:
  data            RecordStore / TrainingView (held-out project physically excluded)
  estimation      stage estimates (Experiment A), S2 stage-additive and S3 interaction-term predictions
  outcomes        aggregation of executed Experiment B runs (shared by S3 training, validation, S4)
  scoring/router  constraint checks, Pareto filter, lexicographic preference, SelectionSteps, traces
  strategies      S1-S3 (prospective) and S4 (retrospective oracle, not deployable)
  counterfactual  counterfactual predictions + append-only hash-chained log
"""
