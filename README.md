# 🤖 AI Agent 監控儀表板

即時監控 AI Agent 運行狀態、錯誤追蹤、效能分析 — 完全本地部署，保護隱私。

[![Python Version](https://img.shields.io/badge/python-3.10+-blue)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## ⚡ 快速安裝

```bash
# Clone 後直接使用
cd agent-dashboard/skills/monitor

# 運行監控 Dashboard
python dashboard.py

# 或使用範例
python example.py
```

## 🎬 Demo

### 文字範例輸出

```
==================================================
Example 1: Basic Usage
==================================================
2026-03-18T04:55:30 INFO     [71383639] task_start
Task started: 71383639
2026-03-18T04:55:30 INFO     [71383639] task_complete
Task completed!
Health: healthy

==================================================
Example 2: Error Classification
==================================================
Error: E1001  Level: L1  Action: return   Description: 輸入錯誤
Error: E2003  Level: L2  Action: retry    Description: 工具錯誤
Error: E3001  Level: L3  Action: degrade  Description: 執行錯誤
Error: E4001  Level: L4  Action: circuit_break  Description: 系統錯誤
```

### 本地運行

```bash
python skills/monitor/example.py
```

## 📂 專案結構

```
agent-dashboard/
├── skills/monitor/           # 核心監控模組
│   ├── dashboard.py         # 即時儀表板
│   ├── alerts.py            # 告警系統
│   ├── health.py            # 健康檢查
│   ├── logging.py           # 日誌收集
│   ├── circuit_breaker.py   # 熔斷機制
│   └── SKILL.md             # Skill 定義
├── docs/                    # 技術文檔
└── README.md
```

## 🚀 功能特性

- ✅ **即時監控** - 追蹤 Agent 每次調用的回應時間、Token 消耗
- ✅ **錯誤追蹤** - 自動分類錯誤類型，異常即時告警
- ✅ **Circuit Breaker** - 防止級聯故障
- ✅ **本地部署** - 資料留在本地，無需雲端
- ✅ **靈活告警** - Email、Slack、Webhook 自定義

## 📄 參考文檔

- [Skill 說明](./skills/monitor/SKILL.md)
- [功能清單](./docs/feature-list.md)
- [功能規格](./docs/functional-spec.md)

## 🤝 授權

MIT License - 詳見 [LICENSE](LICENSE)

---

<p align="center">Made with 🚀 for AI Builders</p>
