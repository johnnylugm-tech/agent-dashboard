#!/usr/bin/env python3
"""
成本分析模組 v2
參考: playbooks/multi-agent-collaboration-v2.md Phase 5 監控指標
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import defaultdict


# 價格配置（每 1K tokens 的美元價格）
# 參考: 2026年主流模型定價
MODEL_PRICING = {
    # OpenAI
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
    
    # Anthropic
    "claude-3-opus": {"input": 0.015, "output": 0.075},
    "claude-3-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
    
    # Google
    "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
    "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
    
    # Meta
    "llama-3-70b": {"input": 0.0009, "output": 0.0009},
    "llama-3-8b": {"input": 0.0002, "output": 0.0002},
    
    # Mistral
    "mistral-large": {"input": 0.002, "output": 0.006},
    "mistral-medium": {"input": 0.0007, "output": 0.0007},
    
    # DeepSeek
    "deepseek-chat": {"input": 0.00014, "output": 0.00028},
}

# 貨幣配置
DEFAULT_CURRENCY = "USD"
CURRENCY_SYMBOLS = {
    "USD": "$",
    "TWD": "NT$",
    "CNY": "¥",
}


@dataclass
class TokenUsage:
    """Token 使用記錄"""
    timestamp: datetime
    agent_id: str
    model: str
    input_tokens: int
    output_tokens: int
    duration_ms: int
    
    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class CostCalculator:
    """成本計算器"""
    
    def __init__(self, pricing: Dict = None):
        self.pricing = pricing or MODEL_PRICING
    
    def calculate(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """
        計算單次請求的美元成本
        
        公式: (input_tokens / 1000 * input_price) + (output_tokens / 1000 * output_price)
        """
        model_key = model.lower()
        
        # 精確匹配
        if model_key in self.pricing:
            prices = self.pricing[model_key]
        else:
            # 模糊匹配
            prices = self._find_closest_model(model_key)
        
        if not prices:
            return 0.0
        
        input_cost = (input_tokens / 1000) * prices["input"]
        output_cost = (output_tokens / 1000) * prices["output"]
        
        return input_cost + output_cost
    
    def _find_closest_model(self, model: str) -> Optional[Dict]:
        """找到最接近的模型定價"""
        for key in self.pricing:
            if key in model or model in key:
                return self.pricing[key]
        return None


class CostTracker:
    """
    成本追蹤器
    
    功能:
    - 記錄每次 Token 使用
    - 按 Agent/模型/時間段統計成本
    - 生成成本趨勢報告
    """
    
    def __init__(self):
        self.usage_records: List[TokenUsage] = []
        self.calculator = CostCalculator()
    
    def record(self, agent_id: str, model: str, input_tokens: int, 
               output_tokens: int, duration_ms: int = 0) -> float:
        """
        記錄一次 Token 使用
        
        Returns:
            本次請求的成本（美元）
        """
        # 計算成本
        cost = self.calculator.calculate(model, input_tokens, output_tokens)
        
        # 記錄
        record = TokenUsage(
            timestamp=datetime.now(),
            agent_id=agent_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_ms=duration_ms
        )
        self.usage_records.append(record)
        
        return cost
    
    def get_agent_cost(self, agent_id: str, period: str = "daily") -> Dict:
        """
        獲取指定 Agent 的成本
        
        Args:
            agent_id: Agent ID
            period: daily / weekly / monthly
        """
        records = self._filter_by_period(agent_id, period)
        
        if not records:
            return {"total_cost": 0, "total_tokens": 0, "requests": 0}
        
        # 按模型分組
        by_model = defaultdict(lambda: {"tokens": 0, "cost": 0, "requests": 0})
        
        for r in records:
            cost = self.calculator.calculate(r.model, r.input_tokens, r.output_tokens)
            by_model[r.model]["tokens"] += r.total_tokens
            by_model[r.model]["cost"] += cost
            by_model[r.model]["requests"] += 1
        
        total_cost = sum(m["cost"] for m in by_model.values())
        total_tokens = sum(m["tokens"] for m in by_model.values())
        
        return {
            "agent_id": agent_id,
            "period": period,
            "total_cost": round(total_cost, 4),
            "total_tokens": total_tokens,
            "requests": len(records),
            "by_model": dict(by_model),
            "avg_cost_per_request": round(total_cost / len(records), 4) if records else 0
        }
    
    def get_all_agents_cost(self, period: str = "daily") -> Dict:
        """獲取所有 Agent 的成本"""
        # 獲取所有 Agent ID
        agent_ids = set(r.agent_id for r in self.usage_records)
        
        agent_costs = {}
        for agent_id in agent_ids:
            agent_costs[agent_id] = self.get_agent_cost(agent_id, period)
        
        total_cost = sum(a["total_cost"] for a in agent_costs.values())
        
        return {
            "period": period,
            "total_cost": round(total_cost, 4),
            "agents": agent_costs
        }
    
    def get_cost_trend(self, agent_id: str = None, days: int = 7) -> Dict:
        """獲取成本趨勢"""
        cutoff = datetime.now() - timedelta(days=days)
        
        if agent_id:
            records = [r for r in self.usage_records 
                      if r.agent_id == agent_id and r.timestamp >= cutoff]
        else:
            records = [r for r in self.usage_records if r.timestamp >= cutoff]
        
        # 按天分組
        daily_cost = defaultdict(float)
        for r in records:
            day = r.timestamp.date()
            cost = self.calculator.calculate(r.model, r.input_tokens, r.output_tokens)
            daily_cost[day] += cost
        
        # 轉為列表
        trend = [{"date": str(day), "cost": round(cost, 4)} 
                 for day, cost in sorted(daily_cost.items())]
        
        # 計算趨勢
        if len(trend) >= 2:
            first_half = sum(t["cost"] for t in trend[:len(trend)//2])
            second_half = sum(t["cost"] for t in trend[len(trend)//2:])
            if first_half > 0:
                change = ((second_half - first_half) / first_half) * 100
                trend_direction = "increasing" if change > 10 else "decreasing" if change < -10 else "stable"
            else:
                change = 0
                trend_direction = "stable"
        else:
            change = 0
            trend_direction = "insufficient_data"
        
        return {
            "agent_id": agent_id,
            "days": days,
            "trend": trend,
            "trend_direction": trend_direction,
            "change_percent": round(change, 1),
            "total_cost": round(sum(t["cost"] for t in trend), 4)
        }
    
    def generate_report(self, period: str = "daily") -> str:
        """生成成本報告"""
        all_cost = self.get_all_agents_cost(period)
        
        lines = [
            f"💰 成本分析報告 - {period}",
            f"總成本: {CURRENCY_SYMBOLS[DEFAULT_CURRENCY]}{all_cost['total_cost']:.4f}",
            "",
            "📊 各 Agent 成本:",
        ]
        
        for agent_id, data in all_cost["agents"].items():
            lines.append(f"  • {agent_id}: ${data['total_cost']:.4f} ({data['requests']} 次請求)")
        
        # 趨勢
        trend = self.get_cost_trend(days=7)
        lines.extend([
            "",
            f"📈 7天趨勢: {trend['trend_direction']} ({trend['change_percent']:+.1f}%)"
        ])
        
        return "\n".join(lines)
    
    def _filter_by_period(self, agent_id: str, period: str) -> List[TokenUsage]:
        """根據時間段過濾記錄"""
        now = datetime.now()
        
        if period == "daily":
            cutoff = now - timedelta(days=1)
        elif period == "weekly":
            cutoff = now - timedelta(days=7)
        elif period == "monthly":
            cutoff = now - timedelta(days=30)
        else:
            cutoff = now - timedelta(days=1)
        
        return [r for r in self.usage_records 
                if r.agent_id == agent_id and r.timestamp >= cutoff]


# 單例
cost_tracker = CostTracker()


# ============ 使用範例 ============

if __name__ == "__main__":
    # 模擬記錄
    import random
    
    models = ["gpt-4", "claude-3-sonnet", "gemini-1.5-flash"]
    agents = ["dev-agent", "research-agent", "review-agent"]
    
    print("📊 模擬成本記錄...")
    
    for _ in range(20):
        agent = random.choice(agents)
        model = random.choice(models)
        input_tok = random.randint(1000, 10000)
        output_tok = random.randint(500, 5000)
        
        cost = cost_tracker.record(
            agent_id=agent,
            model=model,
            input_tokens=input_tok,
            output_tokens=output_tok,
            duration_ms=random.randint(1000, 10000)
        )
    
    # 生成報告
    print("\n" + "="*50)
    print(cost_tracker.generate_report("daily"))
    print("="*50)
    
    # 單個 Agent
    print("\n📈 dev-agent 成本趨勢:")
    trend = cost_tracker.get_cost_trend("dev-agent", days=7)
    print(f"  趨勢: {trend['trend_direction']} ({trend['change_percent']:+.1f}%)")
    print(f"  總成本: ${trend['total_cost']:.4f}")
