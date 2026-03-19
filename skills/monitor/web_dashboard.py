#!/usr/bin/env python3
"""
Agent Monitor Web Dashboard - Light Version

Simple Flask web dashboard for v2
"""

from flask import Flask, render_template_string, jsonify
from datetime import datetime
import os

app = Flask(__name__)

DEFAULT_PORT = 8080

# ============================================================================
# Mock Data
# ============================================================================

def get_agents():
    return [
        {"id": "agent-001", "name": "Code Generator", "status": "running", "health": 92},
        {"id": "agent-002", "name": "Reviewer", "status": "running", "health": 88},
        {"id": "agent-003", "name": "Tester", "status": "idle", "health": 95},
    ]

def get_metrics():
    return {
        "requests": 850,
        "success_rate": 96.2,
        "latency": 0.8,
        "cost_daily": 8.50
    }

def get_alerts():
    return [
        {"level": "warning", "title": "High Latency", "message": "P95 > 3s", "time": "15 min ago"}
    ]

# ============================================================================
# HTML Template
# ============================================================================

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent Monitor v2</title>
    <style>
        body { font-family: system-ui, -apple-system, sans-serif; background: #0d1117; color: #c9d1d9; margin: 0; padding: 20px; }
        h1 { color: #58a6ff; }
        .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }
        .stat { background: #161b22; padding: 20px; border-radius: 8px; border: 1px solid #30363d; }
        .stat .label { color: #8b949e; font-size: 12px; }
        .stat .value { font-size: 28px; font-weight: bold; color: #58a6ff; }
        .grid { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }
        .card { background: #161b22; padding: 20px; border-radius: 8px; border: 1px solid #30363d; }
        .card h2 { color: #8b949e; font-size: 14px; margin: 0 0 15px 0; }
        .agent { display: flex; justify-content: space-between; padding: 10px; background: #0d1117; margin: 5px 0; border-radius: 6px; }
        .status { width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin-right: 10px; }
        .running { background: #3fb950; }
        .idle { background: #d29922; }
        .failed { background: #f85149; }
    </style>
</head>
<body>
    <h1>🚀 Agent Monitor v2</h1>
    <div class="stats">
        <div class="stat"><div class="label">REQUESTS</div><div class="value">{{ m.requests }}</div></div>
        <div class="stat"><div class="label">SUCCESS RATE</div><div class="value">{{ m.success_rate }}%</div></div>
        <div class="stat"><div class="label">LATENCY</div><div class="value">{{ m.latency }}s</div></div>
        <div class="stat"><div class="label">DAILY COST</div><div class="value">${{ m.cost_daily }}</div></div>
    </div>
    <div class="grid">
        <div class="card">
            <h2>🤖 AGENTS</h2>
            {% for a in agents %}
            <div class="agent">
                <span><span class="status {{ a.status }}"></span>{{ a.name }}</span>
                <span>{{ a.health }}/100</span>
            </div>
            {% endfor %}
        </div>
        <div class="card">
            <h2>⚠️ ALERTS</h2>
            {% for a in alerts %}
            <div class="agent">
                <span>{{ a.title }}</span>
                <span>{{ a.time }}</span>
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML, agents=get_agents(), metrics=get_metrics(), alerts=get_alerts())

@app.route('/api/agents')
def api_agents():
    return jsonify(get_agents())

@app.route('/api/metrics')
def api_metrics():
    return jsonify(get_metrics())

@app.route('/api/alerts')
def api_alerts():
    return jsonify(get_alerts())

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.getenv('PORT', DEFAULT_PORT))
    print(f"\n🚀 Agent Monitor v2 Dashboard")
    print(f"   http://localhost:{port}\n")
    app.run(host='0.0.0.0', port=port, debug=True)
