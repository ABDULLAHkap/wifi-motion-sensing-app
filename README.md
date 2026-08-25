# Wi-Fi Motion Sensing App

Experimental Android/Flutter project for detecting room activity from changes in an existing Wi-Fi connection, using an Android phone connected to a Wi-Fi router.

## Current capabilities

- Flutter Android dashboard with live RSSI, frequency and link-speed readings
- Native Kotlin Wi-Fi bridge and Android runtime permissions
- Rolling room calibration and on-device motion score
- Live signal history and motion/no-motion indication
- Labelled CSV experiment recorder for `EMPTY`, `PERSON_STILL`, `PERSON_WALKING`, and `OBJECT_MOVING`
- FastAPI sample/history endpoints and optional server-side motion analysis
- Random-forest motion-model trainer using recording-grouped train/test splits
- Measured model evaluation: accuracy, balanced accuracy, precision, recall, F1, ROC-AUC and confusion matrix
- Experimental occupancy trainer for 0 / 1 / 2 / 3+ people with held-out accuracy reporting
- Dataset-readiness checker to prevent misleading model evaluation
- GitHub Actions checks for Flutter APK builds, Flutter tests, backend tests and ML imports

> Important: ordinary Android phones and routers usually do not expose full Wi-Fi CSI (Channel State Information). Motion detection can be evaluated from RSSI variation, but exact human counting and precise object identification cannot be guaranteed. Occupancy estimation remains experimental and must be validated on real recordings.

## Stack

- Flutter / Dart — mobile UI and local detector
- Android / Kotlin — native Wi-Fi sensing bridge
- Python / FastAPI — optional backend
- NumPy / pandas / scikit-learn — model training and evaluation

## Real-device workflow

1. Install the Android APK and keep the phone/router positions fixed.
2. Let the room settle and tap **Calibrate Room**.
3. Record at least three separate sessions of at least 60 samples for each label: `EMPTY`, `PERSON_STILL`, `PERSON_WALKING`, `OBJECT_MOVING`.
4. Copy the CSV files into `ml/data/`.
5. Run `python ml/check_dataset_readiness.py`.
6. When it reports `READY`, run `python ml/train_motion_model.py`.
7. Read measured results from `ml/models/motion_model_metrics.json`.
8. Repeat recordings in different room positions/times to test generalization rather than relying on one environment.

## Accuracy policy

The project does not publish an invented accuracy percentage. Accuracy is generated only from held-out recording files, so windows from the same recording are not mixed between training and testing. The motion report contains:

- `accuracy`
- `balanced_accuracy`
- `precision_motion`
- `recall_motion`
- `f1_motion`
- `roc_auc`
- `confusion_matrix`

The occupancy model similarly reports accuracy, balanced accuracy, macro F1 and a multiclass confusion matrix.

## Repository structure

- `mobile/` — Flutter/Android application
- `backend/` — FastAPI service and server-side signal analysis
- `ml/` — dataset checks, feature extraction, training and evaluation
- `docs/` — architecture and experiment notes

## Remaining hardware-dependent validation

The software pipeline is implemented, but a real phone/router environment is still required to produce genuine accuracy numbers. Until those recordings exist, no responsible model can claim a specific real-world accuracy. Exact occupancy estimation should be treated as experimental because RSSI alone provides much less information than CSI-capable hardware.
