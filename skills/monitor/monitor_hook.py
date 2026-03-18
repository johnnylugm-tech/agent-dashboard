#!/usr/bin/env python3
"""
自動嵌入對話流程模組 v3
參考: playbooks/multi-agent-collaboration-v2.md Phase 3 設計模式

功能：
- 自動嵌入到 OpenClaw 生命週期
- Middleware 模式自動追蹤
- Event Hook 自動觸發
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps


class EventType(Enum):
    """事件類型"""
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    TASK_START = "task_start"
    TASK_END = "task_end"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    ERROR = "error"
    RETRY = "retry"
    HUMAN_APPROVAL = "human_approval"


@dataclass
class ConversationEvent:
    """對話事件"""
    event_id: str
    event_type: EventType
    agent_id: str
    session_id: str
    user_id: str
    timestamp: datetime
    
    # 內容
    prompt: str = ""
    response: str = ""
    result: str = ""
    error: str = ""
    
    # 指標
    tokens_input: int = 0
    tokens_output: int = 0
    duration_ms: int = 0
    success: bool = True
    
    # 上下文
    metadata: Dict = field(default_factory=dict)


class MonitorHook:
    """
    監控鉤子 - 自動嵌入到 OpenClaw 生命週期
    
    使用方式：
    1. Middleware 模式：在 Gateway 層攔截
    2. Hook 模式：在每個 Agent 調用前後觸發
    3. Decorator 模式：用裝飾器包裝函數
    """
    
    def __init__(self):
        self.events: List[ConversationEvent] = []
        self.active_conversations: Dict[str, Dict] = {}
        self.enabled = True
        
        # 事件處理器
        self.handlers: Dict[EventType, List[Callable]] = {
            event_type: [] for event_type in EventType
        }
        
        # 配置
        self.config = {
            "auto_track": True,
            "store_events": True,
            "max_events": 10000,
            "flush_interval": 60  # 秒
        }
    
    # ============ Middleware 模式 ============
    
    def middleware(self):
        """
        Middleware 裝飾器 - 自動包裝異步函數
        
        用法：
        @monitor.middleware()
        async def process_message(message, next):
            # 自動記錄開始
            self.on_agent_start(agent_id, message)
            
            # 執行
            result = await next()
            
            # 自動記錄結果
            self.on_agent_end(agent_id, result)
            
            return result
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                if not self.enabled:
                    return await func(*args, **kwargs)
                
                # 從上下文獲取信息
                context = kwargs.get("context", {})
                agent_id = context.get("agent_id", "unknown")
                session_id = context.get("session_id", "unknown")
                user_id = context.get("user_id", "unknown")
                
                # 記錄開始
                self.on_agent_start(agent_id, session_id, user_id, 
                                 prompt=kwargs.get("prompt", ""))
                
                start_time = time.time()
                
                try:
                    # 執行
                    result = await func(*args, **kwargs)
                    
                    # 記錄成功
                    duration = int((time.time() - start_time) * 1000)
                    self.on_agent_end(agent_id, session_id, user_id,
                                    response=result, success=True,
                                    duration_ms=duration)
                    
                    return result
                    
                except Exception as e:
                    # 記錄錯誤
                    duration = int((time.time() - start_time) * 1000)
                    self.on_error(agent_id, session_id, user_id,
                               error=str(e), duration_ms=duration)
                    raise
        
        return wrapper
    
    # ============ Hook 模式 ============
    
    def register_handler(self, event_type: EventType, handler: Callable):
        """註冊事件處理器"""
        self.handlers[event_type].append(handler)
    
    def trigger(self, event: ConversationEvent):
        """觸發事件"""
        # 觸發註冊的處理器
        for handler in self.handlers[event.event_type]:
            try:
                handler(event)
            except Exception as e:
                print(f"Handler error: {e}")
        
        # 存儲事件
        if self.config["store_events"]:
            self.events.append(event)
            
            # 清理舊事件
            if len(self.events) > self.config["max_events"]:
                self.events = self.events[-self.config["max_events"]:]
    
    # ============ 事件觸發方法 ============
    
    def on_agent_start(self, agent_id: str, session_id: str, user_id: str,
                      prompt: str = "", metadata: Dict = None):
        """Agent 開始"""
        event = ConversationEvent(
            event_id=f"evt-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(self.events)}",
            event_type=EventType.AGENT_START,
            agent_id=agent_id,
            session_id=session_id,
            user_id=user_id,
            timestamp=datetime.now(),
            prompt=prompt,
            metadata=metadata or {}
        )
        
        # 追蹤活躍對話
        self.active_conversations[session_id] = {
            "agent_id": agent_id,
            "start_time": datetime.now(),
            "prompt": prompt
        }
        
        self.trigger(event)
        return event
    
    def on_agent_end(self, agent_id: str, session_id: str, user_id: str,
                    response: str = "", success: bool = True,
                    duration_ms: int = 0, tokens_used: int = 0):
        """Agent 結束"""
        event = ConversationEvent(
            event_id=f"evt-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(self.events)}",
            event_type=EventType.AGENT_END,
            agent_id=agent_id,
            session_id=session_id,
            user_id=user_id,
            timestamp=datetime.now(),
            response=response,
            success=success,
            duration_ms=duration_ms,
            tokens_input=tokens_used // 2,
            tokens_output=tokens_used // 2
        )
        
        # 清理活躍對話
        if session_id in self.active_conversations:
            del self.active_conversations[session_id]
        
        self.trigger(event)
        return event
    
    def on_task_start(self, agent_id: str, session_id: str, task: str):
        """任務開始"""
        event = ConversationEvent(
            event_id=f"evt-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(self.events)}",
            event_type=EventType.TASK_START,
            agent_id=agent_id,
            session_id=session_id,
            user_id=self.active_conversations.get(session_id, {}).get("user_id", ""),
            timestamp=datetime.now(),
            prompt=task
        )
        self.trigger(event)
        return event
    
    def on_task_end(self, agent_id: str, session_id: str, task: str,
                   result: str = "", success: bool = True):
        """任務結束"""
        event = ConversationEvent(
            event_id=f"evt-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(self.events)}",
            event_type=EventType.TASK_END,
            agent_id=agent_id,
            session_id=session_id,
            user_id=self.active_conversations.get(session_id, {}).get("user_id", ""),
            timestamp=datetime.now(),
            result=result,
            success=success
        )
        self.trigger(event)
        return event
    
    def on_tool_call(self, agent_id: str, session_id: str, tool_name: str,
                    tool_input: str = ""):
        """工具調用"""
        event = ConversationEvent(
            event_id=f"evt-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(self.events)}",
            event_type=EventType.TOOL_CALL,
            agent_id=agent_id,
            session_id=session_id,
            user_id=self.active_conversations.get(session_id, {}).get("user_id", ""),
            timestamp=datetime.now(),
            prompt=tool_name,
            metadata={"tool_input": tool_input}
        )
        self.trigger(event)
        return event
    
    def on_error(self, agent_id: str, session_id: str, user_id: str,
                error: str, duration_ms: int = 0):
        """錯誤發生"""
        event = ConversationEvent(
            event_id=f"evt-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(self.events)}",
            event_type=EventType.ERROR,
            agent_id=agent_id,
            session_id=session_id,
            user_id=user_id,
            timestamp=datetime.now(),
            error=error,
            duration_ms=duration_ms,
            success=False
        )
        self.trigger(event)
        
        # 觸發錯誤處理流程
        self._handle_error(event)
        
        return event
    
    def _handle_error(self, event: ConversationEvent):
        """錯誤處理流程 - 參考 playbook v2 Phase 4"""
        # 這裡可以連接 alerts_v2.py 的警報系統
        # 如果需要
        
        # 簡單日誌
        print(f"[Monitor] Error: {event.agent_id} - {event.error}")
    
    # ============ 查詢方法 ============
    
    def get_active_conversations(self) -> List[Dict]:
        """獲取活躍對話"""
        return list(self.active_conversations.values())
    
    def get_events(self, session_id: str = None, agent_id: str = None,
                  event_type: EventType = None, limit: int = 100) -> List[ConversationEvent]:
        """獲取事件"""
        filtered = self.events
        
        if session_id:
            filtered = [e for e in filtered if e.session_id == session_id]
        if agent_id:
            filtered = [e for e in filtered if e.agent_id == agent_id]
        if event_type:
            filtered = [e for e in filtered if e.event_type == event_type]
        
        return filtered[-limit:]
    
    def get_conversation_summary(self, session_id: str) -> Dict:
        """獲取對話摘要"""
        events = self.get_events(session_id=session_id)
        
        if not events:
            return {}
        
        return {
            "session_id": session_id,
            "total_events": len(events),
            "start_time": events[0].timestamp.isoformat() if events else None,
            "end_time": events[-1].timestamp.isoformat() if events else None,
            "duration_ms": sum(e.duration_ms for e in events),
            "total_tokens": sum(e.tokens_input + e.tokens_output for e in events),
            "errors": sum(1 for e in events if not e.success),
            "success_rate": sum(1 for e in events if e.success) / len(events) if events else 0
        }


# ============ OpenClaw 整合 ============

class OpenClawIntegration:
    """
    OpenClaw 整合適配器
    
    自動適配不同的 OpenClaw 版本和配置
    """
    
    def __init__(self, monitor: MonitorHook):
        self.monitor = monitor
    
    def detect_openclaw_version(self) -> str:
        """檢測 OpenClaw 版本"""
        # 實際應該讀取 OpenClaw 配置
        return "v1.0"
    
    def get_integration_method(self) -> str:
        """獲取整合方式"""
        version = self.detect_openclaw_version()
        
        if version.startswith("v1"):
            return "webhook"
        elif version.startswith("v2"):
            return "plugin"
        else:
            return "api"
    
    def generate_config(self) -> Dict:
        """生成 OpenClaw 配置"""
        method = self.get_integration_method()
        
        if method == "webhook":
            return {
                "webhook_url": os.getenv("OPENCLAW_WEBHOOK_URL", "http://localhost:8050/webhook"),
                "events": ["message", "agent_end", "error"]
            }
        elif method == "plugin":
            return {
                "plugin_name": "agent-monitor",
                "enabled": True,
                "config": self.monitor.config
            }
        else:
            return {
                "api_endpoint": "http://localhost:8050/api/monitor",
                "auth_token": os.getenv("OPENCLAW_API_TOKEN", "")
            }


# 單例
monitor_hook = MonitorHook()


# ============ 使用範例 ============

if __name__ == "__main__":
    # 測試自動嵌入
    
    print("="*50)
    print("🚀 測試自動嵌入對話流程")
    print("="*50)
    
    # 1. 模擬 Agent 開始
    monitor_hook.on_agent_start(
        agent_id="musk",
        session_id="session-001",
        user_id="johnny",
        prompt="查詢高鐵時刻表"
    )
    print("✅ Agent 開始")
    
    # 2. 模擬任務開始
    monitor_hook.on_task_start(
        agent_id="musk",
        session_id="session-001",
        task="查詢 TDX API"
    )
    print("✅ 任務開始")
    
    # 3. 模擬工具調用
    monitor_hook.on_tool_call(
        agent_id="musk",
        session_id="session-001",
        tool_name="web_search"
    )
    print("✅ 工具調用")
    
    # 4. 模擬錯誤
    monitor_hook.on_error(
        agent_id="musk",
        session_id="session-001",
        user_id="johnny",
        error="TDX API 審核失敗"
    )
    print("✅ 錯誤記錄")
    
    # 5. 模擬 Agent 結束
    monitor_hook.on_agent_end(
        agent_id="musk",
        session_id="session-001",
        user_id="johnny",
        response="已改用 PDF 方案",
        success=True,
        duration_ms=1500
    )
    print("✅ Agent 結束")
    
    # 6. 查詢摘要
    summary = monitor_hook.get_conversation_summary("session-001")
    print("\n📊 對話摘要:")
    print(f"  - 總事件數: {summary['total_events']}")
    print(f"  - 總時長: {summary['duration_ms']}ms")
    print(f"  - 錯誤數: {summary['errors']}")
    print(f"  - 成功率: {summary['success_rate']*100:.0f}%")
    
    # 7. OpenClaw 整合配置
    integration = OpenClawIntegration(monitor_hook)
    config = integration.generate_config()
    print("\n🔗 OpenClaw 整合配置:")
    print(f"  - 方式: {integration.get_integration_method()}")
    print(f"  - 配置: {config}")
    
    print("\n" + "="*50)
