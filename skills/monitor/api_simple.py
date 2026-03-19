#!/usr/bin/env python3
"""
Agent Monitor REST API Server - 簡化版

提供 REST API 供外部系統查詢監控數據
"""

import os
import json
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ============== 數據存儲（內存） ==============

class DataStore:
    def __init__(self):
        self.agents = {}
        self.alerts = []
        self.journeys = {}
        self.cost_records = []
    
    def add_agent(self, agent_id, agent_type, parent_id=None):
        self.agents[agent_id] = {
            "id": agent_id,
            "type": agent_type,
            "parent_id": parent_id,
            "status": "active",
            "requests": 0,
            "errors": 0,
            "latency_ms": 0,
            "health_score": 100
        }
    
    def add_alert(self, alert):
        self.alerts.append(alert)
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-1000:]
    
    def add_journey(self, journey):
        self.journeys[journey["session_id"]] = journey

store = DataStore()

# 預設添加一些 agent
store.add_agent("musk", "main")
store.add_agent("pm-agent", "pm", "musk")
store.add_agent("dev-agent", "dev", "musk")

# ============== API 端點 ==============

@app.route('/')
def index():
    return jsonify({
        "name": "Agent Monitor API",
        "version": "2.0.0",
        "endpoints": [
            "/api/health",
            "/api/agents",
            "/api/agents/<id>",
            "/api/alerts",
            "/api/cost",
            "/api/journey/<session_id>"
        ]
    })


@app.route('/api/health')
def health():
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/agents', methods=['GET'])
def agents_list():
    return jsonify(list(store.agents.values()))


@app.route('/api/agents/<agent_id>', methods=['GET'])
def agent_detail(agent_id):
    if agent_id in store.agents:
        return jsonify(store.agents[agent_id])
    return jsonify({"error": "Not found"}), 404


@app.route('/api/agents', methods=['POST'])
def agent_create():
    data = request.json
    store.add_agent(
        data.get('agent_id'),
        data.get('agent_type', 'main'),
        data.get('parent_id')
    )
    return jsonify({"status": "ok"})


@app.route('/api/agents/<agent_id>/metrics', methods=['POST'])
def agent_update_metrics(agent_id):
    if agent_id not in store.agents:
        return jsonify({"error": "Not found"}), 404
    
    data = request.json
    agent = store.agents[agent_id]
    agent['requests'] = data.get('requests', agent['requests'])
    agent['errors'] = data.get('errors', agent['errors'])
    agent['latency_ms'] = data.get('latency_ms', agent['latency_ms'])
    
    # 計算健康分數
    if agent['requests'] > 0:
        success_rate = (agent['requests'] - agent['errors']) / agent['requests']
        agent['health_score'] = int(success_rate * 100)
    
    return jsonify(agent)


@app.route('/api/alerts', methods=['GET'])
def alerts_list():
    limit = int(request.args.get('limit', 100))
    return jsonify(store.alerts[-limit:])


@app.route('/api/alerts', methods=['POST'])
def alerts_create():
    data = request.json
    alert = {
        "id": f"alert-{len(store.alerts)}",
        "timestamp": datetime.now().isoformat(),
        "level": data.get('level', 'warning'),
        "message": data.get('message', ''),
        "agent_id": data.get('agent_id', 'unknown')
    }
    store.add_alert(alert)
    return jsonify(alert)


@app.route('/api/cost', methods=['GET'])
def cost_summary():
    return jsonify({
        "total_cost": len(store.cost_records) * 0.01,  # 模擬
        "requests": len(store.cost_records),
        "agents": list(set(r.get('agent_id') for r in store.cost_records))
    })


@app.route('/api/cost', methods=['POST'])
def cost_record():
    data = request.json
    record = {
        "timestamp": datetime.now().isoformat(),
        "agent_id": data.get('agent_id'),
        "model": data.get('model', 'gpt-4'),
        "input_tokens": data.get('input_tokens', 0),
        "output_tokens": data.get('output_tokens', 0)
    }
    store.cost_records.append(record)
    return jsonify({"status": "ok", "cost": 0.01})


@app.route('/api/journey/<session_id>', methods=['GET'])
def journey_detail(session_id):
    if session_id in store.journeys:
        return jsonify(store.journeys[session_id])
    return jsonify({"error": "Not found"}), 404


@app.route('/api/journey', methods=['POST'])
def journey_create():
    data = request.json
    journey = {
        "session_id": data.get('session_id'),
        "user_id": data.get('user_id'),
        "agent_id": data.get('agent_id'),
        "start_time": datetime.now().isoformat(),
        "steps": []
    }
    store.add_journey(journey)
    return jsonify({"status": "ok"})


@app.route('/api/journey/<session_id>/step', methods=['POST'])
def journey_add_step(session_id):
    if session_id not in store.journeys:
        return jsonify({"error": "Session not found"}), 404
    
    data = request.json
    step = {
        "timestamp": datetime.now().isoformat(),
        "action": data.get('action', ''),
        "input": data.get('input', ''),
        "output": data.get('output', '')
    }
    store.journeys[session_id]["steps"].append(step)
    return jsonify({"status": "ok"})


# ============== 啟動 ==============

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting Agent Monitor API on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)
