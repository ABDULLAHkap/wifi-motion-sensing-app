# Wi-Fi Motion Sensing App

Experimental Android/Flutter project for detecting room activity from changes in an existing Wi-Fi connection, using only an Android phone connected to a Wi-Fi router.

## Project goal

The app will start by reading Wi-Fi measurements exposed by Android, calibrating an empty-room baseline, and estimating motion/no-motion from signal variation. Later phases will add machine-learning experiments for occupancy estimation (for example: 0, 1, 2, 3+ people) where the available measurements are good enough.

> Important: ordinary Android phones and routers usually do not expose full Wi-Fi CSI (Channel State Information). Exact human counting or precise object tracking is therefore not guaranteed. The first phase is a research prototype based on Android-accessible Wi-Fi metrics such as RSSI.

## Planned stack

- Flutter / Dart — mobile UI
- Android / Kotlin — native Wi-Fi sensing bridge
- Python / FastAPI — optional backend and ML API
- NumPy / pandas / scikit-learn — experiments and model training

## Roadmap

1. Flutter dashboard
2. Native Android Wi-Fi measurement bridge
3. Room calibration and motion score
4. Live graph and history
5. Real-device data collection
6. ML motion classifier
7. Experimental occupancy estimation
8. Optional FastAPI cloud backend

## Repository structure

- `mobile/` — Flutter app
- `backend/` — FastAPI service
- `ml/` — training and preprocessing scripts
- `docs/` — architecture and experiment notes
