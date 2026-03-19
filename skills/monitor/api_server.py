#!/usr/bin/env python3
"""
Agent Monitor REST API Server

提供 REST API 供外部系統查詢監控數據
"""

import os
import json
from flask import Flask, jsonify, request
from flask_cors import CORS

# 導入監控模組
import sys
import os
monitor_path = os.path.join(os.path.dirname(__file__))
sys.path.insert(0, monitor_path)

# 避免與標準庫衝突
import logging as stdlib_logging
import importlib

# 確保正確載入模組
importlib.import_module('alerts_v2')
importlib.import_module('health_score')
importlib.import_module('cost_tracker')
importlib.import_module('unified_dashboard')
importlib.import_module('journey_tracker')

from alerts_v2 import alert_manager
from health_score import health_scorer, AgentMetrics
from cost_tracker import cost_tracker
from unified_dashboard import unified_dashboard
from journey_tracker import journey_tracker
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ============== 數據端點 ==============

@app.route('/api/health', methods=['GET'])
def health():
    """服務健康檢查"""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "agent-monitor-api"
    })


@app.route('/api/metrics/summary', methods=['GET'])
def metrics_summary():
    """獲取監控摘要"""
    return jsonify(unified_dashboard.get_summary())


@app.route('/api/metrics/agents', methods=['GET'])
def metrics_agents():
    """獲取所有 Agent 狀態"""
    summary = unified_dashboard.get_summary()
    return jsonify(summary.get("agents", []))


@app.route('/api/metrics/<agent_id>', methods=['GET'])
def metrics_agent(agent_id):
    """獲取單個 Agent 監控數據"""
    summary = unified_dashboard.get_summary()
    for agent in summary.get("agents", []):
        if agent["id"] == agent_id:
            return jsonify(agent)
    return jsonify({"error": "Agent not found"}), 404


@app.route('/api/metrics/trend', methods=['GET'])
def metrics_trend():
    """獲取效能趨勢"""
    period = request.args.get('period', '1h')
    return jsonify(unified_dashboard.get_trend(period))


@app.route('/api/agents/relationship', methods=['GET'])
def agent_relationship():
    """獲取 Agent 關係圖"""
    return jsonify(unified_dashboard.get_agent_relationship())


# ============== 警報端點 ==============

@app.route('/api/alerts', methods=['GET'])
def alerts_list():
    """獲取警報列表"""
    limit = int(request.args.get('limit', 100))
    agent_id = request.args.get('agent_id')
    
    alerts = alert_manager.get_alert_history(agent_id, limit)
    return jsonify(alerts)


@app.route('/api/alerts/<alert_id>', methods=['GET'])
def alert_detail(alert_id):
    """獲取單個警報詳情"""
    alerts = alert_manager.get_alert_history()
    for alert in alerts:
        if alert.get("id") == alert_id:
            return jsonify(alert)
    return jsonify({"error": "Alert not found"}), 404


@app.route('/api/alerts/check', methods=['POST'])
def alerts_check():
    """手動觸發警報檢查"""
    data = request.json
    agent_id = data.get('agent_id', 'unknown')
    metrics = data.get('metrics', {})
    
    alerts = alert_manager.check_and_notify(metrics, agent_id)
    return jsonify({
        "triggered": len(alerts),
        "alerts": alerts
    })


# ============== 健康評分端點 ==============

@app.route('/api/health/<agent_id>', methods=['GET'])
def health_score(agent_id):
    """獲取 Agent 健康評分"""
    # 從 unified_dashboard 獲取數據
    summary = unified_dashboard.get_summary()
    
    for agent in summary.get("agents", []):
        if agent["id"] == agent_id:
            # 構造 metrics
            metrics = AgentMetrics(
                agent_id=agent_id,
                timestamp=datetime.now(),
                total_requests=agent.get("requests", 0),
                successful_requests=agent.get("requests", 0) - agent.get("errors", 0),
                failed_requests=agent.get("errors", 0),
                latency_p95_ms=agent.get("latency_ms", 0)
            )
            return jsonify(health_scorer.calculate(metrics))
    
    return jsonify({"error": "Agent not found"}), 404


# ============== 成本端點 ==============

@app.route('/api/cost/summary', methods=['GET'])
def cost_summary():
    """獲取成本摘要"""
    period = request.args.get('period', 'daily')
    return jsonify(cost_tracker.get_all_agents_cost(period))


@app.route('/api/cost/<agent_id>', methods=['GET'])
def cost_agent(agent_id):
    """獲取單個 Agent 成本"""
    period = request.args.get('period', 'daily')
    return jsonify(cost_tracker.get_agent_cost(agent_id, period))


@app.route('/api/cost/trend', methods=['GET'])
def cost_trend():
    """獲取成本趨勢"""
    agent_id = request.args.get('agent_id')
    days = int(request.args.get('days', 7))
    return jsonify(cost_tracker.get_cost_trend(agent_id, days))


@app.route('/api/cost/record', methods=['POST'])
def cost_record():
    """記錄 Token 使用"""
    data = request.json
    
    cost = cost_tracker.record(
        agent_id=data.get('agent_id'),
        model=data.get('model', 'gpt-4'),
        input_tokens=data.get('input_tokens', 0),
        output_tokens=data.get('output_tokens', 0),
        duration_ms=data.get('duration_ms', 0)
    )
    
    return jsonify({"cost": cost})


# ============== Journey 端點 ==============

@app.route('/api/journey/<session_id>', methods=['GET'])
def journey_detail(session_id):
    """獲取對話旅程"""
    return jsonify({
        "journey": journey_tracker.export_journey_json(session_id)
    })


@app.route('/api/journey/user/<user_id>', methods=['GET'])
def journey_user(user_id):
    """獲取用戶所有旅程"""
    limit = int(request.args.get('limit', 10))
    journeys = journey_tracker.get_user_journeys(user_id, limit)
    
    return jsonify({
        "journeys": [
            {
                "journey_id": j.journey_id,
                "session_id": j.session_id,
                "start_time": j.start_time.isoformat(),
                "duration_minutes": j.duration_minutes,
                "agent_count": j.agent_count,
                "success_rate": j.success_rate
            }
            for j in journeys
        ]
    })


@app.route('/api/journey/patterns', methods=['GET'])
def journey_patterns():
    """分析行為模式"""
    user_id = request.args.get('user_id')
    return jsonify(journey_tracker.analyze_patterns(user_id))


# ============== 監控端點 ==============

@app.route('/api/monitor/start', methods=['POST'])
def monitor_start():
    """開始監控對話"""
    data = request.json
    
    journey_id = journey_tracker.start_journey(
        user_id=data.get('user_id'),
        session_id=data.get('session_id'),
        initial_agent=data.get('agent_id', 'musk')
    )
    
    # 註冊到儀表板
    unified_dashboard.register_agent(
        agent_id=data.get('agent_id'),
        agent_type=data.get('agent_type', 'main')
    )
    
    return jsonify({"journey_id": journey_id})


@app.route('/api/monitor/event', methods=['POST'])
def monitor_event():
    """記錄監控事件"""
    data = request.json
    
    event_type = data.get('type')
    session_id = data.get('session_id')
    agent_id = data.get('agent_id', 'unknown')
    user_id = data.get('user_id', 'unknown')
    
    if event_type == 'task_start':
        journey_tracker.add_step(
            session_id=session_id,
            agent_id=agent_id,
            agent_type=data.get('agent_type', 'main'),
            action='task_start',
            input_text=data.get('input', '')
        )
    elif event_type == 'task_end':
        journey_tracker.add_step(
            session_id=session_id,
            agent_id=agent_id,
            agent_type=data.get('agent_type', 'main'),
            action='task_end',
            output_text=data.get('output', ''),
            success=data.get('success', True)
        )
    elif event_type == 'error':
        journey_tracker.add_step(
            session_id=session_id,
            agent_id=agent_id,
            agent_type=data.get('agent_type', 'main'),
            action='error',
            error=data.get('error', ''),
            success=False
        )
    
    return jsonify({"status": "ok"})


@app.route('/api/monitor/end', methods=['POST'])
def monitor_end():
    """結束監控對話"""
    data = request.json
    journey_tracker.end_journey(data.get('session_id'))
    return jsonify({"status": "ok"})


# ============== Root Cause 端點 ==============

@app.route('/api/analyze/error', methods=['POST'])
def analyze_error():
    """分析錯誤根因"""
    from root_cause_analysis import root_cause_analyzer
    
    data = request.json
    
    analysis = root_cause_analyzer.analyze(
        error_message=data.get('error_message', ''),
        agent_id=data.get('agent_id', 'unknown'),
        session_id=data.get('session_id', ''),
        context=data.get('context', []),
        use_ai=data.get('use_ai', False)
    )
    
    return jsonify({
        "analysis_id": analysis.analysis_id,
        "root_cause": analysis.root_cause,
        "confidence": analysis.confidence,
        "category": analysis.category.value,
        "severity": analysis.severity.value,
        "recommendations": analysis.recommendations,
        "can_auto_fix": analysis.can_auto_fix
    })


# ============== 配置端點 ==============

@app.route('/api/config', methods=['GET'])
def config_get():
    """獲取配置"""
    return jsonify({
        "alerts": alert_manager.config,
        "thresholds": {
            "critical": alert_manager.THRESHOLDS["critical"],
            "warning": alert_manager.THRESHOLDS["warning"]
        }
    })


# ============== 主頁 ==============

@app.route('/', methods=['GET'])
def index():
    """API 首頁"""
    return jsonify({
        "name": "Agent Monitor API",
        "version": "2.0.0",
        "endpoints": {
            "health": "/api/health",
            "metrics": "/api/metrics/summary",
            "agents": "/api/metrics/agents",
            "alerts": "/api/alerts",
            "health_scores": "/api/health/<agent_id>",
            "cost": "/api/cost/summary",
            "journey": "/api/journey/<session_id>",
            "analyze": "/api/analyze/error"
        }
    })


# ============== 啟動 ==============

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting Agent Monitor API on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=True)
