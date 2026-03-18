"""
警報通知模組

警報觸發規則、嚴重性分級、通知報告生成
"""

import time
from enum import Enum
from typing import Callable, Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime


class AlertSeverity(Enum):
    """警報嚴重性"""
    INFO = "info"           # 信息
    WARNING = "warning"     # 警告
    ERROR = "error"         # 錯誤
    CRITICAL = "critical"   # 嚴重


class AlertSource(Enum):
    """警報來源"""
    CIRCUIT_BREAKER = "circuit_breaker"
    HEALTH_CHECK = "health_check"
    ERROR_RATE = "error_rate"
    RESPONSE_TIME = "response_time"
    TASK_FAILURE = "task_failure"
    CUSTOM = "custom"


@dataclass
class AlertRule:
    """警報規則"""
    name: str
    source: AlertSource
    condition: str  # "gt", "lt", "eq", "gte", "lte"
    threshold: float
    severity: AlertSeverity
    cooldown_seconds: int = 60  # 冷卻時間
    enabled: bool = True
    
    def evaluate(self, value: float) -> bool:
        """評估條件"""
        if not self.enabled:
            return False
        
        if self.condition == "gt":
            return value > self.threshold
        elif self.condition == "lt":
            return value < self.threshold
        elif self.condition == "eq":
            return value == self.threshold
        elif self.condition == "gte":
            return value >= self.threshold
        elif self.condition == "lte":
            return value <= self.threshold
        return False


@dataclass
class Alert:
    """警報實例"""
    id: str
    rule_name: str
    source: AlertSource
    severity: AlertSeverity
    title: str
    message: str
    value: float
    threshold: float
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    resolved: bool = False
    resolved_at: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "rule_name": self.rule_name,
            "source": self.source.value,
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "value": self.value,
            "threshold": self.threshold,
            "timestamp": datetime.fromtimestamp(self.timestamp).isoformat(),
            "acknowledged": self.acknowledged,
            "resolved": self.resolved,
            "resolved_at": datetime.fromtimestamp(self.resolved_at).isoformat() if self.resolved_at else None,
            "metadata": self.metadata
        }


class AlertManager:
    """
    警報管理器
    
    負責：
    - 警報規則管理
    - 警報觸發與評估
    - 警報歷史記錄
    - 通知生成
    """
    
    def __init__(self, agent_id: str = "default"):
        self.agent_id = agent_id
        self._rules: Dict[str, AlertRule] = {}
        self._active_alerts: Dict[str, Alert] = {}
        self._alert_history: List[Alert] = []
        self._last_trigger_time: Dict[str, float] = {}  # rule_name -> last trigger time
        
        # 通知回調
        self._notification_callbacks: List[Callable[[Alert], None]] = []
        
        # 內置默認規則
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """設置默認規則"""
        default_rules = [
            AlertRule(
                name="high_error_rate",
                source=AlertSource.ERROR_RATE,
                condition="gt",
                threshold=0.1,
                severity=AlertSeverity.ERROR,
                cooldown_seconds=60
            ),
            AlertRule(
                name="critical_error_rate",
                source=AlertSource.ERROR_RATE,
                condition="gt",
                threshold=0.3,
                severity=AlertSeverity.CRITICAL,
                cooldown_seconds=30
            ),
            AlertRule(
                name="slow_response",
                source=AlertSource.RESPONSE_TIME,
                condition="gt",
                threshold=5000,
                severity=AlertSeverity.WARNING,
                cooldown_seconds=120
            ),
            AlertRule(
                name="very_slow_response",
                source=AlertSource.RESPONSE_TIME,
                condition="gt",
                threshold=10000,
                severity=AlertSeverity.ERROR,
                cooldown_seconds=60
            ),
            AlertRule(
                name="circuit_open",
                source=AlertSource.CIRCUIT_BREAKER,
                condition="eq",
                threshold=1,  # state == "open" represented as 1
                severity=AlertSeverity.CRITICAL,
                cooldown_seconds=30
            ),
            AlertRule(
                name="task_failure_spike",
                source=AlertSource.TASK_FAILURE,
                condition="gt",
                threshold=5,
                severity=AlertSeverity.ERROR,
                cooldown_seconds=60
            ),
        ]
        
        for rule in default_rules:
            self._rules[rule.name] = rule
    
    def add_rule(self, rule: AlertRule):
        """添加警報規則"""
        self._rules[rule.name] = rule
    
    def remove_rule(self, rule_name: str):
        """移除警報規則"""
        if rule_name in self._rules:
            del self._rules[rule_name]
    
    def get_rule(self, rule_name: str) -> Optional[AlertRule]:
        """獲取警報規則"""
        return self._rules.get(rule_name)
    
    def list_rules(self) -> List[AlertRule]:
        """列出所有規則"""
        return list(self._rules.values())
    
    def evaluate(
        self, 
        source: AlertSource, 
        value: float, 
        metadata: Dict = None
    ) -> List[Alert]:
        """
        評估警報條件
        
        Args:
            source: 數據來源
            value: 當前值
            metadata: 附加元數據
            
        Returns:
            觸發的警報列表
        """
        triggered = []
        
        for rule in self._rules.values():
            if rule.source != source:
                continue
            
            # 檢查冷卻時間
            if rule.name in self._last_trigger_time:
                elapsed = time.time() - self._last_trigger_time[rule.name]
                if elapsed < rule.cooldown_seconds:
                    continue
            
            # 評估條件
            if rule.evaluate(value):
                alert = self._create_alert(rule, value, metadata or {})
                triggered.append(alert)
                self._last_trigger_time[rule.name] = time.time()
        
        return triggered
    
    def _create_alert(self, rule: AlertRule, value: float, metadata: Dict) -> Alert:
        """創建警報實例"""
        import uuid
        
        alert_id = str(uuid.uuid4())[:8]
        
        # 根據規則和數據生成消息
        title, message = self._generate_alert_message(rule, value)
        
        alert = Alert(
            id=alert_id,
            rule_name=rule.name,
            source=rule.source,
            severity=rule.severity,
            title=title,
            message=message,
            value=value,
            threshold=rule.threshold,
            metadata=metadata
        )
        
        # 存儲警報
        self._active_alerts[alert_id] = alert
        
        # 觸發通知
        self._notify(alert)
        
        return alert
    
    def _generate_alert_message(self, rule: AlertRule, value: float) -> tuple:
        """生成警報消息"""
        condition_text = {
            "gt": ">",
            "lt": "<",
            "eq": "=",
            "gte": ">=",
            "lte": "<="
        }
        
        op = condition_text.get(rule.condition, rule.condition)
        
        if rule.source == AlertSource.ERROR_RATE:
            title = f"錯誤率過高 ({value:.1%} {op} {rule.threshold:.1%})"
            message = f"錯誤率達到 {value:.1%}，超過閾值 {rule.threshold:.1%}"
        elif rule.source == AlertSource.RESPONSE_TIME:
            title = f"響應時間過長 ({value/1000:.1f}s {op} {rule.threshold/1000:.1f}s)"
            message = f"平均響應時間達到 {value/1000:.1f}秒，超過閾值 {rule.threshold/1000:.1f}秒"
        elif rule.source == AlertSource.CIRCUIT_BREAKER:
            title = "熔斷器已斷開"
            message = f"熔斷器 '{metadata.get('name', 'default')}' 已進入 OPEN 狀態"
        elif rule.source == AlertSource.TASK_FAILURE:
            title = f"任務失敗數過多 ({value} {op} {rule.threshold})"
            message = f"過去一段時間內有 {int(value)} 個任務失敗"
        else:
            title = f"警報: {rule.name}"
            message = f"指標 {rule.name} = {value} {op} {rule.threshold}"
        
        return title, message
    
    def acknowledge(self, alert_id: str) -> bool:
        """確認警報"""
        if alert_id in self._active_alerts:
            self._active_alerts[alert_id].acknowledged = True
            return True
        return False
    
    def resolve(self, alert_id: str) -> bool:
        """解除警報"""
        if alert_id in self._active_alerts:
            alert = self._active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = time.time()
            
            # 移到歷史
            self._alert_history.append(alert)
            del self._active_alerts[alert_id]
            return True
        return False
    
    def get_active_alerts(
        self, 
        severity: Optional[AlertSeverity] = None,
        source: Optional[AlertSource] = None
    ) -> List[Alert]:
        """獲取活動警報"""
        alerts = list(self._active_alerts.values())
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if source:
            alerts = [a for a in alerts if a.source == source]
        
        return sorted(alerts, key=lambda a: a.severity.value)  # 按嚴重性排序
    
    def get_alert_history(
        self, 
        limit: int = 100,
        severity: Optional[AlertSeverity] = None
    ) -> List[Alert]:
        """獲取警報歷史"""
        history = self._alert_history[-limit:]
        
        if severity:
            history = [a for a in history if a.severity == severity]
        
        return history
    
    def on_notification(self, callback: Callable[[Alert], None]):
        """註冊通知回調"""
        self._notification_callbacks.append(callback)
    
    def _notify(self, alert: Alert):
        """觸發通知"""
        for callback in self._notification_callbacks:
            try:
                callback(alert)
            except Exception:
                pass
    
    def clear(self):
        """清除所有警報"""
        self._active_alerts.clear()
        self._alert_history.clear()
        self._last_trigger_time.clear()


class AlertReporter:
    """
    警報報告生成器
    
    生成警報通知報告
    """
    
    def __init__(self, alert_manager: AlertManager):
        self.alert_manager = alert_manager
    
    def generate_report(
        self, 
        format: str = "text"
    ) -> str:
        """
        生成警報報告
        
        Args:
            format: 輸出格式 ("text", "markdown", "json")
            
        Returns:
            報告內容
        """
        active = self.alert_manager.get_active_alerts()
        
        if format == "json":
            import json
            return json.dumps([a.to_dict() for a in active], indent=2, ensure_ascii=False)
        
        lines = []
        
        # 標題
        lines.append("# 🚨 警報報告")
        lines.append(f"\n**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**活動警報數**: {len(active)}")
        
        if not active:
            lines.append("\n✅ 沒有活動警報")
            return "\n".join(lines)
        
        # 按嚴重性分組
        by_severity = {}
        for alert in active:
            if alert.severity not in by_severity:
                by_severity[alert.severity] = []
            by_severity[alert.severity].append(alert)
        
        # 輸出
        severity_emoji = {
            AlertSeverity.CRITICAL: "🔴",
            AlertSeverity.ERROR: "🟠",
            AlertSeverity.WARNING: "🟡",
            AlertSeverity.INFO: "🔵"
        }
        
        for severity in [AlertSeverity.CRITICAL, AlertSeverity.ERROR, 
                         AlertSeverity.WARNING, AlertSeverity.INFO]:
            if severity not in by_severity:
                continue
            
            alerts = by_severity[severity]
            emoji = severity_emoji.get(severity, "⚪")
            lines.append(f"\n## {emoji} {severity.value.upper()} ({len(alerts)})")
            
            for alert in alerts:
                lines.append(f"\n### {alert.title}")
                lines.append(f"- **規則**: {alert.rule_name}")
                lines.append(f"- **訊息**: {alert.message}")
                lines.append(f"- **時間**: {datetime.fromtimestamp(alert.timestamp).strftime('%H:%M:%S')}")
                lines.append(f"- **ID**: `{alert.id}`")
        
        return "\n".join(lines)
    
    def generate_summary(self) -> Dict:
        """生成警報摘要"""
        active = self.alert_manager.get_active_alerts()
        
        summary = {
            "total": len(active),
            "by_severity": {},
            "by_source": {},
            "oldest_unack": None
        }
        
        for alert in active:
            # 按嚴重性
            sev = alert.severity.value
            summary["by_severity"][sev] = summary["by_severity"].get(sev, 0) + 1
            
            # 按來源
            src = alert.source.value
            summary["by_source"][src] = summary["by_source"].get(src, 0) + 1
            
            # 最舊未確認
            if not alert.acknowledged:
                if summary["oldest_unack"] is None or alert.timestamp < summary["oldest_unack"]:
                    summary["oldest_unack"] = alert.timestamp
        
        return summary


# 便捷函數
def create_alert_manager(agent_id: str = "default") -> AlertManager:
    """創建警報管理器"""
    return AlertManager(agent_id=agent_id)
