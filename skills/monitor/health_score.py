#!/usr/bin/env python3
"""
Agent 健康評分模組 v2
參考: playbooks/multi-agent-collaboration-v2.md Phase 5 監控指標
"""

from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class HealthLevel(Enum):
    """健康等級"""
    HEALTHY = "🟢"
    WARNING = "🟡"
    CRITICAL = "🔴"
    UNKNOWN = "⚪"


@dataclass
class AgentMetrics:
    """Agent 指標數據"""
    agent_id: str
    timestamp: datetime
    
    # 基礎指標
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    
    # 效能指標
    avg_latency_ms: float = 0.0
    latency_p50_ms: float = 0.0
    latency_p95_ms: float = 0.0
    latency_p99_ms: float = 0.0
    
    # 品質指標
    avg_confidence: float = 0.0
    retry_count: int = 0
    human_intervention_count: int = 0
    
    # 可用性
    uptime_seconds: int = 0
    downtime_seconds: int = 0
    
    @property
    def success_rate(self) -> float:
        """計算成功率"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    @property
    def error_rate(self) -> float:
        """計算錯誤率"""
        return 1.0 - self.success_rate
    
    @property
    def retry_rate(self) -> float:
        """計算重試率"""
        if self.total_requests == 0:
            return 0.0
        return self.retry_count / self.total_requests
    
    @property
    def availability(self) -> float:
        """計算可用性"""
        total = self.uptime_seconds + self.downtime_seconds
        if total == 0:
            return 1.0
        return self.uptime_seconds / total
    
    @property
    def human_intervention_rate(self) -> float:
        """計算人類干預率"""
        if self.total_requests == 0:
            return 0.0
        return self.human_intervention_count / self.total_requests


class HealthScorer:
    """
    健康評分計算器
    
    評分公式 (playbook v2 Phase 5):
    - 成功率權重: 40%
    - 錯誤率權重: 30%
    - 延遲權重: 20%
    - 可用性權重: 10%
    """
    
    # 評分權重
    WEIGHTS = {
        "success_rate": 0.40,      # 成功率 40%
        "error_rate": 0.30,        # 錯誤率 30%
        "latency": 0.20,           # 延遲 20%
        "availability": 0.10       # 可用性 10%
    }
    
    # 閾值配置
    THRESHOLDS = {
        "healthy": 90,
        "warning": 70,
        "critical": 0
    }
    
    # 延遲參考（毫秒）
    LATENCY_REFERENCE = {
        "excellent": 500,    # < 500ms
        "good": 1000,       # < 1s
        "fair": 2000,       # < 2s
        "poor": 5000        # < 5s
    }
    
    def calculate(self, metrics: AgentMetrics) -> Dict:
        """
        計算健康評分
        
        Returns:
            {
                "score": 85,
                "level": "🟡",
                "status": "Warning",
                "details": {...}
            }
        """
        
        # 1. 成功率得分 (0-100)
        success_score = metrics.success_rate * 100
        
        # 2. 錯誤率得分 (0-100) - 錯誤率越低越好
        error_score = (1 - metrics.error_rate) * 100
        
        # 3. 延遲得分 (0-100) - 延遲越低越好
        if metrics.latency_p95_ms <= self.LATENCY_REFERENCE["excellent"]:
            latency_score = 100
        elif metrics.latency_p95_ms <= self.LATENCY_REFERENCE["good"]:
            latency_score = 80
        elif metrics.latency_p95_ms <= self.LATENCY_REFERENCE["fair"]:
            latency_score = 60
        elif metrics.latency_p95_ms <= self.LATENCY_REFERENCE["poor"]:
            latency_score = 40
        else:
            latency_score = 20
        
        # 4. 可用性得分
        availability_score = metrics.availability * 100
        
        # 加權計算總分
        total_score = (
            success_score * self.WEIGHTS["success_rate"] +
            error_score * self.WEIGHTS["error_rate"] +
            latency_score * self.WEIGHTS["latency"] +
            availability_score * self.WEIGHTS["availability"]
        )
        
        # 確定等級
        if total_score >= self.THRESHOLDS["healthy"]:
            level = HealthLevel.HEALTHY
            status = "Healthy"
        elif total_score >= self.THRESHOLDS["warning"]:
            level = HealthLevel.WARNING
            status = "Warning"
        else:
            level = HealthLevel.CRITICAL
            status = "Critical"
        
        return {
            "agent_id": metrics.agent_id,
            "timestamp": metrics.timestamp.isoformat(),
            "score": round(total_score, 1),
            "level": level.value,
            "status": status,
            "details": {
                "success_rate": {
                    "value": round(metrics.success_rate * 100, 1),
                    "score": round(success_score, 1),
                    "weight": self.WEIGHTS["success_rate"]
                },
                "error_rate": {
                    "value": round(metrics.error_rate * 100, 1),
                    "score": round(error_score, 1),
                    "weight": self.WEIGHTS["error_rate"]
                },
                "latency_p95": {
                    "value": round(metrics.latency_p95_ms, 1),
                    "score": latency_score,
                    "weight": self.WEIGHTS["latency"]
                },
                "availability": {
                    "value": round(availability_score, 1),
                    "score": round(availability_score, 1),
                    "weight": self.WEIGHTS["availability"]
                }
            },
            "recommendations": self._generate_recommendations(metrics, total_score)
        }
    
    def _generate_recommendations(self, metrics: AgentMetrics, score: float) -> List[str]:
        """根據指標生成優化建議"""
        recommendations = []
        
        if metrics.error_rate > 0.1:
            recommendations.append(f"錯誤率過高 ({metrics.error_rate*100:.1f}%)，建議檢查錯誤日誌")
        
        if metrics.latency_p95_ms > 2000:
            recommendations.append(f"P95 延遲過高 ({metrics.latency_p95_ms:.0f}ms)，建議優化處理速度")
        
        if metrics.retry_rate > 0.15:
            recommendations.append(f"重試率過高 ({metrics.retry_rate*100:.1f}%)，建議檢查工具穩定性")
        
        if metrics.human_intervention_rate > 0.05:
            recommendations.append(f"人類干預率過高 ({metrics.human_intervention_rate*100:.1f}%)，建議優化流程")
        
        if metrics.availability < 0.99:
            recommendations.append(f"可用性過低 ({metrics.availability*100:.1f}%)，建議檢查系統穩定性")
        
        if not recommendations:
            recommendations.append("各項指標正常，繼續保持！")
        
        return recommendations
    
    def get_trend(self, history: List[AgentMetrics], days: int = 7) -> Dict:
        """
        計算趨勢
        參考: playbooks/multi-agent-collaboration-v2.md Phase 5 效能趨勢圖
        """
        if not history:
            return {"trend": "unknown", "change": 0}
        
        recent = history[-days:]
        if len(recent) < 2:
            return {"trend": "insufficient_data", "change": 0}
        
        scores = [self.calculate(m)["score"] for m in recent]
        
        # 簡單線性趨勢
        first_half = sum(scores[:len(scores)//2]) / (len(scores)//2)
        second_half = sum(scores[len(scores)//2:]) / (len(scores) - len(scores)//2)
        
        change = second_half - first_half
        
        if change > 5:
            trend = "improving"
        elif change < -5:
            trend = "declining"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "change": round(change, 1),
            "avg_score": round(sum(scores) / len(scores), 1)
        }


# 單例
health_scorer = HealthScorer()


# ============ 使用範例 ============

if __name__ == "__main__":
    # 模擬數據
    metrics = AgentMetrics(
        agent_id="test-agent",
        timestamp=datetime.now(),
        total_requests=100,
        successful_requests=85,
        failed_requests=15,
        avg_latency_ms=1200,
        latency_p50_ms=800,
        latency_p95_ms=3500,
        latency_p99_ms=8000,
        avg_confidence=0.82,
        retry_count=12,
        human_intervention_count=3,
        uptime_seconds=3600,
        downtime_seconds=60
    )
    
    # 計算健康評分
    result = health_scorer.calculate(metrics)
    
    print(f"\n{'='*50}")
    print(f"Agent 健康評分報告")
    print(f"{'='*50}")
    print(f"Agent: {result['agent_id']}")
    print(f"時間: {result['timestamp']}")
    print(f"\n🆔 健康評分: {result['level']} {result['score']} 分")
    print(f"狀態: {result['status']}")
    
    print(f"\n📊 分項得分:")
    for key, detail in result['details'].items():
        print(f"  {key}: {detail['value']}% → {detail['score']}分 (權重 {detail['weight']*100:.0f}%)")
    
    print(f"\n💡 優化建議:")
    for rec in result['recommendations']:
        print(f"  • {rec}")
    
    print(f"\n{'='*50}")
