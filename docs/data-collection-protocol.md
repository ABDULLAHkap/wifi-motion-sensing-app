# Real-room data collection protocol

This project must validate what the current phone/router can actually distinguish before enabling person-count claims.

## Fixed setup

- Keep the router in one location.
- Keep the sensing phone fixed in one position and orientation.
- Keep the same Wi-Fi band/channel during a session when possible.
- Calibrate before each experiment group.
- Record at least 3 separate runs per condition; 5+ is preferred.
- Each run should be at least 2 minutes initially.

## Motion labels

1. `EMPTY`: no person moving in the test area.
2. `PERSON_STILL`: one person present and intentionally still.
3. `PERSON_WALKING`: one person follows a repeated walking path.
4. `OBJECT_MOVING`: move a defined object/door/chair while documenting exactly what changed.

Do not mix conditions during these first baseline recordings.

## Occupancy experiments

Only after the motion baseline is collected, create separate occupancy recordings with a new `occupancy` field:

- `0`
- `1`
- `2`
- `3+`

For each occupancy class, collect multiple independent runs and vary positions carefully. Keep experiment files separate so train/test splitting can be done by experiment rather than randomly mixing adjacent samples.

## Mixed activity experiments

After basic occupancy validation, test controlled combinations such as:

- 1 person still
- 1 person walking
- 2 people still
- 1 still + 1 walking
- 2 walking
- 3+ mixed activity

These are research labels. The app must not show them as reliable live predictions unless held-out experiments demonstrate useful accuracy.

## What to record

Each row should include at least:

- timestamp
- label or occupancy class
- RSSI (dBm)
- frequency (MHz)
- link speed (Mbps)
- experiment/run identifier
- optional room/device notes

## Acceptance rule

A model should only be integrated into the user-facing app after evaluation on independent experiment runs. Report confusion matrices and per-class precision/recall. If classes cannot be separated reliably, keep the result experimental rather than forcing an exact person count.
