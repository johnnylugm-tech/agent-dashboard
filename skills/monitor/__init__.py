"""
Monitor Skill - AI Agent 監控模組

Phase 1: 錯誤分類 + 結構化日誌 + 健康檢查
Phase 2: 熔斷機制 + 警報通知 + 指標儀表板
"""

import sys
import os

# 確保可以找到同目錄下的模塊
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from models import Task, Error, HealthStatus, TaskStatus, ErrorLevel, HealthLevel
from errors import ErrorClassifier, ErrorCode
from logging import StructuredLogger
from health import HealthChecker
from reporting import Reporter

# Phase 2 新增
from circuit_breaker import (
    CircuitBreaker, 
    CircuitBreakerManager, 
    CircuitState, 
    CircuitConfig,
    CircuitOpenError,
    create_circuit_breaker
)
from alerts import (
    AlertManager,
    AlertReporter,
    AlertSeverity,
    AlertSource,
    AlertRule,
    Alert,
    create_alert_manager
)
from dashboard import (
    Dashboard,
    MetricsCollector,
    create_dashboard
)

__version__ = "2.0.0"
__all__ = [
    # Phase 1
    "AgentMonitor",
    "ErrorClassifier", 
    "ErrorCode",
    "StructuredLogger",
    "HealthChecker",
    "Reporter",
    "Task",
    "Error",
    "HealthStatus",
    "TaskStatus",
    "ErrorLevel",
    "HealthLevel",
    # Phase 2 - Circuit Breaker
    "CircuitBreaker",
    "CircuitBreakerManager",
    "CircuitState",
    "CircuitConfig",
    "CircuitOpenError",
    "create_circuit_breaker",
    # Phase 2 - Alerts
    "AlertManager",
    "AlertReporter",
    "AlertSeverity",
    "AlertSource",
    "AlertRule",
    "Alert",
    "create_alert_manager",
    # Phase 2 - Dashboard
    "Dashboard",
    "MetricsCollector",
    "create_dashboard",
]


class AgentMonitor:
    """
    Agent 監控主類
    
    整合錯誤分類、日誌、健康檢查、熔斷器、警報於一體
    """
    
    def __init__(
        self, 
        agent_id: str, 
        log_path: str = "./logs",
        thresholds: dict = None,
        circuit_breaker_config: dict = None
    ):
        self.agent_id = agent_id
        self.logger = StructuredLogger(agent_id=agent_id, log_path=log_path)
        self.error_classifier = ErrorClassifier()
        self.health_checker = HealthChecker(thresholds=thresholds)
        self.reporter = Reporter(agent_id=agent_id)
        
        # Phase 2 新增
        self.circuit_breaker_manager = CircuitBreakerManager()
        self.alert_manager = AlertManager(agent_id=agent_id)
        self.metrics_collector = MetricsCollector()
        
        # 設置默認熔斷器
        if circuit_breaker_config:
            cb_config = CircuitConfig(**circuit_breaker_config)
        else:
            cb_config = None
        self.circuit_breaker = self.circuit_breaker_manager.get_or_create(
            "default", cb_config
        )
        
        # 連接警報到健康檢查
        self._setup_alert_integration()
        
        self._tasks = {}
    
    def _setup_alert_integration(self):
        """設置警報集成"""
        def on_circuit_state_change(event, data):
            if data.get("to") == "open":
                self.alert_manager.evaluate(
                    AlertSource.CIRCUIT_BREAKER,
                    1,  # 表示 open
                    {"name": "default"}
                )
        
        self.circuit_breaker.on(CircuitEvent.STATE_CHANGE, on_circuit_state_change)
    
    def task_start(self, task_name: str, context: dict = None) -> str:
        """開始一個任務"""
        import uuid
        from datetime import datetime
        task_id = str(uuid.uuid4())[:8]
        
        task = Task(
            task_id=task_id,
            task_name=task_name,
            agent_id=self.agent_id,
            context=context or {}
        )
        task.start()
        
        self._tasks[task_id] = task
        self.logger.info(
            "task_start",
            task_id=task_id,
            task_name=task_name,
            context=context
        )
        
        return task_id
    
    def task_complete(self, task_id: str, result: dict = None):
        """任務完成"""
        if task_id not in self._tasks:
            return
        
        task = self._tasks[task_id]
        task.complete(result=result)
        
        self.logger.info(
            "task_complete",
            task_id=task_id,
            duration_ms=task.duration_ms,
            result=result
        )
        
        # 記錄指標
        self.metrics_collector.record("tasks_completed", 1)
        self.metrics_collector.record("response_time", task.duration_ms)
        
        # 更新健康檢查指標
        self.health_checker.record_task_completed(task)
    
    def task_error(self, task_id: str, error: dict):
        """任務錯誤"""
        if task_id in self._tasks:
            task = self._tasks[task_id]
            task.fail(error=error)
            
            self.logger.error(
                "task_error",
                task_id=task_id,
                error=error,
                duration_ms=task.duration_ms
            )
            
            # 記錄錯誤
            error_info = self.error_classifier.classify(error, task.context)
            self.health_checker.record_error(error_info)
            
            # 記錄指標
            self.metrics_collector.record("tasks_failed", 1)
    
    def execute_with_circuit(
        self, 
        func, 
        *args, 
        fallback=None, 
        **kwargs
    ):
        """使用熔斷器執行函數"""
        return self.circuit_breaker.call(func, *args, fallback=fallback, **kwargs)
    
    def health_check(self) -> dict:
        """健康檢查"""
        return self.health_checker.check()
    
    def get_metrics(self) -> dict:
        """獲取指標"""
        return self.health_checker.get_metrics()
    
    def generate_report(self, report_type: str = "hourly") -> dict:
        """生成報告"""
        if report_type == "hourly":
            return self.reporter.generate_hourly_report(self.health_checker)
        elif report_type == "daily":
            return self.reporter.generate_daily_report(self.health_checker)
        else:
            raise ValueError(f"Unknown report type: {report_type}")
    
    def get_dashboard(self, format: str = "markdown") -> str:
        """生成儀表板"""
        dashboard = Dashboard(
            agent_id=self.agent_id,
            metrics_collector=self.metrics_collector,
            health_checker=self.health_checker,
            circuit_breaker_manager=self.circuit_breaker_manager,
            alert_manager=self.alert_manager
        )
        
        if format == "compact":
            return dashboard.generate_compact()
        return dashboard.generate()
    
    def check_alerts(self):
        """檢查警報條件"""
        # 評估錯誤率警報
        stats = self.metrics_collector.get_stats("error_rate")
        if stats["count"] > 0:
            self.alert_manager.evaluate(
                AlertSource.ERROR_RATE,
                stats["latest"]
            )
        
        # 評估響應時間警報
        stats = self.metrics_collector.get_stats("response_time")
        if stats["count"] > 0:
            self.alert_manager.evaluate(
                AlertSource.RESPONSE_TIME,
                stats["avg"]
            )
    
    def get_alerts(self, severity: str = None) -> list:
        """獲取警報"""
        sev = AlertSeverity(severity) if severity else None
        return self.alert_manager.get_active_alerts(severity=sev)


# 引入 CircuitEvent 用於回調
from circuit_breaker import CircuitEvent
from alerts import AlertSource as AlertSource
