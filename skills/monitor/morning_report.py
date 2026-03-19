#!/usr/bin/env python3
"""
Morning Report Generator - 晨間報告生成器

一鍵生成每日健康檢查報告
"""

from datetime import datetime, timedelta
from typing import Dict, List
import json


class MorningReportGenerator:
    """晨間報告生成器"""
    
    def __init__(self, health_tracker=None, cost_tracker=None, 
                 alert_manager=None, journey_tracker=None):
        """
        初始化
        
        Args:
            health_tracker: 健康追蹤器
            cost_tracker: 成本追蹤器
            alert_manager: 警報管理器
            journey_tracker: Journey 追蹤器
        """
        self.health = health_tracker
        self.cost = cost_tracker
        self.alerts = alert_manager
        self.journey = journey_tracker
    
    def generate(self, date: str = None) -> str:
        """
        生成晨間報告
        
        Args:
            date: 日期 (預設今天)
            
        Returns:
            報告字串
        """
        date = date or datetime.now().strftime("%Y-%m-%d")
        
        lines = [
            f"\n{'='*60}",
            f"🌅 Morning Report - {date}",
            f"{'='*60}",
            ""
        ]
        
        # 1. 總覽
        lines.append("📊 總覽")
        lines.append("-" * 40)
        
        # 健康分數
        if self.health:
            health_score = self.health.get_current_score()
            lines.append(f"  健康評分: {health_score}/100")
        
        # 成本
        if self.cost:
            daily_cost = self.cost.get_agent_cost("all", "daily")
            lines.append(f"  昨日成本: ${daily_cost.get('total_cost', 0):.2f}")
        
        # 警報
        if self.alerts:
            yesterday_alerts = self.alerts.get_alert_history(limit=100)
            lines.append(f"  昨日警報: {len(yesterday_alerts)} 次")
        
        lines.append("")
        
        # 2. 趨勢
        lines.append("📈 趨勢 (7天)")
        lines.append("-" * 40)
        
        if self.cost:
            trend = self.cost.get_cost_trend(days=7)
            daily = trend.get("daily", {})
            for day, cost in sorted(daily.items())[-7:]:
                lines.append(f"  {day}: ${cost:.2f}")
        
        lines.append("")
        
        # 3. 異常警報
        lines.append("⚠️ 異常警報")
        lines.append("-" * 40)
        
        if self.alerts:
            critical = [a for a in self.alerts.get_alert_history(limit=50) 
                       if a.get("level") == "critical"]
            if critical:
                for alert in critical[:5]:
                    lines.append(f"  🔴 {alert.get('title')}: {alert.get('message')}")
            else:
                lines.append("  ✅ 無重大異常")
        
        lines.append("")
        
        # 4. 今日待辦
        lines.append("📋 今日待辦")
        lines.append("-" * 40)
        lines.append("  - 檢查 Agent 運行狀態")
        lines.append("  - 確認成本趨勢")
        lines.append("  - 查看警報記錄")
        
        lines.append(f"\n{'='*60}")
        lines.append(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return "\n".join(lines)
    
    def generate_json(self, date: str = None) -> Dict:
        """生成 JSON 格式報告"""
        date = date or datetime.now().strftime("%Y-%m-%d")
        
        return {
            "date": date,
            "generated_at": datetime.now().isoformat(),
            "overview": {
                "health_score": self.health.get_current_score() if self.health else 0,
                "daily_cost": self.cost.get_agent_cost("all", "daily").get("total_cost", 0) if self.cost else 0,
                "alert_count": len(self.alerts.get_alert_history(limit=100)) if self.alerts else 0
            },
            "cost_trend": self.cost.get_cost_trend(days=7).get("daily", {}) if self.cost else {},
            "critical_alerts": [
                a for a in self.alerts.get_alert_history(limit=50)
                if a.get("level") == "critical"
            ] if self.alerts else []
        }
    
    def send_to_slack(self, webhook_url: str):
        """發送到 Slack"""
        import requests
        
        report = self.generate_json()
        
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"🌅 Morning Report - {report['date']}"}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*健康評分:*\n{report['overview']['health_score']}/100"},
                    {"type": "mrkdwn", "text": f"*昨日成本:*\n${report['overview']['daily_cost']:.2f}"},
                    {"type": "mrkdwn", "text": f"*警報數:*\n{report['overview']['alert_count']}"}
                ]
            }
        ]
        
        requests.post(webhook_url, json={"blocks": blocks})


# 使用範例
if __name__ == "__main__":
    # 模擬數據（實際使用時連接真實追蹤器）
    class MockHealth:
        def get_current_score(self): return 85
    
    class MockCost:
        def get_agent_cost(self, agent_id, period):
            return {"total_cost": 12.50}
        def get_cost_trend(self, days=7):
            return {"daily": {"2026-03-13": 10.0, "2026-03-14": 12.0, "2026-03-15": 8.0}}
    
    class MockAlerts:
        def get_alert_history(self, limit=100):
            return []
    
    generator = MorningReportGenerator(
        health_tracker=MockHealth(),
        cost_tracker=MockCost(),
        alert_manager=MockAlerts()
    )
    
    print(generator.generate())
