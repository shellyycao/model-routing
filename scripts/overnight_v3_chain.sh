#!/bin/zsh
# Overnight chain for the approved v3 work (user-approved 2026-11-18):
#   1. wait for the running Experiment B process (do not touch it)
#   2. retry its void_infra runs ONCE (--retry-void-infra; void records are kept)
#   3. pre-registered repeats: repeat_index 1-2 for A-A-A B-B-B C-C-C A-C-A A-A-C A-C-C on all 4 projects
# Limits for each paid step are the exact worst case from that step's own --plan output.
set -u
cd "$(dirname "$0")/.."
PY=.venv/bin/python
PROJECTS=(customer_churn energy_consumption retail_sales support_operations)
WAIT_PID=${1:-}
log() { echo "=== $* $(date)"; }

if [[ -n "$WAIT_PID" ]]; then
  log "waiting for Experiment B pid $WAIT_PID"
  while kill -0 "$WAIT_PID" 2>/dev/null; do sleep 30; done
fi
log "Experiment B process finished"

run_step() {   # $1 = label, rest = grid args
  local label=$1; shift
  local plan
  plan=$($PY -m experiments.run_workflow_grid --protocol v3 "$@" --plan 2>&1) || { log "$label PLAN FAILED"; echo "$plan"; return 1; }
  echo "$plan" | head -40
  local lim
  lim=$(echo "$plan" | $PY -c 'import sys,json;t=sys.stdin.read();j=json.loads(t[:t.rindex("}")+1]);print(j.get("worst_case_api_attempts_incl_retries",0), j.get("worst_case_input_tokens",0), j.get("worst_case_output_tokens",0))')
  read calls tin tout <<< "$lim"
  if [[ "$calls" == "0" ]]; then log "$label: nothing to run"; return 0; fi
  log "$label start (limits calls=$calls in=$tin out=$tout)"
  $PY -m experiments.run_workflow_grid --protocol v3 "$@" --execute --max-calls "$calls" --max-input-tokens "$tin" --max-output-tokens "$tout"
  log "$label exit $?"
}

run_step "void_infra retry" --projects "${PROJECTS[@]}" --stages 3 --retry-void-infra
run_step "repeats" --projects "${PROJECTS[@]}" --stages 3 --paths A-A-A B-B-B C-C-C A-C-A A-A-C A-C-C --repeats 2 --repeat-start 1
log "chain complete"
