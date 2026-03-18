"""
健康檢查模組

Agent 狀態檢查 + 定期報告
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from collections import deque
from dataclasses import dataclass, field


@dataclass
class HealthThresholds:
    """健康閾值配置"""
    error_rate: float = 0.1          # 10% 錯誤率
    response_time: int = 5000         # 5秒響應時間
    max_active_tasks: int = 100      # 最大活動任務數
    max_retries: int = 3             # 最大重試次數
    warning_error_rate: float = 0.05 # 5% 警告閾值
    warning_response_time: int = 3000 # 3秒警告閾值


@dataclass
class TaskRecord:
    """任務記錄"""
    task_id: str
    task_name: str
    started_at: float
    completed_at: Optional[float] = None
    success: bool = True
    error_code: Optional[str] = None
    retry_count: int = 0


class HealthChecker:
    """
    健康檢查器
    
    檢查項目：
    - 錯誤率
    - 平均響應時間
    - 活動任務數
    - 熔斷狀態
    """
    
    def __init__(self, thresholds: Optional[Dict] = None):
        # 設置閾值
        if thresholds:
            self.thresholds = HealthThresholds(**thresholds)
        else:
            self.thresholds = HealthThresholds()
        
        # 任務記錄（保留最近 1000 個）
        self._task_history: deque = deque(maxlen=1000)
        
        # 錯誤記錄
        self._error_history: deque = deque(maxlen=1000)
        
        # 熔斷狀態
        self._circuit_breaker_state = "closed"  # closed, open, half_open
        self._circuit_breaker_failures = 0
        self._circuit_breaker_last_failure: Optional[float] = None
        self._circuit_breaker_recovery_timeout = 60  # 60秒
    
    def record_task_completed(self, task):
        """記錄完成的任務"""
        record = TaskRecord(
            task_id=task.task_id,
            task_name=task.task_name,
            started_at=task.started_at.timestamp() if task.started_at else time.time(),
            completed_at=task.completed_at.timestamp() if task.completed_at else time.time(),
            success=task.status.value == "completed",
            error_code=task.error.get("code") if task.error else None
        )
        self._task_history.append(record)
        
        # 如果成功，重置熔斷計數
        if record.success:
            self._circuit_breaker_failures = 0
    
    def record_error(self, error_info: Dict):
        """記錄錯誤"""
        self._error_history.append({
            "timestamp": time.time(),
            "level": error_info.get("level"),
            "code": error_info.get("code"),
            "message": error_info.get("message"),
            "recoverable": error_info.get("recoverable", True)
        })
        
        # 更新熔斷狀態
        if not error_info.get("recoverable", True):
            self._circuit_breaker_failures += 1
            self._circuit_breaker_last_failure = time.time()
            
            if self._circuit_breaker_failures >= 5:
                self._circuit_breaker_state = "open"
    
    def check(self) -> Dict:
        """執行健康檢查"""
        checks = {
            "error_rate": self._check_error_rate(),
            "avg_response_time": self._check_response_time(),
            "active_tasks": self._check_active_tasks(),
            "circuit_breaker": self._check_circuit_breaker()
        }
        
        # 計算整體狀態
        statuses = [check["status"] for check in checks.values()]
        if "fail" in statuses:
            overall_status = "unhealthy"
        elif "warn" in statuses:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "checks": checks,
            "metrics": self.get_metrics()
        }
    
    def _check_error_rate(self) -> Dict:
        """檢查錯誤率"""
        # 最近的任務（過去5分鐘）
        cutoff = time.time() - 300
        recent_tasks = [t for t in self._task_history if t.started_at >= cutoff]
        
        if not recent_tasks:
            return {"status": "pass", "value": 0, "threshold": self.thresholds.error_rate}
        
        failed = sum(1 for t in recent_tasks if not t.success)
        error_rate = failed / len(recent_tasks)
        
        # 判斷狀態
        if error_rate > self.thresholds.error_rate:
            status = "fail"
        elif error_rate > self.thresholds.warning_error_rate:
            status = "warn"
        else:
            status = "pass"
        
        return {
            "status": status,
            "value": round(error_rate, 4),
            "threshold": self.thresholds.error_rate,
            "warning_threshold": self.thresholds.warning_error_rate,
            "recent_total": len(recent_tasks),
            "recent_failed": failed
        }
    
    def _check_response_time(self) -> Dict:
        """檢查平均響應時間"""
        # 最近的任務（過去5分鐘）
        cutoff = time.time() - 300
        recent = [t for t in self._task_history 
                  if t.completed_at and t.started_at >= cutoff]
        
        if not recent:
            return {"status": "pass", "value": 0, "threshold": self.thresholds.response_time}
        
        total_time = sum((t.completed_at - t.started_at) * 1000 for t in recent)
        avg_time = total_time / len(recent)
        
        # 判斷狀態
        if avg_time > self.thresholds.response_time:
            status = "fail"
        elif avg_time > self.thresholds.warning_response_time:
            status = "warn"
        else:
            status = "pass"
        
        return {
            "status": status,
            "value": int(avg_time),
            "threshold": self.thresholds.response_time,
            "warning_threshold": self.thresholds.warning_response_time,
            "recent_total": len(recent)
        }
    
    def _check_active_tasks(self) -> Dict:
        """檢查活動任務數"""
        active = [t for t in self._task_history if t.completed_at is None]
        count = len(active)
        
        status = "fail" if count > self.thresholds.max_active_tasks else "pass"
        
        return {
            "status": status,
            "value": count,
            "threshold": self.thresholds.max_active_tasks
        }
    
    def _check_circuit_breaker(self) -> Dict:
        """檢查熔斷狀態"""
        # 檢查是否可以恢復
        if self._circuit_breaker_state == "open":
            if self._circuit_breaker_last_failure:
                elapsed = time.time() - self._circuit_breaker_last_failure
                if elapsed > self._circuit_breaker_recovery_timeout:
                    self._circuit_breaker_state = "half_open"
        
        status = "pass" if self._circuit_breaker_state == "closed" else "fail"
        
        return {
            "status": status,
            "state": self._circuit_breaker_state,
            "failure_count": self._circuit_breaker_failures
        }
    
    def get_metrics(self) -> Dict:
        """獲取指標"""
        total = len(self._task_history)
        completed = sum(1 for t in self._task_history if t.completed_at is not None)
        failed = sum(1 for t in self._task_history if not t.success and t.completed_at)
        
        # 計算平均持續時間
        completed_tasks = [t for t in self._task_history if t.completed_at]
        if completed_tasks:
            total_duration = sum(
                (t.completed_at - t.started_at) * 1000 
                for t in completed_tasks
            )
            avg_duration = int(total_duration / len(completed_tasks))
        else:
            avg_duration = 0
        
        return {
            "total_tasks": total,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "success_rate": round((completed - failed) / completed, 4) if completed > 0 else 1.0,
            "avg_duration_ms": avg_duration,
            "error_count": len(self._error_history)
        }
    
    def reset(self):
        """重置健康檢查器"""
        self._task_history.clear()
        self._error_history.clear()
        self._circuit_breaker_state = "closed"
        self._circuit_breaker_failures = 0
        self._circuit_breaker_last_failure = None


# 便捷函數
def create_health_checker(thresholds: Dict = None) -> HealthChecker:
    """創建健康檢查器"""
    return HealthChecker(thresholds=thresholds)
