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

# 或使用範例
python skills/monitor/example.py
```

---

## 📦 版本資訊

### v2.0.0 (2026-03-19)

**十點反饋全部實現！**

| Phase | 功能 | 狀態 |
|--------|------|------|
| Phase 1 | 異常通知 + 健康評分 + 成本分析 | ✅ |
| Phase 2 | 統一儀表板 + 趨勢圖 + 跨對話追蹤 | ✅ |
| Phase 3 | 自動嵌入 + OpenClaw 整合 + 根因分析 | ✅ |

#### 新增功能

- `alerts_v2.py` - 多渠道異常通知（Telegram/Slack/Email/Webhook）
- `health_score.py` - Agent 健康評分（0-100 分）
- `cost_tracker.py` - Token 成本分析
- `unified_dashboard.py` - 統一監控儀表板
- `journey_tracker.py` - 跨對話追蹤
- `monitor_hook.py` - 自動嵌入對話流程
- `root_cause_analysis.py` - 自動化根因分析

#### 錯誤分類（L1-L4）

| 等級 | 類型 | 處理方式 |
|------|------|----------|
| L1 | 輸入錯誤 | 立即返回 |
| L2 | 工具錯誤 | 重試 |
| L3 | 執行錯誤 | 降級/上報 |
| L4 | 系統錯誤 | 熔斷/警報 |

---

## 🎬 快速開始

### 基礎範例

```bash
python skills/monitor/example.py
```

輸出：
```
==================================================
Example 1: Basic Usage
==================================================
2026-03-18T04:55:30 INFO [71383639] task_start
Task started: 71383639
2026-03-18T04:55:30 INFO [71383639] task_complete
Task completed!
Health: healthy
```

### 健康評分

```python
from skills.monitor.health_score import health_scorer, AgentMetrics
from datetime import datetime

metrics = AgentMetrics(
    agent_id="test-agent",
    timestamp=datetime.now(),
    total_requests=100,
    successful_requests=85,
    failed_requests=15,
    latency_p95_ms=3500
)

result = health_scorer.calculate(metrics)
print(f"健康評分: {result['score']} {result['level']}")
# 輸出: 健康評分: 77.3 🟡
```

### 異常通知

```python
from skills.monitor.alerts_v2 import alert_manager

alerts = alert_manager.check_and_notify(
    metrics={"error_rate": 0.25, "latency_p95": 6.5},
    agent_id="test-agent"
)
```

---

## 📂 專案結構

```
agent-dashboard/
├── skills/monitor/          # 核心監控模組
│   ├── example.py          # 使用範例
│   ├── dashboard.py        # 即時儀表板
│   ├── alerts.py           # 基礎警報
│   ├── alerts_v2.py        # 多渠道警報 (NEW)
│   ├── health.py           # 健康檢查
│   ├── health_score.py     # 健康評分 (NEW)
│   ├── cost_tracker.py     # 成本分析 (NEW)
│   ├── errors.py           # 錯誤分類
│   ├── circuit_breaker.py # 熔斷機制
│   ├── logging.py          # 日誌收集
│   ├── unified_dashboard.py # 統一儀表板 (NEW)
│   ├── journey_tracker.py  # 跨對話追蹤 (NEW)
│   ├── monitor_hook.py    # 自動嵌入 (NEW)
│   └── root_cause_analysis.py # 根因分析 (NEW)
├── docs/                   # 技術文檔
├── V2_PLAN.md             # 開發規劃
├── FEEDBACK.md            # 用戶反饋
├── PHASE3_PROPOSAL.md    # Phase 3 提案
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

---

## 📖 使用場景

### 場景 1：單一 Agent 監控

```python
from skills.monitor import Monitor

monitor = Monitor()
monitor.start()
# 監控單一 agent
```

### 場景 2：多 Agent 協作監控

```python
from skills.monitor.unified_dashboard import unified_dashboard

dashboard = unified_dashboard()
dashboard.register_agent("musk", "main")
dashboard.register_agent("dev-agent", "dev", parent_id="musk")
print(dashboard.get_summary())
```

### 場景 3：錯誤根因分析

```python
from skills.monitor.root_cause_analysis import root_cause_analyzer

analysis = root_cause_analyzer.analyze(
    error_message="Tool execution timeout after 30s",
    agent_id="dev-agent"
)
print(f"根因: {analysis.root_cause}")
print(f"建議: {analysis.recommendations}")
```

---

## 🌍 OpenClaw 整合

### Webhook 模式

```python
from skills.monitor.monitor_hook import monitor_hook

# 自動追蹤每次對話
monitor_hook.on_agent_start(agent_id, session_id, user_id, prompt)
# ... 執行任務 ...
monitor_hook.on_agent_end(agent_id, session_id, user_id, response)
```

### Plugin 模式

參考 `monitor_hook.py` 中的 `OpenClawIntegration` 類別。

---

## 📄 License

MIT License - 詳見 [LICENSE](LICENSE)

---

## 🙏 致謝

- 參考 [playbooks/multi-agent-collaboration-v2.md](playbooks/multi-agent-collaboration-v2.md)
- 用戶反饋持續優化

---

Made with 🚀 for AI Builders
