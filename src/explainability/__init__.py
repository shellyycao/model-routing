"""Explainability (XAI Researcher).

  explanations  deterministic template explanations rendered ONLY from a DecisionTrace; every sentence
                is a claim bound to trace fields
  validation    two SEPARATE kinds of evaluation:
                  * computational faithfulness (claims vs trace fields, router replay) -> FaithfulnessCheck
                  * empirical validity (logged counterfactual vs executed outcome) -> CounterfactualValidation
"""
