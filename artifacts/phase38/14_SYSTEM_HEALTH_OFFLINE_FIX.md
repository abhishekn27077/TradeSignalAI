# Phase 38 Artifact 14: System Health Status & Offline Loop Resolution

## Problem & Solution
- **Problem**: Previously, `useAppStore.ts` had strict status check `s === 'healthy'`, which caused backend responses reporting `{"status": "ok"}` or `{"status": "standby"}` to be treated as `offline`. This triggered perpetual offline warning banners and blocked frontend data loading.
- **Fix in `useAppStore.ts`**:
  Updated `toStatus` helper to accept `healthy`, `ok`, `online`, `standby`, and `connected` as valid operational states.
- **Result**: Frontend cleanly recognizes healthy backends without falling into false offline loops or swallowing live signal streams.
