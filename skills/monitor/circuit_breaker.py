"""
熔斷機制（Circuit Breaker）

防止故障蔓延，實現故障隔離和自動恢復
"""

import time
from enum import Enum
from typing import Callable, Any, Optional, Dict
from dataclasses import dataclass, field
from datetime import datetime


class CircuitState(Enum):
    """熔斷器狀態"""
    CLOSED = "closed"     # 正常關閉
    OPEN = "open"         # 斷開（熔斷）
    HALF_OPEN = "half_open"  # 半開（測試恢復）


class CircuitEvent(Enum):
    """熔斷器事件"""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    STATE_CHANGE = "state_change"


@dataclass
class CircuitConfig:
    """熔斷器配置"""
    failure_threshold: int = 5          # 失敗次數閾值
    recovery_timeout: int = 60           # 恢復超時（秒）
    half_open_max_calls: int = 3         # 半開狀態最大測試次數
    success_threshold: int = 2          # 半開狀態成功次數閾值
    timeout: float = 30.0                # 調用超時（秒）


@dataclass
class CircuitMetrics:
    """熔斷器指標"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    state_changes: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    opened_at: Optional[float] = None
    half_open_calls: int = 0
    half_open_successes: int = 0


class CircuitBreaker:
    """
    熔斷器實現
    
    狀態轉換:
    CLOSED -> OPEN (failure_threshold reached)
    OPEN -> HALF_OPEN (recovery_timeout elapsed)
    HALF_OPEN -> CLOSED (success_threshold calls succeed)
    HALF_OPEN -> OPEN (any call fails)
    """
    
    def __init__(self, name: str = "default", config: Optional[CircuitConfig] = None):
        self.name = name
        self.config = config or CircuitConfig()
        
        # 狀態
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._last_state_change_time = time.time()
        
        # 半開狀態計數
        self._half_open_calls = 0
        self._half_open_successes = 0
        
        # 指標
        self._metrics = CircuitMetrics()
        
        # 回調
        self._callbacks: Dict[CircuitEvent, list] = {
            event: [] for event in CircuitEvent
        }
    
    @property
    def state(self) -> CircuitState:
        """獲取當前狀態（自動狀態轉換）"""
        self._check_state_transition()
        return self._state
    
    @property
    def is_available(self) -> bool:
        """是否可用（可接受調用）"""
        return self.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)
    
    @property
    def metrics(self) -> Dict:
        """獲取指標"""
        return {
            "name": self.name,
            "state": self.state.value,
            "total_calls": self._metrics.total_calls,
            "successful_calls": self._metrics.successful_calls,
            "failed_calls": self._metrics.failed_calls,
            "rejected_calls": self._metrics.rejected_calls,
            "failure_count": self._failure_count,
            "last_failure_time": self._metrics.last_failure_time,
            "last_success_time": self._metrics.last_success_time,
            "uptime_seconds": int(time.time() - self._last_state_change_time)
        }
    
    def call(self, func: Callable, *args, fallback: Any = None, **kwargs) -> Any:
        """
        執行帶熔斷的調用
        
        Args:
            func: 要執行的函數
            *args: 位置參數
            fallback: 熔斷時的返回值
            **kwargs: 關鍵字參數
            
        Returns:
            函數執行結果或 fallback
            
        Raises:
            Exception: 如果函數執行失敗且沒有提供 fallback
        """
        if not self.is_available:
            self._metrics.rejected_calls += 1
            self._emit_event(CircuitEvent.FAILURE, {"reason": "circuit_open"})
            if fallback is not None:
                return fallback
            raise CircuitOpenError(f"Circuit '{self.name}' is OPEN")
        
        self._metrics.total_calls += 1
        start_time = time.time()
        
        try:
            # 檢查超時
            result = func(*args, **kwargs)
            
            # 記錄成功
            elapsed = time.time() - start_time
            self._on_success(elapsed)
            return result
            
        except Exception as e:
            # 記錄失敗
            elapsed = time.time() - start_time
            self._on_failure(elapsed, str(e))
            
            if fallback is not None:
                return fallback
            raise
    
    def _on_success(self, elapsed: float):
        """處理成功調用"""
        self._metrics.successful_calls += 1
        self._metrics.last_success_time = time.time()
        
        if self._state == CircuitState.HALF_OPEN:
            self._half_open_successes += 1
            # 檢查是否達到成功閾值
            if self._half_open_successes >= self.config.success_threshold:
                self._transition_to(CircuitState.CLOSED)
        
        self._emit_event(CircuitEvent.SUCCESS, {"elapsed": elapsed})
    
    def _on_failure(self, elapsed: float, error: str):
        """處理失敗調用"""
        self._metrics.failed_calls += 1
        self._metrics.last_failure_time = time.time()
        self._failure_count += 1
        
        if self._state == CircuitState.HALF_OPEN:
            # 半開狀態下任何失敗都回到 OPEN
            self._transition_to(CircuitState.OPEN)
        elif self._state == CircuitState.CLOSED:
            # 關閉狀態下達到閾值則斷開
            if self._failure_count >= self.config.failure_threshold:
                self._transition_to(CircuitState.OPEN)
        
        self._emit_event(CircuitEvent.FAILURE, {
            "elapsed": elapsed,
            "error": error,
            "failure_count": self._failure_count
        })
    
    def _transition_to(self, new_state: CircuitState):
        """狀態轉換"""
        old_state = self._state
        self._state = new_state
        self._last_state_change_time = time.time()
        self._metrics.state_changes += 1
        
        if new_state == CircuitState.OPEN:
            self._metrics.opened_at = time.time()
            # 重置半開計數
            self._half_open_calls = 0
            self._half_open_successes = 0
        elif new_state == CircuitState.HALF_OPEN:
            # 重置半開計數
            self._half_open_calls = 0
            self._half_open_successes = 0
        elif new_state == CircuitState.CLOSED:
            # 重置失敗計數
            self._failure_count = 0
        
        self._emit_event(CircuitEvent.STATE_CHANGE, {
            "from": old_state.value,
            "to": new_state.value
        })
    
    def _check_state_transition(self):
        """檢查並執行自動狀態轉換"""
        if self._state == CircuitState.OPEN:
            # 檢查是否超過恢復超時
            if self._last_failure_time:
                elapsed = time.time() - self._last_failure_time
                if elapsed >= self.config.recovery_timeout:
                    self._transition_to(CircuitState.HALF_OPEN)
    
    def _emit_event(self, event: CircuitEvent, data: dict):
        """觸發事件回調"""
        for callback in self._callbacks.get(event, []):
            try:
                callback(event, data)
            except Exception:
                pass  # 不讓回調影響主邏輯
    
    def on(self, event: CircuitEvent, callback: Callable):
        """註冊事件回調"""
        self._callbacks[event].append(callback)
    
    def reset(self):
        """手動重置熔斷器"""
        self._transition_to(CircuitState.CLOSED)
        self._metrics = CircuitMetrics()
    
    def force_open(self):
        """強制斷開（用於測試或維護）"""
        self._transition_to(CircuitState.OPEN)
    
    def force_close(self):
        """強制關閉（用於測試或維護）"""
        self._transition_to(CircuitState.CLOSED)
    
    def test_half_open(self) -> bool:
        """
        測試半開狀態（手動觸發測試）
        
        Returns:
            True 如果成功轉換到半開狀態
        """
        if self._state == CircuitState.OPEN:
            self._transition_to(CircuitState.HALF_OPEN)
            return True
        return False


class CircuitOpenError(Exception):
    """熔斷器斷開異常"""
    pass


class CircuitBreakerManager:
    """
    熔斷器管理器
    
    管理多個熔斷器實例
    """
    
    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
    
    def get_or_create(
        self, 
        name: str, 
        config: Optional[CircuitConfig] = None
    ) -> CircuitBreaker:
        """獲取或創建熔斷器"""
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(name=name, config=config)
        return self._breakers[name]
    
    def get(self, name: str) -> Optional[CircuitBreaker]:
        """獲取熔斷器"""
        return self._breakers.get(name)
    
    def remove(self, name: str):
        """移除熔斷器"""
        if name in self._breakers:
            del self._breakers[name]
    
    def get_all_metrics(self) -> Dict:
        """獲取所有熔斷器指標"""
        return {
            name: breaker.metrics 
            for name, breaker in self._breakers.items()
        }
    
    def check_all(self) -> Dict:
        """檢查所有熔斷器狀態"""
        return {
            name: breaker.state.value 
            for name, breaker in self._breakers.items()
        }


# 便捷函數
def create_circuit_breaker(
    name: str = "default",
    failure_threshold: int = 5,
    recovery_timeout: int = 60
) -> CircuitBreaker:
    """創建熔斷器"""
    config = CircuitConfig(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout
    )
    return CircuitBreaker(name=name, config=config)
