# SKILL.md - AI Agent Monitor Skill

> Phase 2: 熔斷機制 + 警報通知 + 指標儀表板

---

## 概述

Monitor Skill 為 AI Agent 提供自我監控能力，實現 Reflection Pattern 的核心功能：
- 錯誤分類（L1-L4）
- 結構化日誌
- 健康檢查
- **熔斷機制（Circuit Breaker）**
- **警報通知**
- **指標儀表板**

**設計模式**: Reflection Pattern  
**依賴**: 零依賴（純 Python + 標準庫）

---

## 安裝

```bash
# 複製到專案目錄
cp -r skills/monitor/ ~/openclaw-projects/agent-dashboard/skills/

# 或使用符號連結
ln -s $(pwd)/skills/monitor ~/openclaw-projects/agent-dashboard/skills/monitor
```

---

## 快速開始

```python
from monitor import AgentMonitor

# 初始化監控器
monitor = AgentMonitor(
    agent_id="my-agent",
    log_path="./logs"
)

# 任務開始
task_id = monitor.task_start(task_name="分析數據")

# ... 執行你的任務 ...

# 任務完成
monitor.task_complete(
    task_id=task_id,
    result={"status": "success", "data": [...]}
)

# 健康檢查
health = monitor.health_check()
print(health)

# 獲取儀表板
dashboard = monitor.get_dashboard()
print(dashboard)
```

---

## 錯誤分類（L1-L4）

### 錯誤層級

| 層級 | 類型 | 影響範圍 | 處理方式 |
|------|------|----------|----------|
| **L1** | 輸入錯誤 | 單次請求 | 立即返回 |
| **L2** | 工具錯誤 | 單次任務 | 重試 |
| **L3** | 執行錯誤 | 任務流程 | 降級/上報 |
| **L4** | 系統錯誤 | 整體系統 | 熔斷/報警 |

### 錯誤碼定義

```python
# L1 - 輸入錯誤 (1000-1999)
E1001 = "INVALID_INPUT"      # 輸入無效
E1002 = "MISSING_REQUIRED"   # 缺少必要字段
E1003 = "INPUT_TOO_LARGE"    # 輸入過大
E1004 = "INVALID_FORMAT"     # 格式錯誤

# L2 - 工具錯誤 (2000-2999)
E2001 = "TOOL_NOT_FOUND"     # 工具不存在
E2002 = "TOOL_FAILED"        # 工具執行失敗
E2003 = "TOOL_TIMEOUT"       # 工具超時
E2004 = "TOOL_UNAVAILABLE"   # 工具不可用

# L3 - 執行錯誤 (3000-3999)
E3001 = "EXECUTION_FAILED"   # 執行失敗
E3002 = "MAX_RETRIES_EXCEEDED"  # 超過重試次數
E3003 = "CONTEXT_OVERFLOW"   # 上下文溢出
E3004 = "RESOURCE_EXHAUSTED" # 資源耗盡

# L4 - 系統錯誤 (4000-4999)
E4001 = "SYSTEM_OVERLOAD"    # 系統過載
E4002 = "RATE_LIMIT"         # 速率限制
E4003 = "MAINTENANCE"        # 維護中
E9999 = "UNKNOWN"            # 未知錯誤
```

---

## 熔斷機制（Circuit Breaker）

### 狀態轉換

```
CLOSED ──(失敗次數≥閾值)──► OPEN
   ▲                           │
   │                           │
   │(連續成功≥閾值)       (超時後)
   │                           │
   └──── HALF_OPEN ◄───────────┘
```

### 配置參數

| 參數 | 默認值 | 說明 |
|------|--------|------|
| `failure_threshold` | 5 | 觸發熔斷的失敗次數 |
| `recovery_timeout` | 60秒 | 嘗試恢復的間隔 |
| `half_open_max_calls` | 3 | 半開狀態最大測試次數 |
| `success_threshold` | 2 | 半開狀態成功次數閾值 |
| `timeout` | 30秒 | 調用超時時間 |

### 使用範例

```python
from monitor import CircuitBreaker, CircuitConfig

# 創建熔斷器
config = CircuitConfig(
    failure_threshold=5,
    recovery_timeout=60,
    success_threshold=2
)
cb = CircuitBreaker(name="api-service", config=config)

# 執行受保護的調用
result = cb.call(
    your_api_function,
    fallback={"status": " degraded", "data": None}
)

# 或使用 Manager 管理多個熔斷器
from monitor import CircuitBreakerManager
manager = CircuitBreakerManager()
api_cb = manager.get_or_create("api", config)

# 獲取熔斷器狀態
print(cb.metrics)
# {'state': 'closed', 'total_calls': 10, 'failed_calls': 0, ...}

# 手動測試半開狀態
cb.test_half_open()

# 手動重置
cb.reset()
```

### 狀態說明

| 狀態 | 說明 | 可接受調用 |
|------|------|------------|
| `CLOSED` | 正常關閉 | ✅ 是 |
| `OPEN` | 熔斷中 | ❌ 否 |
| `HALF_OPEN` | 測試恢復 | ✅ 是 |

---

## 警報通知

### 嚴重性分級

| 等級 | 說明 | Emoji |
|------|------|-------|
| `INFO` | 信息 | 🔵 |
| `WARNING` | 警告 | 🟡 |
| `ERROR` | 錯誤 | 🟠 |
| `CRITICAL` | 嚴重 | 🔴 |

### 內置警報規則

```python
# 默認規則
- high_error_rate: 錯誤率 > 10% (ERROR)
- critical_error_rate: 錯誤率 > 30% (CRITICAL)
- slow_response: 響應時間 > 5秒 (WARNING)
- very_slow_response: 響應時間 > 10秒 (ERROR)
- circuit_open: 熔斷器斷開 (CRITICAL)
```

### 使用範例

```python
from monitor import AlertManager, AlertSeverity, AlertSource

# 創建警報管理器
alerts = AlertManager(agent_id="my-agent")

# 添加自定義規則
from monitor import AlertRule
alerts.add_rule(AlertRule(
    name="high_latency",
    source=AlertSource.RESPONSE_TIME,
    condition="gt",
    threshold=3000,
    severity=AlertSeverity.WARNING,
    cooldown_seconds=60
))

# 評估警報條件
triggered = alerts.evaluate(AlertSource.ERROR_RATE, 0.15)
for alert in triggered:
    print(f"{alert.severity.value}: {alert.title}")

# 獲取活動警報
active = alerts.get_active_alerts()
critical = alerts.get_active_alerts(severity=AlertSeverity.CRITICAL)

# 確認/解除警報
alerts.acknowledge(alert_id)
alerts.resolve(alert_id)

# 註冊通知回調
def send_notification(alert):
    print(f"Sending alert: {alert.title}")

alerts.on_notification(send_notification)

# 生成警報報告
from monitor import AlertReporter
reporter = AlertReporter(alerts)
report = reporter.generate_report(format="markdown")
```

---

## 指標儀表板

### Markdown 儀表板

```python
from monitor import Dashboard, MetricsCollector, HealthChecker

# 創建組件
metrics = MetricsCollector()
health = HealthChecker()

# 記錄指標
metrics.record("error_rate", 0.05)
metrics.record("response_time", 1500)

# 創建儀表板
dashboard = Dashboard(
    agent_id="my-agent",
    metrics_collector=metrics,
    health_checker=health
)

# 生成儀表板
print(dashboard.generate())
```

### 輸出示例

```markdown
# Agent 監控儀表板

**Agent**: `my-agent`
**更新時間**: 2026-03-17 21:45:00

### 📊 關鍵指標
- **錯誤率**: 5.0%
- **響應時間**: 1500ms

### 🏥 健康狀態: ✅ healthy
- ✅ error_rate: 0.05
- ✅ avg_response_time: 1500
- ✅ circuit_breaker: closed

### ❌ 錯誤率: 5.0%
```
[████░░░░░] 5.0%
```

### 簡潔模式

```python
print(dashboard.generate_compact())
# ✅ 健康: healthy | ❌ 錯誤: 5.0% | 🚨 警報: 0
```

---

## 完整範例：整合所有功能

```python
from monitor import (
    AgentMonitor,
    AlertSeverity,
    AlertSource
)

# 初始化（包含所有 Phase 2 功能）
monitor = AgentMonitor(
    agent_id="production-agent",
    log_path="./logs",
    thresholds={"error_rate": 0.1},
    circuit_breaker_config={"failure_threshold": 5}
)

# 定義任務
def risky_operation(data):
    # 可能失敗的操作
    import random
    if random.random() < 0.3:
        raise Exception("Random failure")
    return {"result": "success", "data": data}

# 執行任務（帶熔斷保護）
task_id = monitor.task_start(task_name="處理數據")

try:
    # 使用熔斷器執行
    result = monitor.execute_with_circuit(
        risky_operation,
        {"test": "data"},
        fallback={"result": "fallback"}
    )
    
    monitor.task_complete(task_id, result=result)
    
except Exception as e:
    monitor.task_error(task_id, {"message": str(e)})

# 檢查健康狀態
health = monitor.health_check()

# 檢查警報
monitor.check_alerts()
alerts = monitor.get_alerts()

# 生成儀表板
dashboard = monitor.get_dashboard()
print(dashboard)

# 獲取熔斷器狀態
cb_status = monitor.circuit_breaker.metrics
print(f"Circuit: {cb_status['state']}")
```

---

## API 參考

### AgentMonitor

```python
class AgentMonitor:
    def __init__(self, agent_id: str, log_path: str = "./logs", 
                 thresholds: dict = None, circuit_breaker_config: dict = None)
    
    # 任務管理
    def task_start(self, task_name: str, context: dict = None) -> str
    def task_complete(self, task_id: str, result: dict = None)
    def task_error(self, task_id: str, error: dict)
    
    # 熔斷器
    def execute_with_circuit(self, func, *args, fallback=None, **kwargs)
    
    # 健康與指標
    def health_check(self) -> dict
    def get_metrics(self) -> dict
    
    # 警報
    def check_alerts(self)
    def get_alerts(self, severity: str = None) -> list
    
    # 儀表板
    def get_dashboard(self, format: str = "markdown") -> str
    
    # 報告
    def generate_report(self, report_type: str = "hourly") -> dict
```

### CircuitBreaker

```python
class CircuitBreaker:
    def __init__(self, name: str, config: CircuitConfig = None)
    
    @property
    def state(self) -> CircuitState
    @property
    def is_available(self) -> bool
    @property
    def metrics(self) -> dict
    
    def call(self, func: Callable, *args, fallback: Any = None, **kwargs) -> Any
    def reset(self)
    def force_open(self)
    def force_close(self)
    def test_half_open(self) -> bool
    def on(self, event: CircuitEvent, callback: Callable)
```

### AlertManager

```python
class AlertManager:
    def __init__(self, agent_id: str)
    
    def add_rule(self, rule: AlertRule)
    def remove_rule(self, rule_name: str)
    def evaluate(self, source: AlertSource, value: float, metadata: dict = None) -> List[Alert]
    def acknowledge(self, alert_id: str) -> bool
    def resolve(self, alert_id: str) -> bool
    def get_active_alerts(self, severity: AlertSeverity = None) -> List[Alert]
    def on_notification(self, callback: Callable[[Alert], None])
```

### Dashboard

```python
class Dashboard:
    def __init__(self, agent_id: str, metrics_collector: MetricsCollector = None,
                 health_checker = None, circuit_breaker_manager = None, alert_manager = None)
    
    def generate(self, widgets: List[Dict] = None, title: str = "Agent 監控儀表板") -> str
    def generate_compact(self) -> str
```

---

## 輸出檔案

```
skills/monitor/
├── __init__.py              # 導出主要類 (Phase 1 + 2)
├── errors.py                # 錯誤分類
├── logging.py               # 結構化日誌
├── health.py                # 健康檢查
├── reporting.py             # 報告生成
├── circuit_breaker.py       # 熔斷機制 (NEW)
├── alerts.py                # 警報通知 (NEW)
├── dashboard.py             # 指標儀表板 (NEW)
├── models.py                # 數據模型
├── example.py               # 範例
└── SKILL.md                # 本文件
```

---

## 版本

| 版本 | 日期 | 備註 |
|------|------|------|
| 2.0.0 | 2026-03-17 | Phase 2: 熔斷 + 警報 + 儀表板 |
| 1.0.0 | 2026-03-17 | Phase 1: 錯誤分類 + 日誌 + 健康檢查 |

---

## 下一步

- [ ] 自動修復策略
- [ ] 歷史趨勢分析
- [ ] 多實例協調
