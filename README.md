# Bad‑Kitty — Cat‑on‑Counter Vision Prototype (Phases 0–1)

A small, humane robot project to discourage cats from walking on kitchen counters.  
**This repo covers Phases 0–1 only:** setup + the vision prototype (detect “cat on countertop” inside a polygon ROI), with snapshots/logging and safety‑minded detection guards (persistence + cooldown). No actuation yet.

---

## Why this exists
- Learn practical robotics & image recognition end‑to‑end.
- Focus on **high precision within a defined ROI** so you don’t punish innocent floor cats or background movement.
- Build a clean, laptop‑first workflow: write code locally, sync to the Raspberry Pi to run.
