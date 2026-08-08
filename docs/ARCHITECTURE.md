# Architecture

## Data flow

```text
Wi-Fi router
    ↕ radio link
Android phone
    ↓ Android Wi-Fi APIs
Native sensing layer (Kotlin)
    ↓ Method/Event Channel
Flutter app
    ├─ calibration
    ├─ motion score
    ├─ live dashboard
    └─ sample collection
          ↓ optional
      FastAPI backend
          ↓
      ML experiments/model
```

## Phase 1: phone-only prototype

The first implementation should use measurements Android exposes without external hardware. The main signal is RSSI sampled over time. Motion can change multipath propagation and therefore produce fluctuations in the received signal.

The algorithm will compare a rolling window with an empty-room calibration baseline. Features can include RSSI standard deviation, mean absolute difference, range, and short-window energy. A threshold-based detector should be built before ML so real measurements can be inspected and labelled.

## Important limitation

RSSI is a single coarse signal-strength measurement. It does not contain the rich per-subcarrier amplitude/phase information normally used by research-grade Wi-Fi sensing systems. Full CSI access depends on Wi-Fi chipset, driver, firmware, router and OS support and is generally unavailable to a normal Flutter application on an unmodified Android phone.

For that reason:

- motion/no-motion is the realistic first target;
- occupancy count is experimental and requires labelled data;
- identifying exact object positions or reliably distinguishing humans from arbitrary moving objects cannot be promised from ordinary RSSI alone.

## Future CSI path

If supported hardware/firmware is later allowed, a CSI collector can replace the RSSI sensing layer while the Flutter UI, backend, data model and ML pipeline remain largely reusable.
