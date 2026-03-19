#!/usr/bin/env python3
"""
Trend Visualizer - 趨勢視覺化

生成簡單的趨勢圖（文字版）
"""

from typing import Dict, List
from datetime import datetime, timedelta


class TrendVisualizer:
    """趨勢視覺化"""
    
    def __init__(self, cost_tracker=None, health_tracker=None):
        """
        初始化視覺化器
        
        Args:
            cost_tracker: CostTracker 實例
            health_tracker: HealthTracker 實例
        """
        self.cost_tracker = cost_tracker
        self.health_tracker = health_tracker
    
    def render_bar_chart(self, data: Dict[str, float], title: str = "Chart") -> str:
        """
        渲染長條圖（文字版）
        
        Args:
            data: 數據字典 {label: value}
            title: 圖表標題
            
        Returns:
            字串圖表
        """
        if not data:
            return "No data"
        
        max_value = max(data.values())
        if max_value == 0:
            max_value = 1
        
        lines = [f"\n{'='*50}", title, f"{'='*50}\n"]
        
        for label, value in sorted(data.items(), key=lambda x: x[1], reverse=True):
            bar_length = int((value / max_value) * 30)
            bar = "█" * bar_length
            lines.append(f"{label:20s} |{bar}| {value:.2f}")
        
        return "\n".join(lines)
    
    def render_cost_trend(self, days: int = 7) -> str:
        """
        渲染成本趨勢
        
        Args:
            days: 天數
            
        Returns:
            趨勢圖
        """
        if not self.cost_tracker:
            return "No cost tracker"
        
        trend = self.cost_tracker.get_cost_trend(days=days)
        
        if not trend.get("daily"):
            return "No data"
        
        return self.render_bar_chart(
            trend["daily"], 
            f"Cost Trend (Last {days} days)"
        )
    
    def render_health_trend(self, days: int = 7) -> str:
        """
        渲染健康分數趨勢
        
        Args:
            days: 天數
            
        Returns:
            趨勢圖
        """
        if not self.health_tracker:
            return "No health tracker"
        
        # 假設有 get_health_trend 方法
        trend = self.health_tracker.get_health_trend(days=days) if hasattr(self.health_tracker, 'get_health_trend') else {}
        
        if not trend:
            return "No data"
        
        return self.render_bar_chart(
            trend, 
            f"Health Score Trend (Last {days} days)"
        )
    
    def render_comparison(self, current: float, previous: float, label: str = "Value") -> str:
        """
        渲染對比（本期 vs 上期）
        
        Args:
            current: 本期值
            previous: 上期值
            label: 標籤
            
        Returns:
            對比結果
        """
        if previous == 0:
            change = 100 if current > 0 else 0
        else:
            change = ((current - previous) / previous) * 100
        
        emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
        
        return f"""
{emoji} {label} Comparison
━━━━━━━━━━━━━━━━━━
Current:  {current:.2f}
Previous: {previous:.2f}
Change:   {change:+.1f}%
"""
    
    def generate_report(self, days: int = 7) -> str:
        """
        生成完整趨勢報告
        
        Args:
            days: 天數
            
        Returns:
            報告
        """
        lines = [
            f"\n{'#'*60}",
            f"# Trend Report - Last {days} days",
            f"{'#'*60}"
        ]
        
        # 成本趨勢
        lines.append(self.render_cost_trend(days))
        
        # 健康趨勢
        lines.append(self.render_health_trend(days))
        
        return "\n".join(lines)


# 使用範例
if __name__ == "__main__":
    from cost_tracker import CostTracker
    
    tracker = CostTracker()
    
    # 模擬一些數據
    tracker.record("agent-001", "gpt-4o", 100, 50)
    tracker.record("agent-001", "gpt-4o", 200, 100)
    tracker.record("agent-002", "claude-3", 150, 75)
    
    visualizer = TrendVisualizer(cost_tracker=tracker)
    
    print(visualizer.render_cost_trend(7))
    print(visualizer.render_comparison(100, 80, "Cost"))
