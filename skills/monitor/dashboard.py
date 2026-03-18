"""
指標儀表板

關鍵指標追蹤 + Markdown 儀表板輸出
"""

import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque


@dataclass
class MetricPoint:
    """指標數據點"""
    timestamp: float
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class MetricDefinition:
    """指標定義"""
    name: str
    description: str
    unit: str = ""
    aggregation: str = "avg"  # avg, sum, min, max, count


class MetricsCollector:
    """
    指標收集器
    
    收集和存儲各類指標數據
    """
    
    def __init__(self, retention_minutes: int = 60):
        self._metrics: Dict[str, deque] = {}
        self._definitions: Dict[str, MetricDefinition] = {}
        self._retention_seconds = retention_minutes * 60
    
    def register_metric(
        self, 
        name: str, 
        description: str = "", 
        unit: str = "",
        aggregation: str = "avg"
    ):
        """註冊指標"""
        self._definitions[name] = MetricDefinition(
            name=name,
            description=description,
            unit=unit,
            aggregation=aggregation
        )
        if name not in self._metrics:
            self._metrics[name] = deque()
    
    def record(self, name: str, value: float, labels: Dict = None):
        """記錄指標值"""
        if name not in self._metrics:
            self.register_metric(name)
        
        point = MetricPoint(
            timestamp=time.time(),
            value=value,
            labels=labels or {}
        )
        self._metrics[name].append(point)
        
        # 清理過期數據
        self._cleanup(name)
    
    def _cleanup(self, name: str):
        """清理過期數據"""
        cutoff = time.time() - self._retention_seconds
        metric_data = self._metrics[name]
        while metric_data and metric_data[0].timestamp < cutoff:
            metric_data.popleft()
    
    def get_values(
        self, 
        name: str, 
        since: Optional[float] = None,
        limit: int = 100
    ) -> List[MetricPoint]:
        """獲取指標值"""
        if name not in self._metrics:
            return []
        
        cutoff = since or (time.time() - self._retention_seconds)
        values = [p for p in self._metrics[name] if p.timestamp >= cutoff]
        return values[-limit:]
    
    def get_stats(self, name: str, since: Optional[float] = None) -> Dict:
        """獲取指標統計"""
        values = self.get_values(name, since, limit=1000)
        
        if not values:
            return {
                "count": 0,
                "min": 0,
                "max": 0,
                "avg": 0,
                "sum": 0
            }
        
        numeric_values = [p.value for p in values]
        
        return {
            "count": len(numeric_values),
            "min": min(numeric_values),
            "max": max(numeric_values),
            "avg": sum(numeric_values) / len(numeric_values),
            "sum": sum(numeric_values),
            "latest": numeric_values[-1],
            "latest_timestamp": values[-1].timestamp
        }
    
    def get_all_metrics(self) -> List[str]:
        """獲取所有指標名"""
        return list(self._definitions.keys())


class Dashboard:
    """
    指標儀表板
    
    生成 Markdown 格式的儀表板輸出
    """
    
    # 預設配置
    DEFAULT_WIDGETS = [
        {"type": "header", "title": "系統概覽"},
        {"type": "metrics_summary"},
        {"type": "health_status"},
        {"type": "header", "title": "性能指標"},
        {"type": "error_rate_chart"},
        {"type": "response_time_chart"},
        {"type": "header", "title": "任務統計"},
        {"type": "task_stats"},
        {"type": "header", "title": "熔斷器狀態"},
        {"type": "circuit_breakers"},
        {"type": "header", "title": "活動警報"},
        {"type": "active_alerts"},
    ]
    
    def __init__(
        self, 
        agent_id: str = "default",
        metrics_collector: Optional[MetricsCollector] = None,
        health_checker=None,
        circuit_breaker_manager=None,
        alert_manager=None
    ):
        self.agent_id = agent_id
        self.metrics_collector = metrics_collector or MetricsCollector()
        self.health_checker = health_checker
        self.circuit_breaker_manager = circuit_breaker_manager
        self.alert_manager = alert_manager
    
    def generate(
        self, 
        widgets: Optional[List[Dict]] = None,
        title: str = "Agent 監控儀表板"
    ) -> str:
        """
        生成 Markdown 儀表板
        
        Args:
            widgets: 部件列表（可自定義）
            title: 儀表板標題
            
        Returns:
            Markdown 格式的儀表板
        """
        widgets = widgets or self.DEFAULT_WIDGETS
        lines = []
        
        # 標題
        lines.append(f"# {title}")
        lines.append(f"\n**Agent**: `{self.agent_id}`")
        lines.append(f"**更新時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # 渲染每個部件
        for widget in widgets:
            widget_type = widget.get("type")
            
            if widget_type == "header":
                level = widget.get("level", 2)
                lines.append(f"\n{'#' * level} {widget.get('title', '')}")
                lines.append("")
                
            elif widget_type == "metrics_summary":
                lines.extend(self._render_metrics_summary())
                
            elif widget_type == "health_status":
                lines.extend(self._render_health_status())
                
            elif widget_type == "error_rate_chart":
                lines.extend(self._render_error_rate())
                
            elif widget_type == "response_time_chart":
                lines.extend(self._render_response_time())
                
            elif widget_type == "task_stats":
                lines.extend(self._render_task_stats())
                
            elif widget_type == "circuit_breakers":
                lines.extend(self._render_circuit_breakers())
                
            elif widget_type == "active_alerts":
                lines.extend(self._render_alerts())
        
        return "\n".join(lines)
    
    def _render_metrics_summary(self) -> List[str]:
        """渲染指標摘要"""
        lines = []
        
        # 獲取關鍵指標
        key_metrics = [
            ("error_rate", "錯誤率", "%"),
            ("response_time", "響應時間", "ms"),
            ("success_rate", "成功率", "%"),
            ("active_tasks", "活動任務", "個"),
        ]
        
        for metric_name, label, unit in key_metrics:
            if self.metrics_collector:
                stats = self.metrics_collector.get_stats(metric_name)
                if stats["count"] > 0:
                    value = stats["latest"]
                    if unit == "%":
                        value_str = f"{value * 100:.1f}%"
                    elif unit == "ms":
                        value_str = f"{value:.0f}ms"
                    else:
                        value_str = f"{value:.0f}"
                    
                    lines.append(f"- **{label}**: {value_str}")
        
        if lines:
            lines.insert(0, "### 📊 關鍵指標")
        
        return lines
    
    def _render_health_status(self) -> List[str]:
        """渲染健康狀態"""
        lines = []
        
        if not self.health_checker:
            return lines
        
        try:
            health = self.health_checker.check()
            status = health.get("status", "unknown")
            
            # 狀態emoji
            status_emoji = {
                "healthy": "✅",
                "degraded": "⚠️",
                "unhealthy": "❌"
            }
            
            emoji = status_emoji.get(status, "❓")
            lines.append(f"### 🏥 健康狀態: {emoji} `{status.upper()}`")
            lines.append("")
            
            # 詳細檢查
            checks = health.get("checks", {})
            for check_name, check_data in checks.items():
                check_status = check_data.get("status", "unknown")
                status_icon = "✅" if check_status == "pass" else ("⚠️" if check_status == "warn" else "❌")
                
                value = check_data.get("value", "N/A")
                if isinstance(value, float):
                    if check_name == "error_rate":
                        value_str = f"{value * 100:.1f}%"
                    else:
                        value_str = str(value)
                else:
                    value_str = str(value)
                
                lines.append(f"- {status_icon} **{check_name}**: {value_str}")
            
        except Exception as e:
            lines.append("### 🏥 健康狀態: ❌ 獲取失敗")
            lines.append("```")
            lines.append(str(e))
            lines.append("```")
        
        return lines
    
    def _render_error_rate(self) -> List[str]:
        """渲染錯誤率"""
        lines = []
        
        if self.metrics_collector:
            stats = self.metrics_collector.get_stats("error_rate")
            if stats["count"] > 0:
                rate = stats["latest"] * 100
                
                # 簡單的條形圖
                bar_length = int(min(rate / 5, 10))
                bar = "█" * bar_length + "░" * (10 - bar_length)
                
                lines.append(f"### ❌ 錯誤率: {rate:.1f}%")
                lines.append(f"```")
                lines.append(f"[{bar}] {rate:.1f}%")
                lines.append(f"```")
        
        return lines
    
    def _render_response_time(self) -> List[str]:
        """渲染響應時間"""
        lines = []
        
        if self.metrics_collector:
            stats = self.metrics_collector.get_stats("response_time")
            if stats["count"] > 0:
                avg_ms = stats["avg"]
                latest_ms = stats["latest"]
                
                # 顏色標記
                if avg_ms < 1000:
                    emoji = "🟢"
                elif avg_ms < 3000:
                    emoji = "🟡"
                else:
                    emoji = "🔴"
                
                lines.append(f"### ⏱️ 響應時間 {emoji}")
                lines.append(f"- 平均: **{avg_ms:.0f}ms**")
                lines.append(f"- 最新: {latest_ms:.0f}ms")
                lines.append(f"- 最小: {stats['min']:.0f}ms")
                lines.append(f"- 最大: {stats['max']:.0f}ms")
        
        return lines
    
    def _render_task_stats(self) -> List[str]:
        """渲染任務統計"""
        lines = []
        
        if self.health_checker:
            try:
                metrics = self.health_checker.get_metrics()
                
                total = metrics.get("total_tasks", 0)
                completed = metrics.get("completed_tasks", 0)
                failed = metrics.get("failed_tasks", 0)
                success_rate = metrics.get("success_rate", 1.0)
                
                lines.append(f"### 📋 任務統計")
                lines.append(f"- 總任務數: **{total}**")
                lines.append(f"- ✅ 完成: {completed}")
                lines.append(f"- ❌ 失敗: {failed}")
                lines.append(f"- 成功率: {success_rate * 100:.1f}%")
                
            except Exception:
                pass
        
        return lines
    
    def _render_circuit_breakers(self) -> List[str]:
        """渲染熔斷器狀態"""
        lines = []
        
        if not self.circuit_breaker_manager:
            return lines
        
        try:
            breakers = self.circuit_breaker_manager.get_all_metrics()
            
            if not breakers:
                lines.append("*無熔斷器配置*")
                return lines
            
            lines.append("| 熔斷器 | 狀態 | 失敗次數 | 運行時間 |")
            lines.append("|--------|------|----------|----------|")
            
            for name, metrics in breakers.items():
                state = metrics.get("state", "unknown")
                failures = metrics.get("failure_count", 0)
                uptime = metrics.get("uptime_seconds", 0)
                
                # 狀態emoji
                state_emoji = {
                    "closed": "✅",
                    "open": "🔴",
                    "half_open": "🟡"
                }
                emoji = state_emoji.get(state, "❓")
                
                # 運行時間格式化
                if uptime < 60:
                    uptime_str = f"{uptime}s"
                elif uptime < 3600:
                    uptime_str = f"{uptime//60}m"
                else:
                    uptime_str = f"{uptime//3600}h"
                
                lines.append(f"| {name} | {emoji} {state} | {failures} | {uptime_str} |")
            
        except Exception as e:
            lines.append(f"獲取熔斷器狀態失敗: {e}")
        
        return lines
    
    def _render_alerts(self) -> List[str]:
        """渲染活動警報"""
        lines = []
        
        if not self.alert_manager:
            return lines
        
        try:
            active = self.alert_manager.get_active_alerts()
            
            if not active:
                lines.append("✅ 沒有活動警報")
                return lines
            
            severity_emoji = {
                "critical": "🔴",
                "error": "🟠",
                "warning": "🟡",
                "info": "🔵"
            }
            
            for alert in active[:10]:  # 最多顯示10個
                emoji = severity_emoji.get(alert.severity.value, "⚪")
                time_str = datetime.fromtimestamp(alert.timestamp).strftime("%H:%M:%S")
                
                lines.append(f"- {emoji} **{alert.title}** (`{time_str}`)")
                lines.append(f"  - {alert.message}")
            
            if len(active) > 10:
                lines.append(f"\n_... 還有 {len(active) - 10} 個警報_")
            
        except Exception as e:
            lines.append(f"獲取警報失敗: {e}")
        
        return lines
    
    def generate_compact(self) -> str:
        """生成簡潔版儀表板（單行格式）"""
        parts = []
        
        # 健康狀態
        if self.health_checker:
            try:
                health = self.health_checker.check()
                status = health.get("status", "unknown")
                emoji = {"healthy": "✅", "degraded": "⚠️", "unhealthy": "❌"}.get(status, "❓")
                parts.append(f"{emoji} 健康: {status}")
            except:
                pass
        
        # 錯誤率
        if self.metrics_collector:
            stats = self.metrics_collector.get_stats("error_rate")
            if stats["count"] > 0:
                rate = stats["latest"] * 100
                parts.append(f"❌ 錯誤: {rate:.1f}%")
        
        # 警報
        if self.alert_manager:
            count = len(self.alert_manager.get_active_alerts())
            if count > 0:
                parts.append(f"🚨 警報: {count}")
        
        return " | ".join(parts) if parts else "✅ 系統正常"


# 便捷函數
def create_dashboard(
    agent_id: str = "default",
    health_checker=None,
    circuit_breaker_manager=None,
    alert_manager=None
) -> Dashboard:
    """創建儀表板"""
    return Dashboard(
        agent_id=agent_id,
        health_checker=health_checker,
        circuit_breaker_manager=circuit_breaker_manager,
        alert_manager=alert_manager
    )
