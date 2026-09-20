#!/usr/bin/env python3
"""
Antigravity Nexus — Unified App Launcher & Process Supervisor
Manages workspace applications, supervises lifecycle, healthchecks ports,
and serves the mission control dashboard.
"""

import os
import sys
import time
import datetime
import socket
import signal
import subprocess
import threading
from typing import Dict, Any, Optional

import psutil
from flask import Flask, jsonify, request, send_file

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(BASE_DIR) == "pradeepthallapelly369" and not os.path.exists(os.path.join(BASE_DIR, "BharatAlpha-AI-Trading-Engine")):
    parent_workspace = os.path.dirname(BASE_DIR)
    if os.path.exists(os.path.join(parent_workspace, "BharatAlpha-AI-Trading-Engine")):
        BASE_DIR = parent_workspace

LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# Select Python executable from launcher venv if available
VENV_PYTHON = os.path.join(BASE_DIR, ".venv_launcher", "bin", "python3")
PYTHON_BIN = VENV_PYTHON if os.path.exists(VENV_PYTHON) else sys.executable

# System PATH including local bins
SYSTEM_ENV = os.environ.copy()
SYSTEM_ENV["PATH"] = f"/Users/apple/.local/bin:{SYSTEM_ENV.get('PATH', '')}"
SYSTEM_ENV["PYTHONUNBUFFERED"] = "1"

NPM_BIN = "/Users/apple/.local/bin/npm" if os.path.exists("/Users/apple/.local/bin/npm") else "npm"

# Registered Applications Registry
APPS_REGISTRY: Dict[str, Dict[str, Any]] = {
    "portfolio": {
        "id": "portfolio",
        "name": "Pradeep Thallapelly Portfolio",
        "description": "Personal Portfolio & Showcase Website highlighting AI/ML engineering and projects.",
        "category": "Web Portfolio",
        "icon_emoji": "🌐",
        "icon_class": "icon-indigo",
        "port": 8080,
        "secondary_port": None,
        "cwd": os.path.join(BASE_DIR, "pradeepthallapelly369.github.io"),
        "command": [PYTHON_BIN, "-m", "http.server", "8080", "--bind", "127.0.0.1"],
        "url": "http://localhost:8080"
    },
    "qlikhunter": {
        "id": "qlikhunter",
        "name": "QlikHunter Automation Engine",
        "description": "Autonomous scouting bot, resume evaluator & application tracking web dashboard.",
        "category": "Career & Jobs",
        "icon_emoji": "🎯",
        "icon_class": "icon-emerald",
        "port": 5050,
        "secondary_port": None,
        "cwd": os.path.join(BASE_DIR, "QlikHunter-Automation-Engine"),
        "command": [PYTHON_BIN, "app.py"],
        "url": "http://localhost:5050"
    },
    "globalcareer": {
        "id": "globalcareer",
        "name": "GlobalCareer AI Engine",
        "description": "Autonomous global job hunting machine with multi-portal tracking and analytics dashboard.",
        "category": "Career & Jobs",
        "icon_emoji": "🌍",
        "icon_class": "icon-blue",
        "port": 8888,
        "secondary_port": None,
        "cwd": os.path.join(BASE_DIR, "GlobalCareer-AI-Engine", "GlobalCareer-AI-Engine"),
        "command": [PYTHON_BIN, "-m", "uvicorn", "dashboard.app:app", "--host", "0.0.0.0", "--port", "8888"],
        "url": "http://localhost:8888"
    },
    "aethermind": {
        "id": "aethermind",
        "name": "AetherMind 70B Local Agent",
        "description": "Local autonomous AI agent platform with live system tools and model connector.",
        "category": "AI Agents",
        "icon_emoji": "🧠",
        "icon_class": "icon-purple",
        "port": 7860,
        "secondary_port": None,
        "cwd": os.path.join(BASE_DIR, "GlobalCareer-AI-Engine", "aether_mind"),
        "command": [PYTHON_BIN, "app.py"],
        "url": "http://localhost:7860"
    },
    "bharatalpha_invest_ui": {
        "id": "bharatalpha_invest_ui",
        "name": "BharatAlpha Invest (Web UI)",
        "description": "Interactive React dashboard for stock screening, AI memos, technical charts, and portfolios.",
        "category": "Trading & FinTech",
        "icon_emoji": "📊",
        "icon_class": "icon-amber",
        "port": 5173,
        "secondary_port": 8000,
        "secondary_url": "http://localhost:8000/docs",
        "cwd": os.path.join(BASE_DIR, "BharatAlpha-AI-Trading-Engine", "bharat_alpha", "frontend"),
        "command": [NPM_BIN, "run", "dev", "--", "--port", "5173", "--host", "127.0.0.1"],
        "url": "http://localhost:5173"
    },
    "bharatalpha_invest_api": {
        "id": "bharatalpha_invest_api",
        "name": "BharatAlpha Invest (API)",
        "description": "Institutional stock market screener, technicals analyzer, and veteran AI analyst backend API.",
        "category": "Trading & FinTech",
        "icon_emoji": "📈",
        "icon_class": "icon-amber",
        "port": 8000,
        "secondary_port": None,
        "cwd": os.path.join(BASE_DIR, "BharatAlpha-AI-Trading-Engine", "bharat_alpha"),
        "command": [PYTHON_BIN, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"],
        "url": "http://localhost:8000/docs"
    },
    "bharatalpha_trade_ui": {
        "id": "bharatalpha_trade_ui",
        "name": "BharatAlpha Trade (Web UI)",
        "description": "High-frequency React options & futures terminal with real-time Greeks and payoff visualizer.",
        "category": "Trading & FinTech",
        "icon_emoji": "⚡",
        "icon_class": "icon-rose",
        "port": 5174,
        "secondary_port": 8001,
        "secondary_url": "http://localhost:8001/docs",
        "cwd": os.path.join(BASE_DIR, "BharatAlpha-AI-Trading-Engine", "bharat_alpha_trade", "frontend"),
        "command": [NPM_BIN, "run", "dev", "--", "--port", "5174", "--host", "127.0.0.1"],
        "url": "http://localhost:5174"
    },
    "bharatalpha_trade_api": {
        "id": "bharatalpha_trade_api",
        "name": "BharatAlpha Trade (API)",
        "description": "FastAPI execution engine & Greeks calculator for algorithmic options trading.",
        "category": "Trading & FinTech",
        "icon_emoji": "📉",
        "icon_class": "icon-rose",
        "port": 8001,
        "secondary_port": None,
        "cwd": os.path.join(BASE_DIR, "BharatAlpha-AI-Trading-Engine", "bharat_alpha_trade"),
        "command": [PYTHON_BIN, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8001"],
        "url": "http://localhost:8001/docs"
    },
    "mirofish_ui": {
        "id": "mirofish_ui",
        "name": "MiroFish Simulation (Web UI)",
        "description": "Multi-agent swarm simulation interface with real-time agent graphing and analysis.",
        "category": "AI Agents",
        "icon_emoji": "🐟",
        "icon_class": "icon-cyan",
        "port": 5175,
        "secondary_port": 5001,
        "secondary_url": "http://localhost:5001",
        "cwd": os.path.join(BASE_DIR, "MiroFish", "frontend"),
        "command": [NPM_BIN, "run", "dev", "--", "--port", "5175", "--host", "127.0.0.1"],
        "url": "http://localhost:5175"
    },
    "mirofish_api": {
        "id": "mirofish_api",
        "name": "MiroFish Engine (API)",
        "description": "Swarm intelligence simulation backend supporting social media and persona agents.",
        "category": "AI Agents",
        "icon_emoji": "🤖",
        "icon_class": "icon-cyan",
        "port": 5001,
        "secondary_port": None,
        "cwd": os.path.join(BASE_DIR, "MiroFish", "backend"),
        "command": [PYTHON_BIN, "run.py"],
        "url": "http://localhost:5001"
    },
    "colibri_studio": {
        "id": "colibri_studio",
        "name": "Colibrì Studio (MoE Orchestrator)",
        "description": "Multi-tier Mixture-of-Experts inference engine & cortex visualizer with dynamic auto-routing.",
        "category": "AI Agents",
        "icon_emoji": "🐦",
        "icon_class": "icon-cyan",
        "port": 8088,
        "secondary_port": None,
        "cwd": os.path.join(BASE_DIR, "GlobalCareer-AI-Engine", "colibri-studio"),
        "command": [PYTHON_BIN, "-m", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8088"],
        "url": "http://localhost:8088"
    }
}

# Runtime tracking state
RUNNING_PROCESSES: Dict[str, subprocess.Popen] = {}
PROCESS_METADATA: Dict[str, Dict[str, Any]] = {}
STATE_LOCK = threading.Lock()

app = Flask(__name__, static_folder=None)


def is_port_in_use(port: int) -> bool:
    """Quick socket check to verify if port is listening."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.2)
        return s.connect_ex(("127.0.0.1", port)) == 0


def kill_port_owner(port: int):
    """Force kill any lingering process on the specified port."""
    try:
        cmd = f"lsof -ti :{port} | xargs kill -9 2>/dev/null || true"
        subprocess.run(cmd, shell=True, timeout=5)
    except Exception as e:
        print(f"Error killing port {port} owner: {e}")


def get_app_status(app_id: str) -> Dict[str, Any]:
    """Retrieve up-to-date status and metrics for an app."""
    config = APPS_REGISTRY[app_id]
    port = config["port"]
    port_open = is_port_in_use(port)

    with STATE_LOCK:
        proc = RUNNING_PROCESSES.get(app_id)
        meta = PROCESS_METADATA.get(app_id, {})

    is_proc_alive = proc is not None and proc.poll() is None

    pid = None
    mem_mb = None
    if is_proc_alive and proc:
        pid = proc.pid
        try:
            p = psutil.Process(pid)
            mem_mb = round(p.memory_info().rss / (1024 * 1024), 1)
        except Exception:
            pass

    # Status deduction
    if port_open:
        status = "RUNNING"
    elif is_proc_alive:
        # Process is alive but port hasn't opened yet
        start_time = meta.get("start_time", time.time())
        if time.time() - start_time > 15:
            status = "FAILED"
        else:
            status = "STARTING"
    else:
        status = "OFFLINE"

    return {
        **config,
        "status": status,
        "pid": pid,
        "memory_mb": mem_mb,
        "port_open": port_open
    }


# Web UI
@app.route("/")
def index():
    dashboard_path = os.path.join(BASE_DIR, "launcher_dashboard.html")
    if os.path.exists(dashboard_path):
        return send_file(dashboard_path)
    return "<h1>Antigravity Nexus</h1><p>launcher_dashboard.html not found</p>", 404


# API: Status & Telemetry
@app.route("/api/status")
def api_status():
    status_map = {}
    for app_id in APPS_REGISTRY:
        status_map[app_id] = get_app_status(app_id)

    # System telemetry
    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory().percent

    return jsonify({
        "telemetry": {
            "cpu_percent": cpu,
            "memory_percent": mem,
            "platform": sys.platform
        },
        "apps": status_map
    })


# API: Start App
@app.route("/api/apps/<app_id>/start", methods=["POST"])
def api_start_app(app_id: str):
    if app_id not in APPS_REGISTRY:
        return jsonify({"success": False, "error": f"Unknown app: {app_id}"}), 404

    config = APPS_REGISTRY[app_id]
    port = config["port"]

    # Check if already running
    if is_port_in_use(port):
        return jsonify({"success": True, "message": f"App {app_id} is already running on port {port}"})

    # Kill stale processes on the port just in case
    kill_port_owner(port)

    log_file_path = os.path.join(LOGS_DIR, f"{app_id}.log")
    try:
        log_out = open(log_file_path, "a", encoding="utf-8")
        log_out.write(f"\n\n--- [LAUNCH] {config['name']} at {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        log_out.flush()

        # Execute
        proc = subprocess.Popen(
            config["command"],
            cwd=config["cwd"],
            stdout=log_out,
            stderr=subprocess.STDOUT,
            env=SYSTEM_ENV,
            start_new_session=True
        )

        with STATE_LOCK:
            RUNNING_PROCESSES[app_id] = proc
            PROCESS_METADATA[app_id] = {
                "start_time": time.time(),
                "pid": proc.pid
            }

        return jsonify({"success": True, "pid": proc.pid})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# API: Stop App
@app.route("/api/apps/<app_id>/stop", methods=["POST"])
def api_stop_app(app_id: str):
    if app_id not in APPS_REGISTRY:
        return jsonify({"success": False, "error": f"Unknown app: {app_id}"}), 404

    config = APPS_REGISTRY[app_id]
    port = config["port"]

    with STATE_LOCK:
        proc = RUNNING_PROCESSES.pop(app_id, None)
        PROCESS_METADATA.pop(app_id, None)

    # Terminate process tree
    if proc and proc.poll() is None:
        try:
            parent = psutil.Process(proc.pid)
            for child in parent.children(recursive=True):
                child.terminate()
            parent.terminate()
            proc.wait(timeout=3)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    # Free port
    kill_port_owner(port)
    if config.get("secondary_port"):
        kill_port_owner(config["secondary_port"])

    return jsonify({"success": True, "message": f"Stopped {app_id}"})


# API: Restart App
@app.route("/api/apps/<app_id>/restart", methods=["POST"])
def api_restart_app(app_id: str):
    api_stop_app(app_id)
    time.sleep(1)
    return api_start_app(app_id)


# API: Get App Logs
@app.route("/api/apps/<app_id>/logs")
def api_get_logs(app_id: str):
    log_file_path = os.path.join(LOGS_DIR, f"{app_id}.log")
    if not os.path.exists(log_file_path):
        return jsonify({"logs": "No logs recorded yet."})

    try:
        with open(log_file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
            tail = lines[-150:] if len(lines) > 150 else lines
            return jsonify({"logs": "".join(tail)})
    except Exception as e:
        return jsonify({"logs": f"Error reading logs: {e}"}), 500


# API: Launch All Apps
@app.route("/api/start-all", methods=["POST"])
def api_start_all():
    results = {}
    for app_id in APPS_REGISTRY:
        results[app_id] = api_start_app(app_id).json
    return jsonify({"success": True, "results": results})


# API: Stop All Apps
@app.route("/api/stop-all", methods=["POST"])
def api_stop_all():
    results = {}
    for app_id in APPS_REGISTRY:
        results[app_id] = api_stop_app(app_id).json
    return jsonify({"success": True, "results": results})


# ══════════════════════════════════════════════════════════════════════════════
# Daily Automations Engine
# ══════════════════════════════════════════════════════════════════════════════
import datetime

AUTOMATIONS_REGISTRY: Dict[str, Dict[str, Any]] = {
    "qlikhunter_daily": {
        "id": "qlikhunter_daily",
        "name": "QlikHunter Job Scout & AI Evaluator",
        "description": "Scrapes global Qlik/PowerBI roles, computes AI fit scores, and emails daily candidate dossiers.",
        "schedule_display": "Daily at 08:00 AM IST",
        "target_hour_ist": 8,
        "target_minute_ist": 0,
        "weekdays_only": False,
        "cwd": os.path.join(BASE_DIR, "QlikHunter-Automation-Engine"),
        "command": [PYTHON_BIN, "main.py"],
        "category": "Career & Jobs",
        "icon_emoji": "🎯",
        "icon_class": "icon-emerald"
    },
    "globalcareer_morning": {
        "id": "globalcareer_morning",
        "name": "GlobalCareer Morning Scan",
        "description": "Scans 300+ global portals across 80+ countries, auto-tailors resumes, and outputs applications.",
        "schedule_display": "Daily at 09:30 AM IST",
        "target_hour_ist": 9,
        "target_minute_ist": 30,
        "weekdays_only": False,
        "cwd": os.path.join(BASE_DIR, "GlobalCareer-AI-Engine", "GlobalCareer-AI-Engine"),
        "command": [PYTHON_BIN, "main.py"],
        "category": "Career & Jobs",
        "icon_emoji": "🌍",
        "icon_class": "icon-blue"
    },
    "globalcareer_evening": {
        "id": "globalcareer_evening",
        "name": "GlobalCareer Evening Scan",
        "description": "Second daily cycle tracking newly posted US & Europe time-zone jobs and updating tracking database.",
        "schedule_display": "Daily at 09:30 PM IST",
        "target_hour_ist": 21,
        "target_minute_ist": 30,
        "weekdays_only": False,
        "cwd": os.path.join(BASE_DIR, "GlobalCareer-AI-Engine", "GlobalCareer-AI-Engine"),
        "command": [PYTHON_BIN, "main.py"],
        "category": "Career & Jobs",
        "icon_emoji": "🌙",
        "icon_class": "icon-purple"
    },
    "bharatalpha_universe": {
        "id": "bharatalpha_universe",
        "name": "BharatAlpha NSE Universe Sync",
        "description": "Post-market refresh of 2500+ NSE equities, applying ₹5000 Cr market-cap cutoff and universe grouping.",
        "schedule_display": "Mon - Fri at 04:00 PM IST",
        "target_hour_ist": 16,
        "target_minute_ist": 0,
        "weekdays_only": True,
        "cwd": os.path.join(BASE_DIR, "BharatAlpha-AI-Trading-Engine", "bharat_alpha"),
        "command": [PYTHON_BIN, "backend/engine/daily_universe_updater.py"],
        "category": "Trading & FinTech",
        "icon_emoji": "📈",
        "icon_class": "icon-amber"
    }
}

AUTOMATION_STATE: Dict[str, Dict[str, Any]] = {
    auto_id: {
        "last_run": None,
        "last_run_epoch": 0,
        "last_status": "IDLE",
        "is_running": False,
        "last_duration_sec": None
    }
    for auto_id in AUTOMATIONS_REGISTRY
}
SCHEDULER_ENABLED = True
AUTO_LOCK = threading.Lock()


def get_ist_now() -> datetime.datetime:
    """Return current timestamp in IST (UTC+5:30)."""
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    return utc_now + datetime.timedelta(hours=5, minutes=30)


def calculate_next_run(auto: Dict[str, Any]) -> str:
    """Compute human-friendly next run time string in IST."""
    now_ist = get_ist_now()
    target_h = auto["target_hour_ist"]
    target_m = auto["target_minute_ist"]
    
    target_today = now_ist.replace(hour=target_h, minute=target_m, second=0, microsecond=0)
    if now_ist >= target_today:
        target_date = target_today + datetime.timedelta(days=1)
    else:
        target_date = target_today

    if auto.get("weekdays_only"):
        while target_date.weekday() >= 5: # 5=Sat, 6=Sun
            target_date += datetime.timedelta(days=1)

    diff = target_date - now_ist
    hours = int(diff.total_seconds() // 3600)
    minutes = int((diff.total_seconds() % 3600) // 60)
    
    time_str = target_date.strftime("%I:%M %p")
    day_label = "Today" if target_date.date() == now_ist.date() else "Tomorrow"
    return f"{day_label} at {time_str} IST (in {hours}h {minutes}m)"


def run_automation_task(auto_id: str):
    """Execute automation in background and stream logs."""
    if auto_id not in AUTOMATIONS_REGISTRY:
        return

    auto = AUTOMATIONS_REGISTRY[auto_id]
    log_path = os.path.join(LOGS_DIR, f"automation_{auto_id}.log")
    
    with AUTO_LOCK:
        if AUTOMATION_STATE[auto_id]["is_running"]:
            return
        AUTOMATION_STATE[auto_id]["is_running"] = True

    start_t = time.time()
    ist_str = get_ist_now().strftime("%Y-%m-%d %I:%M:%S %p IST")
    try:
        with open(log_path, "a", encoding="utf-8") as out:
            out.write(f"\n\n════════════════════════════════════════════════════════\n")
            out.write(f"🚀 [AUTO-RUN] {auto['name']} started at {ist_str}\n")
            out.write(f"════════════════════════════════════════════════════════\n")
            out.flush()

            proc = subprocess.run(
                auto["command"],
                cwd=auto["cwd"],
                stdout=out,
                stderr=subprocess.STDOUT,
                env=SYSTEM_ENV,
                timeout=1800 # 30 min max
            )
            exit_code = proc.returncode

        duration = round(time.time() - start_t, 1)
        with AUTO_LOCK:
            AUTOMATION_STATE[auto_id]["is_running"] = False
            AUTOMATION_STATE[auto_id]["last_run"] = ist_str
            AUTOMATION_STATE[auto_id]["last_run_epoch"] = time.time()
            AUTOMATION_STATE[auto_id]["last_status"] = "SUCCESS" if exit_code == 0 else "ERROR"
            AUTOMATION_STATE[auto_id]["last_duration_sec"] = duration

    except Exception as e:
        duration = round(time.time() - start_t, 1)
        with AUTO_LOCK:
            AUTOMATION_STATE[auto_id]["is_running"] = False
            AUTOMATION_STATE[auto_id]["last_run"] = ist_str
            AUTOMATION_STATE[auto_id]["last_run_epoch"] = time.time()
            AUTOMATION_STATE[auto_id]["last_status"] = "ERROR"
            AUTOMATION_STATE[auto_id]["last_duration_sec"] = duration
        with open(log_path, "a", encoding="utf-8") as out:
            out.write(f"\n[Execution Exception]: {e}\n")


def scheduler_daemon_loop():
    """Background daemon loop that triggers automations at their scheduled times."""
    print("⏰ Antigravity Nexus Automation Scheduler daemon started.")
    while True:
        try:
            time.sleep(25)
            if not SCHEDULER_ENABLED:
                continue

            now_ist = get_ist_now()
            cur_h = now_ist.hour
            cur_m = now_ist.minute
            is_weekday = now_ist.weekday() < 5

            for auto_id, auto in AUTOMATIONS_REGISTRY.items():
                if auto.get("weekdays_only") and not is_weekday:
                    continue

                if auto["target_hour_ist"] == cur_h and auto["target_minute_ist"] == cur_m:
                    last_epoch = AUTOMATION_STATE[auto_id]["last_run_epoch"]
                    # Prevent running multiple times within the same minute
                    if time.time() - last_epoch > 70:
                        threading.Thread(target=run_automation_task, args=(auto_id,), daemon=True).start()
        except Exception as e:
            print(f"Scheduler loop error: {e}")


# API: Automations Status
@app.route("/api/automations")
def api_automations():
    res = {}
    with AUTO_LOCK:
        for auto_id, auto in AUTOMATIONS_REGISTRY.items():
            state = AUTOMATION_STATE[auto_id]
            res[auto_id] = {
                **auto,
                **state,
                "next_run": calculate_next_run(auto),
                "scheduler_enabled": SCHEDULER_ENABLED
            }
    return jsonify({
        "scheduler_enabled": SCHEDULER_ENABLED,
        "current_time_ist": get_ist_now().strftime("%I:%M:%S %p IST"),
        "automations": res
    })


# API: Manual Run Trigger
@app.route("/api/automations/<auto_id>/run", methods=["POST"])
def api_trigger_automation(auto_id: str):
    if auto_id not in AUTOMATIONS_REGISTRY:
        return jsonify({"success": False, "error": f"Unknown automation: {auto_id}"}), 404

    if AUTOMATION_STATE[auto_id]["is_running"]:
        return jsonify({"success": False, "error": "Automation is already in progress."})

    threading.Thread(target=run_automation_task, args=(auto_id,), daemon=True).start()
    return jsonify({"success": True, "message": f"Triggered {AUTOMATIONS_REGISTRY[auto_id]['name']}"})


# API: Get Automation Logs
@app.route("/api/automations/<auto_id>/logs")
def api_get_automation_logs(auto_id: str):
    log_file_path = os.path.join(LOGS_DIR, f"automation_{auto_id}.log")
    if not os.path.exists(log_file_path):
        return jsonify({"logs": "No execution logs recorded yet. Click 'Run Now' to execute."})

    try:
        with open(log_file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
            tail = lines[-150:] if len(lines) > 150 else lines
            return jsonify({"logs": "".join(tail)})
    except Exception as e:
        return jsonify({"logs": f"Error reading logs: {e}"}), 500


# API: Toggle Scheduler
@app.route("/api/automations/toggle", methods=["POST"])
def api_toggle_scheduler():
    global SCHEDULER_ENABLED
    SCHEDULER_ENABLED = not SCHEDULER_ENABLED
    return jsonify({"success": True, "scheduler_enabled": SCHEDULER_ENABLED})


def main():
    hub_port = int(os.environ.get("HUB_PORT", 3333))
    print(f"============================================================")
    print(f" 🚀 Antigravity Nexus — Universal App Launcher & Scheduler")
    print(f" 🌐 Dashboard available at: http://localhost:{hub_port}")
    print(f"============================================================")

    # Start background scheduler thread
    threading.Thread(target=scheduler_daemon_loop, daemon=True).start()

    app.run(host="0.0.0.0", port=hub_port, debug=False)


if __name__ == "__main__":
    main()

