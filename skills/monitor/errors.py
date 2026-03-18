"""
錯誤分類模組

L1-L4 錯誤分類體系
"""

from typing import Dict, Any, Optional
from enum import Enum


class ErrorCode(Enum):
    """錯誤碼定義"""
    # L1 - 輸入錯誤 (1000-1999)
    E1001 = "INVALID_INPUT"       # 輸入無效
    E1002 = "MISSING_REQUIRED"    # 缺少必要字段
    E1003 = "INPUT_TOO_LARGE"     # 輸入過大
    E1004 = "INVALID_FORMAT"      # 格式錯誤
    
    # L2 - 工具錯誤 (2000-2999)
    E2001 = "TOOL_NOT_FOUND"      # 工具不存在
    E2002 = "TOOL_FAILED"         # 工具執行失敗
    E2003 = "TOOL_TIMEOUT"        # 工具超時
    E2004 = "TOOL_UNAVAILABLE"    # 工具不可用
    
    # L3 - 執行錯誤 (3000-3999)
    E3001 = "EXECUTION_FAILED"    # 執行失敗
    E3002 = "MAX_RETRIES_EXCEEDED" # 超過重試次數
    E3003 = "CONTEXT_OVERFLOW"    # 上下文溢出
    E3004 = "RESOURCE_EXHAUSTED"  # 資源耗盡
    
    # L4 - 系統錯誤 (4000-4999)
    E4001 = "SYSTEM_OVERLOAD"     # 系統過載
    E4002 = "RATE_LIMIT"          # 速率限制
    E4003 = "MAINTENANCE"         # 維護中
    E9999 = "UNKNOWN"             # 未知錯誤


# 錯誤碼到層級的映射
ERROR_CODE_LEVEL = {
    # L1
    "E1001": "L1", "E1002": "L1", "E1003": "L1", "E1004": "L1",
    # L2
    "E2001": "L2", "E2002": "L2", "E2003": "L2", "E2004": "L2",
    # L3
    "E3001": "L3", "E3002": "L3", "E3003": "L3", "E3004": "L3",
    # L4
    "E4001": "L4", "E4002": "L4", "E4003": "L4", "E9999": "L4",
}

# 錯誤碼到動作的映射
ERROR_CODE_ACTION = {
    # L1 - 立即返回
    "E1001": "return", "E1002": "return", "E1003": "return", "E1004": "return",
    # L2 - 重試
    "E2001": "return", "E2002": "retry", "E2003": "retry", "E2004": "fallback",
    # L3 - 降級/上報
    "E3001": "degrade", "E3002": "escalate", "E3003": "compress", "E3004": "reduce",
    # L4 - 熔斷/報警
    "E4001": "circuit_break", "E4002": "wait", "E4003": "wait", "E9999": "escalate",
}

# 層級說明
LEVEL_DESCRIPTIONS = {
    "L1": "輸入錯誤 - 單次請求立即返回",
    "L2": "工具錯誤 - 單次任務重試",
    "L3": "執行錯誤 - 任務流程降級或上報",
    "L4": "系統錯誤 - 整體系統熔斷或報警",
}

# 預設重試次數
DEFAULT_MAX_RETRIES = {
    "L1": 0,
    "L2": 3,
    "L3": 1,
    "L4": 0,
}


class ErrorClassifier:
    """錯誤分類器"""
    
    def __init__(self):
        self._error_patterns = self._build_patterns()
    
    def _build_patterns(self) -> Dict:
        """建立錯誤模式匹配規則"""
        return {
            # L1 patterns
            ("invalid", "input"): "E1001",
            ("missing", "required"): "E1002",
            ("too large", "input size"): "E1003",
            ("format", "invalid"): "E1004",
            
            # L2 patterns
            ("tool", "not found"): "E2001",
            ("tool", "failed"): "E2002",
            ("timeout", "tool"): "E2003",
            ("tool", "unavailable"): "E2004",
            
            # L3 patterns
            ("execution", "failed"): "E3001",
            ("max retries", "exceeded"): "E3002",
            ("context", "overflow"): "E3003",
            ("resource", "exhausted"): "E3004",
            
            # L4 patterns
            ("system", "overload"): "E4001",
            ("rate limit", "exceeded"): "E4002",
            ("maintenance", "mode"): "E4003",
        }
    
    def classify(self, error: Dict[str, Any], context: Optional[Dict] = None) -> Dict:
        """
        分類錯誤
        
        Args:
            error: 錯誤信息，應包含 code, message 等字段
            context: 錯誤上下文
        
        Returns:
            分類結果，包含 level, code, message, action, max_retries
        """
        error_code = error.get("code", "E9999")
        error_message = error.get("message", "")
        
        # 如果沒有明確的錯誤碼，嘗試通過模式匹配
        if error_code == "E9999" or not error_code:
            error_code = self._match_pattern(error_message)
        
        # 獲取層級
        level = ERROR_CODE_LEVEL.get(error_code, "L1")
        
        # 獲取建議動作
        action = ERROR_CODE_ACTION.get(error_code, "escalate")
        
        # 獲取最大重試次數
        max_retries = DEFAULT_MAX_RETRIES.get(level, 0)
        
        # 檢查是否可恢復
        recoverable = action in ["retry", "degrade", "compress", "reduce"]
        
        return {
            "level": level,
            "code": error_code,
            "message": error_message or self._get_default_message(error_code),
            "action": action,
            "max_retries": max_retries,
            "recoverable": recoverable,
            "description": LEVEL_DESCRIPTIONS.get(level, ""),
            "context": context or {}
        }
    
    def _match_pattern(self, message: str) -> str:
        """通過模式匹配錯誤碼"""
        message_lower = message.lower()
        
        for patterns, code in self._error_patterns.items():
            if all(p in message_lower for p in patterns):
                return code
        
        return "E9999"
    
    def _get_default_message(self, code: str) -> str:
        """獲取錯誤碼的默認消息"""
        try:
            return ErrorCode[code].name.replace("_", " ").title()
        except KeyError:
            return "Unknown Error"
    
    def get_action(self, level: str) -> str:
        """獲取層級對應的動作"""
        for code, lvl in ERROR_CODE_LEVEL.items():
            if lvl == level:
                return ERROR_CODE_ACTION.get(code, "escalate")
        return "escalate"
    
    def get_level_description(self, level: str) -> str:
        """獲取層級描述"""
        return LEVEL_DESCRIPTIONS.get(level, "")


# 便捷函數
def classify_error(error: Dict, context: Optional[Dict] = None) -> Dict:
    """便捷函數：分類錯誤"""
    classifier = ErrorClassifier()
    return classifier.classify(error, context)
