"""
結構化日誌模組

標準 JSON 格式輸出，可分析
"""

import json
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path


class LogLevel:
    """日誌級別"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class StructuredLogger:
    """
    結構化日誌記錄器
    
    輸出格式：
    {
        "timestamp": "2026-03-17T12:00:00.000Z",
        "level": "INFO",
        "agent_id": "agent-001",
        "task_id": "task-001",
        "event": "task_start",
        "message": "任務開始執行",
        "context": {},
        "metrics": {}
    }
    """
    
    def __init__(
        self, 
        agent_id: str, 
        log_path: Optional[str] = None,
        console: bool = True,
        color: bool = True
    ):
        self.agent_id = agent_id
        self.console = console
        self.color = color and sys.stdout.isatty()
        
        # 設置日誌路徑
        if log_path:
            self.log_path = Path(log_path)
            self.log_path.mkdir(parents=True, exist_ok=True)
            self._log_file = None
        else:
            self.log_path = None
            self._log_file = None
        
        # 顏色碼
        self._colors = {
            "DEBUG": "\033[36m",    # 青色
            "INFO": "\033[32m",     # 綠色
            "WARNING": "\033[33m",  # 黃色
            "ERROR": "\033[31m",    # 紅色
            "CRITICAL": "\033[35m", # 紫色
            "RESET": "\033[0m"
        }
    
    def _get_log_file(self):
        """獲取日誌文件對象"""
        if self._log_file is None and self.log_path:
            date_str = datetime.utcnow().strftime("%Y-%m-%d")
            filename = f"agent-{self.agent_id}-{date_str}.jsonl"
            self._log_file = open(self.log_path / filename, "a", encoding="utf-8")
        return self._log_file
    
    def _format_entry(
        self, 
        level: str, 
        event: str, 
        message: str,
        task_id: Optional[str] = None,
        context: Optional[Dict] = None,
        metrics: Optional[Dict] = None
    ) -> Dict:
        """格式化日誌條目"""
        return {
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z",
            "level": level,
            "agent_id": self.agent_id,
            "task_id": task_id,
            "event": event,
            "message": message,
            "context": context or {},
            "metrics": metrics or {}
        }
    
    def _write(self, entry: Dict):
        """寫入日誌"""
        # 寫入文件
        log_file = self._get_log_file()
        if log_file:
            log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")
            log_file.flush()
        
        # 輸出到控制台
        if self.console:
            self._write_console(entry)
    
    def _write_console(self, entry: Dict):
        """輸出到控制台"""
        level = entry["level"]
        message = entry["message"]
        
        # 構建輸出字符串
        timestamp = entry["timestamp"][:19]
        task_info = f"[{entry['task_id']}] " if entry.get("task_id") else ""
        
        if self.color:
            color = self._colors.get(level, "")
            reset = self._colors["RESET"]
            output = f"{timestamp} {color}{level:8}{reset} {task_info}{message}"
        else:
            output = f"{timestamp} {level:8} {task_info}{message}"
        
        # 根據級別選擇輸出流
        if level in ["ERROR", "CRITICAL"]:
            print(output, file=sys.stderr)
        else:
            print(output)
    
    def _log(
        self, 
        level: str, 
        event: str, 
        message: str,
        task_id: Optional[str] = None,
        context: Optional[Dict] = None,
        metrics: Optional[Dict] = None
    ):
        """記錄日誌"""
        entry = self._format_entry(level, event, message, task_id, context, metrics)
        self._write(entry)
    
    def _extract_kwargs(self, kwargs: Dict) -> tuple:
        """從kwargs中提取特定參數"""
        task_id = kwargs.pop('task_id', None)
        context = kwargs.pop('context', None)
        metrics = kwargs.pop('metrics', None)
        return task_id, context, metrics
    
    def debug(self, event: str, message: str = "", **kwargs):
        """DEBUG 級別"""
        task_id, context, metrics = self._extract_kwargs(kwargs)
        self._log(LogLevel.DEBUG, event, message or event, task_id=task_id, context=context, metrics=metrics)
    
    def info(self, event: str, message: str = "", **kwargs):
        """INFO 級別"""
        task_id, context, metrics = self._extract_kwargs(kwargs)
        self._log(LogLevel.INFO, event, message or event, task_id=task_id, context=context, metrics=metrics)
    
    def warning(self, event: str, message: str = "", **kwargs):
        """WARNING 級別"""
        task_id, context, metrics = self._extract_kwargs(kwargs)
        self._log(LogLevel.WARNING, event, message or event, task_id=task_id, context=context, metrics=metrics)
    
    def error(self, event: str, message: str = "", **kwargs):
        """ERROR 級別"""
        task_id, context, metrics = self._extract_kwargs(kwargs)
        self._log(LogLevel.ERROR, event, message or event, task_id=task_id, context=context, metrics=metrics)
    
    def critical(self, event: str, message: str = "", **kwargs):
        """CRITICAL 級別"""
        task_id, context, metrics = self._extract_kwargs(kwargs)
        self._log(LogLevel.CRITICAL, event, message or event, task_id=task_id, context=context, metrics=metrics)
    
    # 便捷方法
    
    def task_start(self, task_id: str, task_name: str, **kwargs):
        """記錄任務開始"""
        self.info("task_start", f"Task started: {task_name}", task_id=task_id, **kwargs)
    
    def task_complete(self, task_id: str, duration_ms: int = 0, **kwargs):
        """記錄任務完成"""
        self.info("task_complete", f"Task completed in {duration_ms}ms", 
                  task_id=task_id, metrics={"duration_ms": duration_ms}, **kwargs)
    
    def task_error(self, task_id: str, error: Dict, **kwargs):
        """記錄任務錯誤"""
        self.error("task_error", f"Task failed: {error.get('message', 'Unknown')}", 
                  task_id=task_id, context={"error": error}, **kwargs)
    
    def tool_call(self, tool: str, params: Dict = None, task_id: str = None, **kwargs):
        """記錄工具調用"""
        self.info("tool_call", f"Calling tool: {tool}", 
                  task_id=task_id, context={"tool": tool, "params": params}, **kwargs)
    
    def tool_result(self, tool: str, success: bool, task_id: str = None, **kwargs):
        """記錄工具結果"""
        event = "tool_success" if success else "tool_error"
        message = f"Tool {tool} {'succeeded' if success else 'failed'}"
        self.info(event, message, task_id=task_id, 
                 context={"tool": tool, "success": success}, **kwargs)
    
    def retry(self, attempt: int, max_attempts: int, task_id: str = None, **kwargs):
        """記錄重試"""
        self.warning("retry", f"Retry attempt {attempt}/{max_attempts}", 
                     task_id=task_id, metrics={"attempt": attempt, "max_attempts": max_attempts}, **kwargs)
    
    def close(self):
        """關閉日誌文件"""
        if self._log_file:
            self._log_file.close()
            self._log_file = None


# 便捷函數
def create_logger(agent_id: str, log_path: str = None) -> StructuredLogger:
    """創建日誌記錄器"""
    return StructuredLogger(agent_id=agent_id, log_path=log_path)
