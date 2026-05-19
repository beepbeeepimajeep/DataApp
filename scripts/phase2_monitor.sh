#!/bin/bash
# Real-time Phase 2 progress monitor
# Refreshes every 2 minutes
# Reads PID from /tmp/phase2.pid
# Display: status, progress, stats, pace, ETA

set -e

LOG_FILE="logs/phase2_full.log"
MANIFEST_FILE="dataapp_outputs/dataset_manifest.jsonl"
PID_FILE="/tmp/phase2.pid"

# Helper: read PID
get_pid() {
    [ -f "$PID_FILE" ] && cat "$PID_FILE" || echo ""
}

# Helper: check if process alive
is_alive() {
    local pid=$1
    [ -z "$pid" ] && return 1
    kill -0 "$pid" 2>/dev/null && return 0 || return 1
}

# Helper: count manifest entries
count_manifest() {
    [ -f "$MANIFEST_FILE" ] && wc -l < "$MANIFEST_FILE" || echo "0"
}

# Helper: extract stats from log
get_stats() {
    local log="$LOG_FILE"
    [ ! -f "$log" ] && return

    local succeeded=$(grep -c "Processing item" "$log" 2>/dev/null || echo "0")
    local failed=$(grep -c "failed:" "$log" 2>/dev/null || echo "0")
    local fallbacks=$(grep -c "fallback\|recursion" "$log" 2>/dev/null || echo "0")

    echo "$succeeded" "$failed" "$fallbacks"
}

# Helper: get last 3 items from log
get_recent_items() {
    local log="$LOG_FILE"
    [ ! -f "$log" ] && return
    grep "Processing item" "$log" 2>/dev/null | tail -3 || true
}

# Helper: recent 429 errors
get_429_errors() {
    local log="$LOG_FILE"
    [ ! -f "$log" ] && return
    grep "429" "$log" 2>/dev/null | tail -5 || true
}

# Helper: get file mtime in seconds ago
mtime_ago() {
    local file=$1
    [ ! -f "$file" ] && echo "999999" && return
    local mtime=$(stat -c %Y "$file" 2>/dev/null || stat -f %m "$file" 2>/dev/null || echo "0")
    local now=$(date +%s)
    echo $((now - mtime))
}

# Main loop
trap 'echo "[$(date)] Monitor stopped"; exit 0' INT TERM

while true; do
    clear
    echo "════════════════════════════════════════════════════════════════════"
    echo "PHASE 2 MONITOR — $(date '+%Y-%m-%d %H:%M:%S')"
    echo "════════════════════════════════════════════════════════════════════"
    echo ""

    PID=$(get_pid)

    if [ -z "$PID" ]; then
        echo "⚠️  No PID file. Expected: $PID_FILE"
        echo ""
    elif is_alive "$PID"; then
        # Process is running
        LOG_AGE=$(mtime_ago "$LOG_FILE")
        MANIFEST_COUNT=$(count_manifest)

        read SUCCEEDED FAILED FALLBACKS < <(get_stats)

        echo "Process: RUNNING (PID $PID)"
        echo "  Log age: ${LOG_AGE}s ago"
        echo ""
        echo "Progress: $MANIFEST_COUNT items in manifest (of 943 target)"
        PCTG=$((MANIFEST_COUNT * 100 / 943))
        echo "  [$PCTG%] ████████░░░░░░░░░░ (estimate)"
        echo ""
        echo "Stats this run:"
        echo "  Items succeeded: $SUCCEEDED"
        echo "  Items failed: $FAILED"
        echo "  Recursion fallbacks: $FALLBACKS"

        if [ $((SUCCEEDED + FAILED)) -gt 0 ]; then
            FAIL_RATE=$((FAILED * 100 / (SUCCEEDED + FAILED)))
            if [ $FAIL_RATE -gt 10 ]; then
                echo "  ⚠️  Failure rate: ${FAIL_RATE}% (HIGH)"
            else
                echo "  Failure rate: ${FAIL_RATE}%"
            fi
        fi

        # Recent 429s
        ERRORS_429=$(get_429_errors)
        if [ -n "$ERRORS_429" ]; then
            echo ""
            echo "Recent 429 errors (last 5):"
            echo "$ERRORS_429" | sed 's/^/  /'
        fi

        echo ""
        echo "Recent items:"
        get_recent_items | sed 's/^/  /'

    else
        # Process is dead
        echo "Process: DEAD (PID $PID no longer running)"
        MANIFEST_COUNT=$(count_manifest)
        echo "  Final manifest count: $MANIFEST_COUNT entries"
        echo ""
    fi

    echo ""
    echo "Next refresh in 2 minutes... (Ctrl-C to stop)"
    sleep 120
done
