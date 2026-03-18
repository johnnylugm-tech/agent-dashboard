#!/usr/bin/env python3
"""
統一監控儀表板 v2
參考: playbooks/multi-agent-collaboration-v2.md Phase 5 監控

功能：
- 聚合多個 Agent 的數據
- 顯示統一視圖
- 效能趨勢圖
- Agent 關係圖
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import defaultdict
import json


@dataclass
class AgentSnapshot:
    """單個 Agent 快照"""
    agent_id: str
    agent_type: str  # pm, dev, research, review, etc.
    parent_id: Optional[str]  # 上級 Agent
    status: str  # active, idle, error, offline
    timestamp: datetime
    
    # 指標
    total_requests: int = 0
    success_count: int = 0
    error_count: int = 0
    avg_latency_ms: float = 0.0
    
    # 健康評分
    health_score: float = 0.0
    health_level: str = "unknown"  # 🟢🟡🔴


class UnifiedDashboard:
    """
    統一監控儀表板
    
    展示同一 Gateway 下所有 Agent 的匯總狀態
    """
    
    def __init__(self):
        self.agents: Dict[str, AgentSnapshot] = {}
        self.call_graph: Dict[str, List[str]] = defaultdict(list)  # parent -> [children]
        self.metrics_history: List[Dict] = []
    
    def register_agent(self, agent_id: str, agent_type: str, parent_id: str = None):
        """註冊 Agent"""
        snapshot = AgentSnapshot(
            agent_id=agent_id,
            agent_type=agent_type,
            parent_id=parent_id,
            status="active",
            timestamp=datetime.now()
        )
        self.agents[agent_id] = snapshot
        
        # 記錄調用關係
        if parent_id:
            self.call_graph[parent_id].append(agent_id)
    
    def update_metrics(self, agent_id: str, metrics: Dict):
        """更新 Agent 指標"""
        if agent_id not in self.agents:
            return
        
        agent = self.agents[agent_id]
        agent.total_requests = metrics.get("total_requests", 0)
        agent.success_count = metrics.get("success_count", 0)
        agent.error_count = metrics.get("error_count", 0)
        agent.avg_latency_ms = metrics.get("avg_latency_ms", 0)
        agent.health_score = metrics.get("health_score", 0)
        agent.health_level = metrics.get("health_level", "unknown")
        agent.timestamp = datetime.now()
    
    def get_summary(self) -> Dict:
        """獲取儀表板摘要"""
        total_agents = len(self.agents)
        active_agents = sum(1 for a in self.agents.values() if a.status == "active")
        error_agents = sum(1 for a in self.agents.values() if a.status == "error")
        
        # 計算匯總指標
        total_requests = sum(a.total_requests for a in self.agents.values())
        total_errors = sum(a.error_count for a in self.agents.values())
        
        avg_health = sum(a.health_score for a in self.agents.values()) / total_agents if total_agents > 0 else 0
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_agents": total_agents,
            "active_agents": active_agents,
            "error_agents": error_agents,
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": total_errors / total_requests if total_requests > 0 else 0,
            "avg_health_score": round(avg_health, 1),
            "agents": [
                {
                    "id": a.agent_id,
                    "type": a.agent_type,
                    "status": a.status,
                    "health": a.health_level,
                    "score": a.health_score,
                    "requests": a.total_requests,
                    "errors": a.error_count,
                    "latency_ms": a.avg_latency_ms
                }
                for a in self.agents.values()
            ]
        }
    
    def get_agent_relationship(self) -> Dict:
        """獲取 Agent 關係圖"""
        nodes = []
        edges = []
        
        # 節點
        for agent_id, agent in self.agents.items():
            nodes.append({
                "id": agent_id,
                "label": f"{agent.agent_type}",
                "status": agent.status,
                "health": agent.health_level
            })
        
        # 邊（調用關係）
        for parent_id, children in self.call_graph.items():
            for child_id in children:
                edges.append({
                    "from": parent_id,
                    "to": child_id
                })
        
        return {"nodes": nodes, "edges": edges}
    
    def get_trend(self, period: str = "1h") -> Dict:
        """效能趨勢數據"""
        # 模擬歷史數據
        now = datetime.now()
        
        if period == "1h":
            intervals = 12  # 5分鐘一個點
            delta = timedelta(minutes=5)
        elif period == "24h":
            intervals = 24
            delta = timedelta(hours=1)
        else:  # 7d
            intervals = 7
            delta = timedelta(days=1)
        
        # 模擬趨勢數據
        trend = []
        for i in range(intervals):
            timestamp = now - delta * (intervals - i - 1)
            
            # 模擬數據（實際應該從數據庫讀取）
            trend.append({
                "timestamp": timestamp.isoformat(),
                "requests": 100 + i * 10 + (hash(str(i)) % 50),
                "success_rate": 0.85 + (i % 10) * 0.01,
                "avg_latency": 1500 + (i % 20) * 100,
                "error_count": 5 + (i % 5)
            })
        
        return {
            "period": period,
            "data": trend
        }
    
    def get_journey(self, session_id: str, user_id: str) -> Dict:
        """
        跨對話追蹤
        追蹤單一用戶在不同 Agent 間流轉的完整旅程
        """
        # 模擬數據
        journey = {
            "session_id": session_id,
            "user_id": user_id,
            "steps": [
                {
                    "step": 1,
                    "agent": "musk",
                    "action": "用戶請求",
                    "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat(),
                    "input": "查詢高鐵時刻表",
                    "output": "已開啟時刻表查詢"
                },
                {
                    "step": 2,
                    "agent": "research-agent",
                    "action": "調研TDX API",
                    "timestamp": (datetime.now() - timedelta(minutes=25)).isoformat(),
                    "input": "查詢高鐵 API",
                    "output": "API 需要審核"
                },
                {
                    "step": 3,
                    "agent": "dev-agent",
                    "action": "開發下載腳本",
                    "timestamp": (datetime.now() - timedelta(minutes=20)).isoformat(),
                    "input": "下載PDF",
                    "output": "完成下載"
                }
            ],
            "total_agents": 3,
            "total_duration_minutes": 30
        }
        
        return journey
    
    def generate_dashboard_json(self) -> str:
        """生成儀表板 JSON 數據（供前端使用）"""
        data = {
            "summary": self.get_summary(),
            "relationship": self.get_agent_relationship(),
            "trend_1h": self.get_trend("1h"),
            "trend_24h": self.get_trend("24h")
        }
        
        return json.dumps(data, ensure_ascii=False, indent=2)


# 單例
unified_dashboard = UnifiedDashboard()


# ============ 使用範例 ============

if __name__ == "__main__":
    # 註冊 Agent（模擬星型架構）
    dashboard = UnifiedDashboard()
    
    # Main Agent
    dashboard.register_agent("musk", "main", parent_id=None)
    dashboard.register_agent("pm-agent", "pm", parent_id="musk")
    dashboard.register_agent("dev-agent", "dev", parent_id="musk")
    dashboard.register_agent("research-agent", "research", parent_id="pm-agent")
    dashboard.register_agent("review-agent", "review", parent_id="musk")
    
    # 更新指標
    dashboard.update_metrics("musk", {
        "total_requests": 100,
        "success_count": 95,
        "error_count": 5,
        "avg_latency_ms": 1200,
        "health_score": 92,
        "health_level": "🟢"
    })
    
    dashboard.update_metrics("dev-agent", {
        "total_requests": 50,
        "success_count": 45,
        "error_count": 5,
        "avg_latency_ms": 2500,
        "health_score": 78,
        "health_level": "🟡"
    })
    
    # 輸出摘要
    print("="*50)
    print("📊 統一監控儀表板")
    print("="*50)
    
    summary = dashboard.get_summary()
    print(f"\n🕐 {summary['timestamp']}")
    print(f"\n📈 總覽:")
    print(f"  - Agent 總數: {summary['total_agents']}")
    print(f"  - 運行中: {summary['active_agents']}")
    print(f"  - 錯誤: {summary['error_agents']}")
    print(f"  - 請求總數: {summary['total_requests']}")
    print(f"  - 錯誤率: {summary['error_rate']*100:.1f}%")
    print(f"  - 平均健康分: {summary['avg_health_score']}")
    
    print(f"\n🤖 Agent 狀態:")
    for agent in summary['agents']:
        print(f"  {agent['health']} {agent['id']} ({agent['type']}): {agent['score']}分")
    
    # 關係圖
    print(f"\n🔗 Agent 關係:")
    rel = dashboard.get_agent_relationship()
    for edge in rel['edges']:
        print(f"  {edge['from']} → {edge['to']}")
    
    # 趨勢
    print(f"\n📈 趨勢 (1h):")
    trend = dashboard.get_trend("1h")
    for point in trend['data'][:3]:
        print(f"  {point['timestamp'][:16]} - {point['requests']} 請求, {point['success_rate']*100:.0f}% 成功")
    
    print("\n" + "="*50)
