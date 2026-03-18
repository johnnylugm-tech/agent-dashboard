"""
數據模型定義
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class TaskStatus(Enum):
    """任務狀態"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ErrorLevel(Enum):
    """錯誤層級"""
    L1 = "L1"  # 輸入錯誤
    L2 = "L2"  # 工具錯誤
    L3 = "L3"  # 執行錯誤
    L4 = "L4"  # 系統錯誤


class HealthLevel(Enum):
    """健康狀態"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class Task:
    """任務模型"""
    task_id: str
    task_name: str
    agent_id: str
    context: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict] = None
    error: Optional[Dict] = None
    
    @property
    def duration_ms(self) -> int:
        """任務執行時間（毫秒）"""
        if self.started_at is None:
            return 0
        end = self.completed_at or datetime.utcnow()
        return int((end - self.started_at).total_seconds() * 1000)
    
    def start(self):
        """開始任務"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.utcnow()
    
    def complete(self, result: Dict = None):
        """完成任務"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.result = result
    
    def fail(self, error: Dict = None):
        """任務失敗"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error = error


@dataclass
class Error:
    """錯誤模型"""
    code: str
    message: str
    level: ErrorLevel
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    recoverable: bool = True
    
    def to_dict(self) -> Dict:
        return {
            "code": self.code,
            "message": self.message,
            "level": self.level.value,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "recoverable": self.recoverable
        }


@dataclass
class HealthStatus:
    """健康狀態"""
    status: HealthLevel
    timestamp: datetime = field(default_factory=datetime.utcnow)
    checks: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat() + "Z",
            "checks": self.checks,
            "metrics": self.metrics
        }


@dataclass
class LogEntry:
    """日誌條目"""
    timestamp: datetime
    level: str
    agent_id: str
    task_id: Optional[str]
    event: str
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat() + "Z",
            "level": self.level,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "event": self.event,
            "message": self.message,
            "context": self.context,
            "metrics": self.metrics
        }
