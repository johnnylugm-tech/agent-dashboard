"""
報告生成模組

定期報告生成
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import time


class Reporter:
    """
    報告生成器
    
    生成每小時/每日報告
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
    
    def generate_hourly_report(self, health_checker) -> Dict:
        """生成每小時報告"""
        now = datetime.utcnow()
        start_of_hour = now.replace(minute=0, second=0, microsecond=0)
        
        return self._generate_report(
            health_checker,
            start_of_hour,
            now,
            "hourly"
        )
    
    def generate_daily_report(self, health_checker) -> Dict:
        """生成每日報告"""
        now = datetime.utcnow()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        return self._generate_report(
            health_checker,
            start_of_day,
            now,
            "daily"
        )
    
    def _generate_report(
        self, 
        health_checker,
        start: datetime,
        end: datetime,
        report_type: str
    ) -> Dict:
        """生成報告"""
        start_ts = start.timestamp()
        end_ts = end.timestamp()
        
        # 過濾任務歷史
        tasks = [
            t for t in health_checker._task_history
            if start_ts <= t.started_at < end_ts
        ]
        
        # 過濾錯誤歷史
        errors = [
            e for e in health_checker._error_history
            if start_ts <= e["timestamp"] < end_ts
        ]
        
        # 計算指標
        completed = [t for t in tasks if t.completed_at]
        failed = [t for t in tasks if not t.success and t.completed_at]
        
        # 計算持續時間
        durations = [
            (t.completed_at - t.started_at) * 1000 
            for t in completed 
            if t.completed_at
        ]
        
        # 按錯誤層級分組
        errors_by_level = {}
        for e in errors:
            level = e.get("level", "unknown")
            errors_by_level[level] = errors_by_level.get(level, 0) + 1
        
        # 計算 SLA
        success_rate = len(completed) - len(failed) / len(completed) if completed else 1.0
        
        # 平均響應時間
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # 健康狀態
        health = health_checker.check()
        
        return {
            "report_type": report_type,
            "agent_id": self.agent_id,
            "period": {
                "start": start.isoformat() + "Z",
                "end": end.isoformat() + "Z"
            },
            "summary": {
                "total_tasks": len(tasks),
                "completed_tasks": len(completed),
                "failed_tasks": len(failed),
                "success_rate": round(success_rate, 4),
                "avg_duration_ms": int(avg_duration),
                "error_count": len(errors)
            },
            "errors_by_level": errors_by_level,
            "health_status": health["status"],
            "sla": {
                "target_success_rate": 0.95,
                "target_avg_duration_ms": 5000,
                "success_rate_met": success_rate >= 0.95,
                "avg_duration_met": avg_duration <= 5000
            },
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
    
    def generate_summary(self, health_checker) -> Dict:
        """生成簡要摘要"""
        metrics = health_checker.get_metrics()
        health = health_checker.check()
        
        return {
            "agent_id": self.agent_id,
            "status": health["status"],
            "total_tasks": metrics["total_tasks"],
            "success_rate": metrics["success_rate"],
            "avg_duration_ms": metrics["avg_duration_ms"],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }


# 便捷函數
def create_reporter(agent_id: str) -> Reporter:
    """創建報告生成器"""
    return Reporter(agent_id=agent_id)
