#!/usr/bin/env python3
"""
OpenClaw 數據串流連接器

功能：
- 從 OpenClaw Gateway 即時拉取監控數據
- WebSocket 串流
- HTTP Polling
"""

import os
import json
import time
import threading
from datetime import datetime
from typing import Dict, List, Callable, Optional
import requests


class OpenClawConnector:
    """
    OpenClaw 數據串流連接器
    
    支援：
    - HTTP Polling
    - WebSocket（未來）
    """
    
    def __init__(self, gateway_url: str = None, api_key: str = None):
        self.gateway_url = gateway_url or os.getenv("OPENCLAW_GATEWAY_URL", "http://localhost:3000")
        self.api_key = api_key or os.getenv("OPENCLAW_API_KEY", "")
        self.running = False
        self.callbacks = []
        self.poll_interval = 5  # 秒
        
        # 緩存數據
        self.last_data = {}
        self.session_data = {}
    
    # ============== 基本連接 ==============
    
    def test_connection(self) -> bool:
        """測試連接"""
        try:
            # 嘗試訪問 health 端點
            response = requests.get(
                f"{self.gateway_url}/api/health",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def get_sessions(self) -> List[Dict]:
        """獲取所有會話"""
        try:
            response = requests.get(
                f"{self.gateway_url}/api/sessions",
                headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error getting sessions: {e}")
        return []
    
    def get_session_messages(self, session_id: str, limit: int = 50) -> List[Dict]:
        """獲取會話消息"""
        try:
            response = requests.get(
                f"{self.gateway_url}/api/sessions/{session_id}/messages",
                params={"limit": limit},
                headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error getting messages: {e}")
        return []
    
    def get_agent_status(self, agent_id: str = None) -> Dict:
        """獲取 Agent 狀態"""
        try:
            if agent_id:
                url = f"{self.gateway_url}/api/agents/{agent_id}"
            else:
                url = f"{self.gateway_url}/api/agents"
            
            response = requests.get(
                url,
                headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error getting agent status: {e}")
        return {}
    
    # ============== 監控數據 ==============
    
    def get_metrics(self) -> Dict:
        """獲取監控指標"""
        sessions = self.get_sessions()
        
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "total_sessions": len(sessions),
            "active_sessions": sum(1 for s in sessions if s.get("status") == "active"),
            "sessions": []
        }
        
        for session in sessions:
            session_metrics = {
                "session_id": session.get("id"),
                "agent_id": session.get("agent_id"),
                "user_id": session.get("user_id"),
                "status": session.get("status"),
                "message_count": session.get("message_count", 0),
                "started_at": session.get("started_at")
            }
            metrics["sessions"].append(session_metrics)
        
        return metrics
    
    def analyze_session(self, session_id: str) -> Dict:
        """分析單個會話"""
        messages = self.get_session_messages(session_id)
        
        if not messages:
            return {}
        
        # 計算統計
        user_messages = [m for m in messages if m.get("role") == "user"]
        assistant_messages = [m for m in messages if m.get("role") == "assistant"]
        
        # 估算 token（簡單估算）
        total_chars = sum(len(m.get("content", "")) for m in messages)
        estimated_tokens = total_chars // 4
        
        return {
            "session_id": session_id,
            "total_messages": len(messages),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "estimated_tokens": estimated_tokens,
            "first_message": messages[0].get("timestamp") if messages else None,
            "last_message": messages[-1].get("timestamp") if messages else None
        }
    
    # ============== Polling ==============
    
    def start_polling(self, callback: Callable = None, interval: int = 5):
        """開始 Polling"""
        self.running = True
        self.poll_interval = interval
        
        if callback:
            self.callbacks.append(callback)
        
        def poll_loop():
            while self.running:
                try:
                    metrics = self.get_metrics()
                    
                    # 觸發 callback
                    for cb in self.callbacks:
                        cb(metrics)
                    
                    self.last_data = metrics
                except Exception as e:
                    print(f"Polling error: {e}")
                
                time.sleep(self.poll_interval)
        
        thread = threading.Thread(target=poll_loop, daemon=True)
        thread.start()
        
        return thread
    
    def stop_polling(self):
        """停止 Polling"""
        self.running = False
    
    # ============== 整合 ==============
    
    def sync_to_monitor(self, monitor_api_url: str = "http://localhost:5001"):
        """同步到監控系統"""
        metrics = self.get_metrics()
        
        try:
            # 發送到本地 API
            response = requests.post(
                f"{monitor_api_url}/api/monitor/sync",
                json=metrics,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    # ============== 模擬數據（測試用） ==============
    
    def generate_mock_data(self) -> Dict:
        """生成模擬數據"""
        import random
        
        agents = ["musk", "pm-agent", "dev-agent", "research-agent"]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_sessions": random.randint(3, 10),
            "active_sessions": random.randint(1, 5),
            "sessions": [
                {
                    "session_id": f"session-{i}",
                    "agent_id": random.choice(agents),
                    "user_id": f"user-{random.randint(1, 100)}",
                    "status": random.choice(["active", "completed", "error"]),
                    "message_count": random.randint(5, 50)
                }
                for i in range(random.randint(3, 10))
            ]
        }


# ============== 使用範例 ==============

if __name__ == "__main__":
    connector = OpenClawConnector()
    
    print("="*50)
    print("🔗 OpenClaw 串流連接器測試")
    print("="*50)
    
    # 測試連接
    print("\n1. 測試連接...")
    connected = connector.test_connection()
    print(f"   連接狀態: {'✅ 成功' if connected else '❌ 失敗 (使用模擬數據)'}")
    
    # 獲取數據
    print("\n2. 獲取監控數據...")
    if connected:
        metrics = connector.get_metrics()
    else:
        metrics = connector.generate_mock_data()
        print("   (使用模擬數據)")
    
    print(f"   總會話數: {metrics['total_sessions']}")
    print(f"   活躍會話: {metrics['active_sessions']}")
    
    # 顯示會話
    print("\n3. 會話列表:")
    for session in metrics.get("sessions", [])[:3]:
        print(f"   - {session.get('agent_id')}: {session.get('status')}")
    
    print("\n" + "="*50)
