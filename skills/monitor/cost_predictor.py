#!/usr/bin/env python3
"""
Cost Predictor - 成本預測

基於歷史數據預測未來成本
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import statistics


class CostPredictor:
    """成本預測器"""
    
    def __init__(self, cost_tracker):
        """
        初始化
        
        Args:
            cost_tracker: CostTracker 實例
        """
        self.tracker = cost_tracker
    
    def predict_daily(self, days: int = 7) -> Dict:
        """
        預測未來每日成本
        
        Args:
            days: 預測天數
            
        Returns:
            預測結果
        """
        # 獲取歷史數據
        history = self._get_history(days * 2)  # 2倍天數作為歷史
        
        if len(history) < 3:
            return {
                "prediction": "insufficient_data",
                "message": "需要更多歷史數據"
            }
        
        # 計算平均值和趨勢
        daily_costs = self._aggregate_daily(history)
        
        if not daily_costs:
            return {"prediction": "no_data", "message": "無歷史數據"}
        
        # 計算預測
        avg_cost = statistics.mean(daily_costs.values())
        trend = self._calculate_trend(list(daily_costs.values()))
        
        # 預測未來
        predictions = {}
        for i in range(1, days + 1):
            date = datetime.now() + timedelta(days=i)
            predicted = avg_cost * (1 + trend * i / 30)  # 簡單線性趨勢
            predictions[date.strftime("%Y-%m-%d")] = round(max(0, predicted), 2)
        
        return {
            "prediction": "success",
            "days": days,
            "avg_daily_cost": round(avg_cost, 2),
            "trend": f"{trend*100:+.1f}%",  # 趨勢百分比
            "predictions": predictions,
            "monthly_estimate": round(avg_cost * 30, 2),
            "confidence": self._get_confidence(len(daily_costs))
        }
    
    def predict_monthly(self) -> Dict:
        """預測本月成本"""
        # 獲取本月歷史
        now = datetime.now()
        start_of_month = now.replace(day=1)
        
        history = [r for r in self.tracker.usage_records 
                  if r.timestamp >= start_of_month]
        
        # 計算當前本月成本
        current_cost = sum(
            self.tracker.calculator.calculate(r.model, r.input_tokens, r.output_tokens)
            for r in history
        )
        
        # 預測剩餘天數
        days_left = (now.replace(day=1) + timedelta(days=32)).replace(day=1) - now
        days_passed = now.day
        
        daily_avg = current_cost / days_passed if days_passed > 0 else 0
        predicted_total = current_cost + (daily_avg * days_left.days)
        
        return {
            "current_cost": round(current_cost, 2),
            "days_passed": days_passed,
            "days_left": days_left.days,
            "daily_avg": round(daily_avg, 2),
            "predicted_total": round(predicted_total, 2),
            "budget": 100.0,  # 可配置的預算
            "budget_remaining": round(100 - predicted_total, 2),
            "status": "over_budget" if predicted_total > 100 else "under_budget"
        }
    
    def get_budget_alert(self, daily_budget: float = 10.0) -> Dict:
        """
        獲取預算警報
        
        Args:
            daily_budget: 每日預算
            
        Returns:
            警報信息
        """
        prediction = self.predict_daily(1)
        
        if prediction.get("prediction") != "success":
            return {"alert": False}
        
        tomorrow_cost = list(prediction["predictions"].values())[0]
        
        if tomorrow_cost > daily_budget:
            return {
                "alert": True,
                "level": "critical" if tomorrow_cost > daily_budget * 1.5 else "warning",
                "predicted_cost": tomorrow_cost,
                "budget": daily_budget,
                "message": f"預測明日成本 ${tomorrow_cost:.2f} 超出預算 ${daily_budget:.2f}"
            }
        
        return {"alert": False, "message": "成本正常"}
    
    def _get_history(self, days: int) -> List:
        """獲取歷史記錄"""
        cutoff = datetime.now() - timedelta(days=days)
        return [r for r in self.tracker.usage_records if r.timestamp >= cutoff]
    
    def _aggregate_daily(self, records: List) -> Dict[str, float]:
        """按天聚合成本"""
        daily = defaultdict(float)
        
        for r in records:
            cost = self.tracker.calculator.calculate(r.model, r.input_tokens, r.output_tokens)
            day = r.timestamp.strftime("%Y-%m-%d")
            daily[day] += cost
        
        return dict(daily)
    
    def _calculate_trend(self, values: List[float]) -> float:
        """計算趨勢（簡單線性回歸）"""
        if len(values) < 2:
            return 0
        
        n = len(values)
        x = list(range(n))
        y = values
        
        # 簡單線性回歸
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0
        
        slope = numerator / denominator
        
        # 轉換為百分比趨勢
        avg = sum(y) / n
        return slope / avg if avg > 0 else 0
    
    def _get_confidence(self, data_points: int) -> str:
        """獲取預測可信度"""
        if data_points >= 14:
            return "high"
        elif data_points >= 7:
            return "medium"
        else:
            return "low"


# 使用範例
if __name__ == "__main__":
    from cost_tracker import CostTracker
    
    tracker = CostTracker()
    
    # 添加一些測試數據
    import random
    for i in range(30):
        cost = random.uniform(5, 20)
        # 這裡只是模擬，實際會從數據庫讀取
    
    predictor = CostPredictor(tracker)
    
    # 預測
    result = predictor.predict_daily(7)
    print("=== 7天成本預測 ===")
    if result.get("prediction") == "success":
        print(f"平均每日: ${result['avg_daily_cost']}")
        print(f"趨勢: {result['trend']}")
        print(f"本月預測: ${result['monthly_estimate']}")
        print(f"可信度: {result['confidence']}")
        print("\n每日預測:")
        for day, cost in result['predictions'].items():
            print(f"  {day}: ${cost}")
