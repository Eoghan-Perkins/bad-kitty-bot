import sys, cv2, numpy as np
from src.detector.onnx_loader import YoloOnnx


def main():
    model = YoloOnnx('src/models/yolov8n.onnx', input_size=640)

    img_path = sys.argv[1] if len(sys.argv) > 1 else 'src/demos/cat1.jpg'
    img = cv2.imread(img_path)
    assert img is not None, f"Could not read image: {img_path}"

    dets = model.infer(img)
    print("Raw detections (first 5):\n", dets[:5])

    # Draw and save for a quick visual check
    vis = img.copy()
    for (x1,y1,x2,y2,score,cls) in dets:
        if score < 0.4:        # quick low threshold for a peek
            continue
        color = (0,255,0)
        cv2.rectangle(vis, (int(x1),int(y1)), (int(x2),int(y2)), color, 2)
        cv2.putText(vis, f"{int(cls)}:{score:.2f}", (int(x1), int(y1)-6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

    cv2.imwrite('out.jpg', vis)
    print("Wrote out.jpg")

if __name__ == "__main__":
    main()