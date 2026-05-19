#!/bin/bash
# Circuit breaker for Phase 2
# Polls every 60 seconds
# Kills Phase 2 if failure_rate > 10% (and >20 items processed)

LOG_FILE="logs/phase2_full.log"
PID_FILE="/tmp/phase2.pid"
BREAKER_LOG="/tmp/phase2_breaker.log"

get_pid() {
    [ -f "$PID_FILE" ] && cat "$PID_FILE" || echo ""
}

is_alive() {
    local pid=$1
    [ -z "$pid" ] && return 1
    kill -0 "$pid" 2>/dev/null && return 0 || return 1
}

get_failure_rate() {
    local log="$LOG_FILE"
    [ ! -f "$log" ] && echo "0" && return

    local succeeded=$(grep -c "Processing item" "$log" 2>/dev/null || echo "0")
    local failed=$(grep -c "failed:" "$log" 2>/dev/null || echo "0")
    local total=$((succeeded + failed))

    if [ "$total" -eq 0 ]; then
        echo "0"
    else
        echo $((failed * 100 / total))
    fi
}

get_item_count() {
    local log="$LOG_FILE"
    [ ! -f "$log" ] && echo "0" && return
    grep -c "Processing item" "$log" 2>/dev/null || echo "0"
}

# Initialize log
echo "[$(date)] Circuit breaker started" >> "$BREAKER_LOG"

# Main loop
while true; do
    PID=$(get_pid)

    if [ -z "$PID" ]; then
        echo "[$(date)] No PID file found, exiting" >> "$BREAKER_LOG"
        exit 0
    fi

    if ! is_alive "$PID"; then
        echo "[$(date)] Process $PID is dead, exiting" >> "$BREAKER_LOG"
        exit 0
    fi

    ITEM_COUNT=$(get_item_count)
    FAIL_RATE=$(get_failure_rate)

    # Trigger: >20 items processed AND failure_rate > 10%
    if [ "$ITEM_COUNT" -gt 20 ] && [ "$FAIL_RATE" -gt 10 ]; then
        echo "[$(date)] CIRCUIT BREAKER TRIGGERED: failure rate ${FAIL_RATE}% > 10% (${ITEM_COUNT} items), killing PID $PID" >> "$BREAKER_LOG"
        kill -9 "$PID" 2>/dev/null || true
        sleep 1
        echo "[$(date)] Circuit breaker exiting" >> "$BREAKER_LOG"
        exit 0
    fi

    # Check every 60 seconds
    sleep 60
done
