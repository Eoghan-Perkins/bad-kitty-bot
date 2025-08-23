import time
import pathlib
import cv2
import numpy as np
import yaml
import sys
from src.tools.monitor_pi import get_cpu_temp

def fourcc_to_str(v):
    try:
        v = int(v)
        return "".join([chr((v >> (8*i)) & 0xFF) for i in range(4)])
    except Exception:
        return "????"


def main():
    # Our helpers
    from src.detector.onnx_loader import YoloOnnx
    from src.detector.postprocess import filter_cats

    # ---------- Config loading ----------
    CONF = yaml.safe_load(open('src/configs/thresholds.yaml', 'r'))
    DEV  = yaml.safe_load(open('src/configs/device.yaml', 'r'))

    CONFIDENCE_THR      = float(CONF.get('confidence_threshold', 0.55))
    PERSISTENCE_TIME_S  = float(CONF.get('persistence_time_s', 0.7))

    # Toggle this off on headless Pi if GUI is a hassle
    SHOW_PREVIEW = True

    # ---------- Setup ----------
    events_dir = pathlib.Path('data/events')
    events_dir.mkdir(parents=True, exist_ok=True)

    # Open camera
    if sys.platform == "darwin":  # macOS
        CAP_BACKEND = cv2.CAP_AVFOUNDATION
    else:
        # Linux Pi later can use V4L2; for now fall back to CAP_ANY
        CAP_BACKEND = cv2.CAP_ANY

    cam_index = int(DEV.get("camera_index", 0))
    cap = cv2.VideoCapture(cam_index, CAP_BACKEND)

    # On macOS, setting width/height/fps is often advisory (may be ignored)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  DEV.get("width", 1280))
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, DEV.get("height", 720))
    cap.set(cv2.CAP_PROP_FPS,          DEV.get("fps", 30))

    print(f"""camera: {cap.get(cv2.CAP_PROP_FRAME_WIDTH)}x{cap.get(cv2.CAP_PROP_FRAME_HEIGHT)}, FPS:{cap.get(cv2.CAP_PROP_FPS)}, fourcc: {fourcc_to_str(cap.get(cv2.CAP_PROP_FOURCC))}""")

    if not cap.isOpened():
        raise RuntimeError(
            f"Could not open camera index {cam_index} with backend {CAP_BACKEND}. "
            "Try a different index (0/1/2), check permissions, or unplug/replug the webcam."
    )
    model = YoloOnnx('src/models/yolov8n.onnx', input_size=640)

    # Persistence state
    cat_active_since = None  # when we first saw a cat
    last_print = time.time()
    frames = 0

    print("Pipeline started. Press 'q' in the preview window (if enabled) or Ctrl+C in the terminal to stop.")

    try:
        while True:
            t0 = time.time()
            ok, frame = cap.read()
            print(f'CPU Temp: {get_cpu_temp()}')
            
            if not ok:
                # Camera hiccup; skip this loop
                continue

            # Inference
            dets = model.infer(frame)                  # (N,6) [x1,y1,x2,y2,score,cls]
            dets = filter_cats(dets, CONFIDENCE_THR)   # keep only class==cat & score>=thr

            # Did we see any cat this frame?
            saw_cat = dets.shape[0] > 0

            now = time.time()
            if saw_cat:
                # start or continue the persistence window
                if cat_active_since is None:
                    cat_active_since = now

                elapsed = now - cat_active_since
                if elapsed >= PERSISTENCE_TIME_S:
                    # Trigger event (Phase-1 = snapshot only)
                    ts = time.strftime('%Y%m%d-%H%M%S')
                    out_path = events_dir / f'event_{ts}.jpg'
                    cv2.imwrite(str(out_path), frame)
                    print(f"[EVENT] Cat persisted {elapsed:.2f}s — saved {out_path.name}")
                    # reset so we won’t immediately trigger again
                    cat_active_since = None
            else:
                # no cat this frame -> reset persistence
                cat_active_since = None

            # Optional preview for debugging
            if SHOW_PREVIEW:
                # Draw boxes for any detections we kept
                for (x1, y1, x2, y2, score, cls_) in dets:
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                    cv2.putText(frame, f"cat {score:.2f}", (int(x1), int(y1) - 6),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)

                cv2.imshow('bad-kitty: preview (no ROI yet)', frame)
                # Press q to quit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            # FPS print every ~2 seconds
            frames += 1
            if now - last_print >= 2.0:
                fps = frames / (now - last_print)
                print(f"FPS: {fps:.1f} | dets: {len(dets)}")
                frames = 0
                last_print = now

            # Small sleep to prevent 100% CPU if needed (tune later)
            # time.sleep(0.001)

    except KeyboardInterrupt:
        print("Stopping...")

    finally:
        cap.release()
        if SHOW_PREVIEW:
            cv2.destroyAllWindows()

if __name__ == "__main__":
    main()