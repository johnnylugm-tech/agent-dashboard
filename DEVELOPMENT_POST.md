# 🤖 AI Agent 監控儀表板開發心得：從 0 到 v3 的演進之路

> 如何用 Python打造一個適合中小團隊的本地部署 Agent 監控系統

---

## 🔥 為什麼要做 Agent 監控？

市面上不缺監控工具 — Datadog、New Relic、LangSmith...但它們都有同一個問題：**貴**、**雲端**、**框架綁定**。

我們的需求很簡單：
1. **本地部署** — 數據不離開服務器
2. **框架無關** — 不管你用 LangChain、AutoGen 還是自研
3. **中小團隊可負擔** — 免費開源

所以我們自己動手做了。

---

## 🛠️ 技術架構

### v1:  MVP（最簡可行產品）

```
├── alerts.py        # 基礎告警
├── health.py       # 健康檢查
├── logging.py      # 日誌收集
└── circuit_breaker.py  # 熔斷機制
```

**核心功能**：
- 錯誤分類 L1-L4
- 熔斷機制
- 基礎健康檢查

**產出時間**：1 週

---

### v2: 監控增強

```
├── alerts_v2.py           # 多渠道通知
├── health_score.py        # 健康評分 (0-100)
├── cost_tracker.py        # Token 成本分析
├── unified_dashboard.py  # 統一儀表板
├── journey_tracker.py     # 跨對話追蹤
├── monitor_hook.py       # 自動嵌入
├── root_cause_analysis.py # 根因分析
├── api_simple.py          # REST API
└── openclaw_connector.py  # OpenClaw 串流
```

**核心功能**：
- 健康評分算法
- Token 成本追蹤
- 多 Agent 協調監控
- 根因分析 (L1-L4 分類)
- REST API

**產出時間**：2 週

---

### v3: 完整版 MVP

```
├── skills/monitor_v3/     # v3 新增
│   ├── storage.py         # SQLite 持久化
│   ├── log_search.py      # 日誌搜尋引擎
│   ├── trace_visualizer.py # 執行路徑視覺化
│   ├── silence_scheduler.py # 靜音時段
│   └── rbac.py           # RBAC 權限控制
└── ...
```

**核心功能**：
- SQLite 持久化存儲
- 全文檢索日誌
- 樹狀執行路徑可視化
- Mermaid 圖導出
- 週期性靜音時段
- Admin/Editor/Viewer 三級權限

**產出時間**：3 週

---

## 🧠 核心算法

### 健康評分 (Health Score)

```python
def calculate_health(metrics: AgentMetrics) -> float:
    # 權重配置
    weights = {
        "success_rate": 0.40,  # 40%
        "error_rate": 0.30,    # 30%
        "latency": 0.20,       # 20%
        "availability": 0.10   # 10%
    }
    
    # 計算各維度分數
    scores = {
        "success_rate": metrics.success_rate * 100,
        "error_rate": (1 - metrics.error_rate) * 100,
        "latency": max(0, 100 - metrics.latency_p95 / 100),
        "availability": metrics.availability
    }
    
    # 加權求和
    health = sum(scores[k] * weights[k] for k in weights)
    return round(health, 1)
```

### 錯誤分類 (L1-L4)

| 等級 | 類型 | 處理方式 |
|------|------|----------|
| L1 | 輸入錯誤 | 立即返回，不重試 |
| L2 | 工具錯誤 | 重試 3 次後降級 |
| L3 | 執行錯誤 | 上報，觸發告警 |
| L4 | 系統錯誤 | 熔斷，停止調用 |

---

## 📊 數據模型

### SQLite Schema

```sql
-- Logs 表
CREATE TABLE logs (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    level TEXT,
    message TEXT,
    agent_id TEXT,
    session_id TEXT,
    trace_id TEXT,
    metadata JSON
);

-- Traces 表
CREATE TABLE traces (
    trace_id TEXT,
    session_id TEXT,
    agent_id TEXT,
    parent_id TEXT,
    step_type TEXT,  -- llm, tool, reasoning
    input_data JSON,
    output_data JSON,
    tokens INTEGER,
    cost REAL,
    duration_ms INTEGER,
    status TEXT
);

-- Alerts 表
CREATE TABLE alerts (
    level TEXT,
    title TEXT,
    message TEXT,
    agent_id TEXT,
    status TEXT  -- triggered, acknowledged, resolved
);
```

---

## 🎯 關鍵設計決策

### 1. 為什麼不用 Elasticsearch？

**理由**：
- 資源佔用高（需要 2GB+ RAM）
- 部署複雜
- 我們的數據量不需要

**解決方案**：SQLite FTS5 全文檢索 + 定期歸檔

### 2. 為什麼不用 Kafka？

**理由**：
- 單機部署麻煩
- 維護成本高

**解決方案**：內存緩存 + SQLite 直接寫入

### 3. 如何實現框架無關？

**關鍵**：只監控「接口」，不侵入框架

```python
# 只需要在調用時包一層
@track_agent("musk")
async def run_agent(prompt: str):
    result = await agent.generate(prompt)
    return result
```

---

## 📈 性能優化

### 批量寫入

```python
# 不是每條日誌都寫入
BATCH_SIZE = 100
BUFFER = []

def log(message):
    BUFFER.append(message)
    if len(BUFFER) >= BATCH_SIZE:
        flush()

def flush():
    cursor.executemany("INSERT...", BUFFER)
    BUFFER.clear()
```

### 索引策略

```sql
CREATE INDEX idx_logs_timestamp ON logs(timestamp);
CREATE INDEX idx_logs_level ON logs(level);
CREATE INDEX idx_logs_agent ON logs(agent_id);
CREATE INDEX idx_logs_session ON logs(session_id);
```

---

## 🔄 開發流程

### 每週迭代

| 週 | 主題 | 產出 |
|----|------|------|
| W1 | 基礎監控 | alerts, health |
| W2 | 統一視圖 | dashboard, journey |
| W3 | 深度整合 | root cause, API |
| W4 | 持久化 | SQLite, search |
| W5 | 企業級 | RBAC, silence |

### Code Review 清單

- [ ] 單元測試覆蓋 > 70%
- [ ] 錯誤處理完整
- [ ] 文檔更新
- [ ] 向後兼容

---

## 💰 成本對比

| 方案 | 月費 | 數據保留 |
|------|------|----------|
| LangSmith | $150/月 | 30 天 |
| Datadog | $200/月 | 15 天 |
| **我們的方案** | **$0** | **無限** |

---

## 🚀 未來規劃

- [ ] React 前端 UI
- [ ] Docker 一鍵部署
- [ ] Prometheus 整合
- [ ] 多租戶支持

---

## 📚 資源

- **GitHub**: https://github.com/johnnylugm-tech/agent-dashboard
- **v3**: https://github.com/johnnylugm-tech/agent-dashboard-v3

---

*如果你也有類似需求，歡迎 Fork + Star ⭐*

**Author**: Johnny Lu  
**Date**: 2026-03-19
