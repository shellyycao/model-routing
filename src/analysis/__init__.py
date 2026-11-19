"""M6 research analysis: saved raw records -> versioned processed tables + figures.

Deterministic and offline. Derives everything only from saved files (no AWS, no model code).
The processed schema is documented in docs/analysis_schema.md (the M7 contract).
"""

SCHEMA_VERSION = "analysis-1.0"
