#!/usr/bin/env bash
set -Eeuo pipefail

ROOT=${GF180_FLOW_ROOT:-/home/kubew/g100-gf180-tools}
DESIGN_DIR=${GF180_DESIGN_DIR:-"$ROOT/gf180-smoke"}
ARTIFACT_ROOT=${GF180_ARTIFACT_ROOT:-"$ROOT/artifacts"}
RUN_TAG=${GF180_RUN_TAG:-"GF180_$(date -u +%Y%m%dT%H%M%SZ)"}
PDK_FAMILY=${GF180_PDK_FAMILY:-gf180mcuD}
STD_CELL_LIBRARY=${GF180_STD_CELL_LIBRARY:-gf180mcu_fd_sc_mcu7t5v0}

source "${GF180_ENV_FILE:-$ROOT/env.sh}"
: "${PDK_ROOT:?env.sh must set PDK_ROOT}"
: "${VOLARE_HOME:?env.sh must set VOLARE_HOME}"
: "${OPENLANE_IMAGE_OVERRIDE:?env.sh must set OPENLANE_IMAGE_OVERRIDE}"

CONFIG=${GF180_CONFIG:-"$DESIGN_DIR/config.json"}
LOG_DIR="$ARTIFACT_ROOT/logs"
RUN_ARTIFACT_DIR="$ARTIFACT_ROOT/$RUN_TAG"
FINAL_DIR="$RUN_ARTIFACT_DIR/final"
REPORT_DIR="$RUN_ARTIFACT_DIR/reports"
STEP_LOG_DIR="$RUN_ARTIFACT_DIR/step-logs"
STATUS_FILE="$RUN_ARTIFACT_DIR/status.txt"
RUN_DIR="$DESIGN_DIR/runs/$RUN_TAG"
LOG_FILE="$LOG_DIR/$RUN_TAG.log"

if [[ ! $RUN_TAG =~ ^[A-Za-z0-9][A-Za-z0-9_.-]*$ ]]; then
  printf 'Invalid run tag: %s (use letters, digits, dot, underscore, hyphen)\n' "$RUN_TAG" >&2
  exit 2
fi

GF180_OPENLANE_ARGS=${GF180_OPENLANE_ARGS:--c FP_SIZING=absolute -c DIE_AREA=0,0,1000,1000 -c FP_CORE_UTIL=25}
OPENLANE_ARGS=()
if [[ -n $GF180_OPENLANE_ARGS ]]; then
  read -r -a OPENLANE_ARGS <<< "$GF180_OPENLANE_ARGS"
fi

for path in \
  "$DESIGN_DIR" \
  "$CONFIG" \
  "$PDK_ROOT/$PDK_FAMILY" \
  "$VOLARE_HOME/volare/gf180mcu/versions"; do
  if [[ ! -e $path ]]; then
    printf 'Required path does not exist: %s\n' "$path" >&2
    exit 2
  fi
done

if [[ -e $RUN_DIR || -e $RUN_ARTIFACT_DIR || -e $LOG_FILE ]]; then
  printf 'Run tag already exists: %s\n' "$RUN_TAG" >&2
  exit 2
fi

docker image inspect "$OPENLANE_IMAGE_OVERRIDE" >/dev/null
mkdir -p "$LOG_DIR" "$FINAL_DIR" "$REPORT_DIR" "$STEP_LOG_DIR" "$DESIGN_DIR/runs"

status=0
if docker run --rm \
  -w "$DESIGN_DIR" \
  -v "$DESIGN_DIR:$DESIGN_DIR" \
  -v "$PDK_ROOT:$PDK_ROOT:ro" \
  -v "$VOLARE_HOME:$VOLARE_HOME:ro" \
  -e PDK_ROOT="$PDK_ROOT" \
  -e PDK="$PDK_FAMILY" \
  -e STD_CELL_LIBRARY="$STD_CELL_LIBRARY" \
  "$OPENLANE_IMAGE_OVERRIDE" openlane \
    --manual-pdk \
    --pdk-root "$PDK_ROOT" \
    -p "$PDK_FAMILY" \
    -s "$STD_CELL_LIBRARY" \
    -j "${GF180_JOBS:-2}" \
    --run-tag "$RUN_TAG" \
    "${OPENLANE_ARGS[@]}" \
    "$CONFIG" 2>&1 | tee "$LOG_FILE"; then
  status=0
else
  status=$?
fi

if [[ -d $RUN_DIR ]]; then
  while IFS= read -r -d '' step_log; do
    relative_path=${step_log#"$RUN_DIR"/}
    if [[ $relative_path == */* ]]; then
      mkdir -p "$STEP_LOG_DIR/${relative_path%/*}"
    else
      mkdir -p "$STEP_LOG_DIR"
    fi
    cp -a "$step_log" "$STEP_LOG_DIR/$relative_path"
  done < <(find "$RUN_DIR" -type f \( -name '*.log' -o -name COMMANDS \) -print0)

  for metadata in flow.log resolved.json; do
    if [[ -s $RUN_DIR/$metadata ]]; then
      cp -a "$RUN_DIR/$metadata" "$REPORT_DIR/"
    fi
  done

  while IFS= read -r -d '' report_dir; do
    relative_path=${report_dir#"$RUN_DIR"/}
    mkdir -p "$REPORT_DIR/$relative_path"
    cp -a "$report_dir/." "$REPORT_DIR/$relative_path/"
  done < <(find "$RUN_DIR" -type d -name reports -print0)
fi

if (( status == 0 )); then
  if [[ ! -d $RUN_DIR/final ]]; then
    printf 'OpenLane reported success but final run directory is missing: %s\n' "$RUN_DIR/final" >&2
    status=1
  else
    cp -a "$RUN_DIR/final/." "$FINAL_DIR/"
    for artifact in \
      "$FINAL_DIR/gds/top.gds" \
      "$FINAL_DIR/nl/top.nl.v" \
      "$FINAL_DIR/lef/top.lef" \
      "$FINAL_DIR/odb/top.odb" \
      "$FINAL_DIR/sdc/top.sdc"; do
      if [[ ! -s $artifact ]]; then
        printf 'Required final artifact is missing or empty: %s\n' "$artifact" >&2
        status=1
      fi
    done
    if ! grep -Fq 'Flow complete.' "$LOG_FILE"; then
      printf 'OpenLane completion marker is absent from %s\n' "$LOG_FILE" >&2
      status=1
    fi
  fi
fi

printf 'run_tag=%s\nexit_status=%s\nrun_dir=%s\nlog=%s\nstep_logs=%s\nfinal_views=%s\nreports=%s\n' \
  "$RUN_TAG" "$status" "$RUN_DIR" "$LOG_FILE" "$STEP_LOG_DIR" "$FINAL_DIR" "$REPORT_DIR" > "$STATUS_FILE"

if (( status != 0 )); then
  printf 'GF180 run failed (status %s); see %s\n' "$status" "$LOG_FILE" >&2
  exit "$status"
fi

printf 'GF180 run complete.\n  Tag: %s\n  Log: %s\n  Step logs: %s\n  Final views: %s\n  Reports: %s\n' \
  "$RUN_TAG" "$LOG_FILE" "$STEP_LOG_DIR" "$FINAL_DIR" "$REPORT_DIR"
