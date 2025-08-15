# Bad‑Kitty — Cat‑on‑Counter Vision Prototype

A small, humane robot project to discourage cats from walking on kitchen counters.  
**Current Phase: 0–1:** setup + the vision prototype (detect “cat on countertop” inside a polygon ROI), with snapshots/logging and safety‑minded detection guards (persistence + cooldown). No actuation yet.

---

## Why this exists
- Learn practical robotics & image recognition end‑to‑end.
- Fun with Raspberry Pi
- The cats are driving my girlfriend insane

## Project Phases & Tasks

Phase 0 — Setup
	•	Flash Raspberry Pi OS; enable SSH & camera; set up Python venv.
	•	Mount/aim camera for full counter coverage; create repo.

Phase 1 — Vision Prototype (learning-first)
	•	Install OpenCV + a ready model (YOLO/MobileNet-SSD with cat class).
	•	Display detections; implement countertop ROI masking.
	•	Tune: confidence, NMS, persistence timer (≥0.5–1.0 s), cooldown (≥20–60 s).
	•	Save snapshots on triggers.

Phase 2 — Actuator Prototype
	•	Option A (Servo): choose bottle with light trigger; design bracket + linkage; set PWM endpoints; add mechanical stop.
	•	Option B (Pump): mount pump/reservoir/nozzle; drive with MOSFET/relay + flyback diode; tune burst duration.

Phase 3 — Integration
	•	Power correctly: separate supply for servo/pump; common ground with Pi.
	•	Implement a simple state machine: IDLE → DETECTING → FIRING → COOLDOWN.
	•	Add web UI controls; log events (timestamp, confidence, ROI overlap, action).

Phase 4 — Enclosure & Reliability
	•	Weather/water-aware enclosure, cable glands, drip loops.
	•	Status LED + kill switch; cable management; quick-release for refills.
	•	48-hour soak test; review logs; adjust thresholds/aiming.

Phase 5 — Polish & Extras (optional)
	•	Scheduling (e.g., arm only at night).
	•	Dashboard/notifications with clips.
	•	Analytics: events/day trend; multi-zone support (e.g., stove).
	•	“Warning beep then mist” mode to allow voluntary retreat.
