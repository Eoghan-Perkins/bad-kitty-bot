#!/usr/bin/env python3
"""
Usage:
  python capture_frame.py --save frame.jpg
  python capture_frame.py --device 1 --width 1920 --height 1080 --save frame.jpg
"""
import argparse
import platform
import sys
import time
import cv2

def open_capture(device_index: int) -> cv2.VideoCapture:
    if platform.system() == "Windows":
        return cv2.VideoCapture(device_index, cv2.CAP_DSHOW)
    return cv2.VideoCapture(device_index)

def main() -> None:
    parser = argparse.ArgumentParser(description="Capture one frame from a webcam and display it.")
    parser.add_argument("--device", type=int, default=0, help="Camera device index (default: 0)")
    parser.add_argument("--width", type=int, default=1280, help="Requested frame width")
    parser.add_argument("--height", type=int, default=720, help="Requested frame height")
    parser.add_argument("--save", type=str, default=None, help="Optional path to save the captured frame (e.g., frame.jpg)")
    args = parser.parse_args()

    cap = open_capture(args.device)
    if not cap.isOpened():
        print(f"Error: could not open camera index {args.device}", file=sys.stderr)
        sys.exit(1)

    # Try to set resolution (some cameras may ignore this)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    # Warm-up: let exposure/white-balance settle
    time.sleep(0.2)
    for _ in range(3):
        cap.read()

    ok, frame = cap.read()
    if not ok or frame is None:
        print("Error: failed to read a frame from the camera.", file=sys.stderr)
        cap.release()
        sys.exit(2)

    if args.save:
        if not cv2.imwrite(args.save, frame):
            print(f"Warning: failed to save image to {args.save}", file=sys.stderr)
        else:
            print(f"Saved frame to {args.save}")

    # Show the frame in a window; press any key to close.
    cv2.imshow("Webcam frame (press any key to close)", frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    cap.release()

if __name__ == "__main__":
    main()
