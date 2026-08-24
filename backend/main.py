from datetime import datetime, timezone

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from motion_analysis import analyze_motion
from storage import init_db, insert_sample, latest_sample, recent_samples

app = FastAPI(
    title="Wi-Fi Motion Sensing API",
    version="0.3.0",
    description="Backend for Wi-Fi sensing samples, room history and live motion analysis.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class WifiSample(BaseModel):
    device_id: str = "android-1"
    room_id: str = "default-room"
    timestamp: str | None = None
    rssi: int = Field(description="Received signal strength in dBm")
    frequency_mhz: int | None = None
    link_speed_mbps: int | None = None
    motion_score: float | None = Field(default=None, ge=0, le=1)
    motion_state: str | None = None


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/")
def root():
    return {
        "project": "wifi-motion-sensing-app",
        "status": "running",
        "phase": "live-motion-analysis",
        "api_version": "0.3.0",
    }


@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}


@app.post("/samples")
def receive_sample(sample: WifiSample):
    payload = sample.model_dump()
    payload["timestamp"] = payload["timestamp"] or datetime.now(timezone.utc).isoformat()
    sample_id = insert_sample(payload)
    return {"accepted": True, "id": sample_id, "sample": payload}


@app.get("/rooms/{room_id}/latest")
def get_latest(room_id: str):
    return {"room_id": room_id, "sample": latest_sample(room_id)}


@app.get("/rooms/{room_id}/history")
def get_history(room_id: str, limit: int = Query(default=120, ge=1, le=1000)):
    samples = recent_samples(room_id, limit)
    return {"room_id": room_id, "count": len(samples), "samples": samples}


@app.get("/rooms/{room_id}/motion")
def get_motion(room_id: str, window: int = Query(default=30, ge=5, le=240)):
    samples = recent_samples(room_id, window)
    analysis = analyze_motion(samples)
    return {"room_id": room_id, "window": window, **analysis}
