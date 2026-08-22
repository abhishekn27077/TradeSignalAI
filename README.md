# TradeSignalAI-v3 🚀 (v1.0.0 Release)

**TradeSignalAI-v3** is an enterprise-grade, multi-agent AI quantitative trading platform designed for real-time market signal processing, AI consensus synthesis, risk management, and order execution via MetaTrader 5 (MT5) and TradingView integration.

---

## 🌟 Key Architecture & Features

```
Market Data (MT5 / TradingView)
         │
         ▼
  Strategy Engine ──► Technical Indicators / Signals
         │
         ▼
   AI Consensus ──► Multi-Agent LLM (OmniRoute Gateway)
         │
         ▼
   Risk Engine  ──► Limits, Correlation, Failsafes & Pre-Trade Checks
         │
         ▼
 Execution Engine ──► Smart Order Router (MT5 DEMO/LIVE)
         │
         ▼
  Journal & Memory ──► Vector Database & Analytics Dashboard
```

- **OmniRoute AI Integration**: Uniform routing to OpenAI, Anthropic, Gemini, DeepSeek, and local LLMs without direct API dependencies.
- **Multi-Agent Consensus**: Technical Analyst, Risk Analyst, Sentiment Specialist, Macro Economist, and Consensus Officer synthesize high-probability trade signals.
- **Hardened Execution Engine**: Supports `EXECUTION_MODE=DEMO` and `EXECUTION_MODE=LIVE` configuration toggles (Defaults strictly to DEMO).
- **Pre-Trade Validation & Failsafe System**: Emergency Kill Switch, Max Drawdown Shutdowns, Daily Loss Limits, and Mandatory SL/TP enforcement.
- **Microservice/Docker Architecture**: Containerized stack with FastAPI, PostgreSQL, Redis, and Nginx.

---

## 🛠️ Quickstart

### 1. Environment Setup
Copy `.env` example and configure your variables:
```bash
cp .env.example .env
```

Ensure `EXECUTION_MODE` is set correctly:
```env
EXECUTION_MODE=DEMO
OMNIROUTE_BASE_URL=http://localhost:20128/v1
```

### 2. Launch with Docker Compose (Production)
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

Access services:
- **Web Dashboard**: `http://localhost`
- **FastAPI Documentation**: `http://localhost/docs`
- **Health Check Endpoint**: `http://localhost/api/v1/health`

---

## 📚 Documentation Directory

- 📖 [User Guide](docs/USER_GUIDE.md)
- 🚀 [Deployment Guide](docs/DEPLOYMENT_GUIDE.md)
- 🔧 [Troubleshooting Guide](docs/TROUBLESHOOTING.md)

---

## 🛡️ License & Disclaimer
TradeSignalAI-v3 is provided for educational and quantitative research purposes. Trading financial markets carries substantial risk. Live trading (`EXECUTION_MODE=LIVE`) should only be enabled after rigorous paper testing.
