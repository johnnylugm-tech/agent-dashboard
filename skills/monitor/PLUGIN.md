# OpenClaw Plugin 配置

## Agent Monitor Plugin

```yaml
name: agent-monitor
version: 2.0.0
description: AI Agent 監控儀表板 - 即時監控錯誤、效能、成本
author: johnnylugm-tech
license: MIT

# Hook 配置
hooks:
  - name: on_agent_start
    enabled: true
    config:
      track_metrics: true
      
  - name: on_agent_end
    enabled: true
    config:
      calculate_cost: true
      
  - name: on_error
    enabled: true
    config:
      trigger_alert: true
      severity_threshold: warning

# 配置
config:
  # 數據存储
  storage:
    type: memory  # memory / sqlite / postgres
    path: ./data/monitor.db
    
  # 警報配置
  alerts:
    enabled: true
    channels:
      - telegram
      - slack
    thresholds:
      error_rate: 0.2
      latency_p95: 5000
      retry_rate: 0.15
      
  # 成本追蹤
  cost:
    enabled: true
    models:
      - gpt-4
      - claude-3
      - gemini
      
  # API 配置
  api:
    enabled: true
    port: 5001
    cors: true

# 權限
permissions:
  - sessions:read
  - agents:read
  - messages:read
  
# 依賴
dependencies:
  - python >= 3.10
  - flask >= 2.0
```

---

## 安裝方式

### 1. 手動安裝

```bash
# Clone 到 OpenClaw plugins 目錄
cp -r agent-monitor ~/.openclaw/plugins/

# 重啟 OpenClaw
openclaw restart
```

### 2. 開發模式

```bash
# 連結到 OpenClaw
ln -s $(pwd)/agent-monitor ~/.openclaw/plugins/

# 查看日誌
tail -f ~/.openclaw/logs/agent-monitor.log
```

---

## 使用方式

### CLI 命令

```bash
# 查看監控狀態
openclaw monitor status

# 查看警報
openclaw monitor alerts

# 查看成本
openclaw monitor cost

# 手動觸發掃描
openclaw monitor scan
```

### API 端點

```bash
# 健康檢查
curl http://localhost:5001/api/health

# 監控摘要
curl http://localhost:5001/api/metrics/summary

# 警報列表
curl http://localhost:5001/api/alerts
```

---

## 數據流向

```
OpenClaw Gateway
       ↓
  [Plugin Hooks]
       ↓
  Agent Monitor
       ↓
   ┌────┴────┐
   ↓          ↓
API Server   Alerts
   ↓
 Grafana / Dashboard
```

---

## 環境變數

| 變數 | 預設 | 說明 |
|------|------|------|
| OPENCLAW_GATEWAY_URL | http://localhost:3000 | Gateway 地址 |
| OPENCLAW_API_KEY | - | API Key |
| MONITOR_PORT | 5001 | API 服務端口 |
| MONITOR_STORAGE | memory | 存儲類型 |

---

## 監控指標

| 指標 | 說明 |
|------|------|
| total_sessions | 總會話數 |
| active_sessions | 活躍會話 |
| error_rate | 錯誤率 |
| avg_latency | 平均延遲 |
| total_cost | 總成本 |

---

## 警報規則

| 級別 | 觸發條件 |
|------|----------|
| Critical | 錯誤率 > 20% |
| Warning | P95 延遲 > 5s |
| Info | 重試率 > 15% |
