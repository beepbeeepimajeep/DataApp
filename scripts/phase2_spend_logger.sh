#!/bin/bash
# Periodic cost tracking for Phase 2
# Every 30 minutes while Phase 2 PID alive
# Appends timestamp + check_spend.py output to /tmp/phase2_spend.log

PID_FILE="/tmp/phase2.pid"
SPEND_LOG="/tmp/phase2_spend.log"

get_pid() {
    [ -f "$PID_FILE" ] && cat "$PID_FILE" || echo ""
}

is_alive() {
    local pid=$1
    [ -z "$pid" ] && return 1
    kill -0 "$pid" 2>/dev/null && return 0 || return 1
}

# Initialize log
echo "[$(date)] Spend logger started" >> "$SPEND_LOG"

# Main loop: every 30 minutes
while true; do
    PID=$(get_pid)

    if [ -z "$PID" ] || ! is_alive "$PID"; then
        echo "[$(date)] Phase 2 process no longer alive, spend logger exiting" >> "$SPEND_LOG"
        exit 0
    fi

    echo "" >> "$SPEND_LOG"
    echo "════════════════════════════════════════════" >> "$SPEND_LOG"
    echo "Spend check at $(date)" >> "$SPEND_LOG"
    echo "════════════════════════════════════════════" >> "$SPEND_LOG"

    # Try to run check_spend.py if it exists
    if [ -x scripts/check_spend.py ]; then
        python3 scripts/check_spend.py 2>&1 >> "$SPEND_LOG" || true
    else
        echo "check_spend.py not available or not executable" >> "$SPEND_LOG"
    fi

    # Wait 30 minutes before next check
    sleep 1800
done
