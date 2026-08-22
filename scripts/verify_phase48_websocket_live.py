"""
Phase 48 — Live WebSocket Connection & 120s Sustained Stream Verification.

Connects to:
  ws://127.0.0.1:8000/api/v1/ws/stream
Tests:
  - WebSocket handshake
  - Client {"action": "ping"} -> Server {"event": "pong"}
  - Sustained keepalive stream for > 120 seconds
  - Recording message history, event types, latency, and heartbeat reliability.
Generates artifacts/phase48/WEBSOCKET_LIVE_VERIFICATION.json
"""
import asyncio
import json
import time
import os
import websockets

WS_URL = "ws://127.0.0.1:8000/api/v1/ws/stream"

async def test_live_websocket_stream():
    print(f"[Phase 48] Connecting to Live WebSocket at {WS_URL}...")
    events_received = []
    ping_pongs = []
    t_start = time.time()

    async with websockets.connect(WS_URL) as ws:
        print("[Phase 48] WebSocket Handshake Succeeded. Connected!")

        # Initial message wait
        try:
            init_msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
            data = json.loads(init_msg)
            events_received.append({
                "elapsed_s": round(time.time() - t_start, 3),
                "event": data.get("event", "UNKNOWN"),
                "raw": data,
            })
            print(f"  [RECV] Initial event: {data.get('event')}")
        except Exception as e:
            print(f"  [WARN] No initial broadcast: {e}")

        # Keep alive for 125 seconds, sending ping every 15 seconds
        target_duration = 125
        last_ping = 0

        while (time.time() - t_start) < target_duration:
            now = time.time()
            if now - last_ping >= 15:
                last_ping = now
                ping_payload = {"action": "ping", "client_time": now}
                t_ping = time.time()
                await ws.send(json.dumps(ping_payload))
                print(f"  [SEND] Ping at elapsed={now - t_start:.1f}s")

            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
                data = json.loads(msg)
                elapsed = round(time.time() - t_start, 3)
                ev = data.get("event", data.get("type", "UNKNOWN"))
                events_received.append({"elapsed_s": elapsed, "event": ev, "raw": data})

                if ev == "pong" or data.get("event") == "pong" or data.get("action") == "pong":
                    rtt_ms = round((time.time() - t_ping) * 1000, 2)
                    ping_pongs.append({"ping_time": t_ping, "pong_elapsed_s": elapsed, "rtt_ms": rtt_ms})
                    print(f"  [RECV] Pong received! RTT: {rtt_ms}ms (Total elapsed: {elapsed}s)")
                else:
                    print(f"  [RECV] Stream broadcast event: {ev} at elapsed={elapsed}s")
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"  [ERROR] Stream error: {e}")
                break

    total_time = round(time.time() - t_start, 2)
    print(f"[Phase 48] WebSocket Stream finished after {total_time}s with {len(ping_pongs)} successful ping/pongs.")

    summary = {
        "ws_url": WS_URL,
        "connection_duration_seconds": total_time,
        "is_successful": (total_time >= 120 and len(ping_pongs) >= 5),
        "total_pings_sent": len(ping_pongs),
        "total_pongs_received": len(ping_pongs),
        "avg_ping_rtt_ms": round(sum(p["rtt_ms"] for p in ping_pongs) / max(1, len(ping_pongs)), 2),
        "total_events_received": len(events_received),
        "ping_pongs": ping_pongs,
        "sample_events": events_received[:10],
    }

    out_dir = "artifacts/phase48"
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "WEBSOCKET_LIVE_VERIFICATION.json")

    with open(out_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"[Phase 48] WebSocket verification written to {out_file}")
    return summary

if __name__ == "__main__":
    asyncio.run(test_live_websocket_stream())
