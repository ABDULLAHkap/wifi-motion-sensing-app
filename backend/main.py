from datetime import datetime, timezone

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(
    title="Wi-Fi Motion Sensing API",
    version="0.1.0",
    description="Experimental backend for Wi-Fi signal measurements and motion scoring.",
)


class WifiSample(BaseModel):
    rssi: int = Field(description="Received signal strength in dBm")
    frequency_mhz: int | None = None
    link_speed_mbps: int | None = None


@app.get("/")
def root():
    return {
        "project": "wifi-motion-sensing-app",
        "status": "running",
        "phase": "prototype",
    }


@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}


@app.post("/samples")
def receive_sample(sample: WifiSample):
    # Persistence and ML inference will be added after real-device data collection.
    return {"accepted": True, "sample": sample.model_dump()}
