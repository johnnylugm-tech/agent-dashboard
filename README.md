# 🤖 AI Agent 監控儀表板

即時監控 AI Agent 運行狀態、錯誤追蹤、效能分析 — 完全本地部署，保護隱私。

[![Python Version](https://img.shields.io/badge/python-3.10+-blue)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## ⚡ 快速安裝

```bash
# Clone
git clone https://github.com/johnnylugm-tech/agent-dashboard.git
cd agent-dashboard

# 安裝依賴
pip install -r requirements.txt

# 運行監控 Dashboard
python skills/monitor/dashboard.py
```

---

## 📦 版本資訊

### v2.0.0 (2026-03-19)

**十點反饋全部實現！**

| 功能 | 狀態 |
|------|------|
| REST API | ✅ |
| OpenClaw 串流 | ✅ |
| Plugin 整合 | ✅ |

---

## 🎬 使用場景

### 場景 1：單一 Agent 監控

```python
from skills.monitor import Monitor

monitor = Monitor()
monitor.start()

# 監控單一 agent
result = monitor.track_agent("musk", task)
print(f"健康狀態: {result['health']}")
```

**輸出：**
```
✅ Agent musk 追蹤完成
   - 任務數: 10
   - 錯誤: 0
   - 健康: 🟢 Healthy
```

---

### 場景 2：多 Agent 協作監控

```python
from skills.monitor.unified_dashboard import unified_dashboard

dashboard = unified_dashboard()

# 註冊 Agent（星型架構）
dashboard.register_agent("musk", "main", parent_id=None)
dashboard.register_agent("pm-agent", "pm", parent_id="musk")
dashboard.register_agent("dev-agent", "dev", parent_id="musk")
dashboard.register_agent("review-agent", "review", parent_id="musk")

# 獲取統一視圖
summary = dashboard.get_summary()
print(f"總 Agent: {summary['total_agents']}")
print(f"運行中: {summary['active_agents']}")
print(f"錯誤: {summary['error_agents']}")
```

**輸出：**
```
📊 統一監控儀表板
   總 Agent: 4
   運行中: 4
   錯誤: 0
   🤖 Agent 狀態:
   🟢 musk (main): 92分
   🟡 pm-agent (pm): 78分
   🟢 dev-agent (dev): 88分
   🟢 review-agent (review): 95分
```

---

### 場景 3：異常警報通知

```python
from skills.monitor.alerts_v2 import alert_manager

# 觸發警報檢查
alerts = alert_manager.check_and_notify(
    metrics={
        "error_rate": 0.25,       # 25% 錯誤率
        "latency_p95": 6500,      # 6.5秒延遲
        "retry_rate": 0.18         # 18% 重試率
    },
    agent_id="dev-agent"
)

# 發送到多渠道
for alert in alerts:
    print(f"🚨 {alert['level']}: {alert['title']}")
```

**輸出：**
```
🚨 CRITICAL: HighErrorRate - 錯誤率 25% > 20%
🚨 WARNING: HighLatency - P95延遲 6.5s > 5s
🚨 WARNING: HighRetryRate - 重試率 18% > 15%
```

---

### 場景 4：健康評分

```python
from skills.monitor.health_score import health_scorer, AgentMetrics
from datetime import datetime

# 構造指標
metrics = AgentMetrics(
    agent_id="dev-agent",
    timestamp=datetime.now(),
    total_requests=100,
    successful_requests=85,
    failed_requests=15,
    latency_p95_ms=3500,
    uptime_seconds=3600,
    downtime_seconds=60
)

# 計算健康分數
result = health_scorer.calculate(metrics)
print(f"健康評分: {result['score']} {result['level']}")
print(f"狀態: {result['status']}")
```

**輸出：**
```
🆔 健康評分: 77.3 🟡
狀態: Warning

📊 分項得分:
  success_rate: 85.0% → 85.0分 (權重 40%)
  error_rate: 15.0% → 85.0分 (權重 30%)
  latency_p95: 3500ms → 40分 (權重 20%)
  availability: 98.4% → 98.4分 (權重 10%)

💡 優化建議:
  • 錯誤率過高 (15.0%)，建議檢查錯誤日誌
  • P95 延遲過高 (3500ms)，建議優化處理速度
```

---

### 場景 5：成本分析

```python
from skills.monitor.cost_tracker import cost_tracker

# 記錄使用
cost_tracker.record(
    agent_id="dev-agent",
    model="gpt-4",
    input_tokens=5000,
    output_tokens=3000,
    duration_ms=5000
)

# 獲取成本報告
report = cost_tracker.generate_report("daily")
print(report)
```

**輸出：**
```
💰 成本分析報告 - daily
總成本: $0.3456

📊 各 Agent 成本:
  • dev-agent: $0.1234 (3 次請求)
  • research-agent: $0.1567 (4 次請求)
  • review-agent: $0.0655 (2 次請求)

📈 7天趨勢: stable (+2.1%)
```

---

### 場景 6：跨對話追蹤

```python
from skills.monitor.journey_tracker import journey_tracker

# 開始旅程
journey_id = journey_tracker.start_journey(
    user_id="johnny",
    session_id="session-001"
)

# 添加步驟
journey_tracker.add_step(
    session_id="session-001",
    agent_id="musk",
    agent_type="main",
    action="task_start",
    input_text="查詢高鐵時刻表"
)

journey_tracker.add_step(
    session_id="session-001",
    agent_id="research-agent",
    agent_type="research",
    action="tool_call",
    input_text="查詢 TDX API"
)

# 分析行為模式
patterns = journey_tracker.analyze_patterns()
print(f"平均時長: {patterns['avg_duration_minutes']} 分鐘")
print(f"常用流程: {patterns['top_flows'][0]['flow']}")
```

**輸出：**
```
📊 行為分析:
  總旅程數: 15
  平均時長: 8.5 分鐘
  平均 Agent 數: 2.3
  常用流程: main → research → dev
```

---

### 場景 7：根因分析

```python
from skills.monitor.root_cause_analysis import root_cause_analyzer

# 分析錯誤
analysis = root_cause_analyzer.analyze(
    error_message="Tool execution timeout after 30s",
    agent_id="dev-agent",
    session_id="session-001",
    context=["查詢API", "處理結果", "返回數據"]
)

print(f"根因: {analysis.root_cause}")
print(f"分類: {analysis.category.value}")
print(f"置信度: {analysis.confidence*100:.0f}%")
print(f"建議: {analysis.recommendations[0]}")
```

**輸出：**
```
🔍 根因分析結果:
   根因: 工具執行超時
   分類: L2 (工具錯誤)
   置信度: 85%
   建議: 增加超時時間或優化工具響應
```

---

### 場景 8：REST API 服務

```bash
# 啟動 API 服務
python skills/monitor/api_simple.py

# 獲取 Agent 列表
curl http://localhost:5001/api/agents

# 註冊新 Agent
curl -X POST http://localhost:5001/api/agents \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "new-agent", "agent_type": "dev"}'

# 觸發警報
curl -X POST http://localhost:5001/api/alerts \
  -H "Content-Type: application/json" \
  -d '{"level": "warning", "message": "High error rate", "agent_id": "dev-agent"}'
```

---

### 場景 9：OpenClaw 整合

```python
from skills.monitor.monitor_hook import monitor_hook
from skills.monitor.openclaw_connector import OpenClawConnector

# 自動嵌入監控
monitor_hook.on_agent_start(
    agent_id="musk",
    session_id="session-001",
    user_id="johnny",
    prompt="查詢天氣"
)

# ... 執行任務 ...

monitor_hook.on_agent_end(
    agent_id="musk",
    session_id="session-001",
    user_id="johnny",
    response="台北天氣：25°C"
)

# OpenClaw 數據串流
connector = OpenClawConnector(gateway_url="http://localhost:3000")
metrics = connector.get_metrics()
print(f"活躍會話: {metrics['active_sessions']}")
```

---

### 場景 10：統一儀表板 + 關係圖

```python
from skills.monitor.unified_dashboard import unified_dashboard

dashboard = unified_dashboard()

# 註冊複雜架構
dashboard.register_agent("musk", "main", parent_id=None)
dashboard.register_agent("pm", "pm", parent_id="musk")
dashboard.register_agent("dev1", "frontend", parent_id="pm")
dashboard.register_agent("dev2", "backend", parent_id="pm")
dashboard.register_agent("review", "review", parent_id="musk")

# 獲取 Agent 關係圖
graph = dashboard.get_agent_relationship()
print("🔗 Agent 關係:")
for edge in graph['edges']:
    print(f"  {edge['from']} → {edge['to']}")

# 獲取趨勢
trend = dashboard.get_trend("1h")
print(f"\n📈 1小時趨勢:")
for point in trend['data'][:3]:
    print(f"  {point['timestamp'][:16]} - {point['requests']} 請求")
```

**輸出：**
```
🔗 Agent 關係:
  musk → pm
  pm → dev1
  pm → dev2
  musk → review

📈 1小時趨勢:
  2026-03-19T13:30 - 45 請求
  2026-03-19T13:35 - 52 請求
  2026-03-19T13:40 - 38 請求
```

---

## 📂 專案結構

```
agent-dashboard/
├── skills/monitor/          # 核心監控模組
│   ├── example.py          # 使用範例
│   ├── dashboard.py        # 即時儀表板
│   ├── alerts.py           # 基礎警報
│   ├── alerts_v2.py       # 多渠道警報
│   ├── health.py           # 健康檢查
│   ├── health_score.py    # 健康評分
│   ├── cost_tracker.py    # 成本分析
│   ├── unified_dashboard.py # 統一儀表板
│   ├── journey_tracker.py # 跨對話追蹤
│   ├── monitor_hook.py    # 自動嵌入
│   ├── root_cause_analysis.py # 根因分析
│   ├── openclaw_connector.py # OpenClaw 串流
│   ├── api_simple.py      # REST API
│   └── PLUGIN.md         # Plugin 配置
└── README.md
```

---

## 🔧 功能矩陣

| 功能 | 基礎版 | 進階版 |
|------|--------|----------|
| 錯誤分類 L1-L4 | ✅ | ✅ |
| 熔斷機制 | ✅ | ✅ |
| 健康檢查 | ✅ | ✅ |
| 多渠道通知 | | ✅ |
| 健康評分 (0-100) | | ✅ |
| Token 成本分析 | | ✅ |
| 統一儀表板 | | ✅ |
| 跨對話追蹤 | | ✅ |
| 自動嵌入 | | ✅ |
| 根因分析 | | ✅ |
| REST API | | ✅ |
| OpenClaw 串流 | | ✅ |

---

## 📄 License

MIT License - 詳見 [LICENSE](LICENSE)

---

Made with 🚀 for AI Builders
