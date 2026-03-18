#!/usr/bin/env python3
"""
自動化根因分析模組 v3
參考: playbooks/multi-agent-collaboration-v2.md Phase 4 錯誤處理

功能：
- 錯誤模式匹配
- AI 輔助分析
- 自動化建議生成
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class ErrorSeverity(Enum):
    """錯誤嚴重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """錯誤類別 - 對應 playbook v2 L1-L4"""
    INPUT_ERROR = "L1"      # 輸入錯誤
    TOOL_ERROR = "L2"       # 工具錯誤
    EXECUTION_ERROR = "L3"  # 執行錯誤
    SYSTEM_ERROR = "L4"     # 系統錯誤


@dataclass
class ErrorRecord:
    """錯誤記錄"""
    error_id: str
    timestamp: datetime
    agent_id: str
    session_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    
    # 錯誤信息
    error_type: str
    error_message: str
    stack_trace: str = ""
    
    # 上下文
    prompt: str = ""
    context: List[str] = field(default_factory=list)
    
    # 歷史
    similar_errors: List[str] = field(default_factory=list)


@dataclass
class RootCauseAnalysis:
    """根因分析結果"""
    analysis_id: str
    timestamp: datetime
    error_id: str
    
    # 分析結果
    root_cause: str
    confidence: float  # 0-1
    
    # 分類
    category: ErrorCategory
    severity: ErrorSeverity
    
    # 建議
    recommendations: List[str]
    can_auto_fix: bool
    
    # 類似錯誤
    similar_errors: List[Dict]
    
    # AI 輔助
    ai_analyzed: bool = False
    ai_analysis: str = ""


class PatternMatcher:
    """
    錯誤模式匹配器
    
    基於規則的錯誤分類
    """
    
    # 錯誤模式 → 根因映射
    PATTERNS = {
        # L1 - 輸入錯誤
        r"(?i)invalid.*input": {
            "cause": "輸入參數無效",
            "category": ErrorCategory.INPUT_ERROR,
            "severity": ErrorSeverity.LOW,
            "action": "validate_input"
        },
        r"(?i)missing.*param": {
            "cause": "缺少必要參數",
            "category": ErrorCategory.INPUT_ERROR,
            "severity": ErrorSeverity.LOW,
            "action": "add_parameter"
        },
        r"(?i)invalid.*format": {
            "cause": "數據格式錯誤",
            "category": ErrorCategory.INPUT_ERROR,
            "severity": ErrorSeverity.LOW,
            "action": "fix_format"
        },
        
        # L2 - 工具錯誤
        r"(?i)tool.*not.*found": {
            "cause": "工具不存在",
            "category": ErrorCategory.TOOL_ERROR,
            "severity": ErrorSeverity.MEDIUM,
            "action": "check_tool_availability"
        },
        r"(?i)tool.*timeout": {
            "cause": "工具執行超時",
            "category": ErrorCategory.TOOL_ERROR,
            "severity": ErrorSeverity.MEDIUM,
            "action": "increase_timeout"
        },
        r"(?i)tool.*failed": {
            "cause": "工具執行失敗",
            "category": ErrorCategory.TOOL_ERROR,
            "severity": ErrorSeverity.MEDIUM,
            "action": "retry_or_replace_tool"
        },
        r"(?i)rate.*limit": {
            "cause": "速率限制",
            "category": ErrorCategory.TOOL_ERROR,
            "severity": ErrorSeverity.MEDIUM,
            "action": "wait_and_retry"
        },
        
        # L3 - 執行錯誤
        r"(?i)execution.*error": {
            "cause": "執行時發生錯誤",
            "category": ErrorCategory.EXECUTION_ERROR,
            "severity": ErrorSeverity.HIGH,
            "action": "analyze_and_fix"
        },
        r"(?i)context.*overflow": {
            "cause": "上下文溢出",
            "category": ErrorCategory.EXECUTION_ERROR,
            "severity": ErrorSeverity.HIGH,
            "action": "compress_context"
        },
        r"(?i)memory.*exhausted": {
            "cause": "記憶體耗盡",
            "category": ErrorCategory.EXECUTION_ERROR,
            "severity": ErrorSeverity.HIGH,
            "action": "reduce_scope"
        },
        
        # L4 - 系統錯誤
        r"(?i)system.*error": {
            "cause": "系統錯誤",
            "category": ErrorCategory.SYSTEM_ERROR,
            "severity": ErrorSeverity.CRITICAL,
            "action": "escalate"
        },
        r"(?i)circuit.*break": {
            "cause": "熔斷觸發",
            "category": ErrorCategory.SYSTEM_ERROR,
            "severity": ErrorSeverity.CRITICAL,
            "action": "wait_for_recovery"
        },
        r"(?i)service.*unavailable": {
            "cause": "服務不可用",
            "category": ErrorCategory.SYSTEM_ERROR,
            "severity": ErrorSeverity.CRITICAL,
            "action": "use_backup"
        }
    }
    
    @classmethod
    def match(cls, error_message: str) -> Optional[Dict]:
        """匹配錯誤模式"""
        import re
        
        for pattern, result in cls.PATTERNS.items():
            if re.search(pattern, error_message):
                return result
        
        return None


class RootCauseAnalyzer:
    """
    根因分析器
    
    1. 模式匹配 - 基於規則的快速分類
    2. 上下文分析 - 分析錯誤上下文
    3. AI 輔助 - 如有需要，使用 LLM 分析
    """
    
    def __init__(self):
        self.error_history: List[ErrorRecord] = []
        self.pattern_matcher = PatternMatcher()
        
        # AI 分析配置
        self.ai_enabled = os.getenv("AI_ANALYSIS_ENABLED", "false").lower() == "true"
        self.ai_model = os.getenv("AI_ANALYSIS_MODEL", "claude-3-sonnet")
    
    def analyze(self, error_message: str, agent_id: str = "",
               session_id: str = "", context: List[str] = None,
               use_ai: bool = False) -> RootCauseAnalysis:
        """
        分析錯誤並返回根因
        
        Args:
            error_message: 錯誤訊息
            agent_id: Agent ID
            session_id: Session ID
            context: 上下文（前幾個對話）
            use_ai: 是否使用 AI 輔助分析
        
        Returns:
            RootCauseAnalysis 對象
        """
        context = context or []
        
        # 1. 模式匹配
        match_result = self.pattern_matcher.match(error_message)
        
        if match_result:
            # 找到匹配的模式
            root_cause = match_result["cause"]
            category = match_result["category"]
            severity = match_result["severity"]
            confidence = 0.85  # 模式匹配的置信度
            can_auto_fix = True
        else:
            # 未找到匹配
            root_cause = "未知錯誤"
            category = ErrorCategory.EXECUTION_ERROR
            severity = ErrorSeverity.MEDIUM
            confidence = 0.3
            can_auto_fix = False
        
        # 2. 查找類似錯誤
        similar = self._find_similar_errors(agent_id, error_message)
        
        # 3. 生成建議
        recommendations = self._generate_recommendations(
            root_cause, category, severity, similar
        )
        
        # 4. AI 輔助分析（可選）
        ai_analyzed = False
        ai_analysis = ""
        
        if use_ai or (self.ai_enabled and confidence < 0.7):
            ai_analyzed, ai_analysis = self._ai_analyze(error_message, context)
            if ai_analyzed:
                confidence = max(confidence, 0.8)
                if not recommendations:
                    recommendations = [ai_analysis]
        
        # 構建結果
        analysis = RootCauseAnalysis(
            analysis_id=f"analysis-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            timestamp=datetime.now(),
            error_id=f"error-{len(self.error_history)}",
            root_cause=root_cause,
            confidence=confidence,
            category=category,
            severity=severity,
            recommendations=recommendations,
            can_auto_fix=can_auto_fix,
            similar_errors=similar,
            ai_analyzed=ai_analyzed,
            ai_analysis=ai_analysis
        )
        
        return analysis
    
    def _find_similar_errors(self, agent_id: str, error_message: str) -> List[Dict]:
        """查找類似錯誤"""
        similar = []
        
        for error in self.error_history[-20:]:  # 最近20條
            if error.agent_id == agent_id:
                # 簡單的相似度計算
                common_words = set(error.error_message.lower().split()) & set(error_message.lower().split())
                if len(common_words) >= 2:
                    similar.append({
                        "error_id": error.error_id,
                        "timestamp": error.timestamp.isoformat(),
                        "message": error.error_message[:100],
                        "root_cause": "已記錄"
                    })
        
        return similar[:5]  # 最多5條
    
    def _generate_recommendations(self, root_cause: str, category: ErrorCategory,
                                 severity: ErrorSeverity, similar: List[Dict]) -> List[str]:
        """生成建議"""
        recommendations = []
        
        # 基於類別的建議
        if category == ErrorCategory.INPUT_ERROR:
            recommendations.extend([
                "檢查輸入參數是否正確",
                "增加輸入驗證邏輯",
                "查看 API 文檔確認參數格式"
            ])
        
        elif category == ErrorCategory.TOOL_ERROR:
            recommendations.extend([
                "檢查工具是否可用",
                "增加重試機制",
                "考慮使用替代工具"
            ])
        
        elif category == ErrorCategory.EXECUTION_ERROR:
            recommendations.extend([
                "壓縮上下文減少長度",
                "分段處理任務",
                "檢查程式碼邏輯錯誤"
            ])
        
        elif category == ErrorCategory.SYSTEM_ERROR:
            recommendations.extend([
                "等待系統恢復",
                "啟用熔斷機制",
                "聯繫技術支持"
            ])
        
        # 基於嚴重程度
        if severity == ErrorSeverity.CRITICAL:
            recommendations.append("⚠️ 立即處理 - 影響重大")
        
        # 基於類似錯誤
        if similar:
            recommendations.append(f"歷史上有 {len(similar)} 次類似錯誤，建議徹底解決")
        
        return recommendations
    
    def _ai_analyze(self, error_message: str, context: List[str]) -> tuple:
        """
        AI 輔助分析
        
        這裡只是框架，實際需要調用 LLM API
        """
        if not self.ai_enabled:
            return False, ""
        
        # 模擬 AI 分析
        # 實際應該調用 OpenAI / Claude / Gemini API
        
        prompt = f"""
請分析以下錯誤並找出根本原因：

錯誤訊息：{error_message}

上下文：
{chr(10).join(context[-5:]) if context else "無"}

請返回：
1. 根本原因（簡短）
2. 建議行動
"""
        
        # 這裡應該調用 LLM
        # response = llm.chat(prompt)
        
        # 模擬返回
        ai_analysis = "（AI 分析需要配置 LLM API）"
        
        return True, ai_analysis
    
    def record_error(self, error_record: ErrorRecord):
        """記錄錯誤"""
        self.error_history.append(error_record)
        
        # 限制歷史長度
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-1000:]
    
    def get_error_statistics(self, agent_id: str = None, days: int = 7) -> Dict:
        """錯誤統計"""
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=days)
        
        errors = [e for e in self.error_history if e.timestamp >= cutoff]
        
        if agent_id:
            errors = [e for e in errors if e.agent_id == agent_id]
        
        # 按類別統計
        by_category = defaultdict(int)
        by_severity = defaultdict(int)
        
        for e in errors:
            by_category[e.category.value] += 1
            by_severity[e.severity.value] += 1
        
        return {
            "total_errors": len(errors),
            "by_category": dict(by_category),
            "by_severity": dict(by_severity),
            "most_common_cause": self._get_most_common_cause(errors)
        }
    
    def _get_most_common_cause(self, errors: List[ErrorRecord]) -> str:
        """獲取最常見錯誤原因"""
        causes = defaultdict(int)
        for e in errors:
            match = self.pattern_matcher.match(e.error_message)
            if match:
                causes[match["cause"]] += 1
        
        if causes:
            return max(causes.items(), key=lambda x: x[1])[0]
        return "未知"


# 單例
root_cause_analyzer = RootCauseAnalyzer()


# ============ 使用範例 ============

if __name__ == "__main__":
    print("="*50)
    print("🔍 測試根因分析")
    print("="*50)
    
    # 測試各種錯誤
    test_cases = [
        ("Tool execution timeout after 30s", "dev-agent", ["查詢 API"]),
        ("Invalid input parameter: missing 'from' field", "research-agent", ["查詢參數"]),
        ("Rate limit exceeded, please wait", "pm-agent", ["請求過快"]),
        ("Context overflow: exceeds max tokens", "musk", ["處理大量數據"]),
    ]
    
    for error_msg, agent, ctx in test_cases:
        print(f"\n📝 錯誤: {error_msg}")
        
        # 分析
        analysis = root_cause_analyzer.analyze(
            error_message=error_msg,
            agent_id=agent,
            session_id="test-session",
            context=ctx
        )
        
        print(f"   分類: {analysis.category.value}")
        print(f"   嚴重: {analysis.severity.value}")
        print(f"   根因: {analysis.root_cause}")
        print(f"   置信: {analysis.confidence*100:.0f}%")
        print(f"   自動修復: {'是' if analysis.can_auto_fix else '否'}")
        
        if analysis.recommendations:
            print(f"   建議:")
            for rec in analysis.recommendations[:2]:
                print(f"     • {rec}")
    
    # 錯誤統計
    print("\n" + "="*50)
    print("📊 錯誤統計 (7天)")
    print("="*50)
    stats = root_cause_analyzer.get_error_statistics()
    print(f"  總錯誤數: {stats['total_errors']}")
    print(f"  按類別: {stats['by_category']}")
    print(f"  按嚴重: {stats['by_severity']}")
    
    print("\n" + "="*50)
