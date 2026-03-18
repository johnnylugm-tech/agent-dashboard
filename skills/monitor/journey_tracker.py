#!/usr/bin/env python3
"""
跨對話追蹤模組 v2
參考: playbooks/multi-agent-collaboration-v2.md Phase 5 監控

功能：
- 追蹤單一用戶在不同 Agent 間流轉的完整旅程
- 記錄每個階段的輸入輸出
- 分析用戶行為模式
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import json


@dataclass
class JourneyStep:
    """旅程步驟"""
    step_id: int
    agent_id: str
    agent_type: str  # main, pm, dev, research, review
    action: str  # task_start, tool_call, task_complete, etc.
    timestamp: datetime
    
    # 內容
    input_text: str = ""
    output_text: str = ""
    
    # 指標
    duration_ms: int = 0
    tokens_used: int = 0
    success: bool = True
    error: str = ""


@dataclass
class UserJourney:
    """用戶旅程"""
    journey_id: str
    user_id: str
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    
    steps: List[JourneyStep] = field(default_factory=list)
    
    @property
    def duration_minutes(self) -> int:
        """總時長（分鐘）"""
        end = self.end_time or datetime.now()
        return int((end - self.start_time).total_seconds() / 60)
    
    @property
    def agent_count(self) -> int:
        """涉及 Agent 數"""
        return len(set(s.agent_id for s in self.steps))
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if not self.steps:
            return 0
        return sum(1 for s in self.steps if s.success) / len(self.steps)


class JourneyTracker:
    """
    跨對話追蹤器
    
    功能：
    - 追蹤單一用戶在不同 Agent 間的流動
    - 記錄完整旅程
    - 分析行為模式
    """
    
    def __init__(self):
        # 按用戶 ID 存儲
        self.journeys_by_user: Dict[str, List[UserJourney]] = defaultdict(list)
        
        # 按 session ID 存儲
        self.journeys_by_session: Dict[str, UserJourney] = {}
        
        # 當前進行中的旅程
        self.active_journeys: Dict[str, UserJourney] = {}
    
    def start_journey(self, user_id: str, session_id: str, initial_agent: str = "musk") -> str:
        """
        開始新的旅程
        
        Returns:
            journey_id
        """
        journey_id = f"journey-{user_id}-{session_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        journey = UserJourney(
            journey_id=journey_id,
            user_id=user_id,
            session_id=session_id,
            start_time=datetime.now()
        )
        
        self.journeys_by_user[user_id].append(journey)
        self.journeys_by_session[session_id] = journey
        self.active_journeys[session_id] = journey
        
        return journey_id
    
    def add_step(self, session_id: str, agent_id: str, agent_type: str,
                action: str, input_text: str = "", output_text: str = "",
                duration_ms: int = 0, tokens_used: int = 0,
                success: bool = True, error: str = "") -> int:
        """
        添加旅程步驟
        
        Returns:
            step_id
        """
        if session_id not in self.active_journeys:
            return -1
        
        journey = self.active_journeys[session_id]
        
        step_id = len(journey.steps) + 1
        
        step = JourneyStep(
            step_id=step_id,
            agent_id=agent_id,
            agent_type=agent_type,
            action=action,
            timestamp=datetime.now(),
            input_text=input_text,
            output_text=output_text,
            duration_ms=duration_ms,
            tokens_used=tokens_used,
            success=success,
            error=error
        )
        
        journey.steps.append(step)
        
        return step_id
    
    def end_journey(self, session_id: str):
        """結束旅程"""
        if session_id in self.active_journeys:
            journey = self.active_journeys[session_id]
            journey.end_time = datetime.now()
            del self.active_journeys[session_id]
    
    def get_journey(self, journey_id: str = None, session_id: str = None) -> Optional[UserJourney]:
        """獲取旅程"""
        if session_id and session_id in self.journeys_by_session:
            return self.journeys_by_session[session_id]
        
        if journey_id:
            for journeys in self.journeys_by_user.values():
                for j in journeys:
                    if j.journey_id == journey_id:
                        return j
        
        return None
    
    def get_user_journeys(self, user_id: str, limit: int = 10) -> List[UserJourney]:
        """獲取用戶的所有旅程"""
        journeys = self.journeys_by_user.get(user_id, [])
        return journeys[-limit:]
    
    def analyze_patterns(self, user_id: str = None) -> Dict:
        """
        分析行為模式
        """
        if user_id:
            journeys = self.journeys_by_user.get(user_id, [])
        else:
            # 全局分析
            journeys = []
            for j_list in self.journeys_by_user.values():
                journeys.extend(j_list)
        
        if not journeys:
            return {"error": "No journey data"}
        
        # 統計
        total_journeys = len(journeys)
        completed_journeys = sum(1 for j in journeys if j.end_time)
        
        # 平均值
        avg_duration = sum(j.duration_minutes for j in journeys if j.end_time) / max(completed_journeys, 1)
        avg_agents = sum(j.agent_count for j in journeys) / total_journeys
        avg_success = sum(j.success_rate for j in journeys) / total_journeys
        
        # 常用流程
        flow_counts = defaultdict(int)
        for j in journeys:
            flow = " → ".join(set(s.agent_type for s in j.steps))
            flow_counts[flow] += 1
        
        top_flows = sorted(flow_counts.items(), key=lambda x: -x[1])[:5]
        
        # 瓶頸分析
        error_agents = defaultdict(int)
        for j in journeys:
            for step in j.steps:
                if not step.success:
                    error_agents[step.agent_type] += 1
        
        return {
            "total_journeys": total_journeys,
            "completed_journeys": completed_journeys,
            "avg_duration_minutes": round(avg_duration, 1),
            "avg_agents_per_journey": round(avg_agents, 1),
            "avg_success_rate": round(avg_success * 100, 1),
            "top_flows": [{"flow": f, "count": c} for f, c in top_flows],
            "bottleneck_agents": dict(error_agents)
        }
    
    def export_journey_json(self, session_id: str) -> str:
        """導出旅程為 JSON"""
        journey = self.journeys_by_session.get(session_id)
        if not journey:
            return "{}"
        
        data = {
            "journey_id": journey.journey_id,
            "user_id": journey.user_id,
            "session_id": journey.session_id,
            "start_time": journey.start_time.isoformat(),
            "end_time": journey.end_time.isoformat() if journey.end_time else None,
            "duration_minutes": journey.duration_minutes,
            "agent_count": journey.agent_count,
            "success_rate": journey.success_rate,
            "steps": [
                {
                    "step": s.step_id,
                    "agent": s.agent_id,
                    "type": s.agent_type,
                    "action": s.action,
                    "timestamp": s.timestamp.isoformat(),
                    "duration_ms": s.duration_ms,
                    "tokens": s.tokens_used,
                    "success": s.success
                }
                for s in journey.steps
            ]
        }
        
        return json.dumps(data, ensure_ascii=False, indent=2)


# 單例
journey_tracker = JourneyTracker()


# ============ 使用範例 ============

if __name__ == "__main__":
    # 模擬用戶旅程
    tracker = JourneyTracker()
    
    # 開始旅程
    journey_id = tracker.start_journey(
        user_id="johnny",
        session_id="session-001",
        initial_agent="musk"
    )
    print(f"🚀 開始旅程: {journey_id}")
    
    # 模擬步驟
    tracker.add_step(
        session_id="session-001",
        agent_id="musk",
        agent_type="main",
        action="task_start",
        input_text="查詢高鐵時刻表",
        output_text="已開啟訂票頁面"
    )
    
    tracker.add_step(
        session_id="session-001",
        agent_id="research-agent",
        agent_type="research",
        action="tool_call",
        input_text="查詢 TDX API",
        output_text="API 需要審核",
        duration_ms=1500
    )
    
    tracker.add_step(
        session_id="session-001",
        agent_id="dev-agent",
        agent_type="dev",
        action="task_complete",
        input_text="下載 PDF",
        output_text="完成下載",
        duration_ms=3000,
        tokens_used=5000
    )
    
    # 結束旅程
    tracker.end_journey("session-001")
    
    # 獲取旅程
    journey = tracker.get_journey(session_id="session-001")
    
    print(f"\n📋 旅程記錄:")
    print(f"  用戶: {journey.user_id}")
    print(f"  總時長: {journey.duration_minutes} 分鐘")
    print(f"  涉及 Agent: {journey.agent_count} 個")
    print(f"  成功率: {journey.success_rate*100:.0f}%")
    
    print(f"\n👣 步驟:")
    for step in journey.steps:
        print(f"  {step.step_id}. {step.agent_type} ({step.agent_id}): {step.action}")
    
    # 分析模式
    print(f"\n📊 行為分析:")
    patterns = tracker.analyze_patterns()
    print(f"  總旅程數: {patterns['total_journeys']}")
    print(f"  平均時長: {patterns['avg_duration_minutes']} 分鐘")
    print(f"  平均 Agent 數: {patterns['avg_agents_per_journey']}")
