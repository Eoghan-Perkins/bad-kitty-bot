# src/vision/pipeline.py
import time, cv2, json, pathlib
import numpy as np
import yaml
from detector.onnx_loader import YoloOnnx
from detector.postprocess import filter_cats
from vision.roi import bbox_roi_overlap  # you implement
from collections import deque

CONF = yaml.safe_load(open('configs/thresholds.yaml'))
DEV  = yaml.safe_load(open('configs/device.yaml'))
ROI_POLY = json.load(open('configs/roi.json'))  # [[x,y], ...]

cap = cv2.VideoCapture(DEV['camera_index'], cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,  DEV['width'])
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, DEV['height'])
cap.set(cv2.CAP_PROP_FPS, DEV['fps'])

model = YoloOnnx('models/yolov8n.onnx', input_size=640)

persist_window_s = CONF['persistence_time_s']
window = deque()  # store timestamps where cat-in-ROI observed

events_dir = pathlib.Path('data/events'); events_dir.mkdir(parents=True, exist_ok=True)

while True:
    ok, frame = cap.read()
    if not ok: continue
    t0 = time.time()

    dets = model.infer(frame)                       # (N,6)
    dets = filter_cats(dets, CONF['confidence_threshold'])

    in_roi = False
    for (x1,y1,x2,y2,score,cls) in dets:
        overlap = bbox_roi_overlap((x1,y1,x2,y2), ROI_POLY)
        if overlap >= CONF['min_roi_overlap']:
            in_roi = True
            break

    now = time.time()
    # Update persistence window
    window.append(now) if in_roi else None
    # Drop old entries
    while window and (now - window[0]) > persist_window_s:
        window.popleft()

    valid_event = len(window) > 0 and (window[-1] - window[0]) >= persist_window_s
    if valid_event:
        # save snapshot
        ts = time.strftime('%Y%m%d-%H%M%S')
        cv2.imwrite(str(events_dir / f'event_{ts}.jpg'), frame)
        window.clear()  # prevent immediate re-trigger; cooldown handled in Phase 2

    # (Optional) debug preview
    # cv2.imshow('preview', frame); 
    # if cv2.waitKey(1) == 27: break