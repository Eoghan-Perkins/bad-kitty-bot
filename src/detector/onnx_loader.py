# src/detector/onnx_loader.py
import cv2
import numpy as np
import onnxruntime as ort

class YoloOnnx:
    def __init__(self, onnx_path: str, input_size: int = 640):
        self.input_size = input_size
        self.session = ort.InferenceSession(
            onnx_path,
            providers=['CPUExecutionProvider']
        )
        # assume single input, single output
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

    def _letterbox(self, img, new_size=640):
        h, w = img.shape[:2]
        scale = min(new_size / h, new_size / w)
        nh, nw = int(round(h * scale)), int(round(w * scale))
        resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
        canvas = np.full((new_size, new_size, 3), 114, dtype=np.uint8)
        top = (new_size - nh) // 2
        left = (new_size - nw) // 2
        canvas[top:top+nh, left:left+nw] = resized
        return canvas, scale, left, top

    def infer(self, bgr_img):
        # preprocess
        lb, scale, pad_x, pad_y = self._letterbox(bgr_img, self.input_size)
        rgb = cv2.cvtColor(lb, cv2.COLOR_BGR2RGB)
        x = (rgb.astype(np.float32) / 255.0).transpose(2,0,1)[None]  # NCHW

        # run
        out = self.session.run([self.output_name], {self.input_name: x})[0]

        # If exported with nms=True, shape is (num_dets, 6): x1,y1,x2,y2,score,class
        dets = out if out.ndim == 2 else out[0]
        # map back to original image coords
        # undo padding/scale
        if dets.size == 0:
            return np.empty((0,6), dtype=np.float32)

        dets = dets.copy()
        dets[:, [0,2]] = (dets[:, [0,2]] - pad_x) / scale
        dets[:, [1,3]] = (dets[:, [1,3]] - pad_y) / scale
        return dets  # (N,6)