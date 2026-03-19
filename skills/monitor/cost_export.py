#!/usr/bin/env python3
"""
Cost Export - 成本數據導出

支援導出為多種格式，方便 BI 系統整合
"""

import json
import csv
from typing import Dict, List
from datetime import datetime
from io import StringIO


class CostExporter:
    """成本數據導出器"""
    
    def __init__(self, cost_tracker):
        """
        初始化導出器
        
        Args:
            cost_tracker: CostTracker 實例
        """
        self.tracker = cost_tracker
    
    def export_json(self, period: str = "daily") -> str:
        """
        導出為 JSON 格式
        
        Args:
            period: 時間週期
            
        Returns:
            JSON 字串
        """
        data = self.tracker.get_all_agents_cost(period)
        return json.dumps(data, indent=2, default=str)
    
    def export_csv(self, period: str = "daily") -> str:
        """
        導出為 CSV 格式
        
        Args:
            period: 時間週期
            
        Returns:
            CSV 字串
        """
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "agent_id", "task_id", "model", "input_tokens", 
            "output_tokens", "total_tokens", "cost", "timestamp"
        ])
        
        # 獲取所有記錄
        for record in self.tracker.usage_records:
            writer.writerow([
                record.agent_id,
                record.task_id or "",
                record.model,
                record.input_tokens,
                record.output_tokens,
                record.total_tokens,
                self.tracker.calculator.calculate(
                    record.model, 
                    record.input_tokens, 
                    record.output_tokens
                ),
                record.timestamp.isoformat()
            ])
        
        return output.getvalue()
    
    def export_by_agent(self, agent_id: str, period: str = "daily") -> Dict:
        """
        按 Agent 導出詳細數據
        
        Args:
            agent_id: Agent ID
            period: 時間週期
            
        Returns:
            導出數據
        """
        return self.tracker.get_agent_cost(agent_id, period)
    
    def export_by_task(self, task_id: str, period: str = "daily") -> Dict:
        """
        按任務導出詳細數據
        
        Args:
            task_id: 任務 ID
            period: 時間週期
            
        Returns:
            導出數據
        """
        return self.tracker.get_task_cost(task_id, period)
    
    def export_summary(self, period: str = "daily") -> Dict:
        """
        導出摘要報告
        
        Args:
            period: 時間週期
            
        Returns:
            摘要數據
        """
        all_agents = self.tracker.get_all_agents_cost(period)
        all_tasks = self.tracker.get_all_tasks_cost(period)
        
        return {
            "period": period,
            "generated_at": datetime.now().isoformat(),
            "total_cost": all_agents["total_cost"],
            "total_agents": len(all_agents.get("agents", {})),
            "total_tasks": len(all_tasks.get("tasks", {})),
            "top_agents": self._get_top_entities(all_agents.get("agents", {}), 5),
            "top_tasks": self._get_top_entities(all_tasks.get("tasks", {}), 5)
        }
    
    def _get_top_entities(self, entities: Dict, top_n: int) -> List[Dict]:
        """獲取 top N 實體"""
        sorted_entities = sorted(
            entities.items(), 
            key=lambda x: x[1].get("total_cost", 0), 
            reverse=True
        )
        return [
            {"id": k, "cost": v.get("total_cost", 0)}
            for k, v in sorted_entities[:top_n]
        ]


# 使用範例
if __name__ == "__main__":
    from cost_tracker import CostTracker
    
    tracker = CostTracker()
    
    # 記錄一些數據
    tracker.record("agent-001", "gpt-4o", 100, 50, task_id="task-001")
    tracker.record("agent-001", "gpt-4o", 200, 100, task_id="task-002")
    tracker.record("agent-002", "claude-3", 150, 75, task_id="task-001")
    
    exporter = CostExporter(tracker)
    
    print("=== JSON Export ===")
    print(exporter.export_json())
    
    print("\n=== CSV Export ===")
    print(exporter.export_csv())
    
    print("\n=== Summary ===")
    print(exporter.export_summary())
