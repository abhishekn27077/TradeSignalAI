# TradeSignalAI-v3 — Troubleshooting Guide

This guide details diagnostics and solutions for common operational issues.

---

## Common Issues & Diagnostics

### 1. Startup Validation Fails (Database Connection Error)
**Symptom**: Application fails to start with log: `Critical startup validation failed! Database or essential component is unreachable.`
**Cause**: PostgreSQL container is starting up or DATABASE_URL credentials are incorrect.
**Solution**:
- Check database container health: `docker-compose -f docker-compose.prod.yml ps db`
- Verify `DATABASE_URL` format in `.env`.

### 2. OmniRoute Gateway Offline
**Symptom**: AI Consensus fails or outputs warnings: `OmniRoute gateway unreachable or standby.`
**Cause**: OmniRoute service is not running or network URL is misconfigured.
**Solution**:
- Test OmniRoute health: `curl http://localhost:20128/v1/health`
- Ensure `OMNIROUTE_BASE_URL` matches your deployed gateway address.

### 3. Trades Rejected with "Emergency Kill Switch is ACTIVE"
**Symptom**: All trade proposals published by Strategy Engine are rejected.
**Cause**: Emergency Kill Switch, Max Drawdown limit, or Daily Loss limit was triggered.
**Solution**:
- Check status endpoint: `GET /api/v1/status`
- Reset kill switch via API or Dashboard after investigating root cause: `POST /api/v1/failsafe/reset`

---

## Log Analysis Commands

View rolling JSON logs:
```bash
tail -f logs/app.log | jq .
```
