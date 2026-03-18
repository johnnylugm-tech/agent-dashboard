#!/usr/bin/env python3
"""
異常自動通知模組 v2
參考: playbooks/multi-agent-collaboration-v2.md Phase 4 錯誤處理
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional

# 通知渠道配置
class AlertChannel:
    """通知渠道基類"""
    def send(self, message: str, level: str): raise NotImplementedError

class TelegramNotifier(AlertChannel):
    """Telegram 通知"""
    def __init__(self, token: str = None, chat_id: str = None):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
    
    def send(self, message: str, level: str):
        if not self.token:
            print(f"[Telegram] {level}: {message}")
            return
        
        # Telegram API 調用
        # import requests
        # url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        # requests.post(url, json={"chat_id": self.chat_id, "text": f"{level}: {message}"})

class SlackNotifier(AlertChannel):
    """Slack 通知"""
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
    
    def send(self, message: str, level: str):
        if not self.webhook_url:
            print(f"[Slack] {level}: {message}")
            return
        
        # Slack API 調用
        # import requests
        # requests.post(self.webhook_url, json={"text": f"{level}: {message}"})

class EmailNotifier(AlertChannel):
    """Email 通知"""
    def __init__(self, smtp_server: str = None, smtp_port: int = 587):
        self.smtp_server = smtp_server or os.getenv("SMTP_SERVER")
        self.smtp_port = smtp_port
        self.sender = os.getenv("SMTP_SENDER")
        self.recipients = os.getenv("SMTP_RECIPIENTS", "").split(",")
    
    def send(self, message: str, level: str):
        if not self.smtp_server:
            print(f"[Email] {level}: {message}")
            return
        
        # Email 發送邏輯
        # import smtplib
        # from email.mime.text import MIMEText

class WebhookNotifier(AlertChannel):
    """Webhook 通知"""
    def __init__(self, url: str = None):
        self.url = url or os.getenv("WEBHOOK_URL")
    
    def send(self, message: str, level: str):
        if not self.url:
            print(f"[Webhook] {level}: {message}")
            return
        
        # Webhook 調用
        # import requests
        # requests.post(self.url, json={"level": level, "message": message})


class AlertManager:
    """
    警報管理器
    根據錯誤率、熔斷狀態等條件觸發通知
    """
    
    # 警報閾值
    THRESHOLDS = {
        "critical": {
            "error_rate": 0.20,      # 錯誤率 > 20%
            "circuit_breaker": True,   # 熔斷觸發
            "agent_down": 60,        # Agent 宕機 > 1分鐘
        },
        "warning": {
            "latency_p95": 5.0,      # P95 延遲 > 5秒
            "retry_rate": 0.15,      # 重試率 > 15%
            "low_confidence": 0.7,   # 信心度 < 0.7
        }
    }
    
    def __init__(self):
        self.channels = {
            "telegram": TelegramNotifier(),
            "slack": SlackNotifier(),
            "email": EmailNotifier(),
            "webhook": WebhookNotifier()
        }
        self.alert_history = []
    
    def check_and_notify(self, metrics: Dict, agent_id: str) -> List[Dict]:
        """
        檢查指標並觸發警報
        參考: playbooks/multi-agent-collaboration-v2.md Phase 5 警報規則
        """
        alerts_triggered = []
        
        # 檢查 critical 條件
        if metrics.get("error_rate", 0) > self.THRESHOLDS["critical"]["error_rate"]:
            alert = self._create_alert(
                agent_id=agent_id,
                level="critical",
                title="HighErrorRate",
                message=f"錯誤率 {metrics['error_rate']*100:.1f}% > 20%",
                channels=["telegram", "slack"]
            )
            alerts_triggered.append(alert)
            self._send_alert(alert)
        
        if metrics.get("circuit_breaker_triggered", False):
            alert = self._create_alert(
                agent_id=agent_id,
                level="critical",
                title="CircuitBreakerTriggered",
                message="熔斷機制已觸發",
                channels=["telegram", "slack", "email"]
            )
            alerts_triggered.append(alert)
            self._send_alert(alert)
        
        # 檢查 warning 條件
        if metrics.get("latency_p95", 0) > self.THRESHOLDS["warning"]["latency_p95"]:
            alert = self._create_alert(
                agent_id=agent_id,
                level="warning",
                title="HighLatency",
                message=f"P95 延遲 {metrics['latency_p95']:.1f}s > 5s",
                channels=["telegram"]
            )
            alerts_triggered.append(alert)
            self._send_alert(alert)
        
        if metrics.get("retry_rate", 0) > self.THRESHOLDS["warning"]["retry_rate"]:
            alert = self._create_alert(
                agent_id=agent_id,
                level="warning",
                title="HighRetryRate",
                message=f"重試率 {metrics['retry_rate']*100:.1f}% > 15%",
                channels=["telegram"]
            )
            alerts_triggered.append(alert)
            self._send_alert(alert)
        
        return alerts_triggered
    
    def _create_alert(self, agent_id: str, level: str, title: str, 
                      message: str, channels: List[str]) -> Dict:
        """創建警報對象"""
        alert = {
            "id": f"alert-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "level": level,  # critical / warning / info
            "title": title,
            "message": message,
            "channels": channels,
            "status": "sent" if channels else "disabled"
        }
        self.alert_history.append(alert)
        return alert
    
    def _send_alert(self, alert: Dict):
        """發送警報到各渠道"""
        for channel_name in alert["channels"]:
            if channel_name in self.channels:
                try:
                    self.channels[channel_name].send(
                        f"[{alert['level'].upper()}] {alert['title']}: {alert['message']}",
                        alert["level"]
                    )
                except Exception as e:
                    print(f"Failed to send to {channel_name}: {e}")
    
    def get_alert_history(self, agent_id: str = None, limit: int = 100) -> List[Dict]:
        """獲取警報歷史"""
        if agent_id:
            return [a for a in self.alert_history if a["agent_id"] == agent_id][-limit:]
        return self.alert_history[-limit:]


# 單例實例
alert_manager = AlertManager()


# ============ 使用範例 ============

if __name__ == "__main__":
    # 模擬監控指標
    test_metrics = {
        "error_rate": 0.25,           # 25% 錯誤率 → critical
        "circuit_breaker_triggered": False,
        "latency_p95": 6.5,          # 6.5s → warning
        "retry_rate": 0.18,          # 18% 重試率 → warning
        "success_rate": 0.75,
        "total_requests": 100
    }
    
    # 觸發檢查
    alerts = alert_manager.check_and_notify(test_metrics, agent_id="test-agent")
    
    print(f"\n觸發 {len(alerts)} 個警報:")
    for alert in alerts:
        print(f"  - [{alert['level']}] {alert['title']}: {alert['message']}")
    
    # 查看歷史
    print(f"\n警報歷史: {len(alert_manager.get_alert_history())} 條")
