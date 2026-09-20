#!/usr/bin/env bash
# ==============================================================================
# Antigravity Nexus — Master CLI App Launcher
# Provides command-line controls to start, stop, monitor and access workspace apps
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_PYTHON="$SCRIPT_DIR/.venv_launcher/bin/python3"
if [ ! -f "$VENV_PYTHON" ]; then
    VENV_PYTHON="python3"
fi

HUB_PORT=3333
HUB_URL="http://localhost:$HUB_PORT"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

print_banner() {
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║            🚀 ANTIGRAVITY NEXUS — APP LAUNCHER HUB            ║${NC}"
    echo -e "${CYAN}║         Unified Process Supervisor & Mission Control           ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

ensure_hub_running() {
    if ! lsof -i :$HUB_PORT > /dev/null 2>&1; then
        echo -e "${YELLOW}⚙️  Starting Nexus Hub on port $HUB_PORT...${NC}"
        nohup "$VENV_PYTHON" "$SCRIPT_DIR/app_launcher.py" > "$SCRIPT_DIR/logs/hub.log" 2>&1 &
        sleep 2
    fi
}

cmd_web() {
    ensure_hub_running
    echo -e "${GREEN}🌐 Nexus Control Hub running at: ${BOLD}$HUB_URL${NC}"
    if command -v open > /dev/null 2>&1; then
        open "$HUB_URL"
    elif command -v xdg-open > /dev/null 2>&1; then
        xdg-open "$HUB_URL"
    fi
}

cmd_start() {
    ensure_hub_running
    TARGET="${1:-all}"
    if [ "$TARGET" = "all" ]; then
        echo -e "${GREEN}🚀 Launching all workspace applications...${NC}"
        curl -s -X POST "$HUB_URL/api/start-all" > /dev/null
        sleep 2
        cmd_status
    else
        echo -e "${GREEN}🚀 Starting app: ${BOLD}$TARGET${NC}..."
        curl -s -X POST "$HUB_URL/api/apps/$TARGET/start" | grep -o '"message":[^,]*' || true
        sleep 1
        cmd_status
    fi
}

cmd_stop() {
    TARGET="${1:-all}"
    if [ "$TARGET" = "all" ]; then
        echo -e "${YELLOW}🛑 Stopping all applications...${NC}"
        if lsof -i :$HUB_PORT > /dev/null 2>&1; then
            curl -s -X POST "$HUB_URL/api/stop-all" > /dev/null || true
        fi
        # Clean common ports on macOS
        for p in 8080 5050 8888 7860 8000 8001 5001; do
            lsof -ti :$p 2>/dev/null | xargs kill -9 2>/dev/null || true
        done
        echo -e "${GREEN}✅ All applications stopped.${NC}"
    else
        echo -e "${YELLOW}🛑 Stopping app: ${BOLD}$TARGET${NC}..."
        curl -s -X POST "$HUB_URL/api/apps/$TARGET/stop" > /dev/null || true
        cmd_status
    fi
}

cmd_status() {
    ensure_hub_running
    echo -e "${BOLD}Current Application Status:${NC}\n"
    "$VENV_PYTHON" -c '
import urllib.request, json

try:
    with urllib.request.urlopen("http://localhost:3333/api/status") as res:
        data = json.loads(res.read().decode())
        apps = data.get("apps", {})
        h_app = "APP NAME"
        h_cat = "CATEGORY"
        h_port = "PORT"
        h_stat = "STATUS"
        h_pid = "PID"
        print(f"{h_app:<35} | {h_cat:<18} | {h_port:<6} | {h_stat:<10} | {h_pid:<6}")
        print("-" * 88)
        for app_id, app in apps.items():
            status = app.get("status", "UNKNOWN")
            pid = str(app.get("pid") or "--")
            port = str(app.get("port"))
            name = app.get("name", app_id)
            cat = app.get("category", "")
            indicator = "🟢 " if status == "RUNNING" else ("🟡 " if status == "STARTING" else "⚪ ")
            stat_str = indicator + status
            print(f"{name:<35} | {cat:<18} | {port:<6} | {stat_str:<10} | {pid:<6}")
except Exception as e:
    print(f"Error fetching status: {e}")
'
    echo ""
}

cmd_logs() {
    TARGET="$1"
    if [ -z "$TARGET" ]; then
        echo -e "${RED}Usage: $0 logs <app_id>${NC}"
        echo "Available apps: portfolio, qlikhunter, globalcareer, aethermind, bharatalpha_invest, bharatalpha_trade, mirofish"
        exit 1
    fi
    LOG_FILE="$SCRIPT_DIR/logs/$TARGET.log"
    if [ -f "$LOG_FILE" ]; then
        tail -f -n 50 "$LOG_FILE"
    else
        echo -e "${YELLOW}No log file found for $TARGET at $LOG_FILE${NC}"
    fi
}

cmd_automations() {
    ensure_hub_running
    echo -e "${BOLD}📅 Daily Scheduled Automations (IST):${NC}\n"
    "$VENV_PYTHON" -c '
import urllib.request, json

try:
    with urllib.request.urlopen("http://localhost:3333/api/automations") as res:
        data = json.loads(res.read().decode())
        autos = data.get("automations", {})
        enabled = data.get("scheduler_enabled", True)
        ist_now = data.get("current_time_ist", "")
        stat_sched = "🟢 ACTIVE" if enabled else "🔴 PAUSED"
        print(f"Master Scheduler: {stat_sched} | Current Time: {ist_now}\n")
        h_id = "ROUTINE ID"
        h_name = "ROUTINE NAME"
        h_sched = "SCHEDULE (IST)"
        h_next = "NEXT EXECUTION"
        h_last = "LAST STATUS"
        print(f"{h_id:<22} | {h_name:<34} | {h_sched:<24} | {h_next:<34} | {h_last}")
        print("-" * 135)
        for auto_id, auto in autos.items():
            name = auto.get("name", auto_id)
            sched = auto.get("schedule_display", "")
            next_run = auto.get("next_run", "--")
            is_run = auto.get("is_running", False)
            last_stat = "🟡 RUNNING" if is_run else auto.get("last_status", "IDLE")
            if last_stat == "SUCCESS":
                last_stat = "🟢 SUCCESS"
            elif last_stat == "ERROR":
                last_stat = "🔴 ERROR"
            print(f"{auto_id:<22} | {name:<34} | {sched:<24} | {next_run:<34} | {last_stat}")
except Exception as e:
    print(f"Error fetching automations: {e}")
'
    echo ""
}

cmd_run_auto() {
    ensure_hub_running
    TARGET="$1"
    if [ -z "$TARGET" ]; then
        echo -e "${RED}Usage: $0 run-auto <automation_id>${NC}"
        echo "Available: qlikhunter_daily, globalcareer_morning, globalcareer_evening, bharatalpha_universe"
        exit 1
    fi
    echo -e "${GREEN}🚀 Triggering automation: ${BOLD}$TARGET${NC}..."
    curl -s -X POST "$HUB_URL/api/automations/$TARGET/run"
    echo ""
}

cmd_install_daemon() {
    PLIST_SRC="$SCRIPT_DIR/com.antigravity.nexus.plist"
    PLIST_DEST="$HOME/Library/LaunchAgents/com.antigravity.nexus.plist"
    echo -e "${YELLOW}⚙️  Installing macOS LaunchAgent...${NC}"
    mkdir -p "$HOME/Library/LaunchAgents"
    cp "$PLIST_SRC" "$PLIST_DEST"
    launchctl unload "$PLIST_DEST" 2>/dev/null || true
    launchctl load "$PLIST_DEST"
    echo -e "${GREEN}✅ Antigravity Nexus LaunchAgent installed & activated!${NC}"
    echo "The Hub and Daily Automations will automatically launch at user login and stay continuously alive."
}

# Main routing
print_banner

case "${1:-web}" in
    web)
        cmd_web
        ;;
    start)
        cmd_start "$2"
        ;;
    stop)
        cmd_stop "$2"
        ;;
    status)
        cmd_status
        ;;
    automations|autos)
        cmd_automations
        ;;
    run-auto)
        cmd_run_auto "$2"
        ;;
    install-daemon)
        cmd_install_daemon
        ;;
    logs)
        cmd_logs "$2"
        ;;
    help|--help|-h)
        echo "Usage: $0 [command] [target]"
        echo ""
        echo "Commands:"
        echo "  web                 Open the Web Control Hub (Default)"
        echo "  start [all|id]      Start all apps or a specific app"
        echo "  stop [all|id]       Stop all apps or a specific app"
        echo "  status              Display real-time status table"
        echo "  automations         Show all daily scheduled automation routines"
        echo "  run-auto <id>       Manually trigger a daily automation routine"
        echo "  install-daemon      Install persistent macOS LaunchAgent"
        echo "  logs <id>           Stream live logs for an app"
        echo ""
        echo "Available app IDs:"
        echo "  portfolio, qlikhunter, globalcareer, aethermind,"
        echo "  bharatalpha_invest_ui, bharatalpha_trade_ui, mirofish_ui"
        echo ""
        echo "Available automation IDs:"
        echo "  qlikhunter_daily, globalcareer_morning, globalcareer_evening, bharatalpha_universe"
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo "Run '$0 help' for available options."
        exit 1
        ;;
esac

