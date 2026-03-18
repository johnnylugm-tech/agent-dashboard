# AI Agent 監控儀表板 - 功能規格書

> **文件版本**：v1.0  
> **建立日期**：2026-03-17  
> **角色**：PM Agent - 功能設計  
> **狀態**：初版草稿

---

## 📋 總覽

本文件定義 AI Agent 監控儀表板的完整功能規格，基於市場調研與競爭分析結果，聚焦於提供**框架無關、本地部署優先、中小團隊可負擔**的監控解決方案。

---

## 1️⃣ 詳細功能清單

### 1.1 Agent 追蹤 (Agent Tracing) - MVP

| 功能項 | 說明 | 優先級 | 技術複雜度 |
|--------|------|--------|------------|
| **1.1.1 執行路徑視覺化** | 樹狀圖展示 Agent 思考/決策路徑，支援展開/摺疊 | P0 | 高 |
| **1.1.2 對話歷史記錄** | 完整儲存 user/assistant/tool 訊息序列 | P0 | 中 |
| **1.1.3 工具調用日誌** | 記錄每次 tool invocation 的輸入/輸出/耗時 | P0 | 中 |
| **1.1.4 時間軸視圖** | 水平時間軸展示每個步驟的時序與延遲 | P0 | 中 |
| **1.1.5 錯誤堆疊追蹤** | 完整 Error + Stack Trace 記錄與分類 | P1 | 低 |
| **1.1.6 對比檢視** | 比較兩次執行的詳細差異 (diff view) | P2 | 高 |

### 1.2 指標監控 (Metrics) - MVP

| 功能項 | 說明 | 優先級 | 技術複雜度 |
|--------|------|--------|------------|
| **1.2.1 Token 儀表板** | 輸入/輸出/總 Token 即時統計，支援 Provider 維度 | P0 | 低 |
| **1.2.2 延遲追蹤** | TTFT (首響) + Total Latency + Per-step latency | P0 | 低 |
| **1.2.3 成本計算** | 依 Provider 計價規則自動計算 Costs ($) | P0 | 中 |
| **1.2.4 成功率監控** | Request success/failure rate + Error breakdown | P0 | 低 |
| **1.2.5 並發監控** | 活躍 Agent 數量 + Queue depth 即時圖表 | P1 | 中 |
| **1.2.6 自訂指標** | 允許用戶定義 custom metrics 維度 | P2 | 高 |

### 1.3 日誌管理 (Logging) - MVP

| 功能項 | 說明 | 優先級 | 技術複雜度 |
|--------|------|--------|------------|
| **1.3.1 結構化日誌** | JSON 格式日誌，支援巢狀結構與搜尋 | P0 | 低 |
| **1.3.2 日誌搜尋** | 全文搜尋 + 多維度過濾 (level, timestamp, agent) | P0 | 中 |
| **1.3.3 日誌匯出** | 支援 JSON / CSV / LOG 格式下載 | P1 | 低 |
| **1.3.4 保留策略** | 設定日誌保留天數，自動清理過期日誌 | P1 | 中 |

### 1.4 告警系統 (Alerting) - MVP

| 功能項 | 說明 | 優先級 | 技術複雜度 |
|--------|------|--------|------------|
| **1.4.1 閾值告警** | 設定 token/ latency/ error rate 閾值觸發告警 | P0 | 中 |
| **1.4.2 多通道通知** | Slack / Email / Webhook 三種通道 | P0 | 中 |
| **1.4.3 告警歷史** | 完整記錄告警觸發、確認、解決時間線 | P1 | 低 |
| **1.4.4 靜音時段** | 設定維護期間暫停告警 | P1 | 低 |
| **1.4.5 告警升級** | 未確認告警自動升級通知更多人 | P2 | 中 |

---

### 1.5 多 Agent 協調 (Multi-Agent Orchestration) - V1.0

| 功能項 | 說明 | 優先級 | 技術複雜度 |
|--------|------|--------|------------|
| **1.5.1 依賴關係圖** | DAG 圖展示 Agent 間依賴與執行順序 | P1 | 高 |
| **1.5.2 跨 Agent 訊息流** | 追蹤 agent-to-agent 訊息傳遞與內容 | P1 | 高 |
| **1.5.3 流程重播** | 完整重現多 Agent 協調整個流程 | P2 | 高 |

### 1.6 評估與品質 (Evaluation) - V1.0

| 功能項 | 說明 | 優先級 | 技術複雜度 |
|--------|------|--------|------------|
| **1.6.1 品質評分** | 內建評分維度：準確性、完整性、一致性 | P1 | 中 |
| **1.6.2 自訂評估指標** | 用戶定義評估維度與評分邏輯 | P1 | 高 |
| **1.6.3 趨勢儀表板** | 評分時間序列圖表 + 異常標註 | P1 | 中 |
| **1.6.4 回歸追蹤** | 記錄每次變更導致的評分變化 | P2 | 中 |

### 1.7 Prompt 管理 (Prompt Management) - V1.0

| 功能項 | 說明 | 優先級 | 技術複雜度 |
|--------|------|--------|------------|
| **1.7.1 版本歷史** | 自動版本化每次 Prompt 修改 | P1 | 中 |
| **1.7.2 效能對比** | 比較不同 Prompt 版本的輸出品質與成本 | P1 | 中 |
| **1.7.3 A/B Testing** | 流量分配 + 統計顯著性計算 | P2 | 高 |

### 1.8 安全與合規 (Security & Compliance) - V1.0

| 功能項 | 說明 | 優先級 | 技術複雜度 |
|--------|------|--------|------------|
| **1.8.1 RBAC 權限** | Admin / Editor / Viewer 三級權限 | P1 | 中 |
| **1.8.2 資料遮蔽** | 自動遮蔽 PII (email, phone, credit card) | P1 | 中 |
| **1.8.3 審計日誌** | 記錄所有管理操作 (登入、配置變更等) | P1 | 低 |

---

### 1.9 部署選項 (Deployment) - V1.5+

| 功能項 | 說明 | 優先級 | 技術複雜度 |
|--------|------|--------|------------|
| **1.9.1 Docker 部署** | 單一 docker-compose 啟動全部服務 | P1 | 中 |
| **1.9.2 K8s Helm Chart** | 企業級 Kubernetes 部署配置 | P2 | 高 |
| **1.9.3 SaaS 雲端** | 全托管雲服務 (可選) | P2 | 高 |

### 1.10 整合能力 (Integrations) - V1.5+

| 功能項 | 說明 | 優先級 | 技術複雜度 |
|--------|------|--------|------------|
| **1.10.1 OpenTelemetry** | 標準 OTLP 協議接入 | P1 | 中 |
| **1.10.2 Webhook** | 自定義事件觸發外部系統 | P1 | 低 |
| **1.10.3 REST API** | 完整 CRUD API 供第三方整合 | P1 | 中 |
| **1.10.4 LLM Provider** | OpenAI / Anthropic / Google / Azure 原生整合 | P1 | 中 |

### 1.11 儀表板客製化 (Customization) - V1.5+

| 功能項 | 說明 | 優先級 | 技術複雜度 |
|--------|------|--------|------------|
| **1.11.1 自訂 Widget** | 用戶可新增/配置儀表板元件 | P2 | 高 |
| **1.11.2 儀表板範本** | 預設範本：Debug / Ops / Cost 等場景 | P2 | 中 |
| **1.11.3 品牌主題** | 自定義 Logo / 顏色 / CSS | P2 | 低 |

---

## 2️⃣ UI/UX 設計方向

### 2.1 設計原則

| 原則 | 說明 |
|------|------|
| **Operational First** | 面向運維人員，首要目標是快速排查問題 |
| **Information Hierarchy** | 異常 > 警告 > 正常，分層次呈現資訊 |
| **Low Friction** | 3 clicks 內到達任何功能 |
| **Performance** | 儀表板載入 < 2s，大數據集支援虛擬滾動 |

### 2.2 整體 Layout

```
┌─────────────────────────────────────────────────────────┐
│ Header: Logo | Search (Cmd+K) | Notifications | Profile│
├──────────┬──────────────────────────────────────────────┤
│          │                                              │
│ Sidebar  │  Main Content Area                           │
│          │                                              │
│ - Dashboard  │  (可根據上下文切換視圖)                    │
│ - Traces  │                                              │
│ - Metrics │                                              │
│ - Logs    │                                              │
│ - Alerts  │                                              │
│ - Settings│                                              │
│          │                                              │
├──────────┴──────────────────────────────────────────────┤
│ Footer: Status | Version | Support                      │
└─────────────────────────────────────────────────────────┘
```

### 2.3 核心頁面設計

#### 2.3.1 Dashboard 首頁
- **Header**: 4 Key Metrics Cards (Requests, Latency, Cost, Errors)
- **Main**: 即時活動時間軸 (Live Feed)
- **Right Panel**: Active Alerts 列表

#### 2.3.2 Traces 追蹤頁面
- **左側**: 執行列表 (可篩選/搜尋)
- **中央**: 選中執行的詳細視圖 (Tree/Graph)
- **右側**: 屬性面板 (Metadata, Timing, Errors)

#### 2.3.3 Metrics 儀表板
- **支援 Grid 佈局自訂**
- **預設 Widget**: Token Usage, Latency P50/P95/P99, Cost Trend, Error Rate
- **時間範圍選擇器**: 1h / 6h / 24h / 7d / 自訂

#### 2.3.4 Logs 日誌頁面
- **類似 Datadog / Splunk 風格**
- **上半部**: 日誌列表 (虛擬滾動)
- **下半部**: 選中日志詳情 (JSON Viewer)
- **右側欄**: Faceted Filters

#### 2.3.5 Alerts 告警頁面
- **配置表**: 規則列表 + 啟用/停用開關
- **歷史表**: 告警觸發記錄
- **編輯器**: 條件 builder (UI 化的 Threshold Editor)

### 2.4 色彩與主題

| 用途 | 色彩 |
|------|------|
| Primary | `#6366F1` (Indigo) |
| Success | `#10B981` (Emerald) |
| Warning | `#F59E0B` (Amber) |
| Error | `#EF4444` (Red) |
| Background | `#0F172A` (Dark) / `#FFFFFF` (Light) |
| Text Primary | `#F8FAFC` (Dark) / `#1E293B` (Light) |

- **支援 Dark / Light Mode 切換**

### 2.5 交互模式

- **Cmd+K**: 全域快速搜尋 (traces, logs, agents)
- **右鍵選單**: 常用操作捷徑
- **拖拽**: 儀表板 Widget 重新排列
- **懸停提示**: 圖表數據點詳細資訊

---

## 3️⃣ 技術架構建議

### 3.1 系統架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                        Clients                               │
│   (Web Dashboard / API Consumers / Webhooks)                │
└─────────────────────────┬─────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     API Gateway                              │
│              (Authentication / Rate Limiting)                │
└─────────────────────────┬─────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│   Trace API   │  │  Metrics API  │  │  Logs API     │
│   (Ingest)    │  │  (Ingest)     │  │  (Ingest)     │
└───────┬───────┘  └───────┬───────┘  └───────┬───────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Message Queue (RabbitMQ)                  │
└─────────────────────────┬─────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│  Trace Worker │  │ Metrics Worker│  │  Log Worker   │
│  (Processing) │  │ (Aggregating) │  │  (Indexing)   │
└───────┬───────┘  └───────┬───────┘  └───────┬───────┘
        │                 │                 │
        ▼                 ▼                 ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│  PostgreSQL   │  │  TimescaleDB  │  │ Elasticsearch │
│  (Traces)    │  │  (Metrics)    │  │   (Logs)      │
└───────────────┘  └───────────────┘  └───────────────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Frontend (React +                         │
│                   Recharts + TanStack Table)                │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 技術棧選型

| 層級 | 技術選擇 | 理由 |
|------|----------|------|
| **Frontend** | React + TypeScript | 生態豐富，團隊熟悉 |
| **UI Framework** | Tailwind CSS + shadcn/ui | 快速開發，現代審美 |
| **State Management** | Zustand | 輕量，適合儀表板場景 |
| **Charts** | Recharts | React 原生，易客製 |
| **Backend** | Python (FastAPI) | AI 生態主力語言 |
| **DB - Traces** | PostgreSQL + JSONB | 靈活 Schema，結構化查詢 |
| **DB - Metrics** | TimescaleDB | 時序資料優化，PostgreSQL 相容 |
| **DB - Logs** | Elasticsearch 或 SQLite FTS | 日誌搜尋首選 |
| **Cache** | Redis | 熱資料緩存 |
| **Message Queue** | RabbitMQ | 輕量，支援 MQTT |
| **Container** | Docker + Docker Compose | 本地部署優先 |

### 3.3 資料模型 (核心 Schema)

```sql
-- Agents
CREATE TABLE agents (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    version VARCHAR(50),
    provider VARCHAR(50),
    config JSONB,
    created_at TIMESTAMP
);

-- Traces
CREATE TABLE traces (
    id UUID PRIMARY KEY,
    agent_id UUID REFERENCES agents(id),
    session_id VARCHAR(255),
    status VARCHAR(20), -- running, completed, failed
    input JSONB,
    output JSONB,
    tokens_used JSONB,
    cost DECIMAL(10,6),
    duration_ms INT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    metadata JSONB
);

-- Trace Steps
CREATE TABLE trace_steps (
    id UUID PRIMARY KEY,
    trace_id UUID REFERENCES traces(id),
    parent_step_id UUID,
    step_type VARCHAR(30), -- llm, tool, reasoning
    name VARCHAR(255),
    input JSONB,
    output JSONB,
    tokens JSONB,
    duration_ms INT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Metrics (TimescaleDB hypertable)
CREATE TABLE metrics (
    time TIMESTAMPTZ,
    agent_id UUID,
    metric_name VARCHAR(100),
    value DOUBLE PRECISION,
    tags JSONB
);

-- Logs
CREATE TABLE logs (
    id UUID PRIMARY KEY,
    trace_id UUID REFERENCES traces(id),
    level VARCHAR(10),
    message TEXT,
    timestamp TIMESTAMPTZ,
    metadata JSONB
);
```

### 3.4 SDK / 接入方式

提供多語言 SDK 降低接入門檻：

```python
# Python SDK 示例
from agent_dashboard import AgentTracker

tracker = AgentTracker(
    endpoint="http://localhost:8000",
    api_key="your-key"
)

@tracker.trace(agent_name="assistant-v1")
async def run_agent(prompt: str):
    # ... agent logic
    pass
```

---

## 4️⃣ 優先級排序

### 4.1 MVP 範圍 (4-6 週)

| ID | 功能 | 預估工時 | 依賴 |
|----|------|---------|------|
| M1 | 基礎專案結構 + Docker 搭建 | 1 週 | - |
| M2 | Agent 追蹤 - SDK + API + 儲存 | 1.5 週 | M1 |
| M3 | 指標準確收集 (Token/Latency/Cost) | 1 週 | M2 |
| M4 | 日誌系統 (收集 + 儲存 + 搜尋) | 1 週 | M1 |
| M5 | 告警系統 (閾值 + 通知) | 0.5 週 | M3 |

### 4.2 V1.0 範圍 (6-8 週)

| ID | 功能 | 預估工時 | 依賴 |
|----|------|---------|------|
| V1 | 多 Agent 協調視圖 | 2 週 | M2 |
| V2 | 評估系統 (評分 + 趨勢) | 2 週 | M2 |
| V3 | Prompt 版本管理 | 1.5 週 | M2 |
| V4 | RBAC + 審計日誌 | 1.5 週 | M1 |
| V5 | 告警升級 + 靜音時段 | 1 週 | M5 |

### 4.3 V1.5+ 範圍 (8-12 週)

| ID | 功能 | 預估工時 | 依賴 |
|----|------|---------|------|
| E1 | Kubernetes Helm Chart | 2 週 | V1 |
| E2 | OpenTelemetry 整合 | 2 週 | M2 |
| E3 | REST API 完整化 | 2 週 | M2 |
| E4 | 多 Provider 整合 | 2 週 | M3 |
| E5 | 儀表板客製化 | 2 週 | V1 |

---

## 5️⃣ 驗收標準 (MVP)

| 功能 | 驗收條件 |
|------|----------|
| Agent 追蹤 | 能夠完整記錄並回放一次 LLM 呼叫 + 工具調用 |
| 指標準確 | Token/Cost 計算與 Provider 帳單誤差 < 1% |
| 日誌搜尋 | 100k 条日志下全文搜尋響應 < 2s |
| 告警 | 設定延遲 > 5s 告警，可正確觸發 Slack 通知 |
| 本地部署 | `docker-compose up` 後 5 分鐘內可訪問 UI |

---

## 📎 附件

- 市場調研報告：`docs/market-research.md`
- 初步功能清單：`docs/feature-list.md`
- 任務追蹤表：`docs/task-tracking.md`

---

**下一步行動**：
1. ✅ 功能規格確認 → 本文件
2. ⏳ UI/UX 設計稿 → Designer
3. ⏳ 技術架構詳細設計 → Tech Lead
4. ⏳ 資料庫 Schema 實作 → Backend
